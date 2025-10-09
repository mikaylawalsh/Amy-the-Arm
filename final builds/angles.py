from adafruit_pca9685 import PCA9685
import busio
import board


def angle_to_pulse_width(angle, min_angle, max_angle):
    """Converts angle to PWM pulse width."""
    angle = max(min(angle, max_angle), min_angle)
    pulse = 1 + ((angle - min_angle) / (max_angle - min_angle)) * (2 - 1)
    duty_cycle = int(pulse * 65535 / 20)
    return duty_cycle

servo_ranges = {
    2: {'min': 0, 'max': 120}, #0-120
    3: {'min': 0, 'max': 95}, #95 
    4: {'min': 0, 'max': 320}, # 0-320
    5: {'min': 0, 'max': 60},
}

# Setup for PCA9685 (DOF 2, 3, 4, 5 control)
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50

min_angle = servo_ranges[3]['min']
max_angle = servo_ranges[3]['max']
duty_cycle = angle_to_pulse_width(95, min_angle, max_angle)
print(duty_cycle)
pca.channels[3].duty_cycle = duty_cycle

print(pca)

