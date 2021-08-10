import begin
import sys
from loguru import logger

from dcevaluator.communication.dc_client import DonkeyCarClient
from dcevaluator.hardware.joystick import JoystickController
from dcevaluator.event.event_handler import EventHandler
from dcevaluator.controller.manual_controller import ManualController
from dcevaluator.evaluator.evaluator import Evaluator

logger.remove()
logger.add(sys.stdout, level="INFO")

@begin.start
def run(name = "No Name", host = "127.0.0.1", port = "9091"):
    logger.info("Starting Donkey Car Evaluator")
    logger.info("Evaluation Name : " + name)
    logger.info("Evaluation Host : " + host)
    logger.info("Evaluation Port : " + port)

    event_handler = EventHandler()

    client = DonkeyCarClient(event_handler, host, int(port))
    client.connect()

    hardware = JoystickController()
    controller = ManualController(client, hardware, event_handler)
    evaluator = Evaluator(event_handler, controller)


