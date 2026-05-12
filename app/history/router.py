from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from .manager import init_db, add_record, get_records, delete_record, update_record

router = APIRouter(prefix="/history", tags=["历史记录"])

class AddRecordRequest(BaseModel):
    type: str
    input_text: str
    output_data: dict

class UpdateRecordRequest(BaseModel):
    input_text: Optional[str] = None
    output_data: Optional[dict] = None

@router.on_event("startup")
async def startup():
    init_db()

@router.post("")
async def create_record(req: AddRecordRequest):
    record_id = add_record(req.type, req.input_text, req.output_data)
    return {"id": record_id, "message": "记录已保存"}

@router.get("")
async def list_records(type: Optional[str] = None, start: Optional[str] = None, end: Optional[str] = None):
    return get_records(type_filter=type, start_date=start, end_date=end)

@router.delete("/{record_id}")
async def remove_record(record_id: int):
    if not delete_record(record_id):
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"message": "记录已删除"}

@router.put("/{record_id}")
async def update_record_handler(record_id: int, req: UpdateRecordRequest):
    success = update_record(record_id, req.input_text, req.output_data)
    if not success:
        raise HTTPException(status_code=404, detail="记录不存在或未更新")
    return {"message": "记录已更新"}