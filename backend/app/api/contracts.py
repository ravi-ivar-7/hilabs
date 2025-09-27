from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import uuid
from datetime import datetime

from ..core.database import get_db
from ..models import Contract, ContractClause
from ..schemas import (
    ContractResponse, 
    ContractStatusResponse, 
    ContractResultsResponse,
    ClauseResponse
)
from ..utils.response_utils import create_success_response, create_error_response
from ..utils.file_utils import validate_file, sanitize_filename, generate_file_hash
from ..services.contract_service import ContractService

router = APIRouter()

@router.post("/upload", response_model=dict)
async def upload_contract(
    file: UploadFile = File(...),
    state: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        if not validate_file(file, state):
            return create_error_response(
                message="Invalid file or state",
                error="FILE_VALIDATION_ERROR"
            )
        
        file_content = await file.read()
        file_hash = generate_file_hash(file_content)
        
        existing_contract = db.query(Contract).filter(Contract.file_hash == file_hash).first()
        if existing_contract:
            return create_error_response(
                message="File already uploaded",
                error="DUPLICATE_FILE"
            )
        
        sanitized_filename = sanitize_filename(file.filename)
        contract_service = ContractService()
        
        result = contract_service.create_contract(
            db, file_content, sanitized_filename, file.filename, state
        )
        
        if not result["success"]:
            return create_error_response(
                message="Contract creation failed",
                error=result["error"]
            )
        
        contract = result["contract"]
        
        queue_result = contract_service.queue_processing(db, str(contract.id))
        if not queue_result["success"]:
            return create_error_response(
                message="Failed to queue processing",
                error=queue_result["error"]
            )
        
        return create_success_response(
            data=ContractResponse.from_orm(contract).dict(),
            message="Contract uploaded successfully"
        )
        
    except Exception as e:
        return create_error_response(
            message="Upload failed",
            error=str(e)
        )

@router.get("/{contract_id}/status", response_model=dict)
async def get_contract_status(
    contract_id: str,
    db: Session = Depends(get_db)
):
    try:
        contract_service = ContractService()
        result = contract_service.get_processing_status(db, contract_id)
        
        if not result["success"]:
            if "not found" in result["error"]:
                raise HTTPException(status_code=404, detail="Contract not found")
            return create_error_response(
                message="Failed to get status",
                error=result["error"]
            )
        
        return create_success_response(
            data=result["status"],
            message="Status retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return create_error_response(
            message="Failed to get status",
            error=str(e)
        )

@router.get("/{contract_id}/results", response_model=dict)
async def get_contract_results(
    contract_id: str,
    db: Session = Depends(get_db)
):
    try:
        contract_service = ContractService()
        result = contract_service.get_contract_results(db, contract_id)
        
        if not result["success"]:
            if "not found" in result["error"]:
                raise HTTPException(status_code=404, detail="Contract not found")
            return create_error_response(
                message="Failed to get results",
                error=result["error"]
            )
        
        contract_data = result["results"]["contract"]
        clauses_data = result["results"]["clauses"]
        summary_data = result["results"]["summary"]
        
        clause_responses = [ClauseResponse.from_orm(clause) for clause in clauses_data]
        
        results_response = ContractResultsResponse(
            contract=ContractResponse.from_orm(contract_data),
            clauses=clause_responses,
            summary=summary_data
        )
        
        return create_success_response(
            data=results_response.dict(),
            message="Results retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return create_error_response(
            message="Failed to get results",
            error=str(e)
        )

@router.get("/{contract_id}", response_model=dict)
async def get_contract(
    contract_id: str,
    db: Session = Depends(get_db)
):
    try:
        contract_service = ContractService()
        result = contract_service.get_contract(db, contract_id)
        
        if not result["success"]:
            if "not found" in result["error"]:
                raise HTTPException(status_code=404, detail="Contract not found")
            return create_error_response(
                message="Failed to get contract",
                error=result["error"]
            )
        
        contract_response = ContractResponse.from_orm(result["contract"])
        
        return create_success_response(
            data=contract_response.dict(),
            message="Contract retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return create_error_response(
            message="Failed to get contract",
            error=str(e)
        )
