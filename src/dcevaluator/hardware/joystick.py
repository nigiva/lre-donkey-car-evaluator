import enum
import pygame
import pygame.display
import os

# To remove error "No device" in Visual Code
os.environ["SDL_VIDEODRIVER"] = "dummy"

SHIFT_AXIS = 0.00390625

class Axis(enum.Enum):
   LeftHorizontal = 0
   LeftVertical = 1
   RightHorizontal = 3
   RightVertical = 4
   LeftBack = 2
   RightBack = 5

class Button(enum.Enum):
   Share = 8
   Options = 9
   Home = 10
   Triangle = 2
   Circle = 1
   Cross = 0
   Square = 3
   LeftBack = 4
   RightBack = 5
   LeftDirection = 15
   RightDirection = 16
   TopDirection = 13
   DownDirection = 14

class JoystickController:
    def __init__(self, id_controller=0):
        pygame.init()
        pygame.display.init()
        pygame.joystick.init()
        self.id = id_controller
        self.refresh()
        self.controller.init()
    
    def refresh(self):
        pygame.event.get()
        self.controller = pygame.joystick.Joystick(self.id)
        self.controller.init()

    def get_axis(self, axis):
        value = self.controller.get_axis(axis.value)
        if (axis in [Axis.LeftVertical, Axis.RightVertical, Axis.LeftHorizontal, Axis.LeftHorizontal]):
            value -= SHIFT_AXIS
        if (axis in [Axis.LeftVertical, Axis.RightVertical]):
            return -value
        return value
    
    def get_axis_positive(self, axis):
        return (self.get_axis(axis) + 1)/2.0

    def get_axis_negative(self, axis):
        return -self.get_axis_positive(axis)
    
    def get_button(self, button):
        self.refresh()
        return self.controller.get_button(button.value)
    
    ## Custome control to drive the car and more generaly controle the software ##
    ## Same for all hardware class ##

    def get_angle_controller(self):
        return self.get_axis(Axis.RightHorizontal)

    def get_throttle_controller(self):
        #p = self.get_axis_positive(Axis.RightBack)
        #n = self.get_axis_negative(Axis.LeftBack)
        #return p + n
        # auto throttle
        angle = self.get_angle_controller()
        angle_satured = 0.4 if abs(angle) > 0.4 else abs(angle)
        return 0.6 - angle_satured

    def get_brake_controller(self):
        return 0

    def get_rec_controller(self):
        return self.get_button(Button.Circle)

    def get_autodrive_controller(self):
        return self.get_button(Button.LeftBack)

    def get_reset_controller(self):
        return self.get_button(Button.Options)
    
    def get_train_controller(self):
        return self.get_button(Button.Share)

    def get_exit_app_controller(self):
        return self.get_button(Button.Home)
    
    def get_start_car(self):
        return self.get_button(Button.RightBack)