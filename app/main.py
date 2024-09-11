from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn
from app.apis import upload, status, webhook
from app.db import models, database

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

app.include_router(upload.router, prefix="/api")
app.include_router(status.router, prefix="/api")
app.include_router(webhook.router, prefix="/api")
app.mount("/processed_images", StaticFiles(directory="processed_images"), name="processed_images")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
