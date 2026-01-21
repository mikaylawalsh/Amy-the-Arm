import math

import matplotlib.pyplot 
as plt



def clamp(v, lo=-1.0,hi=1.0):
    return 
max(lo, min(hi, v))

def ik_3link_tip_only(l1, l2, l3, x, y, psi_deg=0.0, elbow="down"):
    """

    Input:  (x,y) = desired end-effector (gripper TIP) position

            psi_deg = desired end-effector direction (0 = flat/right, 90 = up)

            elbow = "down" or "up" (two IK solutions)



    Output: (t1_deg, t2_deg, t3_deg, xw, yw)

            where (xw,yw) is the computed wrist point (end of link2)

    """

    psi = math.radians(psi_deg)
    # Compute wrist point automatically (wrist = tip - L3 * direction)
    xw = x - l3 * math.cos(psi)

    yw = y - l3 * math.sin(psi)
  
    r2 = xw*xw + yw*yw

    cos_t2 = (r2 - l1*l1 - l2*l2) / (2*l1*l2)

    if cos_t2 < -1.0or cos_t2 > 1.0:
        return None  # unreachable

    cos_t2 = clamp(cos_t2)

    t2 = math.acos(cos_t2)

    if elbow == "up":

    t2 = -t2

    t1 = math.atan2(yw, xw) - math.atan2(l2*math.sin(t2), l1 + l2*math.cos(t2))

    # Wrist angle to achieve psi
    t3 = psi - t1 - t2

    return (math.degrees(t1), math.degrees(t2), math.degrees(t3), xw, yw)

def fk_3link(l1, l2, l3, t1_deg, t2_deg, t3_deg):
    t1 = math.radians(t1_deg)
    t2 = math.radians(t2_deg)
    t3 = math.radians(t3_deg)

    x0, y0 = 0.0, 0.0

    x1 = x0 + l1 * math.cos(t1)

    y1 = y0 + l1 * math.sin(t1)

    x2 = x1 + l2 * math.cos(t1 + t2)

    y2 = y1 + l2 * math.sin(t1 + t2)
  
    x3 = x2 + l3 * math.cos(t1 + t2 + t3)

    y3 = y2 + l3 * math.sin(t1 + t2 + t3)

    return (x0,y0), (x1,y1), (x2,y2), (x3,y3)



def draw_angle_arc(ax, center, start_deg, end_deg, radius=2.0, label=None):
    """

    Draw a small arc at 'center' from start_deg to end_deg (degrees),

    where degrees are in global plot coordinates (0° = +x axis).

    """
    # Normalize direction for smooth arc drawing
    # Ensure arc goes the "short way" visually (fine for diagram)
    steps = 40
    start = math.radians(start_deg)
    end = math.radians(end_deg)
  
    # If end < start, wrap for nicer arc
    if end < start:
        end += 2*math.pi

    ts = [start + (end-start)*i/(steps-1) for i in range(steps)]

    xs = [center[0] + radius*math.cos(t) for t in ts]

    ys = [center[1] + radius*math.sin(t) for t in ts]

    ax.plot(xs, ys)

    if label:
        mid = ts[len(ts)//2]
        lx = center[0] + (radius+0.6)*math.cos(mid)
        ly = center[1]+ (radius+0.6)*math.sin(mid)
        ax.text(lx, ly, label, fontsize=12)

def plot_diagram(l1, 
l2, l3, 
x_target, y_target, 
psi_deg=0.0,
elbow="down"):

    sol = ik_3link_tip_only(l1, l2, l3, x_target, y_target, psi_deg, elbow)

    if sol is None:

        print("Target is unreachable with these link lengths.")
        return



    t1_deg, t2_deg, t3_deg, xw, yw = sol

    p0, p1, p2, p3 = fk_3link(l1, l2, l3, t1_deg, t2_deg, t3_deg)



    print(f"theta1={t1_deg:.2f}°,
 theta2={t2_deg:.2f}°, theta3={t3_deg:.2f}°")

    print(f"Computed wrist point: ({xw:.2f},
{yw:.2f})")

    print(f"FK tip reached: ({p3[0]:.2f},
{p3[1]:.2f})  target=({x_target:.2f},
{y_target:.2f})")

    fig, ax = plt.subplots()
  
    # Links

    ax.plot([p0[0], p1[0]], [p0[1], p1[1]],
"r-", 
linewidth=3,
label="L1")

    ax.plot([p1[0], p2[0]], [p1[1], p2[1]],
"g-", 
linewidth=3,
label="L2")

    ax.plot([p2[0], p3[0]], [p2[1], p3[1]],
"b-", 
linewidth=3,
label="L3")

    # Joints

    ax.plot(p0[0], p0[1],
"ko")

    ax.plot(p1[0], p1[1],
"ko")

    ax.plot(p2[0], p2[1],
"ko")

    ax.plot(p3[0], p3[1],
"ko")

    # Points: target + wrist

    ax.plot(x_target, y_target, "kx",
markersize=10,
label="Target (tip)")

    ax.plot(xw, yw, "k+", 
markersize=10,
label="Computed wrist")



    # ---- Angle arcs + labels (like your old diagram) ----

    # Global directions of each link:

    a1 = t1_deg

    a2 = t1_deg 
+ t2_deg

    a3 = t1_deg 
+ t2_deg + t3_deg



    # θ1 at base: from +x (0°) to link1 direction

    draw_angle_arc(ax, p0, 0.0, a1,
radius=max(2.0, l1*0.12),
label=f"θ1={t1_deg:.1f}°")



    # θ2 at joint1: from link1 direction to link2 direction

    draw_angle_arc(ax, p1, a1, a2, radius=max(2.0, l2*0.12),
label=f"θ2={t2_deg:.1f}°")



    # θ3 at joint2: from link2 direction to link3 direction

    draw_angle_arc(ax, p2, a2, a3, radius=max(2.0, l3*0.25),
label=f"θ3={t3_deg:.1f}°")



    # Cosmetics

    ax.set_aspect("equal", 
adjustable="box")

    ax.grid(True)

    ax.legend()

    ax.set_title(f"3-Link IK Diagram (psi={psi_deg}°,
 elbow={elbow})")

    plt.show()



# ----------------- Example run -----------------

if 
__name__ == 
"__main__":

    l1, l2, l3 = 
18, 16.5, 
7   # your lengths

    x, y = 
20, 3               
# ONE target point (tip)

    plot_diagram(l1, l2, l3, x, y, psi_deg=0,
elbow="down")
