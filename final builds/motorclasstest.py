import board
import busio
import time

from adafruit_pca9685 import PCA9685

from motors import Servo

# Setup for PCA9685 (DOF 2, 3, 4, 5 control)
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50

grip = Servo(pca, 5, 60)
grip.move_proportion(0)
print(grip.last_angle)
print(grip.pca.channels[grip.pca_channel].duty_cycle)
time.sleep(2)
grip.move_proportion(1)
print(grip.last_angle)
time.sleep(2)
print(grip.pca.channels[grip.pca_channel].duty_cycle)
