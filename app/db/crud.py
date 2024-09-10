from sqlalchemy.orm import Session 
from . import models, schema
import uuid

def create_product(db: Session, product: schema.ProductCreate):
    db_product = models.Product(
        product_name = product.product_name,
        input_image_url = product.input_image_urls,
        request_id = str(uuid.uuid4())
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def get_product_by_request_id(db: Session, request_id: str):
    return db.query(models.Product).filter(models.Product.request_id == request_id).first()

def update_product_status(db: Session, request_id: str, status: str, output_image_urls: str):
    db_product = get_product_by_request_id(db, request_id)
    db_product.status = status
    db_product.output_image_urls = output_image_urls
    db.commit()
    db.refresh(db_product)
    return db_product
    