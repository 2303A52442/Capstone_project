from sqlalchemy import Column, ForeignKey, Integer

from app.db.base import Base


class RoleOwner(Base):
    __tablename__ = "role_owners"

    role_id = Column(Integer, ForeignKey("target_roles.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
