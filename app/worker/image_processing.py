import aiohttp
import asyncio
from PIL import Image
from io import BytesIO
from celery import Celery
from sqlalchemy.orm import sessionmaker
from db.database import engine, SessionLocal
from db import crud, models
import requests

celery = Celery(__name__, broker='redis://localhost:6379/0')

@celery.task
def process_images(request_id):
    Session = sessionmaker(bind=engine)
    db = Session()
    
    product = crud.get_product_by_request_id(db, request_id)
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
    webhook_url = "http://localhost:8000/webhook/"
    payload = {
        "request_id" : request_id,
        "status" : "Completed",
        "output_image_urls" : ",".join(output_urls)
    }
    response = requests.post(webhook_url, json=payload)
    if response.status_code != 200:
        print("Failed to trigger status change")
        
    db.close()