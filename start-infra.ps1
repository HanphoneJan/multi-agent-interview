#!/usr/bin/env pwsh

param(
    [switch]$Stop,
    [switch]$Restart,
    [switch]$Logs,
    [switch]$Health,
    [string]$Service = ""
)

$ErrorActionPreference = "Stop"
$ComposeFile = "docker-compose.infra.yml"

function Write-Info($msg) { Write-Host $msg -ForegroundColor Cyan }
function Write-Success($msg) { Write-Host $msg -ForegroundColor Green }
function Write-Warn($msg) { Write-Host $msg -ForegroundColor Yellow }
function Write-ErrorLine($msg) { Write-Host $msg -ForegroundColor Red }

function Test-DockerRunning {
    try {
        docker ps > $null 2>&1
        return $true
    } catch {
        return $false
    }
}

function Start-Infrastructure {
    Write-Info "Starting infrastructure services..."
    Write-Info "Services: PostgreSQL (15432), Redis (16379), Milvus (29530)"

    docker compose -f $ComposeFile up -d
    if ($LASTEXITCODE -ne 0) {
        Write-ErrorLine "Failed to start services"
        exit 1
    }

    Write-Success "Infrastructure services started."
    Write-Info ""
    Write-Info "Connection info:"
    Write-Info "  PostgreSQL: localhost:15432 (user: postgres, db: ai_interview)"
    Write-Info "  Redis:      localhost:16379"
    Write-Info "  Milvus:     localhost:29530"
    Write-Info ""
    Write-Info "Check status: docker compose -f $ComposeFile ps"
}

function Stop-Infrastructure {
    Write-Info "Stopping infrastructure services..."
    docker compose -f $ComposeFile down
    Write-Success "Infrastructure services stopped."
}

function Show-Logs {
    if ($Service) {
        docker compose -f $ComposeFile logs -f $Service
    } else {
        docker compose -f $ComposeFile logs -f
    }
}

function Show-Status {
    Write-Info "Infrastructure services status:"
    docker compose -f $ComposeFile ps
}

function Test-ContainerHealth {
    param(
        [string]$ContainerName
    )

    $status = docker inspect --format='{{.State.Status}}' $ContainerName 2>$null
    if (-not $status) {
        Write-ErrorLine "  $ContainerName: container not found"
        return $false
    }

    $health = docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' $ContainerName 2>$null
    if ($status -ne "running") {
        Write-ErrorLine "  $ContainerName: $status"
        return $false
    }

    if ($health -eq "healthy" -or $health -eq "none") {
        Write-Success "  $ContainerName: running ($health)"
        return $true
    }

    Write-Warn "  $ContainerName: running ($health)"
    return $false
}

function Test-Port {
    param(
        [string]$Name,
        [int]$Port
    )

    $connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue
    if ($connection.TcpTestSucceeded) {
        Write-Success "  $Name: localhost:$Port reachable"
        return $true
    }

    Write-ErrorLine "  $Name: localhost:$Port unreachable"
    return $false
}

function Show-Health {
    Write-Info "Infrastructure health check"

    $allHealthy = $true

    Write-Info ""
    Write-Info "[1/3] Container status"
    $containers = @(
        "milvus-etcd",
        "milvus-minio",
        "milvus-standalone",
        "postgres-ai-interview",
        "redis-ai-interview"
    )
    foreach ($container in $containers) {
        if (-not (Test-ContainerHealth -ContainerName $container)) {
            $allHealthy = $false
        }
    }

    Write-Info ""
    Write-Info "[2/3] Port reachability"
    foreach ($portCheck in @(
        @{ Name = "PostgreSQL"; Port = 15432 },
        @{ Name = "Redis"; Port = 16379 },
        @{ Name = "Milvus"; Port = 29530 }
    )) {
        if (-not (Test-Port -Name $portCheck.Name -Port $portCheck.Port)) {
            $allHealthy = $false
        }
    }

    Write-Info ""
    Write-Info "[3/3] Resource usage"
    docker stats --no-stream --format "table {{.Name}}`t{{.CPUPerc}}`t{{.MemUsage}}`t{{.MemPerc}}"

    Write-Info ""
    if ($allHealthy) {
        Write-Success "All infrastructure services look healthy."
    } else {
        Write-Warn "Some infrastructure checks need attention."
        Write-Info "Logs: docker compose -f $ComposeFile logs -f [service]"
    }
}

if (-not (Test-DockerRunning)) {
    Write-ErrorLine "Docker is not running. Please start Docker first."
    exit 1
}

if ($Health) {
    Show-Health
    exit 0
}

if ($Logs) {
    Show-Logs
    exit 0
}

if ($Stop) {
    Stop-Infrastructure
    exit 0
}

if ($Restart) {
    Stop-Infrastructure
    Start-Infrastructure
    exit 0
}

Start-Infrastructure
Show-Status
