import sys
import os
from pathlib import Path

backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

os.environ['DATABASE_URL'] = f"sqlite:///{backend_path}/contracts.db"

from datetime import datetime
import logging

from app.core.database import get_db
from app.models.contract import Contract, FileRecord, ProcessingLog

from preprocessing.pdf_extractor import PDFExtractor
from preprocessing.text_cleaner import TextCleaner

from celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name='tasks.stage1_preprocessing.preprocess_contract')
def preprocess_contract(self, contract_id: str):
    """Extract text from contract PDF - Phase 2 preprocessing"""
    try:
        db = next(get_db())
        
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            logger.error(f"Contract {contract_id} not found")
            return {"success": False, "error": "Contract not found"}
        
        contract.status = "preprocessing"
        contract.processing_message = "Stage 1: Starting text extraction"
        contract.processing_progress = 0
        contract.processing_started_at = datetime.utcnow()
        
        log_entry = ProcessingLog(
            contract_id=contract_id,
            level="INFO",
            message="Stage 1: Text extraction started",
            component="stage1_preprocessing",
            celery_task_id=self.request.id
        )
        db.add(log_entry)
        db.commit()
        
        self.update_state(state='PROGRESS', meta={'progress': 0, 'message': 'Stage 1: Starting text extraction'})
        
        pdf_extractor = PDFExtractor()
        text_cleaner = TextCleaner()
        
        # Step 1: Loading PDF (20% progress)
        contract.processing_message = "Stage 1: Loading PDF file for preprocessing"
        contract.processing_progress = 20
        db.commit()
        self.update_state(state='PROGRESS', meta={'progress': 20, 'message': 'Stage 1: Loading PDF file for preprocessing'})
        
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
        contract.processing_message = "Stage 1: Extracting and cleaning text from PDF"
        contract.processing_progress = 60
        db.commit()
        self.update_state(state='PROGRESS', meta={'progress': 60, 'message': 'Stage 1: Extracting and cleaning text from PDF'})
        
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
        contract.processing_message = "Stage 1: Saving preprocessed text to filesystem"
        contract.processing_progress = 80
        db.commit()
        self.update_state(state='PROGRESS', meta={'progress': 80, 'message': 'Stage 1: Saving preprocessed text to filesystem'})
        
        # Store extracted text in contract record
        contract.extracted_text = cleaned_text
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
        base_path = Path(__file__).parent.parent.parent / "upload"
        text_file_path = base_path / contract.storage_bucket / extracted_filename
        text_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(text_file_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_text)
        
        # Step 4: Storing results and queuing Stage 2 (100% progress)
        contract.processing_message = "Stage 1: Text extraction completed, queuing classification"
        contract.processing_progress = 100
        contract.status = "preprocessing_completed"
        contract.processing_completed_at = datetime.utcnow()
        
        completion_log = ProcessingLog(
            contract_id=contract_id,
            level="INFO",
            message=f"Stage 1 completed successfully. Extracted {len(cleaned_text)} characters.",
            component="stage1_preprocessing",
            celery_task_id=self.request.id
        )
        db.add(completion_log)
        
        db.commit()
        
        # Queue Stage 2: Classification
        try:
            classification_task = celery_app.send_task(
                'tasks.stage2_classification.classify_contract',
                args=[contract_id],
                queue='contract_classification'
            )
            
            contract.celery_task_id = classification_task.id
            contract.processing_message = "Stage 1 completed, Stage 2 classification queued"
            db.commit()
            
            logger.info(f"Contract {contract_id} preprocessing completed, classification task {classification_task.id} queued")
            
        except Exception as e:
            logger.error(f"Failed to queue classification task for contract {contract_id}: {str(e)}")
            contract.processing_message = "Text extraction completed"
            db.commit()
            # Don't fail the preprocessing task if classification queuing fails
        
        self.update_state(state='SUCCESS', meta={'progress': 100, 'message': contract.processing_message})
        
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
        
        try:
            db = next(get_db())
            contract = db.query(Contract).filter(Contract.id == contract_id).first()
            if contract:
                contract.status = "failed"
                contract.processing_message = "Text extraction failed"
                contract.processing_progress = 0
                contract.error_message = str(e)
                contract.processing_completed_at = datetime.utcnow()
                
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
