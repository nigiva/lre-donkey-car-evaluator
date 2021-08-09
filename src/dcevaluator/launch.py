import begin
import sys
from loguru import logger

from dcevaluator.communication.basic_client import BasicClient

logger.remove()
logger.add(sys.stdout, level="TRACE")

@begin.start
def run(name = "No Name", host = "127.0.0.1", port = "9091"):
    logger.info("Starting Donkey Car Evaluator")
    logger.info("Evaluation Name : " + name)
    logger.info("Evaluation Host : " + host)
    logger.info("Evaluation Port : " + port)

    client = BasicClient(host, int(port))
    client.connect()