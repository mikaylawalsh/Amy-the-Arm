import time
import tkinter as tk
from tkinter import ttk, PhotoImage
import RPi.GPIO as GPIO
import board
import busio
from adafruit_pca9685 import PCA9685


# -----------------------------
# Global state
# -----------------------------
#gripper_state = 0  # 0 = closed, 60 = open

# DOF 0 time offset tracking
# positive -> moved right
# negative -> moved left
dof0_offset_time = 0.0

# DOF 1 time offset tracking
# positive -> moved OUT
# negative -> moved IN
dof1_offset_time = 0.0

# Track arrow key press times
key_press_times = {}


# -----------------------------
# GPIO pins (DOF 0 and DOF 1)
# -----------------------------
input1 = 13   # H-Bridge Input 1 (BCM 13)
input2 = 12   # H-Bridge Input 2 (BCM 12)
enable1 = 14  # PWM enable 1 (BCM 14)

input3 = 19   # H-Bridge Input 3 (BCM 19)
input4 = 16   # H-Bridge Input 4 (BCM 16)
enable2 = 15  # PWM enable 2 (BCM 15)


# -----------------------------
# PCA9685 setup (DOF 2,3,4,5)
# -----------------------------
#i2c = busio.I2C(board.SCL, board.SDA)
#pca = PCA9685(i2c)
#pca.frequency = 50

# DOF 0: rotation left/right
# DOF 1: extend arm in/out
# DOF 2: arm up/down
# DOF 3: wrist flex up/down
# DOF 4: gripper rotation left/right
# DOF 5: gripper open/close


# -----------------------------
# GPIO init
# -----------------------------
GPIO.setmode(GPIO.BCM)
GPIO.setup(input1, GPIO.OUT)
GPIO.setup(input2, GPIO.OUT)
GPIO.setup(enable1, GPIO.OUT)
GPIO.setup(input3, GPIO.OUT)
GPIO.setup(input4, GPIO.OUT)
GPIO.setup(enable2, GPIO.OUT)


# -----------------------------
# PWM init for DOF 0 and DOF 1
# -----------------------------
def init_bot():
    p1 = GPIO.PWM(enable1, 25)  # DOF 0
    p2 = GPIO.PWM(enable2, 100)  # DOF 1

    p1.start(25)
    p2.start(100)

    return p1, p2

#p1 = init_bot()                         #SEE IF THIS WORKS
p1, p2 = init_bot()


# ??
def set_pwm_for_direction(direction):
    """Rotate gripper base on DOF 4."""
    if direction == "right":
        update_servo_angle(4, 10)
    elif direction == "left":
        update_servo_angle(4, -10)


# -----------------------------
# DC motor helpers (DOF 0 / DOF 1)
# -----------------------------
def turn_right(i1, i2):
    GPIO.output(i1, GPIO.HIGH)
    GPIO.output(i2, GPIO.LOW)


def turn_left(i1, i2):
    GPIO.output(i1, GPIO.LOW)
    GPIO.output(i2, GPIO.HIGH)


def make_it_stop(i1, i2):
    GPIO.output(i1, GPIO.LOW)
    GPIO.output(i2, GPIO.LOW)


def turn_right_timed(t, i1, i2):
    """Move in right direction for t seconds, then stop."""
    if t <= 0:
        return
    print(f"Turning RIGHT for {t:.2f} seconds")
    turn_right(i1, i2)
    time.sleep(t)
    make_it_stop(i1, i2)
    print("Stopped RIGHT movement")


def turn_left_timed(t, i1, i2):
    """Move in left direction for t seconds, then stop."""
    if t <= 0:
        return
    print(f"Turning LEFT for {t:.2f} seconds")
    turn_left(i1, i2)
    time.sleep(t)
    make_it_stop(i1, i2)
    print("Stopped LEFT movement")



# -----------------------------
# DOF 1 semantic helpers
# -----------------------------
def extend_arm():
    """Physical OUT movement for DOF 1."""
    turn_right(input3, input4)


def retract_arm():
    """Physical IN movement for DOF 1."""
    turn_left(input3, input4)


def extend_arm_timed(t):
    """Move DOF 1 OUT for t seconds."""
    turn_right_timed(t, input3, input4)


def retract_arm_timed(t):
    """Move DOF 1 IN for t seconds."""
    turn_left_timed(t, input3, input4)


def cleanup():
    try:
        p1.stop()
        p2.stop()
    except Exception:
        pass

    try:
        GPIO.cleanup()              # ??
    except Exception:
        pass

    try:
        pca.deinit()            #??
    except Exception:
        pass


# -----------------------------
# Tkinter App
# -----------------------------
class RobotControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Robot Control")
        self.root.geometry("1180x620")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.notebook = ttk.Notebook(self.root)
        self.manual_access_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.manual_access_tab, text="Manual Access")
        self.notebook.pack(expand=True, fill="both")

        self.create_manual_access_ui()

    def on_close(self):
        cleanup()
        self.root.destroy()

    def create_manual_access_ui(self):
        self.feedback_label = tk.Label(
            self.manual_access_tab,
            text="No key pressed",
            font=("Arial", 14)
        )
        self.feedback_label.grid(row=0, column=0, pady=20, columnspan=3)

        controls_frame = tk.Frame(self.manual_access_tab)
        controls_frame.grid(row=1, column=0, pady=20, columnspan=3)

        top_controls_frame = tk.Frame(controls_frame)
        top_controls_frame.grid(row=0, column=0, pady=20)

        wasd_frame = tk.Frame(top_controls_frame)
        wasd_frame.grid(row=0, column=0, padx=20)
        self.create_control_buttons(
            wasd_frame,
            [
                ("W", "Extend Arm UP", "w_key.png"),
                ("S", "Extend Arm DOWN", "s_key.png"),
                ("A", "Flex Wrist UP", "a_key.png"),
                ("D", "Flex Wrist DOWN", "d_key.png"),
            ]
        )

        arrow_frame = tk.Frame(top_controls_frame)
        arrow_frame.grid(row=0, column=1, padx=20)
        self.create_control_buttons(
            arrow_frame,
            [
                ("Up Arrow", "Move Arm IN", "up_key.png"),
                ("Down Arrow", "Move Arm OUT", "down_key.png"),
                ("Right Arrow", "Turn Arm RIGHT", "right_key.png"),
                ("Left Arrow", "Turn Arm LEFT", "left_key.png"),
            ]
        )

        bottom_controls_frame = tk.Frame(controls_frame)
        bottom_controls_frame.grid(row=1, column=0, pady=10)

        self.create_control_buttons(
            bottom_controls_frame,
            [
                ("E", "Rotate Gripper LEFT", "e_key.png"),
                ("R", "Rotate Gripper RIGHT", "r_key.png"),
                ("C", "Toggle Gripper OPEN/CLOSE", "c_key.png"),
                ("ESC", "Reset to home position", "up_key.png"),
            ]
        )


        # Key bindings
        self.root.bind("<KeyPress-Right>", self.handle_keypress)
        self.root.bind("<KeyPress-Left>", self.handle_keypress)
        self.root.bind("<KeyRelease-Right>", self.handle_keyrelease)
        self.root.bind("<KeyRelease-Left>", self.handle_keyrelease)
        
        self.root.bind("<KeyPress-Up>", self.handle_keypress)
        self.root.bind("<KeyPress-Down>", self.handle_keypress)
        self.root.bind("<KeyRelease-Up>", self.handle_keyrelease)
        self.root.bind("<KeyRelease-Down>", self.handle_keyrelease)
        
        ## ??? entire function


    def create_control_buttons(self, frame, controls):
        for idx, (key, description, image_file) in enumerate(controls):
            row = idx // 2
            col = idx % 2

            frame_item = tk.Frame(frame)
            frame_item.grid(row=row, column=col, pady=5, padx=10, sticky="w")

            try:
                img = PhotoImage(file=image_file)
                img_label = tk.Label(frame_item, image=img)
                img_label.image = img
                img_label.pack(side="left", padx=10)
            except Exception:
                img_label = tk.Label(frame_item, text="[img]")
                img_label.pack(side="left", padx=10)

            desc_label = tk.Label(
                frame_item,
                text=f"{key}: {description}",
                font=("Arial", 10),
                anchor="w"
            )
            desc_label.pack(side="left")

    def handle_keypress(self, event):                   # KEY HANDLER
        global key_press_times

        key = event.keysym
        self.feedback_label.config(text=f"Key pressed: {key}")

        # DOF 0
        if key == 'Right':
            if 'Right' not in key_press_times:
                key_press_times['Right'] = time.time()
            turn_right(input1, input2)

        elif key == 'Left':
            if 'Left' not in key_press_times:
                key_press_times['Left'] = time.time()
            turn_left(input1, input2)

        # DOF 1
        # Up = IN
        # Down = OUT
        elif key == 'Up':
            if 'Up' not in key_press_times:
                key_press_times['Up'] = time.time()
            retract_arm()

        elif key == 'Down':
            if 'Down' not in key_press_times:
                key_press_times['Down'] = time.time()
            extend_arm()

        # Servo DOFs
        elif key == 'w':
            update_servo_angle(2, 5)

        elif key == 's':
            update_servo_angle(2, -5)

        elif key == 'a':
            update_servo_angle(3, -10)

        elif key == 'd':
            update_servo_angle(3, 10)

        elif key == 'e':
            set_pwm_for_direction("left")

        elif key == 'r':
            set_pwm_for_direction("right")

        elif key == 'c':
            gripper()

        elif key == 'Escape':
            finalize_active_arrow_keys()

            # Reset servos to base positions
            for dof in current_servo_angles.keys():
                set_servo_position(dof, servo_ranges[dof]["min"])

            # Custom preferred home positions
            set_servo_position(2, 25)
            set_servo_position(4, 270)

            # Return motor-driven joints home
            return_dof_home()

            # Ensure motors are off
            make_it_stop(input1, input2)
            make_it_stop(input3, input4)

            self.feedback_label.config(text="Returned to home position")

    def handle_keyrelease(self, event):
        global dof0_offset_time, dof1_offset_time, key_press_times

        key = event.keysym

        if key == 'Right':
            make_it_stop(input1, input2)
            if 'Right' in key_press_times:
                elapsed = time.time() - key_press_times.pop('Right')
                dof0_offset_time += elapsed
                print(f"DOF 0 moved RIGHT for {elapsed:.3f}s, total offset = {dof0_offset_time:.3f}s")

        elif key == 'Left':
            make_it_stop(input1, input2)
            if 'Left' in key_press_times:
                elapsed = time.time() - key_press_times.pop('Left')
                dof0_offset_time -= elapsed
                print(f"DOF 0 moved LEFT for {elapsed:.3f}s, total offset = {dof0_offset_time:.3f}s")

        elif key == 'Up':
            make_it_stop(input3, input4)
            if 'Up' in key_press_times:
                elapsed = time.time() - key_press_times.pop('Up')
                dof1_offset_time -= elapsed
                print(f"DOF 1 moved IN (Up key) for {elapsed:.3f}s, total offset = {dof1_offset_time:.3f}s")

        elif key == 'Down':
            make_it_stop(input3, input4)
            if 'Down' in key_press_times:
                elapsed = time.time() - key_press_times.pop('Down')
                dof1_offset_time += elapsed
                print(f"DOF 1 moved OUT (Down key) for {elapsed:.3f}s, total offset = {dof1_offset_time:.3f}s")

        elif key == 'w':
            make_it_stop_vertical()
            print("Stopped moving DOF 2")

        elif key == 's':
            make_it_stop_vertical()
            print("Stopped moving DOF 2")

    def handle_keypress_0(self, event):                   # KEY HANDLER
        global key_press_times

        key = event.keysym
        self.feedback_label.config(text=f"Key pressed: {key}")

        # DOF 0
        if key == 'Right':
            if 'Right' not in key_press_times:
                key_press_times['Right'] = time.time()
            turn_right(input1, input2)

        elif key == 'Left':
            if 'Left' not in key_press_times:
                key_press_times['Left'] = time.time()
            turn_left(input1, input2)

       

    def handle_keyrelease_0(self, event):
        global dof0_offset_time, dof1_offset_time, key_press_times

        key = event.keysym

        if key == 'Right':
            make_it_stop(input1, input2)
            if 'Right' in key_press_times:
                elapsed = time.time() - key_press_times.pop('Right')
                dof0_offset_time += elapsed
                print(f"DOF 0 moved RIGHT for {elapsed:.3f}s, total offset = {dof0_offset_time:.3f}s")

        elif key == 'Left':
            make_it_stop(input1, input2)
            if 'Left' in key_press_times:
                elapsed = time.time() - key_press_times.pop('Left')
                dof0_offset_time -= elapsed
                print(f"DOF 0 moved LEFT for {elapsed:.3f}s, total offset = {dof0_offset_time:.3f}s")


# -----------------------------
# Run app
# -----------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = RobotControlApp(root)

    # Initialize servo positions
    #for dof in current_servo_angles.keys():
        #set_servo_position(dof, servo_ranges[dof]["min"])

    # Preferred startup positions
    #set_servo_position(2, 25)
    #set_servo_position(4, 270)

    try:
        root.mainloop()
    finally:
        cleanup()
