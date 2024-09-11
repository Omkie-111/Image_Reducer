from app.worker.image_processing import celery

celery.conf.update(
    task_routes={
        'worker.image_processing.process_images': 'main-queue',
    }
)

if __name__ == "__main__":
    celery.start()
