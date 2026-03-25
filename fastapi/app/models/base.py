"""Core metadata for SQLAlchemy Core tables"""
from sqlalchemy import MetaData

# Global metadata for all table definitions
# This replaces the ORM's DeclarativeBase approach
metadata = MetaData()
