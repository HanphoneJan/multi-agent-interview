"""Tests for learning service"""
import pytest
from app.services.learning_service import (
    get_resource_by_id,
    get_resources,
    create_resource,
    update_resource,
    delete_resource,
    create_interaction,
    get_user_interactions,
    increment_resource_views,
    increment_resource_completions,
    update_resource_rating,
)
from app.schemas.learning import ResourceCreate, ResourceUpdate, UserResourceInteractionCreate
from app.core.constants import ResourceType, Difficulty
from app.core.exceptions import NotFoundError


@pytest.mark.asyncio
async def test_get_resource_by_id_returns_none_when_not_found(db):
    """Test getting non-existent resource returns None"""
    result = await get_resource_by_id(db, 99999)
    assert result is None


@pytest.mark.asyncio
async def test_get_resource_by_id_returns_resource(db):
    """Test getting existing resource by ID"""
    # Create a resource first
    resource_data = ResourceCreate(
        name="Test Resource",
        resource_type=ResourceType.COURSE,
        tags="test,beginner",
        url="https://example.com/test",
        duration_or_quantity="5 hours",
        difficulty=Difficulty.EASY
    )
    created = await create_resource(db, resource_data)

    # Get it by ID
    result = await get_resource_by_id(db, created["id"])
    assert result is not None
    assert result["id"] == created["id"]
    assert result["name"] == "Test Resource"


@pytest.mark.asyncio
async def test_get_resources_returns_list(db):
    """Test getting resources list"""
    # Create a resource
    resource_data = ResourceCreate(
        name="List Test Resource",
        resource_type=ResourceType.QUESTION,
        tags="test,article",
        url="https://example.com/article",
        duration_or_quantity="10 min read",
        difficulty=Difficulty.MEDIUM
    )
    await create_resource(db, resource_data)

    # Get all resources
    result = await get_resources(db)
    assert isinstance(result, list)
    assert len(result) >= 1


@pytest.mark.asyncio
async def test_get_resources_with_type_filter(db):
    """Test getting resources with type filter"""
    # Create resources with different types
    await create_resource(db, ResourceCreate(
        name="Video Resource",
        resource_type=ResourceType.VIDEO,
        tags="video",
        url="https://example.com/video",
        duration_or_quantity="15 min",
        difficulty=Difficulty.EASY
    ))

    # Filter by video type
    result = await get_resources(db, resource_type=ResourceType.VIDEO)
    assert len(result) >= 1
    for r in result:
        assert r["resource_type"] == ResourceType.VIDEO


@pytest.mark.asyncio
async def test_get_resources_with_difficulty_filter(db):
    """Test getting resources with difficulty filter"""
    # Create a hard resource
    await create_resource(db, ResourceCreate(
        name="Hard Question",
        resource_type=ResourceType.QUESTION,
        tags="algorithm,hard",
        url="https://example.com/hard",
        duration_or_quantity="1 hour",
        difficulty=Difficulty.HARD
    ))

    # Filter by hard difficulty
    result = await get_resources(db, difficulty=Difficulty.HARD)
    assert len(result) >= 1
    for r in result:
        assert r["difficulty"] == Difficulty.HARD


@pytest.mark.asyncio
async def test_create_resource_success(db):
    """Test creating a resource"""
    resource_data = ResourceCreate(
        name="Python Tutorial",
        resource_type=ResourceType.COURSE,
        tags="python,beginner",
        url="https://example.com/python",
        duration_or_quantity="10 hours",
        difficulty=Difficulty.EASY
    )

    result = await create_resource(db, resource_data)
    assert result["name"] == "Python Tutorial"
    assert result["resource_type"] == ResourceType.COURSE
    assert result["views"] == 0
    assert result["completions"] == 0
    assert result["rating"] == 0.0
    assert result["rating_count"] == 0


@pytest.mark.asyncio
async def test_update_resource_success(db):
    """Test updating a resource"""
    # Create a resource first
    created = await create_resource(db, ResourceCreate(
        name="Original Name",
        resource_type=ResourceType.COURSE,
        tags="original",
        url="https://example.com/original",
        duration_or_quantity="1 hour",
        difficulty=Difficulty.EASY
    ))

    # Update it
    update_data = ResourceUpdate(name="Updated Name", tags="updated")
    result = await update_resource(db, created["id"], update_data)

    assert result["name"] == "Updated Name"
    assert result["tags"] == "updated"
    # Other fields should remain unchanged
    assert result["url"] == "https://example.com/original"


@pytest.mark.asyncio
async def test_update_resource_not_found(db):
    """Test updating non-existent resource raises NotFoundError"""
    update_data = ResourceUpdate(name="New Name")
    with pytest.raises(NotFoundError):
        await update_resource(db, 99999, update_data)


@pytest.mark.asyncio
async def test_update_resource_no_changes(db):
    """Test updating resource with no changes"""
    # Create a resource
    created = await create_resource(db, ResourceCreate(
        name="No Change Test",
        resource_type=ResourceType.COURSE,
        tags="test",
        url="https://example.com/test",
        duration_or_quantity="1 hour",
        difficulty=Difficulty.EASY
    ))

    # Update with empty data
    result = await update_resource(db, created["id"], ResourceUpdate())
    assert result["name"] == "No Change Test"


@pytest.mark.asyncio
async def test_delete_resource_success(db):
    """Test deleting a resource"""
    # Create a resource
    created = await create_resource(db, ResourceCreate(
        name="To Delete",
        resource_type=ResourceType.COURSE,
        tags="delete",
        url="https://example.com/delete",
        duration_or_quantity="1 hour",
        difficulty=Difficulty.EASY
    ))

    # Delete it
    result = await delete_resource(db, created["id"])
    assert result is True

    # Verify it's gone
    found = await get_resource_by_id(db, created["id"])
    assert found is None


@pytest.mark.asyncio
async def test_delete_resource_not_found(db):
    """Test deleting non-existent resource raises NotFoundError"""
    with pytest.raises(NotFoundError):
        await delete_resource(db, 99999)


@pytest.mark.asyncio
async def test_increment_resource_views(db):
    """Test incrementing resource views"""
    # Create a resource
    created = await create_resource(db, ResourceCreate(
        name="View Test",
        resource_type=ResourceType.QUESTION,
        tags="views",
        url="https://example.com/views",
        duration_or_quantity="5 min",
        difficulty=Difficulty.EASY
    ))

    # Increment views
    result = await increment_resource_views(db, created["id"])
    assert result["views"] == 1

    # Increment again
    result = await increment_resource_views(db, created["id"])
    assert result["views"] == 2


@pytest.mark.asyncio
async def test_increment_resource_views_not_found(db):
    """Test incrementing views for non-existent resource raises NotFoundError"""
    with pytest.raises(NotFoundError):
        await increment_resource_views(db, 99999)


@pytest.mark.asyncio
async def test_increment_resource_completions(db):
    """Test incrementing resource completions"""
    # Create a resource
    created = await create_resource(db, ResourceCreate(
        name="Complete Test",
        resource_type=ResourceType.COURSE,
        tags="complete",
        url="https://example.com/complete",
        duration_or_quantity="10 hours",
        difficulty=Difficulty.MEDIUM
    ))

    # Increment completions
    result = await increment_resource_completions(db, created["id"])
    assert result["completions"] == 1


@pytest.mark.asyncio
async def test_update_resource_rating(db):
    """Test updating resource rating"""
    # Create a resource
    created = await create_resource(db, ResourceCreate(
        name="Rating Test",
        resource_type=ResourceType.VIDEO,
        tags="rating",
        url="https://example.com/rating",
        duration_or_quantity="20 min",
        difficulty=Difficulty.EASY
    ))

    # Add first rating (5 stars)
    result = await update_resource_rating(db, created["id"], 5.0)
    assert result["rating"] == 5.0
    assert result["rating_count"] == 1

    # Add second rating (3 stars)
    result = await update_resource_rating(db, created["id"], 3.0)
    assert result["rating_count"] == 2
    # Average should be (5.0 + 3.0) / 2 = 4.0
    assert result["rating"] == 4.0


@pytest.mark.asyncio
async def test_update_resource_rating_not_found(db):
    """Test updating rating for non-existent resource raises NotFoundError"""
    with pytest.raises(NotFoundError):
        await update_resource_rating(db, 99999, 5.0)


@pytest.mark.asyncio
async def test_create_interaction_view(db, test_user):
    """Test creating view interaction"""
    # Create a resource
    created = await create_resource(db, ResourceCreate(
        name="Interaction Test",
        resource_type=ResourceType.QUESTION,
        tags="interaction",
        url="https://example.com/interaction",
        duration_or_quantity="5 min",
        difficulty=Difficulty.EASY
    ))

    # Create interaction
    interaction_data = UserResourceInteractionCreate(
        resource_id=created["id"],
        interaction_type="view",
        value=0
    )
    result = await create_interaction(db, test_user.id, interaction_data)

    assert result["resource_id"] == created["id"]
    assert result["user_id"] == test_user.id
    assert result["interaction_type"] == "view"


@pytest.mark.asyncio
async def test_create_interaction_not_found(db, test_user):
    """Test creating interaction for non-existent resource raises NotFoundError"""
    interaction_data = UserResourceInteractionCreate(
        resource_id=99999,
        interaction_type="view",
        value=0
    )
    with pytest.raises(NotFoundError):
        await create_interaction(db, test_user.id, interaction_data)


@pytest.mark.asyncio
async def test_get_user_interactions(db, test_user):
    """Test getting user interactions"""
    # Create a resource
    created = await create_resource(db, ResourceCreate(
        name="User Interactions Test",
        resource_type=ResourceType.QUESTION,
        tags="user",
        url="https://example.com/user",
        duration_or_quantity="30 min",
        difficulty=Difficulty.HARD
    ))

    # Create multiple interactions
    await create_interaction(db, test_user.id, UserResourceInteractionCreate(
        resource_id=created["id"],
        interaction_type="view",
        value=0
    ))
    await create_interaction(db, test_user.id, UserResourceInteractionCreate(
        resource_id=created["id"],
        interaction_type="complete",
        value=1
    ))

    # Get interactions
    result = await get_user_interactions(db, test_user.id)
    assert isinstance(result, list)
    assert len(result) >= 2
