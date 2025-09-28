"""
Stage 2: Contract Classification Task
Celery task for extracting clauses, comparing with templates, and classifying as Standard/Non-Standard.
"""

import logging
import sys
import os
from datetime import datetime
from pathlib import Path
from celery import Celery
from sqlalchemy.orm import Session

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))

from app.core.database import get_db
from app.models import Contract, ContractClause, ProcessingLog, FileRecord
from classification.clause_extractor import ClauseExtractor
from classification.similarity_matcher import SimilarityMatcher
from classification.classification_engine import ClassificationEngine
from templates.template_loader import TemplateLoader

# Import shared Celery app
from celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name='tasks.stage2_classification.classify_contract')
def classify_contract(self, contract_id: str):
    """
    Main classification task that processes a contract through all classification stages.
    
    Args:
        contract_id: UUID of the contract to classify
    """
    try:
        # Get database session
        db = next(get_db())
        
        # Get contract from database
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise Exception(f"Contract not found: {contract_id}")
        
        if contract.status not in ['preprocessing_completed', 'preprocessed']:
            raise Exception(f"Contract {contract_id} is not ready for classification (status: {contract.status})")
        
        logger.info(f"Starting Stage 2 classification for contract {contract_id}")
        
        # Update status to classification processing
        contract.status = "classifying"
        contract.processing_message = "Stage 2: Starting clause classification"
        contract.processing_progress = 10
        contract.processing_started_at = datetime.utcnow()
        
        # Add processing log
        log_entry = ProcessingLog(
            contract_id=contract_id,
            level="INFO",
            message="Stage 2: Classification started",
            component="stage2_classification",
            celery_task_id=self.request.id
        )
        db.add(log_entry)
        db.commit()
        
        self.update_state(state='PROGRESS', meta={'progress': 10, 'message': 'Stage 2: Starting clause classification'})
        
        # Step 1: Extract clauses from contract (30% progress)
        contract.processing_message = "Stage 2: Extracting contract clauses"
        contract.processing_progress = 30
        db.commit()
        self.update_state(state='PROGRESS', meta={'progress': 30, 'message': 'Stage 2: Extracting contract clauses'})
        
        # Get extracted text from file record
        extracted_text_file = db.query(FileRecord).filter(
            FileRecord.contract_id == contract_id,
            FileRecord.file_type == "extracted_text"
        ).first()
        
        if not extracted_text_file:
            raise Exception("No extracted text file found for contract")
        
        # Read extracted text from filesystem
        base_path = Path(__file__).parent.parent.parent / "upload"
        text_file_path = base_path / extracted_text_file.storage_bucket / extracted_text_file.storage_object_key
        
        if not text_file_path.exists():
            raise Exception(f"Extracted text file not found: {text_file_path}")
        
        with open(text_file_path, 'r', encoding='utf-8') as f:
            extracted_text = f.read()
        
        clause_extractor = ClauseExtractor()
        extracted_attributes = clause_extractor.extract_all_attributes(extracted_text)
        
        # Step 2: Load template clauses (50% progress)
        contract.processing_message = "Stage 2: Loading template clauses"
        contract.processing_progress = 50
        db.commit()
        self.update_state(state='PROGRESS', meta={'progress': 50, 'message': 'Stage 2: Loading template clauses'})
        
        template_loader = TemplateLoader()
        template_data = template_loader.load_template(contract.state)
        if not template_data:
            raise Exception(f"Failed to load template for state {contract.state}")
        template_attributes = template_data.get('attributes', {})
        
        # Step 3: Compare and classify clauses (70% progress)
        contract.processing_message = "Stage 2: Classifying contract clauses"
        contract.processing_progress = 70
        db.commit()
        self.update_state(state='PROGRESS', meta={'progress': 70, 'message': 'Stage 2: Classifying contract clauses'})
        
        classification_engine = ClassificationEngine()
        classifications = classification_engine.classify_all_attributes(extracted_attributes, template_attributes)
        
        # Step 4: Store results in database (90% progress)
        contract.processing_message = "Stage 2: Storing classification results"
        contract.processing_progress = 90
        db.commit()
        self.update_state(state='PROGRESS', meta={'progress': 90, 'message': 'Stage 2: Storing classification results'})
        
        # Store classification results
        total_clauses = len(classifications)
        standard_clauses = sum(1 for c in classifications.values() if c['classification'] == 'Standard')
        non_standard_clauses = total_clauses - standard_clauses
        
        # Store individual clause results
        for clause_number, (attribute_name, result) in enumerate(classifications.items(), 1):
            clause = ContractClause(
                contract_id=contract_id,
                clause_number=clause_number,
                attribute_name=attribute_name,
                clause_text=extracted_attributes.get(attribute_name, ""),
                classification=result['classification'],
                confidence_score=result.get('confidence_score', 0),
                template_match_text=template_attributes.get(attribute_name, ""),
                similarity_score=int(result.get('similarity_score', 0) * 100),
                match_type=result.get('match_type', 'unknown'),
                processing_notes=result.get('reason', 'No reasoning provided')
            )
            db.add(clause)
        
        # Step 5: Finalize classification (100% progress)
        contract.processing_message = "Stage 2: Classification completed successfully"
        contract.processing_progress = 100
        contract.status = "completed"
        contract.processing_completed_at = datetime.utcnow()
        contract.total_clauses = total_clauses
        contract.standard_clauses = standard_clauses
        contract.non_standard_clauses = non_standard_clauses
        
        # Add completion log
        completion_log = ProcessingLog(
            contract_id=contract_id,
            level="INFO",
            message=f"Stage 2 completed successfully. Classified {total_clauses} clauses: {standard_clauses} Standard, {non_standard_clauses} Non-Standard.",
            component="stage2_classification",
            celery_task_id=self.request.id
        )
        db.add(completion_log)
        
        self.update_state(state='SUCCESS', meta={'progress': 100, 'message': 'Stage 2: Classification completed successfully'})
        
        # Single commit at the end
        db.commit()
        db.close()
        
        logger.info(f"Successfully classified contract {contract_id}")
        return {
            'success': True,
            'contract_id': contract_id,
            'total_clauses': total_clauses,
            'standard_clauses': standard_clauses,
            'non_standard_clauses': non_standard_clauses
        }
        
    except Exception as e:
        logger.error(f"Classification failed for contract {contract_id}: {str(e)}")
        
        # Update contract with error status
        try:
            db = next(get_db())
            contract = db.query(Contract).filter(Contract.id == contract_id).first()
            if contract:
                contract.status = "failed"
                contract.processing_message = f"Stage 2: Classification failed - {str(e)}"
                contract.processing_progress = 0
                contract.error_message = str(e)
                contract.processing_completed_at = datetime.utcnow()
                
                # Add error log
                error_log = ProcessingLog(
                    contract_id=contract_id,
                    level="ERROR",
                    message=f"Stage 2 classification failed: {str(e)}",
                    component="stage2_classification",
                    celery_task_id=self.request.id if hasattr(self, 'request') else None
                )
                db.add(error_log)
                db.commit()
            db.close()
        except Exception as db_error:
            logger.error(f"Failed to update database after error: {str(db_error)}")
        
        return {"success": False, "error": str(e)}

def extract_contract_clauses(contract: Contract, task_instance) -> dict:
    """Extract the 5 required attributes from contract text."""
    logger.info(f"Extracting clauses from contract {contract.id}")
    
    # Get extracted text from file record
    db = next(get_db())
    
    extracted_text_file = db.query(FileRecord).filter(
        FileRecord.contract_id == contract.id,
        FileRecord.file_type == "extracted_text"
    ).first()
    
    if not extracted_text_file:
        raise Exception("No extracted text file found for contract")
    
    # Read extracted text from filesystem
    base_path = Path(__file__).parent.parent.parent / "upload"
    text_file_path = base_path / extracted_text_file.storage_bucket / extracted_text_file.storage_object_key
    
    if not text_file_path.exists():
        raise Exception(f"Extracted text file not found: {text_file_path}")
    
    with open(text_file_path, 'r', encoding='utf-8') as f:
        extracted_text = f.read()
    
    # Initialize clause extractor
    extractor = ClauseExtractor()
    
    # Extract all required attributes
    extracted_attributes = extractor.extract_all_attributes(extracted_text)
    
    # Validate extraction
    validation_results = extractor.validate_extraction(extracted_attributes)
    
    # Log extraction results
    for attr_name, clause_text in extracted_attributes.items():
        is_valid = validation_results.get(attr_name, False)
        status = "✓" if is_valid else "✗"
        logger.info(f"{status} {attr_name}: {'Found' if clause_text else 'Not found'}")
    
    return extracted_attributes

def load_template_clauses(state: str, task_instance) -> dict:
    """Load and extract clauses from standard template."""
    logger.info(f"Loading template clauses for state {state}")
    
    # Initialize template loader
    template_loader = TemplateLoader()
    
    # Load template
    template = template_loader.load_template(state)
    if not template:
        raise Exception(f"Failed to load template for state {state}")
    
    # Get template attributes
    template_attributes = template.get('attributes', {})
    
    # Log template loading results
    for attr_name, clause_text in template_attributes.items():
        status = "✓" if clause_text else "✗"
        logger.info(f"{status} Template {attr_name}: {'Found' if clause_text else 'Not found'}")
    
    return template_attributes

def classify_clauses(contract_attributes: dict, template_attributes: dict, task_instance) -> dict:
    """Compare contract clauses with template and classify."""
    logger.info("Classifying contract clauses")
    
    # Initialize classification engine
    classifier = ClassificationEngine()
    
    # Classify all attributes
    classifications = classifier.classify_all_attributes(contract_attributes, template_attributes)
    
    return classifications

def store_classification_results(db: Session, contract: Contract, 
                               extracted_attributes: dict, classifications: dict):
    """Store classification results in database."""
    logger.info(f"Storing classification results for contract {contract.id}")
    
    # Delete existing clause records for this contract
    db.query(ContractClause).filter(ContractClause.contract_id == contract.id).delete()
    
    # Store each classified clause
    for attr_name, clause_text in extracted_attributes.items():
        classification_result = classifications.get(attr_name, {})
        
        clause = ContractClause(
            contract_id=contract.id,
            clause_number=get_clause_number(attr_name),
            attribute_name=attr_name,
            clause_text=clause_text,
            classification=classification_result.get('classification', 'Unknown'),
            confidence_score=classification_result.get('confidence_score', 0),
            similarity_score=classification_result.get('similarity_score', 0.0),
            match_type=classification_result.get('match_type', 'unknown')
        )
        
        db.add(clause)
    
    db.commit()
    logger.info(f"Stored {len(extracted_attributes)} clause records")

def generate_classification_summary(classifications: dict) -> dict:
    """Generate summary statistics for classifications."""
    classifier = ClassificationEngine()
    return classifier.generate_summary(classifications)

def finalize_contract_classification(db: Session, contract: Contract, summary: dict):
    """Update contract with final classification summary."""
    contract.total_clauses = summary['total_clauses']
    contract.standard_clauses = summary['standard_clauses']
    contract.non_standard_clauses = summary['non_standard_clauses']
    contract.processing_completed_at = db.execute("SELECT CURRENT_TIMESTAMP").scalar()
    
    db.commit()

def update_contract_status(db: Session, contract: Contract, status: str, 
                          message: str, progress: int):
    """Update contract processing status."""
    contract.status = status
    contract.processing_message = message
    contract.processing_progress = progress
    
    db.commit()
    
    # Update Celery task state
    if current_task:
        current_task.update_state(
            state='PROGRESS',
            meta={
                'current': progress,
                'total': 100,
                'status': message
            }
        )

def get_clause_number(attribute_name: str) -> int:
    """Get clause number for attribute."""
    clause_mapping = {
        'Medicaid Timely Filing': 1,
        'Medicare Timely Filing': 2,
        'No Steerage/SOC': 3,
        'Medicaid Fee Schedule': 4,
        'Medicare Fee Schedule': 5
    }
    return clause_mapping.get(attribute_name, 0)
