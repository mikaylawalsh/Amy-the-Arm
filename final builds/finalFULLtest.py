import time
import tkinter as tk
from tkinter import ttk, PhotoImage
import RPi.GPIO as GPIO
import board
import busio
from adafruit_pca9685 import PCA9685

# Setup for GPIO pins (DOF 0 and DOF 1 control)
input1 = 13  # H-Bridge Input 1 (BCM 13)
input2 = 12  # H-Bridge Input 2 (BCM 12)
enable1 = 14  # PWM enable 1 (BCM 14)

input3 = 19  # H-Bridge Input 3 (BCM 19)
input4 = 16  # H-Bridge Input 4 (BCM 16)
enable2 = 15  # PWM enable 2 (BCM 15)

# Setup for PCA9685 (DOF 2, 3, 4, 5 control)
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50

# Servo ranges for DOF 2 to DOF 5
servo_ranges = {
    2: {'min': 0, 'max': 120},
    3: {'min': 0, 'max': 95},
    4: {'min': 0, 'max': 320},
    5: {'min': 0, 'max': 60},
}

current_servo_angles = {
    2: 0,
    3: 0,
    4: 0,
    5: 0,
}

# Initialize GPIO for H-Bridge and PWM
GPIO.setmode(GPIO.BCM)
GPIO.setup(input1, GPIO.OUT)
GPIO.setup(input2, GPIO.OUT)
GPIO.setup(enable1, GPIO.OUT)
GPIO.setup(input3, GPIO.OUT)
GPIO.setup(input4, GPIO.OUT)
GPIO.setup(enable2, GPIO.OUT)



def init_bot():
    # Initialize PWM for DOF 0 and DOF 1
    p1 = GPIO.PWM(enable1, 100)  # DOF 0
    p2 = GPIO.PWM(enable2, 100) # DOF 1
    p1.start(50)  # Duty cycle for DOF 0
    p2.start(100)  # Duty cycle for DOF 1 (starting at 25% for neutral)
    return p1, p2
    
p1, p2 = init_bot()
    
def turn_right_o(t, i1, i2):
    GPIO.output(i1, GPIO.HIGH)
    GPIO.output(i2, GPIO.LOW)
    time.sleep(t)
    make_it_stop(i1, i2)
    #time.sleep(1)
    
def turn_right(i1, i2):
    turn_left_o(.001, i1, i2)
    GPIO.output(i1, GPIO.HIGH)
    GPIO.output(i2, GPIO.LOW)

def turn_left_o(t, i1, i2):
    GPIO.output(i1, GPIO.LOW)
    GPIO.output(i2, GPIO.HIGH)
    time.sleep(t)
    make_it_stop(i1, i2)
    #time.sleep(1)
    
def turn_left(i1, i2):
    GPIO.output(i1, GPIO.LOW)
    GPIO.output(i2, GPIO.HIGH)

def make_it_stop(i1, i2):
    GPIO.output(i1, GPIO.LOW)
    GPIO.output(i2, GPIO.LOW)

def cleanup():
    p1.stop()
    p2.stop()
    GPIO.cleanup()

def update_servo_angle(channel, angle_change):
    """Simulate updating the servo angle based on the given angle change."""
    if channel in current_servo_angles:
        current_angle = current_servo_angles[channel]
        new_angle = max(servo_ranges[channel]['min'], min(current_angle + angle_change, servo_ranges[channel]['max']))
        current_servo_angles[channel] = new_angle
        print(f"Servo {channel} moved to {new_angle}°")
        set_servo_position(channel, new_angle)

def set_servo_position(channel, angle):
    """Simulate setting the servo to a given angle."""
    min_angle = servo_ranges[channel]['min']
    max_angle = servo_ranges[channel]['max']
    duty_cycle = angle_to_pulse_width(angle, min_angle, max_angle)
    pca.channels[channel].duty_cycle = duty_cycle
    print(f"Servo on channel {channel} set to angle {angle}°, Duty Cycle: {duty_cycle}")

def angle_to_pulse_width(angle, min_angle, max_angle):
    """Converts angle to PWM pulse width."""
    angle = max(min(angle, max_angle), min_angle)
    pulse = 1 + ((angle - min_angle) / (max_angle - min_angle)) * (2 - 1)
    duty_cycle = int(pulse * 65535 / 20)
    return duty_cycle

def set_pwm_for_direction(direction):
    """Simulate the robot's movement."""
    if direction == "right":
        update_servo_angle(4, 10)  # Move DOF 4 right (simulate by increasing angle)
    elif direction == "left":
        update_servo_angle(4, -10)  # Move DOF 4 left (simulate by decreasing angle)
    else:
        update_servo_angle(4, 0)  # Return to neutral position

class RobotControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Robot Control")
        self.root.geometry("1150x500")

        # Create a notebook (tab control)
        self.notebook = ttk.Notebook(self.root)
        
        # Create the tabs
        self.manual_access_tab = ttk.Frame(self.notebook)
        self.queue_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.manual_access_tab, text="Manual Access")
        self.notebook.add(self.queue_tab, text="Queue")

        self.notebook.pack(expand=True, fill="both")

        # Initialize Manual Access UI components
        self.create_manual_access_ui()

    def create_manual_access_ui(self):
        # Create labels for feedback
        self.feedback_label = tk.Label(self.manual_access_tab, text="No key pressed", font=("Arial", 14))
        self.feedback_label.grid(row=0, column=0, pady=20, columnspan=2)

        # Create a frame for controls and descriptions
        controls_frame = tk.Frame(self.manual_access_tab)
        controls_frame.grid(row=1, column=0, pady=20, columnspan=2)

        # Create descriptions of controls with images
        controls_desc = [
            ("Up Arrow", "Extend Arm OUT", "up_key.png"),
            ("Down Arrow", "Extend Arm IN", "down_key.png"),
            ("Right Arrow", "Turn Arm RIGHT", "right_key.png"),
            ("Left Arrow", "Turn Arm LEFT", "left_key.png"),
            ("W", "Extend Arm UP", "w_key.png"),
            ("S", "Extend Arm DOWN", "s_key.png"),
            ("A", "Flex Wrist UP", "a_key.png"),
            ("D", "Flex Wrist DOWN", "d_key.png"),
            ("E", "Rotate Gripper LEFT", "e_key.png"),
            ("R", "Rotate Gripper RIGHT", "r_key.png"),
            ("C", "Toggle Gripper OPEN/CLOSE", "c_key.png"),
        ]

        # Create labels and images dynamically for the WASD and Arrow keys first
        top_controls_frame = tk.Frame(controls_frame)
        top_controls_frame.grid(row=0, column=0, pady=20)

        # WASD keys (second row)
        wasd_frame = tk.Frame(top_controls_frame)
        wasd_frame.grid(row=0, column=0, padx=20)
        self.create_control_buttons(wasd_frame, [("W", "Extend Arm UP", "w_key.png"),
                                                 ("S", "Extend Arm DOWN", "s_key.png"),
                                                 ("A", "Flex Wrist UP", "a_key.png"),
                                                 ("D", "Flex Wrist DOWN", "d_key.png")])

        # Arrow keys (first row)
        arrow_frame = tk.Frame(top_controls_frame)
        arrow_frame.grid(row=0, column=1, padx=20)
        self.create_control_buttons(arrow_frame, [("Up Arrow", "Extend Arm OUT", "up_key.png"),
                                                  ("Down Arrow", "Extend Arm IN", "down_key.png"),
                                                  ("Right Arrow", "Turn Arm RIGHT", "right_key.png"),
                                                  ("Left Arrow", "Turn Arm LEFT", "left_key.png")])

        # Bottom controls
        bottom_controls_frame = tk.Frame(controls_frame)
        bottom_controls_frame.grid(row=1, column=0, pady=10)

        self.create_control_buttons(bottom_controls_frame, [("E", "Rotate Gripper LEFT", "e_key.png"),
                                                           ("R", "Rotate Gripper RIGHT", "r_key.png"),
                                                           ("C", "Toggle Gripper OPEN/CLOSE", "c_key.png")])

        # Bind keypress events
        self.root.bind("<KeyPress-Right>", self.handle_keypress)
        self.root.bind("<KeyPress-Left>", self.handle_keypress)
        self.root.bind("<KeyRelease-Right>", self.handle_keyrelease)
        self.root.bind("<KeyRelease-Left>", self.handle_keyrelease)
        self.root.bind("<KeyPress-Up>", self.handle_keypress)
        self.root.bind("<KeyPress-Down>", self.handle_keypress)
        self.root.bind("<KeyRelease-Up>", self.handle_keyrelease)
        self.root.bind("<KeyRelease-Down>", self.handle_keyrelease)
        self.root.bind("<w>", self.handle_keypress)
        self.root.bind("<s>", self.handle_keypress)
        self.root.bind("<a>", self.handle_keypress)
        self.root.bind("<d>", self.handle_keypress)
        self.root.bind("<e>", self.handle_keypress)
        self.root.bind("<r>", self.handle_keypress)
        self.root.bind("<c>", self.handle_keypress)
        self.root.bind("<Escape>", self.handle_keypress)
        self.root.bind("<KeyRelease>", self.handle_keyrelease)

    def create_control_buttons(self, frame, controls):
        for idx, (key, description, image_file) in enumerate(controls):
            row = idx // 2
            col = idx % 2

            frame_item = tk.Frame(frame)
            frame_item.grid(row=row, column=col, pady=5, padx=10, sticky="w")

            # Load the image icon
            img = PhotoImage(file=image_file)

            # Label for the image
            img_label = tk.Label(frame_item, image=img)
            img_label.image = img  # Keep a reference to the image
            img_label.pack(side="left", padx=10)

            # Label for the key description
            desc_label = tk.Label(frame_item, text=f"{key}: {description}", font=("Arial", 10), anchor="w")
            desc_label.pack(side="left")

    def handle_keypress(self, event):
        key = event.keysym
        self.feedback_label.config(text=f"Key pressed: {key}")

        # Handle each key event and update robot status
        if key == 'Right':
            turn_right_o(1, input1, input2)
            update_servo_angle(0, 10)  # Simulate angle change for DOF 0
        elif key == 'Left':
            turn_left_o(1, input1, input2)
            update_servo_angle(0, -10)  # Simulate angle change for DOF 0
        elif key == 'Up':
            turn_right(input3, input4)
            update_servo_angle(1, 10)  # Simulate movement for DOF 1
        elif key == 'Down':
            turn_left(input3, input4)
            update_servo_angle(1, -10)  # Simulate movement for DOF 1
        elif key == 'w':
            update_servo_angle(2, 5)  # Move DOF 2 Up
        elif key == 's':
            update_servo_angle(2, -5)  # Move DOF 2 Down
        elif key == 'a':
            update_servo_angle(3, -10)  # Move DOF 3 Down
        elif key == 'd':
            update_servo_angle(3, 10)  # Move DOF 3 Up
        elif key == 'e':
            set_pwm_for_direction("left")
        elif key == 'r':
            set_pwm_for_direction("right")
        elif key == 'c':
            # Toggle DOF 5 (Gripper)
            if current_servo_angles[5] == 0:
                update_servo_angle(5, 60)
            elif current_servo_angles[5] == 15:
                update_servo_angle(5, 60)
            else:
                update_servo_angle(5, -45)
                
        elif key == 'Escape':
            for dof in current_servo_angles.keys():
                update_servo_angle(dof, servo_ranges[dof]["min"])  # Initialize all servos to min
                update_servo_angle(2, 25)

    def handle_keyrelease(self, event):
        key = event.keysym
        if key == 'Right':
            make_it_stop(input1, input2)
            update_servo_angle(0, 10)  # Simulate angle change for DOF 0
        elif key == 'Left':
            make_it_stop(input1, input2)
            update_servo_angle(0, -10)  # Simulate angle change for DOF 0
        elif key == 'Up':
            make_it_stop(input3, input4)
            update_servo_angle(1, 10)  # Simulate movement for DOF 1
        elif key == 'Down':
            make_it_stop(input3, input4)
            update_servo_angle(1, -10)  # Simulate movement for DOF 1
        #if key in current_servo_angles:
            # Keep the last known position of the servo
            #print(f"Released key: {key}, Servo {key} remains at {current_servo_angles[key]}°")

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = RobotControlApp(root)
    for dof in current_servo_angles.keys():
        update_servo_angle(dof, servo_ranges[dof]["min"])  # Initialize all servos to their min 
    update_servo_angle(2, 25)
    root.mainloop()
