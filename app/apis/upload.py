from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.db import crud, schema
from app.worker import image_processing
from app.db_dependency import get_db
import pandas as pd

router = APIRouter()

@router.post("/upload", response_model=schema.ProductList)
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        df = pd.read_csv(file.file)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid CSV file format")

    required_columns = {'Serial Number', 'Product Name', 'Input Image Urls'}
    if not required_columns.issubset(df.columns):
        raise HTTPException(status_code=400, detail=f"CSV file must contain the following columns: {required_columns}")

    products = []
    for _, row in df.iterrows():
        product = schema.ProductCreate(
            serial_number=row['Serial Number'],
            product_name=row['Product Name'],
            input_image_urls=row['Input Image Urls']
        )
        db_product = crud.create_product(db=db, product=product)
        products.append(db_product)
        image_processing.process_images.delay(db_product.id)

    return {"products": products}
