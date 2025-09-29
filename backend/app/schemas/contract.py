from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid


class ContractUploadRequest(BaseModel):
    state: str = Field(..., pattern="^(TN|WA)$")


class ContractUploadResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size: int
    state: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ContractResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size: int
    state: str
    status: str
    processing_progress: Optional[int] = None
    processing_message: Optional[str] = None
    created_at: datetime
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    total_clauses: Optional[int] = None
    standard_clauses: Optional[int] = None
    non_standard_clauses: Optional[int] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class ContractStatusResponse(BaseModel):
    id: str
    status: str
    processing_progress: Optional[int] = None
    processing_message: Optional[str] = None
    created_at: datetime
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ClauseResponse(BaseModel):
    id: str
    clause_number: int
    attribute_name: str
    clause_text: str
    classification: Optional[str] = None
    confidence_score: Optional[int] = None
    template_match_text: Optional[str] = None
    similarity_score: Optional[int] = None
    match_type: Optional[str] = None
    extraction_method: Optional[str] = None
    classification_steps: Optional[str] = None
    template_attribute: Optional[str] = None

    class Config:
        from_attributes = True


class ContractResultsResponse(BaseModel):
    contract: ContractResponse
    clauses: List[ClauseResponse]
    summary: dict

    class Config:
        from_attributes = True


class ClauseFeedbackRequest(BaseModel):
    clause_id: str
    original_classification: str
    user_classification: str = Field(..., pattern="^(Standard|Non-Standard|Ambiguous)$")
    confidence_rating: int = Field(..., ge=1, le=5)
    user_comments: Optional[str] = None


class ClauseFeedbackResponse(BaseModel):
    id: str
    clause_id: str
    original_classification: str
    user_classification: str
    confidence_rating: int
    user_comments: Optional[str] = None
    review_timestamp: datetime

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    services: dict
