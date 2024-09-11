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