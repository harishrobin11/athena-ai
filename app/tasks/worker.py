import time
from app.core.celery_app import celery_app
from app.core.logger import logger

@celery_app.task(bind=True, max_retries=3)
def process_document_task(self, document_id: int, user_id: int):
    """
    Background task to process, OCR, and embed a document into the RAG vector store.
    """
    logger.info(f"Starting background processing for document {document_id}")
    
    # Simulate heavy processing (OCR, chunking, embedding)
    for i in range(1, 11):
        time.sleep(0.5) # Simulate work
        # self.update_state(state='PROGRESS', meta={'current': i, 'total': 10})
        logger.info(f"Processing document {document_id}: {i*10}%")
        
    logger.info(f"Successfully processed document {document_id}")
    return {"status": "success", "document_id": document_id}

@celery_app.task(bind=True)
def run_workflow_task(self, workflow_id: int, event_data: dict):
    """
    Background task to execute a multi-step automation workflow.
    """
    logger.info(f"Executing workflow {workflow_id} in background")
    time.sleep(2) # Simulate execution
    return {"status": "success", "workflow_id": workflow_id}
