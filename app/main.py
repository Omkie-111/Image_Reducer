from fastapi import FastAPI
import uvicorn
from app.apis import upload, status, webhook
from app.db import models, database

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

app.include_router(upload.router, prefix="/api")
app.include_router(status.router, prefix="/api")
app.include_router(webhook.router, prefix="/api")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
