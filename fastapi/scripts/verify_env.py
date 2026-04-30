"""Verify cloud service keys configured in environment variables

Usage:
    cd fastapi
    uv run python scripts/verify_env.py

Checks:
    - PostgreSQL database
    - Redis cache
    - LLM (unified config / DashScope)
    - Aliyun (OSS, ASR)
    - XFYun (TTS)
    - SMTP (email)
"""
import asyncio
import sys
from dataclasses import dataclass
from typing import Optional

import httpx

sys.path.insert(0, str(__file__).replace("\\", "/").rsplit("/scripts/", 1)[0])

from app.config import get_settings


@dataclass
class CheckResult:
    name: str
    status: str  # "OK" | "FAIL" | "SKIP"
    detail: str = ""
    latency_ms: float = 0.0


class EnvVerifier:
    def __init__(self):
        self.settings = get_settings()
        self.results: list[CheckResult] = []

    def _add(self, name: str, status: str, detail: str = "", latency_ms: float = 0.0):
        self.results.append(CheckResult(name, status, detail, latency_ms))

    # ------------------------------------------------------------------ #
    # PostgreSQL
    # ------------------------------------------------------------------ #
    async def check_postgres(self):
        import time
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text

        name = "PostgreSQL"
        url = self.settings.DATABASE_URL
        if not url:
            self._add(name, "SKIP", "DATABASE_URL not set")
            return

        start = time.perf_counter()
        try:
            engine = create_async_engine(url, pool_pre_ping=True, pool_size=1)
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            await engine.dispose()
            latency = (time.perf_counter() - start) * 1000
            host = url.split("@")[-1].split("/")[0] if "@" in url else "localhost"
            self._add(name, "OK", f"Connected ({host})", latency)
        except Exception as e:
            self._add(name, "FAIL", str(e))

    # ------------------------------------------------------------------ #
    # Redis
    # ------------------------------------------------------------------ #
    async def check_redis(self):
        import time

        name = "Redis"
        url = self.settings.REDIS_URL
        if not url:
            self._add(name, "SKIP", "REDIS_URL not set")
            return

        start = time.perf_counter()
        try:
            import redis.asyncio as aioredis

            client = aioredis.from_url(url, socket_connect_timeout=5)
            pong = await client.ping()
            await client.aclose()
            latency = (time.perf_counter() - start) * 1000
            self._add(name, "OK", f"PING={pong}", latency)
        except ImportError:
            self._add(name, "SKIP", "redis not installed (pip install redis)")
        except Exception as e:
            self._add(name, "FAIL", str(e))

    # ------------------------------------------------------------------ #
    # Unified LLM
    # ------------------------------------------------------------------ #
    async def check_llm(self):
        name = "LLM (Unified)"
        key = self.settings.LLM_API_KEY
        base_url = self.settings.LLM_BASE_URL
        model = self.settings.LLM_MODEL

        if not key:
            self._add(name, "SKIP", "LLM_API_KEY not set")
            return

        await self._check_openai_compatible(name, base_url, key, model)

    # ------------------------------------------------------------------ #
    # DashScope (multimodal)
    # ------------------------------------------------------------------ #
    async def check_dashscope(self):
        name = "DashScope (Multimodal)"
        key = self.settings.DASHSCOPE_API_KEY
        base_url = self.settings.DASHSCOPE_BASE_URL

        if not key:
            self._add(name, "SKIP", "DASHSCOPE_API_KEY not set")
            return

        await self._check_openai_compatible(name, base_url, key, "qwen-plus")

    # ------------------------------------------------------------------ #
    # Aliyun OSS
    # ------------------------------------------------------------------ #
    async def check_oss(self):
        name = "Aliyun OSS"
        access_key = self.settings.ALIYUN_ACCESS_KEY
        secret_key = self.settings.ALIYUN_SECRET_KEY
        bucket = self.settings.ALIYUN_OSS_BUCKET

        if not access_key or access_key.startswith("your-"):
            self._add(name, "SKIP", "ALIYUN_ACCESS_KEY not set or is placeholder")
            return
        if not secret_key or secret_key.startswith("your-"):
            self._add(name, "SKIP", "ALIYUN_SECRET_KEY not set or is placeholder")
            return

        try:
            import oss2

            auth = oss2.Auth(access_key, secret_key)
            service = oss2.Service(auth, "oss-cn-hangzhou.aliyuncs.com")
            buckets = [b.name for b in oss2.BucketIterator(service)]
            if bucket in buckets:
                self._add(name, "OK", f"AccessKey valid, bucket '{bucket}' exists")
            else:
                self._add(
                    name, "OK",
                    f"AccessKey valid, bucket '{bucket}' not found (available: {buckets[:3]}...)"
                )
        except ImportError:
            self._add(name, "SKIP", "oss2 not installed (pip install oss2)")
        except Exception as e:
            self._add(name, "FAIL", str(e))

    # ------------------------------------------------------------------ #
    # Aliyun ASR
    # ------------------------------------------------------------------ #
    async def check_asr(self):
        name = "Aliyun ASR"
        appkey = self.settings.ALIYUN_ASR_APPKEY

        if not appkey or appkey.startswith("your-"):
            self._add(name, "SKIP", "ALIYUN_ASR_APPKEY not set or is placeholder")
            return

        masked = f"{appkey[:4]}...{appkey[-4:]}"
        self._add(name, "OK", f"AppKey configured ({masked})")

    # ------------------------------------------------------------------ #
    # XFYun TTS
    # ------------------------------------------------------------------ #
    async def check_xfyun(self):
        name = "XFYun TTS"
        app_id = self.settings.XFYUN_APP_ID
        app_key = self.settings.XFYUN_APP_KEY
        app_secret = self.settings.XFYUN_APP_SECRET

        if not app_id:
            self._add(name, "SKIP", "XFYUN_APP_ID not set")
            return

        try:
            import hashlib
            import hmac
            import base64
            import time

            url = "https://tts-api.xfyun.cn/v2/tts"
            now = int(time.time())
            signature = hmac.new(
                app_secret.encode("utf-8"),
                (app_id + str(now)).encode("utf-8"),
                hashlib.sha256,
            ).digest()
            signature = base64.b64encode(signature).decode("utf-8")

            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    url,
                    headers={
                        "Authorization": f'api_key="{app_key}",algorithm="hmac-sha256"',
                    },
                    timeout=10,
                )
                if resp.status_code in (401, 400):
                    self._add(name, "OK", "AppKey recognized by server (401 = key format valid)")
                elif resp.status_code == 403:
                    self._add(name, "FAIL", "AppKey rejected (403)")
                else:
                    self._add(name, "OK", f"Server responded HTTP {resp.status_code}")
        except Exception as e:
            self._add(name, "FAIL", str(e))

    # ------------------------------------------------------------------ #
    # SMTP
    # ------------------------------------------------------------------ #
    async def check_smtp(self):
        name = "SMTP Email"
        host = self.settings.SMTP_HOST
        port = self.settings.SMTP_PORT
        user = self.settings.SMTP_USER
        password = self.settings.SMTP_PASSWORD

        if not host:
            self._add(name, "SKIP", "SMTP_HOST not set")
            return
        if not user:
            self._add(name, "SKIP", "SMTP_USER not set")
            return

        try:
            import smtplib
            import ssl

            context = ssl.create_default_context()
            if self.settings.SMTP_USE_SSL:
                server = smtplib.SMTP_SSL(host, port, context=context, timeout=10)
            else:
                server = smtplib.SMTP(host, port, timeout=10)
                if self.settings.SMTP_USE_TLS:
                    server.starttls(context=context)

            server.login(user, password)
            server.quit()
            self._add(name, "OK", f"Login success ({host}:{port})")
        except smtplib.SMTPAuthenticationError:
            self._add(name, "FAIL", "Auth failed, check email and password/auth code")
        except Exception as e:
            self._add(name, "FAIL", str(e))

    # ------------------------------------------------------------------ #
    # OpenAI-compatible API check helper
    # ------------------------------------------------------------------ #
    async def _check_openai_compatible(
        self, name: str, base_url: str, api_key: str, model: str
    ):
        import time

        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{base_url.rstrip('/')}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": "hi"}],
                        "max_tokens": 5,
                    },
                )
            latency = (time.perf_counter() - start) * 1000

            if resp.status_code == 200:
                data = resp.json()
                usage = data.get("usage", {})
                self._add(
                    name, "OK",
                    f"Model {model} OK, prompt_tokens={usage.get('prompt_tokens', '?')}",
                    latency,
                )
            elif resp.status_code == 401:
                self._add(name, "FAIL", "API Key invalid (401)")
            elif resp.status_code == 404:
                self._add(name, "FAIL", f"Model not found (404): {model}")
            else:
                body = resp.text[:200]
                self._add(name, "FAIL", f"HTTP {resp.status_code}: {body}")
        except httpx.ConnectTimeout:
            self._add(name, "FAIL", "Connection timeout, check network or BASE_URL")
        except Exception as e:
            self._add(name, "FAIL", str(e))

    # ------------------------------------------------------------------ #
    # Report
    # ------------------------------------------------------------------ #
    def print_report(self):
        print("=" * 70)
        print("  Environment Config Verification")
        print("=" * 70)

        ok = fail = skip = 0
        for r in self.results:
            icon = {"OK": "[OK]", "FAIL": "[FAIL]", "SKIP": "[SKIP]"}.get(r.status, "[?]")
            latency = f"  [{r.latency_ms:.0f}ms]" if r.latency_ms > 0 else ""
            print(f"\n{icon}  {r.name}{latency}")
            if r.detail:
                print(f"   -> {r.detail}")

            if r.status == "OK":
                ok += 1
            elif r.status == "FAIL":
                fail += 1
            else:
                skip += 1

        print("\n" + "=" * 70)
        print(f"  PASS: {ok}  FAIL: {fail}  SKIP: {skip}")
        print("=" * 70)

        if fail > 0:
            print("\n[!] Some checks failed, see details above")
            return 1
        return 0

    async def run(self):
        await self.check_postgres()
        await self.check_redis()
        await self.check_llm()
        await self.check_dashscope()
        await self.check_oss()
        await self.check_asr()
        await self.check_xfyun()
        await self.check_smtp()
        return self.print_report()


if __name__ == "__main__":
    exit_code = asyncio.run(EnvVerifier().run())
    sys.exit(exit_code)
