from threading import Thread
import time
from dcevaluator.utils.utils import launch_func_in_thread

from PIL import Image
import base64
from io import BytesIO
import collections
import numpy as np
import cv2

class ManualController:
    def __init__(self, client, hardware, event_handler, delay_before_check = 0.016):
        """
        Manual Controller with Hardware

        :param client: Client instance
        :param hardware: Hardware instance
        :param event_handler: Event Handler instance
        :param delay_before_check: Delay between each hardware status check
        """
        self.client = client
        self.hardware = hardware
        self.event_handler = event_handler

        self.delay_before_check = delay_before_check

        self.running = True
        self.deque = collections.deque(maxlen = 4)
        self.event_handler.on_telemetry = launch_func_in_thread(self.on_telemetry)

        self.controller_thread = Thread(target=self.loop)
        self.controller_thread.start()

        Thread(target=self.loop_decode).start()
        

    def loop(self):
        """
        Process request from the hardware
        """
        while self.running:
            time.sleep(self.delay_before_check)
            if self.event_handler.car_is_ready:
                if not self.event_handler.car_controller_is_ready and self.hardware.get_start_car():
                    self.event_handler.car_controller_is_ready = True

                if self.event_handler.car_is_driving:
                    angle = self.hardware.get_angle_controller()
                    throttle = self.hardware.get_throttle_controller()
                    brake = self.hardware.get_brake_controller()
                    self.client.send_car_control_request(angle, throttle, brake)

                if self.hardware.get_reset_controller():
                    self.client.send_reset_car_request()
                    self.event_handler.car_is_driving = False
                
                if self.hardware.get_exit_app_controller():
                    self.stop()
    
    def loop_decode(self):
        while self.running:
            if len(self.deque) > 0: 
                base64_img = self.deque.pop()
                byte_string_img = base64.b64decode(base64_img)
                byte_img = BytesIO(byte_string_img)
                img = Image.open(byte_img)
                cv2.imshow('view', cv2.cvtColor(np.array(img), cv2.COLOR_BGR2RGB))
                cv2.waitKey(1)

    def on_telemetry(self, request):
        base64_img = request["image"]
        self.deque.append(base64_img)

    def stop(self):
        """
        Stop the controller
        """
        self.client.send_quit_app_request()
        self.event_handler.car_is_driving = False
        self.running = False

