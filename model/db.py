import os
from sqlalchemy import create_engine, text
import pandas as pd


def _env(name: str, default: str) -> str:
    return os.getenv(name, default)


def get_engine():
    host = _env("DB_HOST", "localhost")
    port = _env("DB_PORT", "3307")
    user = _env("DB_USER", "thaochie")
    password = _env("DB_PASSWORD", "thaochie")
    database = _env("DB_NAME", "DACN")
    url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
    return create_engine(url, pool_pre_ping=True, pool_recycle=3600)


def load_products() -> pd.DataFrame:
    query = text(
        """
        SELECT
            p.Id,
            p.Name,
            COALESCE(p.CleanName, p.Name) AS CleanName,
            COALESCE(p.Brand, '') AS Brand,
            CAST(p.Price AS DECIMAL(18, 2)) AS Price,
            CAST(p.OriginalPrice AS DECIMAL(18, 2)) AS OriginalPrice,
            CAST(p.DiscountRate AS DOUBLE) AS DiscountRate,
            CAST(p.Rating AS DOUBLE) AS Rating,
            p.ReviewCount,
            COALESCE(p.ImageUrl, '') AS ImageUrl,
            p.CategoryId,
            COALESCE(c.Name, 'Unknown') AS CategoryName
        FROM Products p
        LEFT JOIN Categories c ON c.Id = p.CategoryId
        """
    )
    return pd.read_sql(query, get_engine())


def load_interactions() -> pd.DataFrame:
    query = text(
        """
        SELECT
            Id,
            UserId,
            SessionId,
            ProductId,
            InteractionType,
            COALESCE(InteractionValue, 1) AS InteractionValue,
            CreatedAt
        FROM UserInteractions
        """
    )
    try:
        return pd.read_sql(query, get_engine())
    except Exception:
        return pd.DataFrame(columns=[
            "Id", "UserId", "SessionId", "ProductId", "InteractionType", "InteractionValue", "CreatedAt"
        ])
