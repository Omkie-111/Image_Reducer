from sqlalchemy import Column, Integer, String, Float
from app.db.database import Base

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True, index=True)
    serial_number = Column(Integer, index=True)
    product_name = Column(String, index=True)
    input_image_urls = Column(String, index=True)
    status = Column(String, default="pending")
    output_image_urls = Column(String, default="")
