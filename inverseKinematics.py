import math
import matplotlib.pyplot as plt 

def findTheta2(l1, l2, x2, y2):
  # Law of cosines angle between l1 and l2
  numerator = x2**2 + y2**2 - l1**2 - l2**2
  denominator = 2 * l1 * l2
  val = numerator/denominator 
  theta2_rad = math.acos(val)
  theta2_deg = math.degrees(theta2_rad)
  return theta2_deg

def findTheta1(l1, l2, x2, y2):
  theta2_deg = findTheta2(l1, l2, x2, y2)
  theta2_rad = math.radians(theta2_deg)
  term1 = math.atan2(y2, x2)
  term2 = math.atan2(l2 * math.sin(theta2_rad), l1 + l2 * math.cos(theta2_rad))
  theta1_rad = term1 - term2
  theta1_deg = math.degrees(theta1_rad)
  return theta1_deg 
