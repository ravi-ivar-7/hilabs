"""
Contract and file storage models for the healthcare contract classification system.
"""
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from .base import BaseModel


class Contract(BaseModel):
    __tablename__ = "contracts"
    
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=False, unique=True)
    
    state = Column(String(2), nullable=False)
    contract_type = Column(String(50), nullable=True)
    
    status = Column(String(20), nullable=False, default="pending")

    processing_started_at = Column(DateTime, nullable=True)
    processing_completed_at = Column(DateTime, nullable=True)
    processing_message = Column(Text, nullable=True)
    processing_progress = Column(Integer, nullable=True, default=0)
    
    storage_bucket = Column(String(100), nullable=False)
    storage_object_key = Column(String(500), nullable=False)
    
    celery_task_id = Column(String(100), nullable=True)
    
    total_clauses = Column(Integer, nullable=True)
    standard_clauses = Column(Integer, nullable=True)
    non_standard_clauses = Column(Integer, nullable=True)
    ambiguous_clauses = Column(Integer, nullable=True)
    
    error_message = Column(Text, nullable=True)

    
    file_records = relationship("FileRecord", back_populates="contract", cascade="all, delete-orphan")
    clauses = relationship("ContractClause", back_populates="contract", cascade="all, delete-orphan")


class FileRecord(BaseModel):
    __tablename__ = "file_records"
    
    contract_id = Column(String, ForeignKey("contracts.id"), nullable=False)
    
    # File information
    file_type = Column(String(20), nullable=False)  # original, extracted_text, processed
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=True)
    
    storage_bucket = Column(String(100), nullable=False)
    storage_object_key = Column(String(500), nullable=False)
    
    extraction_method = Column(String(50), nullable=True)
    processing_notes = Column(Text, nullable=True)
    
    contract = relationship("Contract", back_populates="file_records")


class ContractClause(BaseModel):
    __tablename__ = "contract_clauses"
    
    contract_id = Column(String, ForeignKey("contracts.id"), nullable=False)
    
    clause_number = Column(Integer, nullable=False)
    attribute_name = Column(String(100), nullable=False)
    clause_text = Column(Text, nullable=False)
    
    classification = Column(String(20), nullable=True)  # Standard, Non-Standard, Ambiguous
    confidence_score = Column(Integer, nullable=True)  # 0-100
    
    template_match_text = Column(Text, nullable=True)
    similarity_score = Column(Integer, nullable=True)  # 0-100
    match_type = Column(String(50), nullable=True)  # exact, lexical_high, semantic_high, etc.
    
    extraction_method = Column(String(50), nullable=True)
    processing_notes = Column(Text, nullable=True)
    
    # Additional spaCy classifier fields
    classification_steps = Column(Text, nullable=True)  # JSON of classification steps
    template_attribute = Column(String(100), nullable=True)  # Which template attribute was matched
    
    contract = relationship("Contract", back_populates="clauses")


class ProcessingLog(BaseModel):
    __tablename__ = "processing_logs"
    
    contract_id = Column(String, ForeignKey("contracts.id"), nullable=True)
    
    # Log information
    level = Column(String(10), nullable=False)  # DEBUG, INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    component = Column(String(50), nullable=False)  # api, extractor, classifier, etc.
    
    celery_task_id = Column(String(100), nullable=True)
    
    log_metadata = Column(Text, nullable=True)
    
    contract = relationship("Contract")
