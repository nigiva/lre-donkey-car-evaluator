import begin
import sys
from loguru import logger
import time

from dcevaluator.communication.dc_client import DonkeyCarClient
from dcevaluator.hardware.joystick import JoystickController
from dcevaluator.event.event_handler import EventHandler
from dcevaluator.controller.auto_controller import AutoController
from dcevaluator.evaluator.evaluator import Evaluator
from dcevaluator.controller.brain import Brain
from dcevaluator.utils.utils import build_log_tag

logger.remove()
logger.add(sys.stdout, level="INFO")

@begin.start
def run(model_path,
        evaluation_name = "No Name", 
        host = "127.0.0.1", 
        port = "9091",
        evaluation_scene = "roboracingleague_1",
        log_path = "last_eval.log",

        nbr_turns_limit = "10",
        nbr_epochs = "10",
        max_time_to_wait = "10",
        delay_between_check_interval = "0.016",
        delay_before_launch_car = "5",

        poll_socket_sleep_sec = "0.016",
        buffer_message_size_read = "16384",
        deltatime_to_compute_fps = "5.0",
        margin_before_car_leaving_road = "6.0",
        deltatime_min_between_turns = "10.0",
        node_after_start_detection_turn = "105",
        deltatime_max_between_nodes = "5",
        deltatime_max_after_driving_to_reach_first_node = 10,

        buffer_requests_size = "4",
        ):
    """
    Donkey Car Evaluator

    This program will evaluate the performance of a model by running it a number of times in a simulator 
    and displaying the results obtained (number of laps, time taken, off road, timout, ...)

    :param model_path: Path of the model to evaluate
    :param evaluation_name: Name of the evaluation
    :param host: host to connect to a server like ip address with string
    :param port: port to connect to a server with int
    :param evaluation_scene: scene to load before the evaluation
    :log_path: the path of the generated log file


    EVALUATOR
    ---------
    :param nbr_turns_limit: limit number of turns from which the evaluation is stopped (to avoid that the car drives to infinity).
    :param nbr_epochs: number of epochs, i.e. the number of times the experiment is reproduced. This prevents us from evaluating once and having surprising results on a stroke of luck.
    :param max_time_to_wait: waiting time for a controller ready to drive the car.
    :param delay_between_check_interval: delay between each verification interval when waiting for a controller to be ready.
    :param delay_before_launch_car: delay time after a scene reset before launching the car. This allows us to be sure that all components are loaded before starting the evaluation.
    

    CLIENT
    ------
    :param poll_socket_sleep_sec: time to sleep before polling socket
    :param buffer_message_size_read: number of bits to read into the socket
    :param delatime_to_compute_fps: deltatime between computation of the FPS
    :param margin_before_car_leaving_road: distance from the center of the road at the active node to the car. Maximum value from which it can be considered that the car has left the road
    :param deltatime_min_between_turns: minimum time interval between two turns from which we can count a turn (incrementation)
    :param node_after_start_detection_turn: node from which we can possibly count a turn. (To avoid false positives on the rest of the road)
    :param deltatime_max_between_nodes: Maximum time interval to travel the distance between two nodes. If the vehicle takes too long, it is probably stuck somewhere but not far enough off the road to be considered 'off road'.
    :param deltatime_max_after_driving_to_reach_first_node: Maximum time interval for the car to reach a node if its default settings have not been changed when the car is launched. This is the case when the car moves before the real start and the evaluator has not captured this departure because the simulator does not respond.

    CONTROLLER
    ----------
    :param buffer_requests_size: Size of buffer of requests

    """

    logger.add(log_path, level="DEBUG")

    logger.info(build_log_tag("Donkey Car Evaluator", "BEGIN"))
    logger.info(build_log_tag(evaluation_name=evaluation_name))
    logger.info(build_log_tag(host=host))
    logger.info(build_log_tag(port=port))
    logger.info(build_log_tag(evaluation_scene=evaluation_scene))
    logger.info(build_log_tag(nbr_turns_limit=nbr_turns_limit))
    logger.info(build_log_tag(nbr_epochs=nbr_epochs))
    logger.info(build_log_tag(log_path=log_path))

    logger.debug(build_log_tag(max_time_to_wait=max_time_to_wait))
    logger.debug(build_log_tag(delay_between_check_interval=delay_between_check_interval))
    logger.debug(build_log_tag(delay_before_launch_car=delay_before_launch_car))
    logger.debug(build_log_tag(poll_socket_sleep_sec=poll_socket_sleep_sec))
    logger.debug(build_log_tag(buffer_message_size_read=buffer_message_size_read))
    logger.debug(build_log_tag(deltatime_to_compute_fps=deltatime_to_compute_fps))
    logger.debug(build_log_tag(margin_before_car_leaving_road=margin_before_car_leaving_road))
    logger.debug(build_log_tag(deltatime_min_between_turns=deltatime_min_between_turns))
    logger.debug(build_log_tag(node_after_start_detection_turn=node_after_start_detection_turn))
    logger.debug(build_log_tag(deltatime_max_between_nodes=deltatime_max_between_nodes))
    logger.debug(build_log_tag(deltatime_max_after_driving_to_reach_first_node=deltatime_max_after_driving_to_reach_first_node))
    logger.debug(build_log_tag(buffer_requests_size=buffer_requests_size))

    event_handler = EventHandler()

    client = DonkeyCarClient(event_handler, host, int(port), 
                            poll_socket_sleep_sec=float(poll_socket_sleep_sec), 
                            buffer_message_size_read=int(buffer_message_size_read), 
                            deltatime_to_compute_fps=float(deltatime_to_compute_fps), 
                            margin_before_car_leaving_road=float(margin_before_car_leaving_road),
                            deltatime_min_between_turns=float(deltatime_min_between_turns), 
                            node_after_start_detection_turn=int(node_after_start_detection_turn), 
                            deltatime_max_between_nodes=float(deltatime_max_between_nodes),
                            deltatime_max_after_driving_to_reach_first_node=float(deltatime_max_after_driving_to_reach_first_node)
                            )
    client.connect()
    logger.info(build_log_tag("RESET SCENE", "WAITING...", delay=10))
    client.send_exit_scene_request()
    # let some time for the simulator
    time.sleep(10)
    logger.info(build_log_tag("RESET SCENE", "DONE"))
    client.send_load_scene_request(evaluation_scene)

    # Mode Manual
    ##hardware = JoystickController()
    ##controller = ManualController(client, hardware, event_handler)

    # Mode Auto
    brain = Brain(model_path)
    controller = AutoController(client, brain, event_handler, buffer_requests_size=int(buffer_requests_size))

    evaluator = Evaluator(event_handler, controller, nbr_turns_limit=int(nbr_turns_limit), 
                                                     nbr_epochs=int(nbr_epochs), 
                                                     max_time_to_wait=float(max_time_to_wait),
                                                     delay_between_check_interval=float(delay_between_check_interval), 
                                                     delay_before_launch_car=float(delay_before_launch_car)
                                                     )


