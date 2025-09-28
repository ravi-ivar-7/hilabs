import sys
import os
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Set database path for worker
os.environ['DATABASE_URL'] = f"sqlite:///{backend_path}/contracts.db"

from celery import Celery
from sqlalchemy.orm import Session
from datetime import datetime
import logging

# Import backend modules
from app.core.database import get_db
from app.models.contract import Contract, FileRecord, ProcessingLog
from app.services.filesystem_service import FileSystemService

# Import preprocessing modules
from preprocessing.pdf_extractor import PDFExtractor
from preprocessing.text_cleaner import TextCleaner
from preprocessing.metadata_extractor import MetadataExtractor

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery('hilabs_worker')
celery_app.config_from_object({
    'broker_url': 'redis://localhost:6379/0',
    'result_backend': 'redis://localhost:6379/0',
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    'timezone': 'UTC',
    'enable_utc': True,
})

@celery_app.task(bind=True)
def extract_contract_text(self, contract_id: str):
    """Extract text from contract PDF - Phase 2 preprocessing"""
    try:
        # Get database session
        db = next(get_db())
        
        # Get contract
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            logger.error(f"Contract {contract_id} not found")
            return {"success": False, "error": "Contract not found"}
        
        # Update status to processing with message and progress
        contract.status = "processing"
        contract.processing_message = "Starting text extraction"
        contract.processing_progress = 0
        contract.processing_started_at = datetime.utcnow()
        
        # Add processing log
        log_entry = ProcessingLog(
            contract_id=contract_id,
            level="INFO",
            message="Text extraction started",
            component="pdf_extractor",
            celery_task_id=self.request.id
        )
        db.add(log_entry)
        db.commit()
        
        # Initialize services
        filesystem_service = FileSystemService()
        pdf_extractor = PDFExtractor()
        text_cleaner = TextCleaner()
        metadata_extractor = MetadataExtractor()
        
        # Step 1: Loading PDF (20% progress)
        contract.processing_message = "Loading PDF file for preprocessing"
        contract.processing_progress = 20
        db.commit()
        self.update_state(state='PROGRESS', meta={'progress': 20, 'message': 'Loading PDF file for preprocessing'})
        
        from pathlib import Path
        base_path = Path(__file__).parent.parent.parent / "upload"
        file_path = base_path / contract.storage_bucket / contract.storage_object_key
        
        with open(file_path, 'rb') as file:
            file_content = file.read()
        
        extraction_result = pdf_extractor.extract_with_fallback(file_content)
        
        if not extraction_result["success"]:
            contract.status = "failed"
            contract.processing_message = "PDF extraction failed"
            contract.processing_progress = 0
            contract.error_message = f"Text extraction failed: {extraction_result['error']}"
            
            # Add error log
            error_log = ProcessingLog(
                contract_id=contract_id,
                level="ERROR",
                message=f"PDF extraction failed: {extraction_result['error']}",
                component="pdf_extractor",
                celery_task_id=self.request.id
            )
            db.add(error_log)
            db.commit()
            return {"success": False, "error": extraction_result["error"]}
        
        # Step 2: Extracting text (60% progress)
        contract.processing_message = "Extracting and cleaning text from PDF"
        contract.processing_progress = 60
        db.commit()
        self.update_state(state='PROGRESS', meta={'progress': 60, 'message': 'Extracting and cleaning text from PDF'})
        
        # Add progress log
        progress_log = ProcessingLog(
            contract_id=contract_id,
            level="INFO",
            message=f"Extracted {len(extraction_result['text'])} characters from {extraction_result['pages']} pages",
            component="pdf_extractor",
            celery_task_id=self.request.id
        )
        db.add(progress_log)
        db.commit()
        
        raw_text = extraction_result["text"]
        cleaning_result = text_cleaner.clean_text(raw_text)
        cleaned_text = cleaning_result["cleaned_text"]
        
        # Step 3: Saving preprocessed text (80% progress)
        contract.processing_message = "Saving preprocessed text to filesystem"
        contract.processing_progress = 80
        db.commit()
        self.update_state(state='PROGRESS', meta={'progress': 80, 'message': 'Saving preprocessed text to filesystem'})
        
        # Create file record for extracted text
        extracted_filename = f"{contract_id}_extracted.txt"
        text_file_record = FileRecord(
            contract_id=contract_id,
            file_type="extracted_text",
            filename=extracted_filename,
            file_size=len(cleaned_text.encode('utf-8')),
            mime_type="text/plain",
            storage_bucket=contract.storage_bucket,
            storage_object_key=extracted_filename,
            extraction_method="pdf_extraction"
        )
        db.add(text_file_record)
        
        # Save extracted text to filesystem
        from pathlib import Path
        base_path = Path(__file__).parent.parent.parent / "upload"
        text_file_path = base_path / contract.storage_bucket / extracted_filename
        text_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(text_file_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_text)
        
        # Step 4: Storing results (100% progress)
        contract.processing_message = "Text extraction and preprocessing completed"
        contract.processing_progress = 100
        contract.status = "preprocessed"
        contract.processing_completed_at = datetime.utcnow()
        
        # Add completion log
        completion_log = ProcessingLog(
            contract_id=contract_id,
            level="INFO",
            message=f"Preprocessing completed successfully. Extracted {len(cleaned_text)} characters.",
            component="text_preprocessor",
            celery_task_id=self.request.id
        )
        db.add(completion_log)
        
        self.update_state(state='SUCCESS', meta={'progress': 100, 'message': 'Text extraction and preprocessing completed'})
        
        db.commit()
        db.close()
        
        return {
            "success": True,
            "contract_id": contract_id,
            "status": "preprocessed",
            "extracted_text_length": len(cleaned_text),
            "text_file_path": str(text_file_path),
            "pages_processed": extraction_result['pages']
        }
        
    except Exception as e:
        logger.error(f"Error processing contract {contract_id}: {str(e)}")
        
        # Update contract status to failed with proper logging
        try:
            db = next(get_db())
            contract = db.query(Contract).filter(Contract.id == contract_id).first()
            if contract:
                contract.status = "failed"
                contract.processing_message = "Text extraction failed"
                contract.processing_progress = 0
                contract.error_message = str(e)
                contract.processing_completed_at = datetime.utcnow()
                
                # Add error log
                error_log = ProcessingLog(
                    contract_id=contract_id,
                    level="ERROR",
                    message=f"Preprocessing failed: {str(e)}",
                    component="text_extractor",
                    celery_task_id=self.request.id if hasattr(self, 'request') else None
                )
                db.add(error_log)
                db.commit()
            db.close()
        except Exception as db_error:
            logger.error(f"Failed to update database after error: {str(db_error)}")
        
        return {"success": False, "error": str(e)}
