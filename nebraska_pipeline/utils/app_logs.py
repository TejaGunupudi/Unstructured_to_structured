import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger("azure.servicebus").setLevel(logging.WARNING)
logging.getLogger("azure.core.pipeline").setLevel(logging.CRITICAL)
log_handler = logging.getLogger(name="nebraska-fileprocessing-pipeline")
