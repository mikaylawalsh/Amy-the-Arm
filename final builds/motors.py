import pigpio
import PCA9685
import RPi.GPIO as gpio
import board
import busio
import time

# # Initialize PCA 9685
# i2c = busio.I2C(board.SCL, board.SDA)
# pca = PCA9685(i2c)
# pca.frequency = 50

# Setup GPIO
# gpio.setmode(gpio.BOARD)

class Servo:
	'''
	Object for servo motor motion.
	
	Attributes:
		pca_channel		PCA channel object;	PCA channel object for this servo
		max_angle;		float;	maximum movement degrees angle of servo
		min_period_us;	float;	minimum microsecond pwm period read by servo
		max_period_us;	float;	maximum microsecond pwm period read by servo
		last_angle;		float;	last angle this Servo was commanded to move to
	'''
	
	def __init__(
		self,
		pca,
		pca_channel,
		max_angle:		float = 180,
		min_period_us:	float = 1000,
		max_period_us:	float = 2000
	) -> None:
		'''
		Initializes servo object.
		'''
		self.pca = pca
		self.pca_channel = pca_channel
		self.max_angle = max_angle
		self.min_period_us = min_period_us
		self.max_period_us = max_period_us
		
#		# Setup PCA9685
#		if pi is None or pwm is None:
#			pi = pigpio.pi()
#			pwm = PCA9685.PWM(pi)
#			pwm.set_pwm_freq(50)
			
	def move_proportion(self, prop):
		'''
		Moves the servo to the position that is the given proportion through its movement arc. 
		'''
		# Record angle
		self.last_angle = prop * self.max_angle
		
		# Compute PWM signal
		period_us = prop * (self.max_period_us - self.min_period_us) + self.min_period_us
		duty_cycle = period_us / (10 ** 6 / self.pca.frequency)
		# pulse = duty_cycle * 4096
		
		# Send PWM signal via PCA channel
		self.pca.channels[self.pca_channel].duty_cycle = duty_cycle

	def move_angle(self, angle):
		'''
		Moves the servo to the given angle.
		'''
		self.last_angle = angle
		move_proportion(angle / self.max_angle)
		
	def get_last_angle(self):
		'''
		'''
		return self.last_angle

class HBridgeDCMotor:
	'''
	Object for DC motor motion via H-bridge.
	
	Attributes:
		l_pin;		int;	pin number for left digital driver
		r_pin;		int;	pin number for right digital driver
		pwm_pin;	int;	pin number for pwm speed modulator
	'''

	def __init__(self, l_pin, r_pin, pwm_pin):
		'''
		Initializes motor object.
		
		Arguments:
			l_pin;		int;	pin number for left digital driver
			r_pin;		int;	pin number for right digital driver
			pwm_pin;	int;	pin number for pwm speed modulator
		'''
		self.l_pin = l_pin
		self.r_pin = r_pin
		self.pwm_pin = pwm_pin
		
		for pin in [l_pin, r_pin]:
			gpio.setup(pin, gpio.OUT)		
		
	def move_left(self, speed_prop=1., duration_s=-1):
		'''
		Moves motor left at given speed and duration.
		If no duration is given, moves until move_stop() is called.

		Arguments:
			speed_prop;		float;	proportion of max speed for motion
			duration_s;		float;	seconds to move the motor before stopping motion. if negative, does not stop motion.
		'''
		self.set_pin_outputs(gpio.HIGH, gpio.LOW, speed_prop * 4096)
		if duration_s > 0:
			time.sleep(duration_s)
			self.move_stop()

	def move_left(self, speed_prop=1., duration_s=-1):
		'''
		Moves motor right at given speed and duration.
		If no duration is given, moves until move_stop() is called.
		
		Arguments:
			speed_prop;		float;	proportion of max speed for motion
			duration_s;		float;	seconds to move the motor before stopping motion. if negative, does not stop motion.
		'''
		self.set_pin_outputs(gpio.LOW, gpio.HIGH, speed_prop * 4096)
		if duration_s > 0:
			time.sleep(duration_s)
			self.move_stop()
		
	def move_stop(self):
		'''
		Stops motor motion.
		'''
		self.set_pin_outputs(gpio.LOW, gpio.LOW, 0.)

	def set_pin_outputs(self, l_output=gpio.LOW, r_output=gpio.LOW, pwm_output=0.):
		'''
		Sets outputs for the left, right, and pwm pins.
		
		Arguments:
			l_output; 	bool;	
		'''
		pwm.set_pwm(self.pwm_pin, 0, pwm_output)	
		gpio.output(self.l_pin, l_output)
		gpio.output(self.r_pin, r_output) 
	
class FeedbackMotor(HBridgeDCMotor):
	'''
	Assumes turning right inreases angle and turning left decreases angle.
	'''
	
	def __init__(self, l_pin, r_pin, pwm_pin, angle_fun, max_angle=360):
		'''
		Initializes motor object.
		
		Arguments:
			l_pin;		int;		pin number for left digital driver
			r_pin;		int;		pin number for right digital driver
			pwm_pin;	int;		pin number for pwm speed modulator
			angle_fun;	function;	function with 0 inputs and 1 output, which is the current angle. assumes function takes same amount of time to execute each call.
			max_angle;	float;		maximum movement degrees angle of motor
		'''
		self.l_pin = l_pin
		self.r_pin = r_pin
		self.pwm_pin = pwm_pin
		self.angle_fun = angle_fun
		
		for pin in [l_pin, r_pin]:
			gpio.setup(pin, gpio.OUT)		
	
	def move_angle(self, angle, speed_prop, alpha=0.2):
		
		angle_delta_learner = None
		old_angle = self.angle_fun()
				
		if angle > old_angle:
			direction = 1
			self.move_right(speed_prop)
		else:
			direction = -1
			self.move_left(speed_prop)

		while True:
			new_angle = self.angle_fun()
			angle_delta = new_angle - old_angle
			if angle_delta_learner is None:
				angle_delta_learner = angle_delta
			else:
				angle_delta_learner = angle_delta_learner - alpha * (angle_delta_learner - angle_delta)
			if direction * (new_angle + angle_delta_learner) > direction * (angle):
				self.move_stop()
				return
			old_angle = new_angle
