from threading import Thread
import time

class ManualController:
    def __init__(self, client, hardware, event_handler, delay_before_check = 0.016):
        """
        Manual Controller with Hardware

        :param client: Client instance
        :param hardware: Hardware instance
        """
        self.client = client
        self.hardware = hardware
        self.event_handler = event_handler

        self.delay_before_check = delay_before_check

        self.running = True
    
        self.controller_thread = Thread(target=self.loop)
        self.controller_thread.start()

    def loop(self):
        while self.running:
            time.sleep(self.delay_before_check)
            if self.event_handler.car_is_ready:
                if not self.event_handler.car_is_driving and self.hardware.get_start_car():
                    self.event_handler.car_is_driving = True

                if self.event_handler.car_is_driving:
                    angle = self.hardware.get_angle_controller()
                    throttle = self.hardware.get_throttle_controller()
                    brake = self.hardware.get_brake_controller()
                    self.client.send_car_control_request(angle, throttle, brake)

                if self.hardware.get_reset_controller():
                    self.client.send_reset_car_request()
                    self.event_handler.car_is_driving = False
                
                if self.hardware.get_exit_app_controller():
                    self.client.send_quit_app_request()
                    self.event_handler.car_is_driving = False
                    self.running = False

