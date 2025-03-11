import os
import sys

# os.environ['DISPLAY'] = ":0.0"
# os.environ['KIVY_WINDOW'] = 'egl_rpi'

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen

from pidev.MixPanel import MixPanel
from pidev.kivy.PassCodeScreen import PassCodeScreen
from pidev.kivy.PauseScreen import PauseScreen
from pidev.kivy import DPEAButton
from pidev.kivy import ImageButton

sys.path.append("/home/soft-dev/Documents/dpea-odrive/")
from dpea_odrive.odrive_helpers import *
MIXPANEL_TOKEN = "x"
MIXPANEL = MixPanel("Project Name", MIXPANEL_TOKEN)

SCREEN_MANAGER = ScreenManager()
MAIN_SCREEN_NAME = 'main'
TRAJ_SCREEN_NAME = 'traj'
GPIO_SCREEN_NAME = 'gpio'
ADMIN_SCREEN_NAME = 'admin'


# 1. Connect to ODrive
print("Finding ODrive...")
od = find_odrive(serial_number="386037573437")
od.clear_errors()
print("Found ODrive!")

# 2. Assert that the brake resistor is enabled (optional)
assert od.config.enable_brake_resistor is True, "Brake resistor not enabled!"

# 3. Configure Axis 1 for current limit, velocity limit, and control mode
ax1 = ODriveAxis(od.axis1, current_lim=10, vel_lim=10)
ax1.set_pos(5)

# Set current limit and velocity limit (You can adjust these as needed)
#ax1.motor.config.current_lim = 10  # Set motor current limit (e.g., 10 Amps)
#ax1.controller.config.vel_limit = 10000  # Set velocity limit (e.g., 10000 RPM)
#ax1.controller.config.pos_gain = 10  # Set position gain
#ax1.controller.config.vel_gain = 0.1  # Set velocity gain

# 4. Set up encoder configuration
od.axis1.encoder.config.cpr = 8192  # Set counts per revolution for the encoder (adjust for your encoder)
#ax1.encoder.config.use_index = True  # Enable the index signal (if applicable)
#ax1.encoder.config.direction = 1  # Set direction (1 for clockwise, -1 for counterclockwise)

#if not ax.is_calibrated():
print("calibrating...")
ax1.calibrate_with_current_lim(10)

# Wait for calibration to finish without using time.sleep()




# 7. Set the motor to closed-loop control
print("Setting motor to closed-loop control...")
ax1.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL  # Set to closed-loop control for normal operation


# 9. Print current encoder position and velocity estimates
print(f"Encoder position: {od.axis1.encoder.pos_estimate}")
print(f"Encoder velocity: {od.axis1.encoder.vel_estimate}")
dump_errors(od)



class ProjectNameGUI(App):
    """
    Class to handle running the GUI Application
    """

    def build(self):
        """
        Build the application
        :return: Kivy Screen Manager instance
        """
        return SCREEN_MANAGER


Window.clearcolor = (1, 1, 1, 1)  # White


class MainScreen(Screen):
    """
    Class to handle the main screen and its associated touch events
    """

    def switch_to_traj(self):
        SCREEN_MANAGER.transition.direction = "left"
        SCREEN_MANAGER.current = TRAJ_SCREEN_NAME

    def switch_to_gpio(self):
        SCREEN_MANAGER.transition.direction = "right"
        SCREEN_MANAGER.current = GPIO_SCREEN_NAME

    def tog_spin_five(self):
        "spin 5 times"
        ax1.set_pos(5)
        ax1.wait_for_motor_to_stop()
        print("Current Position in Turns = ", round(ax1.get_pos(), 2))
        ax1.set_relative_pos(-5)
        ax1.wait_for_motor_to_stop()
        dump_errors(od)
        od.clear_errors()

    def set_motor_vel(self,speed, acel):
        ax1.set_ramped_vel(speed, acel)

    def set_motor_acel(self,acel,speed):
        ax1.set_ramped_vel(speed, acel)



    def admin_action(self):
        """
        Hidden admin button touch event. Transitions to passCodeScreen.
        This method is called from pidev/kivy/PassCodeScreen.kv
        :return: None
        """
        SCREEN_MANAGER.current = 'passCode'


class TrajectoryScreen(Screen):
    """
    Class to handle the trajectory control screen and its associated touch events
    """

    def switch_screen(self):
        SCREEN_MANAGER.transition.direction = "right"
        SCREEN_MANAGER.current = MAIN_SCREEN_NAME

    def runTrajectory(self, pos, accel, speed, decel):
        print("running Trajectory...")
        ax1.set_pos_traj(pos, accel, speed, decel)
        ax1.wait_for_motor_to_stop()
        print("Current position in Turns = ", round(ax1.get_pos(), 2))
        ax1.set_pos_traj(- pos, accel, speed, decel)
        ax1.wait_for_motor_to_stop()
        print("Current position in Turns = ", round(ax1.get_pos(), 2))


class GPIOScreen(Screen):
    """
    Class to handle the GPIO screen and its associated touch/listening events
    """

    def switch_screen(self):
        SCREEN_MANAGER.transition.direction = "left"
        SCREEN_MANAGER.current = MAIN_SCREEN_NAME


class AdminScreen(Screen):
    """
    Class to handle the AdminScreen and its functionality
    """

    def __init__(self, **kwargs):
        """
        Load the AdminScreen.kv file. Set the necessary names of the screens for the PassCodeScreen to transition to.
        Lastly super Screen's __init__
        :param kwargs: Normal kivy.uix.screenmanager.Screen attributes
        """
        Builder.load_file('AdminScreen.kv')

        PassCodeScreen.set_admin_events_screen(
            ADMIN_SCREEN_NAME)  # Specify screen name to transition to after correct password
        PassCodeScreen.set_transition_back_screen(
            MAIN_SCREEN_NAME)  # set screen name to transition to if "Back to Game is pressed"

        super(AdminScreen, self).__init__(**kwargs)

    @staticmethod
    def transition_back():
        """
        Transition back to the main screen
        :return:
        """
        SCREEN_MANAGER.current = MAIN_SCREEN_NAME

    @staticmethod
    def shutdown():
        """
        Shutdown the system. This should free all steppers and do any cleanup necessary
        :return: None
        """
        os.system("sudo shutdown now")

    @staticmethod
    def exit_program():
        """
        Quit the program. This should free all steppers and do any cleanup necessary
        :return: None
        """
        quit()


"""
Widget additions
"""

Builder.load_file('main.kv')
SCREEN_MANAGER.add_widget(MainScreen(name=MAIN_SCREEN_NAME))
SCREEN_MANAGER.add_widget(TrajectoryScreen(name=TRAJ_SCREEN_NAME))
SCREEN_MANAGER.add_widget(GPIOScreen(name=GPIO_SCREEN_NAME))
SCREEN_MANAGER.add_widget(PassCodeScreen(name='passCode'))
SCREEN_MANAGER.add_widget(PauseScreen(name='pauseScene'))
SCREEN_MANAGER.add_widget(AdminScreen(name=ADMIN_SCREEN_NAME))

"""
MixPanel
"""


def send_event(event_name):
    """
    Send an event to MixPanel without properties
    :param event_name: Name of the event
    :return: None
    """
    global MIXPANEL

    MIXPANEL.set_event_name(event_name)
    MIXPANEL.send_event()


if __name__ == "__main__":
    # send_event("Project Initialized")
    # Window.fullscreen = 'auto'
    ProjectNameGUI().run()