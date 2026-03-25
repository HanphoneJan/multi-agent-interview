"""Learning service"""
from datetime import datetime
from typing import Optional, List

from sqlalchemy import select, insert, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning import resources, user_resource_interactions
from app.schemas.learning import ResourceCreate, ResourceUpdate, UserResourceInteractionCreate
from app.core.constants import ResourceType, Difficulty
from app.core.exceptions import NotFoundError


# ============ Resource Management ============

async def get_resource_by_id(db: AsyncSession, resource_id: int) -> Optional[dict]:
    """Get resource by ID"""
    result = await db.execute(
        select(resources).where(resources.c.id == resource_id)
    )
    resource = result.first()
    if resource:
        return dict(resource._asdict())
    return None


async def get_resources(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    resource_type: Optional[ResourceType] = None,
    difficulty: Optional[Difficulty] = None
) -> List[dict]:
    """Get resources list with optional filters"""
    query = select(resources)

    if resource_type:
        query = query.where(resources.c.resource_type == resource_type)

    if difficulty:
        query = query.where(resources.c.difficulty == difficulty)

    query = query.offset(skip).limit(limit).order_by(resources.c.created_at.desc())

    result = await db.execute(query)
    resource_list = result.all()
    return [dict(r._asdict()) for r in resource_list]


async def create_resource(db: AsyncSession, resource_data: ResourceCreate) -> dict:
    """Create new resource"""
    stmt = insert(resources).values(
        name=resource_data.name,
        resource_type=resource_data.resource_type,
        tags=resource_data.tags,
        url=resource_data.url,
        duration_or_quantity=resource_data.duration_or_quantity,
        difficulty=resource_data.difficulty,
        views=0,
        completions=0,
        rating=0.0,
        rating_count=0
    ).returning(resources.c.id)

    result = await db.execute(stmt)
    await db.commit()

    resource_id = result.scalar_one()
    return await get_resource_by_id(db, resource_id)


async def update_resource(
    db: AsyncSession,
    resource_id: int,
    resource_data: ResourceUpdate
) -> Optional[dict]:
    """Update resource"""
    # Check if resource exists
    resource = await get_resource_by_id(db, resource_id)
    if not resource:
        raise NotFoundError("Resource not found")

    # Build update values
    update_values = {}
    for key, value in resource_data.model_dump(exclude_unset=True).items():
        update_values[key] = value

    if not update_values:
        return resource

    # Update resource
    await db.execute(
        update(resources)
        .where(resources.c.id == resource_id)
        .values(**update_values)
    )
    await db.commit()

    return await get_resource_by_id(db, resource_id)


async def delete_resource(db: AsyncSession, resource_id: int) -> bool:
    """Delete resource"""
    # Check if resource exists
    resource = await get_resource_by_id(db, resource_id)
    if not resource:
        raise NotFoundError("Resource not found")

    # Delete resource (cascade will delete related records)
    await db.execute(
        delete(resources).where(resources.c.id == resource_id)
    )
    await db.commit()

    return True


# ============ User Interaction Management ============

async def create_interaction(
    db: AsyncSession,
    user_id: int,
    interaction_data: UserResourceInteractionCreate
) -> dict:
    """Create user resource interaction"""
    # Check if resource exists
    resource = await get_resource_by_id(db, interaction_data.resource_id)
    if not resource:
        raise NotFoundError("Resource not found")

    stmt = insert(user_resource_interactions).values(
        user_id=user_id,
        resource_id=interaction_data.resource_id,
        interaction_type=interaction_data.interaction_type,
        value=interaction_data.value
    ).returning(user_resource_interactions.c.id)

    result = await db.execute(stmt)
    await db.commit()

    interaction_id = result.scalar_one()

    # Get the created interaction
    result = await db.execute(
        select(user_resource_interactions)
        .where(user_resource_interactions.c.id == interaction_id)
    )
    interaction = result.first()
    return dict(interaction._asdict())


async def get_user_interactions(
    db: AsyncSession,
    user_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[dict]:
    """Get user's interactions"""
    result = await db.execute(
        select(user_resource_interactions)
        .where(user_resource_interactions.c.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .order_by(user_resource_interactions.c.created_at.desc())
    )
    interactions = result.all()
    return [dict(i._asdict()) for i in interactions]


# ============ Resource Statistics ============

async def increment_resource_views(db: AsyncSession, resource_id: int) -> Optional[dict]:
    """Increment resource view count"""
    # Check if resource exists
    resource = await get_resource_by_id(db, resource_id)
    if not resource:
        raise NotFoundError("Resource not found")

    await db.execute(
        update(resources)
        .where(resources.c.id == resource_id)
        .values(views=resources.c.views + 1)
    )
    await db.commit()

    return await get_resource_by_id(db, resource_id)


async def increment_resource_completions(db: AsyncSession, resource_id: int) -> Optional[dict]:
    """Increment resource completion count"""
    # Check if resource exists
    resource = await get_resource_by_id(db, resource_id)
    if not resource:
        raise NotFoundError("Resource not found")

    await db.execute(
        update(resources)
        .where(resources.c.id == resource_id)
        .values(completions=resources.c.completions + 1)
    )
    await db.commit()

    return await get_resource_by_id(db, resource_id)


async def update_resource_rating(
    db: AsyncSession,
    resource_id: int,
    new_rating: float
) -> Optional[dict]:
    """Update resource rating with new rating value"""
    # Check if resource exists
    resource = await get_resource_by_id(db, resource_id)
    if not resource:
        raise NotFoundError("Resource not found")

    # Calculate new average rating
    current_rating = resource["rating"]
    current_count = resource["rating_count"]

    new_count = current_count + 1
    new_average = ((current_rating * current_count) + new_rating) / new_count

    await db.execute(
        update(resources)
        .where(resources.c.id == resource_id)
        .values(
            rating=new_average,
            rating_count=new_count
        )
    )
    await db.commit()

    return await get_resource_by_id(db, resource_id)
