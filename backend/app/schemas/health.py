"""
Pydantic schemas for the health check endpoint.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """
    Response schema for system health check status.
    """
    status: str = Field(..., description="Overall API service health status")
    mongodb: str = Field(..., description="MongoDB Atlas connection health status")
    timestamp: datetime = Field(..., description="Timestamp of the health check execution")
