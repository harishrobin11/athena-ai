"""
Athena EAIOS - Security & Authentication Layer
Module: app.models.user
Description: Extends the enterprise database model schema to enforce multi-tenant 
             Role-Based Access Control (RBAC) boundaries.
"""

import enum
from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.sql import func
from app.db.base import Base  # Adjust path to match your SQLAlchemy setup


class DepartmentRole(str, enum.Enum):
    """Defines the isolated organizational tiers permitted within the operating system."""
    FINANCE = "FINANCE"
    PROCUREMENT = "PROCUREMENT"
    ADMIN = "ADMIN"


class EnterpriseUser(Base):
    __tablename__ = "enterprise_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # NEW: Secure Multi-Tenant Separation Hook
    department = Column(
        Enum(DepartmentRole), 
        default=DepartmentRole.PROCUREMENT, 
        nullable=False
    )
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())