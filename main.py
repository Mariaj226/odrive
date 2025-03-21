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
from dpea_odrive.odrive_helpers import digital_read

sys.path.append("/home/soft-dev/Documents/dpea-odrive/")
from dpea_odrive.odrive_helpers import *
MIXPANEL_TOKEN = "x"
MIXPANEL = MixPanel("Project Name", MIXPANEL_TOKEN)

SCREEN_MANAGER = ScreenManager()
MAIN_SCREEN_NAME = 'main'
TRAJ_SCREEN_NAME = 'traj'
GPIO_SCREEN_NAME = 'gpio'
ADMIN_SCREEN_NAME = 'admin'


# Connect to ODrive
print("Finding ODrive...")
od = find_odrive(serial_number="386037573437")
od.clear_errors()
print("Found ODrive!")

assert od.config.enable_brake_resistor is True, "Brake resistor not enabled!"
ax1 = ODriveAxis(od.axis1, current_lim=10, vel_lim=10)
ax1.set_pos(5)

#  Set up encoder configuration
od.axis1.encoder.config.cpr = 8192

#if not ax.is_calibrated():
print("calibrating...")
ax1.calibrate_with_current_lim(10)





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
        ax1.set_pos_traj(0, accel, speed, decel)
        ax1.wait_for_motor_to_stop()
        print("Current position in Turns = ", round(ax1.get_pos(), 2))


class GPIOScreen(Screen):


    def toggleGPIO(self):
        od.config.gpio4_mode = GPIO_MODE_ANALOG_IN
        read = analog_read(od, 4)
        i = 0
        while (i <= 100):
            if(read >= 0.1):
                ax1.set_ramped_vel(0, 3)
            else:
                ax1.set_ramped_vel(10,3)
            sleep(0.1)
            read = analog_read(od, 4)
            i = i + 1
        ax1.set_ramped_vel(0, 3)
        print("Stopping")

    def toggleGPIO2(self):
        od.config.gpio3_mode = GPIO_MODE_ANALOG_IN
        read = analog_read(od, 3)
        i = 0
        while(i<=10):
            print("Value: " + str(read))
            ax1.set_ramped_vel(read * 4, 3)
            read = analog_read(od, 3)
            sleep (2)
            i = i + 1
        ax1.set_ramped_vel(0, 3)
        print("Stopping")








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