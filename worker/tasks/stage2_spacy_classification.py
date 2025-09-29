"""
Stage 2: spaCy-based Contract Classification Task
Celery task for classifying contract clauses using spaCy NLP and HiLabs analysis.
"""

import logging
import sys
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass, asdict

# Set up paths for Docker container or local development
if os.path.exists('/app'):
    sys.path.insert(0, "/app")
    if 'DATABASE_URL' not in os.environ:
        os.environ['DATABASE_URL'] = "sqlite:////app/data/contracts.db"
    UPLOAD_BASE_PATH = Path("/app/upload")
else:
    backend_path = Path(__file__).parent.parent.parent / "backend"
    sys.path.insert(0, str(backend_path))
    if 'DATABASE_URL' not in os.environ:
        os.environ['DATABASE_URL'] = f"sqlite:///{backend_path}/app/data/contracts.db"
    UPLOAD_BASE_PATH = Path(__file__).parent.parent.parent / "upload"

from celery_app import celery_app
from app.core.database import get_db, init_db
from app.models.contract import Contract, ContractClause, ProcessingLog, FileRecord
from templates.template_loader import TemplateLoader, TemplateClause
from classification.spacy_classifier import SpacyClassifier


logger = logging.getLogger(__name__)

@dataclass
class ClassificationDecision:
    """Classification decision for a single clause."""
    clause_id: int
    attribute: str
    template_used: str
    label: str
    score: float
    rule: str
    text: str
    confidence: str = ""

@celery_app.task(bind=True, name='tasks.stage2_spacy_classification.classify_contract')
def classify_contract(self, contract_id: str):
    """
    Main spaCy-based classification task that processes contract clauses.
    
    Args:
        contract_id: UUID of the contract to classify
    """
    try:
        db = next(get_db())
        
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise Exception(f"Contract not found: {contract_id}")
        
        if contract.status != 'preprocessing_completed':
            raise Exception(f"Contract {contract_id} is not ready for classification (status: {contract.status})")
        
        logger.info(f"Starting Stage 2 spaCy classification for contract {contract_id}")
        
        contract.status = "classifying"
        contract.processing_message = "Stage 2: Starting spaCy-based clause classification"
        contract.processing_progress = 0
        contract.processing_started_at = datetime.utcnow()
        
        log_entry = ProcessingLog(
            contract_id=contract_id,
            level="INFO",
            message="Stage 2: spaCy classification started",
            component="stage2_spacy_classification",
            celery_task_id=self.request.id
        )
        db.add(log_entry)
        db.commit()
        
        self.update_state(state='PROGRESS', meta={'progress': 0, 'message': 'Stage 2: Starting spaCy classification'})
        
        # Step 1: Load clause data (20% progress)
        contract.processing_message = "Stage 2: Loading extracted clauses"
        contract.processing_progress = 20
        db.commit()
        self.update_state(state='PROGRESS', meta={'progress': 20, 'message': 'Stage 2: Loading extracted clauses'})
        
        clauses_filename = f"{contract_id}_clauses.json"
        clauses_file_path = UPLOAD_BASE_PATH / contract.storage_bucket / clauses_filename
        
        if not clauses_file_path.exists():
            raise Exception(f"Clause data file not found: {clauses_file_path}")
        
        with open(clauses_file_path, 'r', encoding='utf-8') as f:
            clause_data = json.load(f)
        
        clauses = clause_data.get('clauses', [])
        logger.info(f"Loaded {len(clauses)} clauses for classification")
        
        # Step 2: Initialize classification components (40% progress)
        contract.processing_message = "Stage 2: Initializing spaCy classifier and templates"
        contract.processing_progress = 40
        db.commit()
        self.update_state(state='PROGRESS', meta={'progress': 40, 'message': 'Stage 2: Initializing spaCy classifier'})
        
        contract_state = "TN" if "TN" in contract.original_filename.upper() else "WA"
        
        template_loader = TemplateLoader()
        templates = template_loader.get_template_clauses(contract_state)
        target_attributes = template_loader.get_target_attributes()
        
        classifier = SpacyClassifier(
            templates=templates,
            target_attributes=target_attributes
        )
        
        init_log = ProcessingLog(
            contract_id=contract_id,
            level="INFO",
            message=f"Initialized spaCy classifier for {contract_state} state with {len(templates)} templates",
            component="spacy_classifier",
            celery_task_id=self.request.id
        )
        db.add(init_log)
        db.commit()
        
        # Step 3: Classify clauses (60% progress)
        contract.processing_message = "Stage 2: Classifying contract clauses"
        contract.processing_progress = 60
        db.commit()
        self.update_state(state='PROGRESS', meta={'progress': 60, 'message': 'Stage 2: Classifying clauses'})
        
        classification_results = classifier.classify_clauses(clauses)
        
        classification_log = ProcessingLog(
            contract_id=contract_id,
            level="INFO",
            message=f"Classified {len(classification_results)} clauses",
            component="spacy_classifier",
            celery_task_id=self.request.id
        )
        db.add(classification_log)
        db.commit()
        
        # Step 4: Save classification results (80% progress)
        contract.processing_message = "Stage 2: Saving classification results"
        contract.processing_progress = 80
        db.commit()
        self.update_state(state='PROGRESS', meta={'progress': 80, 'message': 'Stage 2: Saving results'})
        
        valid_classifications = [r for r in classification_results if r.label in ['Standard', 'Non-Standard', 'Ambiguous']]
        
        standard_count = len([r for r in valid_classifications if r.label == 'Standard'])
        non_standard_count = len([r for r in valid_classifications if r.label == 'Non-Standard'])
        ambiguous_count = len([r for r in valid_classifications if r.label == 'Ambiguous'])
        
        for result in valid_classifications:
            steps_json = json.dumps([{
                "step_name": step.step_name,
                "passed": step.passed,
                "score": step.score,
                "reason": step.reason
            } for step in result.steps]) if result.steps else None
            
            clause_record = ContractClause(
                contract_id=contract_id,
                clause_number=result.clause_id,
                attribute_name=result.attribute,
                clause_text=result.text,
                classification=result.label,
                confidence_score=int(result.score * 100),
                template_match_text=result.template_used,
                similarity_score=int(result.score * 100),
                match_type=result.rule,
                extraction_method="spacy_nlp",
                classification_steps=steps_json,
                template_attribute=result.attribute
            )
            db.add(clause_record)
        
        results_filename = f"{contract_id}_classification_results.json"
        results_file_path = UPLOAD_BASE_PATH / contract.storage_bucket / results_filename
        
        results_data = {
            "contract_id": contract_id,
            "classification_metadata": {
                "total_clauses": len(clauses),
                "classified_clauses": len(valid_classifications),
                "contract_state": contract_state,
                "templates_used": len(templates),
                "classification_method": "spacy_nlp",
                "classification_timestamp": datetime.utcnow().isoformat()
            },
            "results": [asdict(result) for result in classification_results]
        }
        
        with open(results_file_path, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)
        
        results_file_record = FileRecord(
            contract_id=contract_id,
            file_type="classification_results",
            filename=results_filename,
            file_size=results_file_path.stat().st_size,
            mime_type="application/json",
            storage_bucket=contract.storage_bucket,
            storage_object_key=results_filename,
            extraction_method="spacy_classification"
        )
        db.add(results_file_record)
        
        # Step 5: Complete classification (100% progress)
        contract.processing_message = "Stage 2: spaCy classification completed"
        contract.processing_progress = 100
        contract.status = "completed"
        contract.processing_completed_at = datetime.utcnow()
        
        contract.total_clauses = len(clauses)
        contract.standard_clauses = standard_count
        contract.non_standard_clauses = non_standard_count
        contract.ambiguous_clauses = ambiguous_count
        
        completion_log = ProcessingLog(
            contract_id=contract_id,
            level="INFO",
            message=f"Stage 2 completed. Results: {standard_count} Standard, {non_standard_count} Non-Standard, {ambiguous_count} Ambiguous",
            component="stage2_spacy_classification",
            celery_task_id=self.request.id
        )
        db.add(completion_log)
        
        db.commit()
        
        logger.info(f"Stage 2 spaCy classification completed for contract {contract_id}")
        
        return {
            "success": True,
            "contract_id": contract_id,
            "total_clauses": len(clauses),
            "classified_clauses": len(valid_classifications),
            "standard_count": standard_count,
            "non_standard_count": non_standard_count,
            "ambiguous_count": ambiguous_count,
            "classification_method": "spacy_nlp"
        }
        
    except Exception as e:
        logger.error(f"Stage 2 spaCy classification failed for contract {contract_id}: {str(e)}")
        
        try:
            db = next(get_db())
            contract = db.query(Contract).filter(Contract.id == contract_id).first()
            if contract:
                contract.status = "failed"
                contract.processing_message = f"Stage 2 classification failed: {str(e)}"
                contract.error_message = str(e)
                
                error_log = ProcessingLog(
                    contract_id=contract_id,
                    level="ERROR",
                    message=f"Stage 2 spaCy classification failed: {str(e)}",
                    component="stage2_spacy_classification",
                    celery_task_id=self.request.id
                )
                db.add(error_log)
                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update contract status on error: {str(db_error)}")
        
        return {
            "success": False,
            "error": str(e),
            "contract_id": contract_id
        }
