from pydantic import BaseModel

class ProductBase(BaseModel):
    serial_number: int
    product_name: str
    input_image_urls: str

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    status: str
    output_image_urls: str

    class Config:
        orm_mode: True

class ProductList(BaseModel):
    products: list[Product]

    class Config:
        orm_mode: True
