from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from ..models import Contract, FileRecord, ContractClause
from ..schemas import ContractResponse, ContractStatusResponse
from .filesystem_service import FileSystemService
from .celery_service import CeleryService
from .preprocessing import PDFExtractor, TextCleaner, MetadataExtractor

logger = logging.getLogger(__name__)

class ContractService:
    def __init__(self):
        self.filesystem_service = FileSystemService()
        self.celery_service = CeleryService()
        self.pdf_extractor = PDFExtractor()
        self.text_cleaner = TextCleaner()
        self.metadata_extractor = MetadataExtractor()
    
    def create_contract(
        self, 
        db: Session, 
        file_bytes: bytes, 
        filename: str, 
        original_filename: str,
        state: str
    ) -> Dict[str, Any]:
        try:
            # Extract file metadata
            file_metadata = self.metadata_extractor.extract_file_metadata(
                file_bytes, filename, state
            )
            
            if not file_metadata["success"]:
                return {
                    "success": False,
                    "error": f"Metadata extraction failed: {file_metadata['error']}",
                    "contract": None
                }
            
            # Create contract record first
            bucket_name = f"contracts-{state.lower()}"
            
            contract = Contract(
                filename=filename,
                original_filename=original_filename,
                file_size=file_metadata["file_size"],
                file_hash=file_metadata["file_hash"],
                state=state,
                status="uploaded",
                storage_bucket=bucket_name,
                storage_object_key=f"{filename}"
            )
            
            db.add(contract)
            db.commit()
            db.refresh(contract)
            
            # Upload file to filesystem
            object_name = f"{contract.id}.pdf"
            upload_success = self.filesystem_service.upload_file(
                bucket_name, object_name, file_bytes
            )
            
            if not upload_success:
                db.delete(contract)
                db.commit()
                return {
                    "success": False,
                    "error": "Failed to upload file to storage",
                    "contract": None
                }
            
            contract.storage_object_key = object_name
            
            file_record = FileRecord(
                contract_id=contract.id,
                file_type="original",
                filename=filename,
                file_size=file_metadata["file_size"],
                mime_type="application/pdf",
                storage_bucket=bucket_name,
                storage_object_key=object_name
            )
            
            db.add(file_record)
            db.commit()
            
            return {
                "success": True,
                "error": None,
                "contract": contract
            }
            
        except Exception as e:
            logger.error(f"Contract creation failed: {str(e)}")
            db.rollback()
            return {
                "success": False,
                "error": str(e),
                "contract": None
            }
    
    def get_contract(self, db: Session, contract_id: str) -> Optional[Contract]:
        return db.query(Contract).filter(Contract.id == contract_id).first()
    
    def get_contracts(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        state: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Contract]:
        query = db.query(Contract)
        
        if state:
            query = query.filter(Contract.state == state)
        if status:
            query = query.filter(Contract.status == status)
        
        return query.offset(skip).limit(limit).all()
    
    def update_contract_status(
        self, 
        db: Session, 
        contract_id: str, 
        status: str,
        error_message: Optional[str] = None
    ) -> bool:
        try:
            contract = self.get_contract(db, contract_id)
            if not contract:
                return False
            
            contract.status = status
            if error_message:
                contract.error_message = error_message
            
            if status == "processing":
                contract.processing_started_at = datetime.utcnow()
            elif status in ["completed", "failed"]:
                contract.processing_completed_at = datetime.utcnow()
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Status update failed: {str(e)}")
            db.rollback()
            return False
    
    def queue_processing(self, db: Session, contract_id: str) -> Dict[str, Any]:
        try:
            contract = self.get_contract(db, contract_id)
            if not contract:
                return {
                    "success": False,
                    "error": "Contract not found",
                    "task_id": None
                }
            
            task_id = self.celery_service.queue_processing_task(contract_id)
            
            contract.celery_task_id = task_id
            contract.status = "queued"
            db.commit()
            
            return {
                "success": True,
                "error": None,
                "task_id": task_id
            }
            
        except Exception as e:
            logger.error(f"Processing queue failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "task_id": None
            }
    
    def get_processing_status(self, db: Session, contract_id: str) -> Dict[str, Any]:
        try:
            contract = self.get_contract(db, contract_id)
            if not contract:
                return {
                    "success": False,
                    "error": "Contract not found",
                    "status": None
                }
            
            task_status = None
            progress = None
            
            if contract.celery_task_id:
                task_info = self.celery_service.get_task_status(contract.celery_task_id)
                task_status = task_info.get("status")
                progress = task_info.get("progress", 0)
            
            return {
                "success": True,
                "error": None,
                "status": {
                    "contract_id": str(contract.id),
                    "status": contract.status,
                    "progress": progress,
                    "message": contract.error_message,
                    "created_at": contract.created_at,
                    "processing_started_at": contract.processing_started_at,
                    "processing_completed_at": contract.processing_completed_at,
                    "task_status": task_status
                }
            }
            
        except Exception as e:
            logger.error(f"Status retrieval failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status": None
            }
    
    def get_contract_results(self, db: Session, contract_id: str) -> Dict[str, Any]:
        try:
            contract = self.get_contract(db, contract_id)
            if not contract:
                return {
                    "success": False,
                    "error": "Contract not found",
                    "results": None
                }
            
            if contract.status != "completed":
                return {
                    "success": False,
                    "error": "Contract processing not completed",
                    "results": None
                }
            
            clauses = db.query(ContractClause).filter(
                ContractClause.contract_id == contract.id
            ).all()
            
            summary = {
                "total_clauses": contract.total_clauses or 0,
                "standard_clauses": contract.standard_clauses or 0,
                "non_standard_clauses": contract.non_standard_clauses or 0,
                "processing_time": None
            }
            
            if contract.processing_started_at and contract.processing_completed_at:
                processing_time = contract.processing_completed_at - contract.processing_started_at
                summary["processing_time"] = str(processing_time)
            
            return {
                "success": True,
                "error": None,
                "results": {
                    "contract": contract,
                    "clauses": clauses,
                    "summary": summary
                }
            }
            
        except Exception as e:
            logger.error(f"Results retrieval failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "results": None
            }
    
    def delete_contract(self, db: Session, contract_id: str) -> bool:
        try:
            contract = self.get_contract(db, contract_id)
            if not contract:
                return False
            
            self.filesystem_service.delete_file(
                contract.storage_bucket, 
                contract.storage_object_key
            )
            
            db.delete(contract)
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Contract deletion failed: {str(e)}")
            db.rollback()
            return False
