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
gripper_state = 0  # 0 = closed, 60 = open

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

input3 = 16   # H-Bridge Input 3 (BCM 19)
input4 = 19   # H-Bridge Input 4 (BCM 16)
enable2 = 15  # PWM enable 2 (BCM 15)


# -----------------------------
# PCA9685 setup (DOF 2,3,4,5)
# -----------------------------
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50

# DOF 0: rotation left/right
# DOF 1: extend arm in/out
# DOF 2: arm up/down
# DOF 3: wrist flex up/down
# DOF 4: gripper rotation left/right
# DOF 5: gripper open/close

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
    p1 = GPIO.PWM(enable1, 100)  # DOF 0
    p2 = GPIO.PWM(enable2, 100)  # DOF 1

    p1.start(100)
    p2.start(100)

    return p1, p2


p1, p2 = init_bot()


# -----------------------------
# Servo helpers
# -----------------------------
def angle_to_pulse_width(angle, min_angle, max_angle):
    """Convert angle to PCA9685 duty cycle."""
    angle = max(min(angle, max_angle), min_angle)
    pulse = 1 + ((angle - min_angle) / (max_angle - min_angle)) * (2 - 1)
    duty_cycle = int(pulse * 65535 / 20)
    return duty_cycle


def set_servo_position(channel, angle):
    """Set servo to a specific angle and update tracked state."""
    min_angle = servo_ranges[channel]['min']
    max_angle = servo_ranges[channel]['max']

    if angle < min_angle or angle > max_angle:
        print(f"Warning: angle {angle} out of range for channel {channel}")

    angle = max(min(angle, max_angle), min_angle)
    current_servo_angles[channel] = angle

    duty_cycle = angle_to_pulse_width(angle, min_angle, max_angle)
    pca.channels[channel].duty_cycle = duty_cycle
    print(f"Servo on channel {channel} set to angle {angle}°, Duty Cycle: {duty_cycle}")


def update_servo_angle(channel, angle_change):
    """Increment or decrement servo angle within its allowed range."""
    if channel in current_servo_angles:
        current_angle = current_servo_angles[channel]
        new_angle = max(
            servo_ranges[channel]['min'],
            min(current_angle + angle_change, servo_ranges[channel]['max'])
        )
        current_servo_angles[channel] = new_angle
        set_servo_position(channel, new_angle)
        print(f"Servo {channel} moved to {new_angle}°")


def make_it_stop_vertical():
    """Hold DOF 2 at its current angle."""
    current_angle = current_servo_angles[2]
    set_servo_position(2, current_angle)
    print("Stopped moving DOF 2")


def gripper():
    """Toggle gripper open/close on channel 5."""
    global gripper_state

    min_angle = servo_ranges[5]['min']
    max_angle = servo_ranges[5]['max']

    if gripper_state == 0:
        gripper_state = 60
    else:
        gripper_state = 0

    duty_cycle = angle_to_pulse_width(gripper_state, min_angle, max_angle)
    pca.channels[5].duty_cycle = duty_cycle
    current_servo_angles[5] = gripper_state

    print(f"Servo on channel 5 set to angle {gripper_state}°, Duty Cycle: {duty_cycle}")


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


# -----------------------------
# Escape / home return helpers
# -----------------------------
def finalize_active_arrow_keys():
    """
    If an arrow key is still being held when Escape is pressed,
    close out its elapsed time so offsets are accurate.
    """
    global dof0_offset_time, dof1_offset_time, key_press_times

    now = time.time()

    if 'Right' in key_press_times:
        elapsed = now - key_press_times.pop('Right')
        dof0_offset_time += elapsed
        make_it_stop(input1, input2)
        print(f"Finalized RIGHT hold: +{elapsed:.3f}s")

    if 'Left' in key_press_times:
        elapsed = now - key_press_times.pop('Left')
        dof0_offset_time -= elapsed
        make_it_stop(input1, input2)
        print(f"Finalized LEFT hold: -{elapsed:.3f}s")

    if 'Up' in key_press_times:
        elapsed = now - key_press_times.pop('Up')
        # Up key = IN
        dof1_offset_time -= elapsed
        make_it_stop(input3, input4)
        print(f"Finalized UP hold (IN): -{elapsed:.3f}s")

    if 'Down' in key_press_times:
        elapsed = now - key_press_times.pop('Down')
        # Down key = OUT
        dof1_offset_time += elapsed
        make_it_stop(input3, input4)
        print(f"Finalized DOWN hold (OUT): +{elapsed:.3f}s")


def return_dof_home():
    """
    Reverse DOF 0 and DOF 1 based on accumulated signed time offsets,
    then reset offsets to zero.
    """
    global dof0_offset_time, dof1_offset_time

    print(f"Returning DOF 0 home. Stored offset = {dof0_offset_time:.3f}s")
    if dof0_offset_time > 0:
        turn_left_timed(abs(dof0_offset_time), input1, input2)
    elif dof0_offset_time < 0:
        turn_right_timed(abs(dof0_offset_time), input1, input2)

    print(f"Returning DOF 1 home. Stored offset = {dof1_offset_time:.3f}s")
    if dof1_offset_time > 0:
        # Went OUT -> go IN to return
        retract_arm_timed(abs(dof1_offset_time))
    elif dof1_offset_time < 0:
        # Went IN -> go OUT to return
        extend_arm_timed(abs(dof1_offset_time))

    dof0_offset_time = 0.0
    dof1_offset_time = 0.0
    print("DOF 0 and DOF 1 offsets reset to zero.")


def cleanup():
    try:
        p1.stop()
        p2.stop()
    except Exception:
        pass

    try:
        GPIO.cleanup()
    except Exception:
        pass

    try:
        pca.deinit()
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

        # Timed movement test section
        timed_test_frame = tk.LabelFrame(
            self.manual_access_tab,
            text="DOF 1 Timed Test",
            padx=15,
            pady=15,
            font=("Arial", 11)
        )
        timed_test_frame.grid(row=2, column=0, pady=20, padx=20, sticky="w")

        tk.Label(
            timed_test_frame,
            text="Seconds:",
            font=("Arial", 11)
        ).grid(row=0, column=0, padx=5, pady=5)

        self.time_entry = tk.Entry(timed_test_frame, width=10, font=("Arial", 11))
        self.time_entry.insert(0, "1.0")
        self.time_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Button(
            timed_test_frame,
            text="DOF1 OUT",
            font=("Arial", 11),
            width=12,
            command=self.test_dof1_out
        ).grid(row=0, column=2, padx=8, pady=5)

        tk.Button(
            timed_test_frame,
            text="DOF1 IN",
            font=("Arial", 11),
            width=12,
            command=self.test_dof1_in
        ).grid(row=0, column=3, padx=8, pady=5)

        # Key bindings
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

    def get_test_time(self):
        try:
            t = float(self.time_entry.get().strip())
            if t <= 0:
                raise ValueError
            return t
        except ValueError:
            self.feedback_label.config(text="Enter a valid positive number for seconds")
            return None

    def test_dof1_out(self):
        t = self.get_test_time()
        if t is None:
            return

        self.feedback_label.config(text=f"Testing DOF1 OUT for {t:.2f}s")
        self.root.update_idletasks()
        extend_arm_timed(t)

    def test_dof1_in(self):
        t = self.get_test_time()
        if t is None:
            return

        self.feedback_label.config(text=f"Testing DOF1 IN for {t:.2f}s")
        self.root.update_idletasks()
        retract_arm_timed(t)

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

    def handle_keypress(self, event):
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


# -----------------------------
# Run app
# -----------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = RobotControlApp(root)

    # Initialize servo positions
    for dof in current_servo_angles.keys():
        set_servo_position(dof, servo_ranges[dof]["min"])

    # Preferred startup positions
    set_servo_position(2, 25)
    set_servo_position(4, 270)

    try:
        root.mainloop()
    finally:
        cleanup()
