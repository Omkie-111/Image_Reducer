from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import crud, schema
from app.db_dependency import get_db

router = APIRouter()

@router.get("/status/{request_id}", response_model=schema.Product)
async def check_status(request_id: int, db: Session = Depends(get_db)):
    db_product = crud.get_product_by_request_id(db, request_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product
