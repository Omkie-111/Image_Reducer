from pydantic import BaseModel

class ProductBase(BaseModel):
    product_name: str
    input_image_urls: str
    
class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    output_image_urls: str
    request_id: str
    status: str
    
    class Config:
        orm_mode = True