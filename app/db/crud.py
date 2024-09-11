from sqlalchemy.orm import Session
from app.db.models import Product
from app.db.schema import ProductCreate

def create_product(db: Session, product: ProductCreate):
    db_product = Product(
        serial_number=product.serial_number,
        product_name=product.product_name,
        input_image_urls=product.input_image_urls
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def get_product_by_request_id(db: Session, request_id: int):
    return db.query(Product).filter(Product.id == request_id).first()

def update_product_status(db: Session, request_id: int, status: str, output_image_urls: str = ""):
    db_product = db.query(Product).filter(Product.id == request_id).first()
    if db_product:
        db_product.status = status
        db_product.output_image_urls = output_image_urls
        db.commit()
        db.refresh(db_product)
    return db_product
