"""
Database connection utilities for AlphaGPT
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from agent.database.models.base import Base


def get_db_url():
    """
    Generate PostgreSQL connection URL
    """
    # --- SỬA ĐỔI: TRẢ VỀ TRỰC TIẾP URL ĐÚNG ---
    # Thay vì đọc biến môi trường lung tung, ta chốt cứng địa chỉ ở đây
    return "postgresql://alpha_user:password123@localhost:5432/alpha_db"
    # ------------------------------------------


def get_db_connection_params():
    """
    Get database connection parameters
    """
    # Cập nhật luôn params cho đồng bộ (dù hàm này ít dùng)
    return {
        "host": "localhost",
        "port": "5432",
        "db": "alpha_db",
        "user": "alpha_user",
        "password": "password123",
    }


def get_db_engine():
    """
    Create and return a SQLAlchemy engine
    """
    db_url = get_db_url()
    return create_engine(db_url)


def get_session_factory(engine=None):
    """
    Get a sessionmaker for creating database sessions
    """
    if engine is None:
        engine = get_db_engine()

    return sessionmaker(bind=engine)


def create_tables(engine=None):
    """
    Create all tables defined in the models
    """
    if engine is None:
        engine = get_db_engine()

    Base.metadata.create_all(engine)