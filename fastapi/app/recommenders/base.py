"""Base recommender class"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseRecommender(ABC):
    """Base class for recommenders"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def recommend(
        self,
        user_id: int,
        limit: int = 10,
        filters: Dict[str, Any] | None = None
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations for a user.

        Args:
            user_id: ID of the user
            limit: Maximum number of recommendations
            filters: Optional filters to apply

        Returns:
            List of recommendations with scores
        """
        pass

    @abstractmethod
    def train(self):
        """
        Train the recommendation model.

        This should be called periodically to update the model.
        """
        pass

    def get_name(self) -> str:
        """Get recommender name"""
        return self.name
