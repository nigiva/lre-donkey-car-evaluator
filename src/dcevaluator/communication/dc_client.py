from loguru import logger
import time
from dcevaluator.communication.basic_client import BasicClient
import json
import re
from dcevaluator.utils.utils import replace_float_notation
from dcevaluator.utils.utils import build_log_tag

class DonkeyCarClient(BasicClient):

    def __init__(self, event_handler, 
                       host = "127.0.0.1", 
                       port = 9091,
                       poll_socket_sleep_sec = 0.016,
                       buffer_message_size_read = 16 * 1024,
                       deltatime_to_compute_fps = 5.0,
                       margin_before_car_leaving_road = 6.0,
                       deltatime_min_between_turns = 10.0,
                       node_after_start_detection_turn = 105,
                       deltatime_max_between_nodes = 5,
                       deltatime_max_after_driving_to_reach_first_node = 10
                       ):
        """
        Donkey Car Client

        :param event_handler: Event Handler instance
        :param host: host to connect to a server like ip address with string
        :param port: port to connect to a server with int
        :param poll_socket_sleep_sec: time to sleep before polling socket
        :param buffer_message_size_read: number of bits to read into the socket
        :param delatime_to_compute_fps: deltatime between computation of the FPS
        :param margin_before_car_leaving_road: distance from the center of the road at the active node to the car. Maximum value from which it can be considered that the car has left the road
        :param deltatime_min_between_turns: minimum time interval between two turns from which we can count a turn (incrementation)
        :param node_after_start_detection_turn: node from which we can possibly count a turn. (To avoid false positives on the rest of the road)
        :param deltatime_max_between_nodes: Maximum time interval to travel the distance between two nodes. If the vehicle takes too long, it is probably stuck somewhere but not far enough off the road to be considered 'off road'.
        :param deltatime_max_after_driving_to_reach_first_node: Maximum time interval for the car to reach a node if its default settings have not been changed when the car is launched. This is the case when the car moves before the real start and the evaluator has not captured this departure because the simulator does not respond.
        """
        super().__init__(host, port, poll_socket_sleep_sec, buffer_message_size_read, deltatime_to_compute_fps)
        self.event_handler = event_handler
        self.margin_before_car_leaving_road = margin_before_car_leaving_road
        self.deltatime_min_between_turns = deltatime_min_between_turns
        self.node_after_start_detection_turn = node_after_start_detection_turn
        self.deltatime_max_between_nodes = deltatime_max_between_nodes
        self.deltatime_max_after_driving_to_reach_first_node = deltatime_max_after_driving_to_reach_first_node

    def on_request_receive(self, request_string):
        """
        When a request is received

        :param request_string: The request as a string
        """
        super().on_request_receive(request_string)

        request = json.loads(replace_float_notation(request_string))

        if "msg_type" in request:
            msg_type = request["msg_type"]
            if msg_type == "scene_selection_ready":
                self.on_scene_selection_ready(request)
            elif msg_type == "scene_loaded":
                self.on_scene_loaded(request)
            elif msg_type == "car_loaded":
                self.on_car_loaded(request)
            elif request["msg_type"] == "telemetry":
                self.on_telemetry(request)
            else:
                logger.info(request_string)


    #############
    ### Event ###
    #############

    def on_scene_selection_ready(self, request):
        """
        When a the scene selection is ready

        :param request: a dict representing the request (telemetry)
        """
        self.event_handler.on_scene_selection_ready(request)
    
    def on_scene_loaded(self, request):
        """
        When a the scene is loaded

        :param request: a dict representing the request (telemetry)
        """
        self.event_handler.on_scene_loaded(request)

    def on_car_loaded(self, request):
        """
        When a car is loaded

        :param request: a dict representing the request (telemetry)
        """
        self.event_handler.on_car_loaded(request)
        self.event_handler.car_is_ready = True

    def on_telemetry(self, request):
        """
        When a the telemetry request is received

        :param request: a dict representing the request (telemetry)
        """
        self.event_handler.on_telemetry(request)

        # Distance from the center of the road at the active node to the car
        distance_center = request["cte"]
        active_node = request["activeNode"]
        current_turn = self.event_handler.turn

        # If the car goes too far off the road (limit < distance from the car) then consider it a "run off the road"      
        # Weird bug : to be sure that it won't catch the same error twice, I check that it is not a false positive with this `self.event_handler.last_node != -1`
        # It is a default value when a car is not driving
        if not self.event_handler.car_is_leaving \
            and self.event_handler.car_is_driving \
            and self.event_handler.last_node != -1 \
            and self.margin_before_car_leaving_road < abs(distance_center):
            self.on_car_leaving_road(request)
    
        if not self.event_handler.car_is_leaving and self.event_handler.car_is_driving:
            logger.debug(build_log_tag(turn=current_turn, active_node=active_node, last_node=self.event_handler.last_node, distance_center=distance_center))

            # When resetting a car, its first active node can be either node=0 or node=112
            # In the case of node=0 or maximum 1, we want to initialize the timers used for the turn counter statistics.
            # The default values of the timers have been initialized to 0 because their value is only known at Runtime
            # It is from this time frame that we will calculate the delays and other statistics
            if self.event_handler.first_time_on_first_turn == 0 and active_node <= 1:
                self.event_handler.init_turn_stat()
            
            # If the car passes the "finish" line (count a turn)
            if self.event_handler.last_node > self.node_after_start_detection_turn and active_node < self.event_handler.last_node:
                logger.debug(build_log_tag(first_time_on_first_turn=self.event_handler.first_time_on_first_turn, last_time_on_last_turn=self.event_handler.last_time_on_last_turn))
                
                # When resetting a car, its first active node can be either node=0 or node=112
                # In the case of node=node_after_start_detection_turn or maximum MAX_NODE, we want to initialize the timers used for the turn counter statistics.
                # The default values of the timers have been initialized to 0 because their value is only known at Runtime
                # It is from this time frame that we will calculate the delays and other statistics
                if self.event_handler.first_time_on_first_turn == 0:
                    self.event_handler.init_turn_stat()

                elif time.time() - self.event_handler.last_time_on_last_turn > self.deltatime_min_between_turns:
                    # Otherwise, if the turn can be counted because it has exceeded the minimum freezing time of the counter (to prevent the counter from shooting up for a short time) 
                    self.each_turn(request)
                
                # We update the statistics of the last node
                self.event_handler.last_node = active_node
                self.event_handler.last_time_on_last_node = time.time()
            
            # If we advance by one or more nodes compared to the last time
            if active_node > self.event_handler.last_node:
                self.each_node(request)
            
            # If the vehicle takes too long to reach the next node, it is probably stuck somewhere but not far enough off the road to be considered 'off road'.
            if self.event_handler.car_is_driving \
                and self.event_handler.last_time_on_last_node != -1 \
                and time.time() - self.event_handler.last_time_on_last_node > self.deltatime_max_between_nodes:
                
                self.on_timeout()
            
            # If the default values have not been changed (the car goes out of the field before the start of the race but the evaluator does not catch this event) 
            # then when it is allowed to run, the vehicle has 10 seconds to reach at least one node.
            if self.event_handler.car_is_driving \
                and self.event_handler.last_time_on_last_node == -1 :
                
                if self.event_handler.first_time_when_car_is_driving == -1:
                    self.event_handler.first_time_when_car_is_driving = time.time()
                elif time.time() - self.event_handler.first_time_when_car_is_driving > self.deltatime_max_after_driving_to_reach_first_node:
                    self.on_timeout()
            

            

    def on_exit_scene(self):
        """
        When scene is exited
        """
        self.event_handler.on_exit_scene()

    def on_quit_app(self):
        """
        When the app is quit
        """
        self.event_handler.on_quit_app()

    def each_turn(self, request):
        """
        At each turn

        :param request: a dict representing the request (telemetry)
        """
        self.event_handler.turn += 1

        self.event_handler.last_time_on_last_turn = time.time()
        delta = self.event_handler.last_time_on_last_turn - self.event_handler.first_time_on_first_turn

        logger.success(build_log_tag("NEW TURN", turn=self.event_handler.turn, deltatime=delta))
        self.event_handler.each_turn(request)

    def each_node(self, request):
        """
        At each node

        :param request: a dict representing the request (telemetry)
        """
        # We update the statistics of the last node
        self.event_handler.last_node = request["activeNode"]
        self.event_handler.last_time_on_last_node = time.time()

        self.event_handler.each_node(request)

    def on_car_leaving_road(self, request):
        """
        When a car leaves the road

        :param request: a dict representing the request (telemetry)
        """
        logger.error("Car is leaving the road !")
        logger.error(build_log_tag("ILLEGAL MOVE", message="Car is leaving the road", active_node=request["activeNode"], distance_center=request["cte"]))

        self.event_handler.on_car_leaving_road(request)
        self.event_handler.car_is_leaving = True

    def on_timeout(self):
        """
        At the timeout
        """
        logger.error("Timeout to reach the next node !")
        logger.error(build_log_tag("TIMEOUT", message="Timeout to reach the next node", max_time = self.deltatime_max_between_nodes))
        self.event_handler.on_timeout()
        self.event_handler.car_is_leaving = True
        

    ####################
    ### Send request ###
    ####################

    def send_get_protocol_version_request(self):
        """
        Ask for the version of the protocol. Will help know when changes are made to these messages.
        """
        request = dict()
        request["msg_type"] = "get_protocol_version"
        self.send_message(json.dumps(request))
    
    def send_get_scene_names_request(self):
        """
        Ask names of the scene you can load. (Menu only)
        """
        request = dict()
        request["msg_type"] = "get_scene_names"
        self.send_message(json.dumps(request))

    def send_load_scene_request(self, scene):
        """
        Asks the sim to load one of the scenes from the Menu screen. (Menu only)

        :param scene: generated_road | warehouse | sparkfun_avc | generated_track (or whatever list the sim returns from get_scene_names)
        """
        request = dict()
        request["msg_type"] = "load_scene"
        request["scene_name"] = str(scene)
        self.send_message(json.dumps(request))
    
    def send_car_config_request(self, body_style, body_r, body_g, body_b, car_name, font_size):
        """
        Once loaded, you may configure your car visual details (scene only)

        :param body_style: donkey | bare | car01 | cybertruck | f1
        :param body_r: string value of integer between 0-255
        :param body_g: string value of integer between 0-255
        :param body_b: string value of integer between 0-255
        :param car_name: string value car name to display over car. Newline accepted for multi-line.
        :param font_size: string value of integer between 10-100 to set size of car name text
        """
        request = dict()
        request["msg_type"] = "car_config"
        request["body_style"] = str(body_style)
        request["body_r"] = str(body_r)
        request["body_g"] = str(body_g)
        request["body_b"] = str(body_b)
        request["car_name"] = str(car_name)
        request["font_size"] = str(font_size)
        self.send_message(json.dumps(request))
    
    def send_cam_config_request(self, fov=100, fish_eye_x=0, fish_eye_y=0, img_w=160, img_h=120, img_d=3, img_enc="PNG", offset_x=0.0, offset_y=3.5, offset_z=0.0, rot_x=90.0):
        """
        Once the scene is loaded, you may configure your car camera sensor details.

        :param fov: string value of float between 10-200. Sets the camera field of view in degrees.
        :param fish_eye_x: string value of float between 0-1. Causes distortion warping in x axis.
        :param fish_eye_y: string value of float between 0-1. Causes distortion warping in y axis.
        :param img_w: string value of integer between 16-512. Sets camera sensor image width.
        :param img_h: string value of integer between 16-512. Sets camera sensor image height.
        :param img_d: string value of integer 1 or 3. Sets camera sensor image depth. In case of 1, you get 3 channels but all identicle with greyscale conversion done on the sim.
        :param img_enc: Image format of data JPG | PNG | TGA
        :param offset_x: string value of float. Moves the camera left and right axis.
        :param offset_y: string value of float. Moves the camera up and down.
        :param offset_z: string value of float. Moves the camera forward and back.
        :param rot_x: string value of float. Degrees. Rotates camera around X axis.
        """
        request = dict()
        request["msg_type"] = "cam_config"
        request["fov"] = str(fov)
        request["fish_eye_x"] = str(fish_eye_x)
        request["fish_eye_y"] = str(fish_eye_y)
        request["img_w"] = str(img_w)
        request["img_h"] = str(img_h)
        request["img_d"] = str(img_d)
        request["img_enc"] = str(img_enc)
        request["offset_x"] = str(offset_x)
        request["offset_y"] = str(offset_y)
        request["offset_z"] = str(offset_z)
        request["rot_x"] = str(rot_x)
        self.send_message(json.dumps(request))

    def send_car_control_request(self, angle, throttle, brake):
        """
        Send car control (angle/steering, throttle, brake)

        :param steering: string value of float between -1 to 1. Maps to full left or right, 16 deg from center.
        :param throttle: string value of float between -1 to 1. Full forward or reverse torque to wheels.
        :param brake: string value of float between 0 to 1.

        """
        request = dict()
        request["msg_type"] = "control"
        request["steering"] = str(angle)
        request["throttle"] = str(throttle)
        request["brake"] = str(brake)
        self.send_message(json.dumps(request))
    
    def send_reset_car_request(self):
        """
        Return the car to the start point

        This command will send the request immediatly and reset the buffers of the client.
        """
        request = dict()
        request["msg_type"] = "reset_car"
        self.event_handler.reset_state()
        # It is not `send_message` because we don't want to wait for the next buffer read to give the request
        self.send_now(json.dumps(request))
        self.reset_buffer()
    
    def send_node_position_request(self, index):
        """
        Ask for a node_position packet
        :param index: node index.
        """
        request = dict()
        request["msg_type"] = "set_position"
        request["index"] = str(index)
        self.send_message(json.dumps(request))
    
    def send_exit_scene_request(self):
        """
        Leave the scene and return to the main menu screen.
        """
        request = dict()
        request["msg_type"] = "exit_scene"
        # It is not `send_message` because we don't want to wait for the next buffer read to give the request
        self.send_now(json.dumps(request))
        self.on_exit_scene()

    def send_quit_app_request(self):
        """
        Close the sim executable. (Menu only)
        """
        request = dict()
        request["msg_type"] = "quit_app"
        # It is not `send_message` because we don't want to wait for the next buffer read to give the request
        self.send_now(json.dumps(request))
        self.reset_buffer()
        self.on_quit_app()
        self.stop()
    
    def stop(self):
        """
        Stop the loop in the client
        """
        self.connected = False
