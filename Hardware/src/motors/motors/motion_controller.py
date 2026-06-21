#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32

import math


class MotionController(Node):

    def __init__(self):
        super().__init__('motion_controller')

        # Publishers
        self.left_pub = self.create_publisher(Float32, '/left_rpm_setpoint', 10)
        self.right_pub = self.create_publisher(Float32, '/right_rpm_setpoint', 10)

        # Subscriber
        self.cmd_sub = self.create_subscription(Twist, '/cmd_vel', self.cmd_callback, 10)

        # Parameters
        self.declare_parameter("wheel_radius", 0.3683 / 2.0)
        self.declare_parameter("track_width", 0.405)

        self.R = self.get_parameter("wheel_radius").value
        self.L = self.get_parameter("track_width").value

        # Deadbands (tuning)
        self.deadband_v = 0.05
        self.deadband_w = 0.10

        self.get_logger().info("Motion Controller Started")

    # ============================================================
    # Publishing
    # ============================================================
    def publish(self, left, right):
        self.left_pub.publish(Float32(data=float(left)))
        self.right_pub.publish(Float32(data=float(right)))

    def stop(self):
        self.publish(0.0, 0.0)

    # ============================================================
    # DECISION LAYER
    # ============================================================
    def cmd_callback(self, msg):

        v = msg.linear.x
        w = msg.angular.z

        # ==================================
        # NO REVERSE ROBOT
        # ==================================
        if v < 0.0:

            if abs(w) < self.deadband_w:
                self.stop()

            elif w > 0:
                self.turn_left(w)

            else:
                self.turn_right(w)

            return

        # ==================================
        # NORMAL LOGIC
        # ==================================

        # STOP
        if abs(v) < self.deadband_v and abs(w) < self.deadband_w:
            self.stop()
            return

        # PURE FORWARD
        if abs(w) < self.deadband_w:
            self.forward(v)
            return

        # PURE TURN
        if abs(v) < self.deadband_v:

            if w > 0:
                self.turn_left(w)
            else:
                self.turn_right(w)

            return

        # FORWARD + TURN
        if w > 0:
            self.forward_left(v, w)
        else:
            self.forward_right(v, w)
    # ============================================================
    # PHYSICS FUNCTIONS
    # ============================================================

    def forward(self, v):

        omega = v / self.R
        rpm = omega * 60.0 / (2.0 * math.pi)

        rpm = max(0.0, rpm)

        self.publish(rpm, rpm)

    def turn_left(self, w):

        omega = abs(w) * self.L / (2.0 * self.R)
        rpm = omega * 60.0 / (2.0 * math.pi)

        # forward-only constraint
        self.publish(0.0, rpm)

    def turn_right(self, w):

        omega = abs(w) * self.L / (2.0 * self.R)
        rpm = omega * 60.0 / (2.0 * math.pi)

        # forward-only constraint
        self.publish(rpm, 0.0)

    def forward_left(self, v, w):

        v_omega = v / self.R
        w_omega = abs(w) * self.L / (2.0 * self.R)

        left_omega = v_omega - w_omega
        right_omega = v_omega + w_omega

        left_rpm = left_omega * 60.0 / (2.0 * math.pi)
        right_rpm = right_omega * 60.0 / (2.0 * math.pi)

        # no reverse constraint
        left_rpm = max(0.0, left_rpm)
        right_rpm = max(0.0, right_rpm)

        self.publish(left_rpm, right_rpm)

    def forward_right(self, v, w):

        v_omega = v / self.R
        w_omega = abs(w) * self.L / (2.0 * self.R)

        left_omega = v_omega + w_omega
        right_omega = v_omega - w_omega

        left_rpm = left_omega * 60.0 / (2.0 * math.pi)
        right_rpm = right_omega * 60.0 / (2.0 * math.pi)

        # no reverse constraint
        left_rpm = max(0.0, left_rpm)
        right_rpm = max(0.0, right_rpm)

        self.publish(left_rpm, right_rpm)


# ============================================================
# MAIN
# ============================================================

def main():
    rclpy.init()
    node = MotionController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()