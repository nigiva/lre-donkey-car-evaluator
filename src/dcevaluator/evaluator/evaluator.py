from loguru import logger
import time
from threading import Thread
from dcevaluator.utils.utils import launch_func_in_thread
from dcevaluator.utils.utils import build_log_tag

class Evaluator:
    def __init__(self, event_handler, 
                       controller, 
                       nbr_turns_limit = 10,
                       nbr_epochs = 10,
                       max_time_to_wait = 10,
                       delay_between_check_interval = 1/60,
                       delay_before_launch_car = 5
                       ):
        """
        Evaluator

        :param event_handler: Event Handler instance.
        :param controller: Controller instance.
        :param nbr_turns_limit: limit number of turns from which the evaluation is stopped (to avoid that the car drives to infinity).
        :param nbr_epochs: number of epochs, i.e. the number of times the experiment is reproduced. This prevents us from evaluating once and having surprising results on a stroke of luck.
        :param max_time_to_wait: waiting time for a controller ready to drive the car.
        :param delay_between_check_interval: delay between each verification interval when waiting for a controller to be ready.
        :param delay_before_launch_car: delay time after a scene reset before launching the car. This allows us to be sure that all components are loaded before starting the evaluation.
        """
        self.event_handler = event_handler
        self.controller = controller
        self.nbr_turns_limit = nbr_turns_limit
        self.nbr_epochs = nbr_epochs
        self.max_time_to_wait = max_time_to_wait
        self.delay_between_check_interval = delay_between_check_interval
        self.delay_before_launch_car = delay_before_launch_car

        self.current_epoch = 1

        self.event_handler.on_car_loaded = launch_func_in_thread(self.wait_car_controller)
        self.event_handler.on_car_leaving_road = launch_func_in_thread(self.when_car_is_leaving)
        self.event_handler.on_timeout = launch_func_in_thread(self.when_timeout)
        self.event_handler.each_turn = launch_func_in_thread(self.check_limit_turn)

        self.time_start_waiting = time.time()

    def wait_car_controller(self, *args, **kwargs):
        """
        Wait until the car controller is ready
        """
        logger.info(build_log_tag("WAITING", message="Wait until the car controller is ready"))
        self.time_start_waiting = time.time()
        while not self.event_handler.car_controller_is_ready:
            time.sleep(self.delay_between_check_interval)
            if time.time() - self.time_start_waiting > self.max_time_to_wait:
                logger.critical("Timeout : No car controller ready to drive !")
                logger.critical(build_log_tag("TIMEOUT", message="No car controller ready to drive !", max_time=self.max_time_to_wait))
                raise RuntimeError("Timeout : No car controller ready to drive !")
        self.run()

    def run(self):
        """
        Wait some secondes and launch car
        """
        self.event_handler.car_is_driving = False
        logger.success(build_log_tag("EVALUATION", "BEGIN", epoch=self.current_epoch))
        logger.info(build_log_tag("WAITING", message="Waiting for the complete loading of all components", delay_before_launch_car=self.delay_before_launch_car))
        time.sleep(self.delay_before_launch_car)
        # This reset is important at this location.
        # If it is done too early (i.e. at the time of sending the reset request) and if there is a lot of latency, then this reset may be corrupted by the old state of the car.
        # Therefore, it is important to wait a little while for the simulator to load and then reset when the car state is stable in the simulator.
        self.event_handler.reset_state()
        self.event_handler.car_is_ready = True
        self.event_handler.car_is_driving = True
        logger.debug(build_log_tag("RESET STATE", car_is_ready=self.event_handler.car_is_ready, car_is_driving=self.event_handler.car_is_driving))
        logger.info(build_log_tag("LET'S GO", message="Launch the car !"))
    
    def when_car_is_leaving(self, *args, **kwargs):
        """
        When a car is leaving the road
        """
        self.end_epoch()

    def when_timeout(self, *args, **kwargs):
        """
        When there is a timeout
        """
        self.end_epoch()

    def end_epoch(self):
        """
        Process the end of a epoch
        """
        self.end_evaluation_and_summary()
        self.current_epoch += 1
        if self.current_epoch > self.nbr_epochs:
            self.stop()
        else:
            self.controller.client.send_reset_car_request()
            self.event_handler.car_is_driving = False
            self.run()
    
    def check_limit_turn(self, *args, **kwargs):
        """
        Check if the current turn has reached the limit
        """
        if self.event_handler.turn >= self.nbr_turns_limit:
            logger.warning(build_log_tag("LIMIT", message="Number of limit turns reached", nbr_turns_limit=self.nbr_turns_limit))
            self.end_epoch()

    def end_evaluation_and_summary(self):
        """
        Log the end of evaluation and print a summary
        """
        logger.success(build_log_tag("EVALUATION", "END", epoch=self.current_epoch))
        logger.info(build_log_tag("SUMMARY", epoch=self.current_epoch, 
                                                turn=self.event_handler.turn,
                                                last_node=self.event_handler.last_node,
                                                first_time_on_first_turn=self.event_handler.first_time_on_first_turn,
                                                last_time_on_last_turn=self.event_handler.last_time_on_last_turn,
                                                last_time_on_last_node=self.event_handler.last_time_on_last_node,
                                                ))
    
    def stop(self):
        """
        Stop the evaluator
        """
        self.controller.stop()
        logger.info(build_log_tag("Donkey Car Evaluator", "END"))        