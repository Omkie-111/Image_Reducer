from sqlalchemy import Column, Integer, String, Text
from .database import Base

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, index=True)
    input_image_urls = Column(Text)
    output_image_urls = Column(Text)
    request_id = Column(String, unique=True, index=True)
    status = Column(String, default="Pending")
    
    
    