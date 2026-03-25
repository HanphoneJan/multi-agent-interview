"""Learning API endpoints"""
import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.learning import (
    ResourceCreate,
    ResourceUpdate,
    ResourceResponse,
    UserResourceInteractionCreate,
)
from app.schemas.common import MessageResponse, PaginatedResponse
from app.services.learning_service import (
    get_resource_by_id,
    get_resources,
    create_resource,
    update_resource,
    delete_resource,
    create_interaction,
    get_user_interactions,
    increment_resource_views,
)
from app.core.exceptions import NotFoundError, ValidationError
from app.core.constants import ResourceType, Difficulty

router = APIRouter(prefix="/learning", tags=["Learning"])


# ============ Resource Management ============

@router.get("/resources", response_model=PaginatedResponse[ResourceResponse])
async def list_resources(
    skip: int = 0,
    limit: int = 100,
    resource_type: Optional[ResourceType] = None,
    difficulty: Optional[Difficulty] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get resources list with optional filters"""
    resources = await get_resources(db, skip, limit, resource_type, difficulty)
    total = len(resources)
    page = (skip // limit) + 1 if limit > 0 else 1
    page_size = limit if limit > 0 else total
    total_pages = max(1, math.ceil(total / page_size)) if page_size > 0 else 1
    return {
        "items": resources,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/resources/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get resource by ID"""
    resource = await get_resource_by_id(db, resource_id)
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found",
        )
    return resource


@router.post(
    "/resources",
    response_model=ResourceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_new_resource(
    resource_data: ResourceCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create new resource"""
    try:
        resource = await create_resource(db, resource_data)
        return resource
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put("/resources/{resource_id}", response_model=ResourceResponse)
async def update_existing_resource(
    resource_id: int,
    resource_data: ResourceUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update resource"""
    try:
        resource = await update_resource(db, resource_id, resource_data)
        return resource
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/resources/{resource_id}", response_model=MessageResponse)
async def delete_existing_resource(
    resource_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete resource"""
    try:
        await delete_resource(db, resource_id)
        return {"message": "Resource deleted successfully"}
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ============ User Interaction Management ============

@router.post("/resources/{resource_id}/interact", response_model=dict)
async def create_user_interaction(
    resource_id: int,
    interaction_data: UserResourceInteractionCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create user resource interaction (requires authentication)"""
    try:
        # Ensure resource_id in path matches body
        if interaction_data.resource_id != resource_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resource ID mismatch",
            )
        interaction = await create_interaction(db, current_user["id"], interaction_data)
        return interaction
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/my-interactions", response_model=PaginatedResponse[dict])
async def list_user_interactions(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's interactions (requires authentication)"""
    interactions = await get_user_interactions(db, current_user["id"], skip, limit)
    total = len(interactions)
    page = (skip // limit) + 1 if limit > 0 else 1
    page_size = limit if limit > 0 else total
    total_pages = max(1, math.ceil(total / page_size)) if page_size > 0 else 1
    return {
        "items": interactions,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


# ============ Resource Statistics ============

@router.post("/resources/{resource_id}/view", response_model=ResourceResponse)
async def record_resource_view(
    resource_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Record a view for a resource (public endpoint)"""
    try:
        resource = await increment_resource_views(db, resource_id)
        return resource
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
