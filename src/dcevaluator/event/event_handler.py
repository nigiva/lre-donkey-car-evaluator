from loguru import logger

class EventHandler:
    def __init__(self):
        self.car_is_ready = False
        self.car_is_leaving = False

        self.last_node = -1
        self.turn = -1
        self.first_time_on_first_turn = 0
        self.last_time_on_last_turn = 0
        
        self.on_scene_selection_ready = self.unimplemented_behavior("on_scene_selection_ready")
        self.on_scene_loaded = self.unimplemented_behavior("on_scene_loaded")
        self.on_car_loaded = self.unimplemented_behavior("on_car_loaded")
        self.on_telemetry = self.unimplemented_behavior("on_telemetry")
        self.on_exit_scene = self.unimplemented_behavior("on_exit_scene")
        self.on_quit_app = self.unimplemented_behavior("on_quit_app")
        self.each_turn = self.unimplemented_behavior("each_turn")
        self.each_node = self.unimplemented_behavior("each_node")
        self.on_car_leaving_road = self.unimplemented_behavior("on_car_leaving_road")

    def unimplemented_behavior(self, *args, **kwargs):
        logger.debug("Unimplemented behavior : " + str(args))
        
        def unimplemented_function(*args, **kwargs):
            pass
        
        return unimplemented_function