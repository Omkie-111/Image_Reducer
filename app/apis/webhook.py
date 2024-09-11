from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db import crud
from app.db_dependency import get_db

router = APIRouter()

@router.post("/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    request_id = data.get("request_id")
    status = data.get("status")
    output_image_urls = data.get("output_image_urls", "")

    if not request_id or not status:
        raise HTTPException(status_code=400, detail="Invalid data")

    db_product = crud.update_product_status(db, request_id, status, output_image_urls)
    return {"message": "Status updated successfully"}
