from loguru import logger
from threading import Thread
import time
from dcevaluator.utils.utils import build_log_tag, launch_func_in_thread

from PIL import Image
import base64
from io import BytesIO
import collections
import numpy as np
import cv2

class AutoController:
    def __init__(self, client, brain, event_handler, buffer_requests_size = 4):
        """
        Manual Controller with Hardware

        :param client: Client instance
        :param brain: Brain instance to do the predictions (Artificial Intelligence)
        :param event_handler: Event Handler instance
        :param buffer_requests_size: Size of buffer of requests
        """
        self.client = client
        self.event_handler = event_handler
        self.brain = brain
        self.buffer_requests_size = buffer_requests_size

        self.running = True
        self.deque = collections.deque(maxlen = self.buffer_requests_size)
        self.event_handler.on_telemetry = launch_func_in_thread(self.on_telemetry)

        self.controller_thread = Thread(target=self.loop)
        self.controller_thread.start()

    def loop(self):
        """
        Process request from the hardware
        """
        self.event_handler.car_controller_is_ready = True
        while self.running:
            logger.debug(build_log_tag(car_controller_is_ready=self.event_handler.car_controller_is_ready, car_is_driving=self.event_handler.car_is_driving))
            
            if self.event_handler.car_is_ready and self.event_handler.car_is_driving and len(self.deque) > 0:
                logger.debug(">>> Predict Now")
                request = self.deque.pop()
                base64_img = request["image"]
                byte_string_img = base64.b64decode(base64_img)
                byte_img = BytesIO(byte_string_img)
                img = np.array(Image.open(byte_img))

                speed = request["speed"]
                accel_x = request["accel_x"]
                accel_y = request["accel_y"]
                accel_z = request["accel_z"]
                gyro_x = request["gyro_x"]
                gyro_y = request["gyro_y"]
                gyro_z = request["gyro_z"]

                angle, throttle, brake = self.brain.predict(img, 
                                                            speed,
                                                            accel_x, 
                                                            accel_y, 
                                                            accel_z, 
                                                            gyro_x, 
                                                            gyro_y, 
                                                            gyro_z
                                                            )
                # To show in realtime the input given to the Brain
                ##cv2.imshow('view', cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                ##cv2.waitKey(1)

                # The AI takes so long to predict that we have to check if the state of the game has not changed before sending an instruction.
                # In fact, sometimes when the car was reset, an instruction to control the car was sent slightly after the reset. 
                # However, just before predicting the action, the game state allowed it. 
                if self.event_handler.car_is_ready and self.event_handler.car_is_driving:
                    self.client.send_car_control_request(angle, throttle, brake)
    
    def on_telemetry(self, request):
        """
        When a telemetry request is received

        :param request: a dict representing the request (telemetry)
        """
        self.deque.append(request)
    
    def stop(self):
        """
        Stop the controller
        """
        self.client.send_quit_app_request()
        self.event_handler.car_is_driving = False
        self.running = False