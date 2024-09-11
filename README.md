# Image Extractor

## Project Overview
This project demonstrates how to build a production-ready asynchronous image processing API using FastAPI, SQLAlchemy, Celery, and Docker. The application allows users to upload a CSV file with product details, process images associated with the products asynchronously, and provides endpoints to check the status of the tasks and handle webhooks for updates.

## Table of Contents
1. [Project Structure](#project-structure)
2. [Setup Instructions](#setup-instructions)
3. [Database Configuration](#database-configuration)
4. [API Endpoints](#api-endpoints)
5. [Running the Application](#running-the-application)
6. [CSV Validation](#csv-validation)
7. [Celery Workers](#celery-workers)
8. [Celery Worker Functions Documentation](#celery-worker-functions-documentation)
9. [Webhook Handling](#webhook-handling)
10. [Conclusion](#conclusion)

## Project Structure
```
image_extractor/
│
├── app/
│   ├── apis/
│   │   ├── __init__.py
│   │   ├── status.py
│   │   ├── upload.py
│   │   └── webhook.py
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── crud.py
│   │   ├── database.py
│   │   ├── models.py
│   │   └── schema.py
│   │
│   ├── worker/
│   │   ├── __init__.py
│   │   ├── image_processing.py
│   │   ├── worker_config.py
│   │
│   ├── db_dependency.py
│   ├── main.py
│   └── requirements.txt
│
├── .env
├── docker-compose.yml
├── Dockerfile
└── README.md
```

## Setup Instructions

### Prerequisites
- Docker
- Docker Compose

### Clone the Repository
```sh
git clone https://github.com/Omkie-111/image_extractor.git
cd image_extractor
```

### Environment Variables
Create a `.env` file with the following content:
```env
DATABASE_URL=postgresql://user:password@db:5432/dbname
REDIS_URL=redis://redis:6379/0
```

### Install Dependencies
```sh
pip install -r app/requirements.txt
```

### Build and Start Services
```sh
docker-compose up --build
```

## Database Configuration

### `app/database.py`
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://user:password@db:5432/dbname"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    Base.metadata.create_all(bind=engine)
```

### Initialize the Database
```python
from app.database import init_db
init_db()
```

## API Endpoints

### `app/apis/upload.py`
```python
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
```
### `app/apis/status.py`
```python
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
```

## Running the Application

### Start the Application
```sh
docker-compose up --build
```

Navigate to `http://localhost:8000` to access the FastAPI application.

## CSV Validation

The upload API includes validation of the CSV file format. It ensures that the file contains the required columns before processing it:
- `Serial Number`
- `Product Name`
- `Input Image Urls`
  
## Celery Workers

### `app/worker/image_processing.py`
```python
import aiohttp
import asyncio
from PIL import Image
from io import BytesIO
from celery import Celery
from app.db.database import SessionLocal
from app.db import crud
import requests

celery = Celery('workers')
celery.conf.broker_url = "redis://redis:6379/0"
celery.conf.result_backend = "redis://redis:6379/0"

@celery.task()
def process_images(request_id):
    db = SessionLocal()
    product = crud.get_product_by_request_id(db, request_id)
    if not product:
        return
    
    input_urls = product.input_image_urls.split(',')
    
    async def download_image(url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return Image.open(BytesIO(await response.read()))
                return None
            
    async def handle_images(urls):
        tasks = [download_image(url) for url in urls]
        images = await asyncio.gather(*tasks)
        processed_images = []
        for image in images:
            if image:
                buffer = BytesIO()
                image.save(buffer, format="JPEG", quality=50)
                processed_images.append(buffer)
        return processed_images
    
    processed_images = asyncio.run(handle_images(input_urls))
    output_urls = ["processed_image_path"]*len(processed_images)
    
    # Call the status update webhook
    webhook_url = "http://web:8000/api/webhook"
    payload = {
        "request_id" : request_id,
        "status" : "Completed",
        "output_image_urls" : ",".join(output_urls)
    }
    response = requests.post(webhook_url, json=payload)
    if response.status_code != 200:
        print("Failed to trigger status change")
        
    db.close()
```

### `app/worker/worker_config.py`
```python
from app.worker.image_processing import celery

celery.conf.update(
    task_routes={
        'worker.image_processing.process_images': 'main-queue',
    }
)

if __name__ == "__main__":
    celery.start()
```

### Start Celery Worker
If needed, you can manually start a Celery worker:
```sh
docker-compose run --rm celery_worker celery -A app.worker.worker_config worker --loglevel=info
```

## Celery Worker Functions Documentation

### 1. `process_images(request_id: int)`
- **Description**: Asynchronously processes images associated with a product upload.
- **Functionality**: Downloads, resizes, and saves images. Updates product status and triggers a webhook upon completion.
- **Key Features**: Uses `aiohttp` for asynchronous HTTP requests and `PIL` for image processing.

### 2. `download_image(url: str)`
- **Description**: Asynchronously downloads an image from a given URL.
- **Functionality**: Fetches image data using `aiohttp`. Returns `PIL.Image` object if successful, `None` on failure.

### 3. `handle_images(urls: List[str])`
- **Description**: Asynchronously handles multiple image downloads and processing.
- **Functionality**: Concurrently downloads and processes images. Returns processed image buffers.

## Webhook Handling

The webhook endpoint is used to update the status of the product once the image processing is completed. This endpoint is called by the Celery worker upon completion of the task.

### `app/apis/webhook.py` Webhook Endpoint
```python
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
```

## Conclusion

This project demonstrates how to integrate FastAPI with SQLAlchemy, Celery, Redis, and PostgreSQL for handling long-running tasks, validating file uploads, and managing task statuses with webhooks. The use of Docker ensures that the application can be easily deployed and scaled. Feel free to customize and extend this setup based on your specific requirements.

## API Endpoints

### Upload CSV
Endpoint: `/upload`
Method: `POST`
Description: Upload a CSV file for processing.
```sh
curl -F "file=@path/to/your/file.csv" http://localhost:8000/upload
```

### Check Task Status
Endpoint: `/status/{task_id}`
Method: `GET`
Description: Check the status of a background task.
```sh
curl http://localhost:8000/status/{task_id}
```
