#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from std_msgs.msg import Float32


class CmdVelToRPM(Node):

    def __init__(self):
        super().__init__('cmd_vel_to_rpm')

        # ==========================
        # Robot Parameters
        # ==========================
        self.declare_parameter('wheel_radius', 0.3683 / 2.0) # m 
        self.declare_parameter('track_width', 0.405) # m

        self.R = self.get_parameter('wheel_radius').value
        self.TW = self.get_parameter('track_width').value

        # ==========================
        # Publishers
        # ==========================
        self.left_pub = self.create_publisher(
            Float32,
            '/left_rpm_setpoint',
            10
        )

        self.right_pub = self.create_publisher(
            Float32,
            '/right_rpm_setpoint',
            10
        )

        # ==========================
        # Subscriber
        # ==========================
        self.cmd_sub = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )

        self.get_logger().info(
            f'CmdVelToRPM Started | R={self.R} m | TW={self.TW} m'
        )

    def cmd_vel_callback(self, msg):

        # Robot velocities from Nav2
        V = msg.linear.x      # m/s
        W = msg.angular.z     # rad/s

        # Differential drive inverse kinematics
        v_left = V - (W * self.TW / 2.0)
        v_right = V + (W * self.TW / 2.0)

        # Convert wheel linear velocity -> RPM
        left_rpm = (v_left * 60.0) / (2.0 * math.pi * self.R)
        right_rpm = (v_right * 60.0) / (2.0 * math.pi * self.R)

        # Prevent negative RPMs
        left_rpm = max(0.0, left_rpm)
        right_rpm = max(0.0, right_rpm)

        # Publish
        left_msg = Float32()
        right_msg = Float32()

        left_msg.data = float(left_rpm)
        right_msg.data = float(right_rpm)

        self.left_pub.publish(left_msg)
        self.right_pub.publish(right_msg)

        self.get_logger().debug(
            f'V={V:.2f}, W={W:.2f} -> '
            f'L={left_rpm:.2f} RPM, '
            f'R={right_rpm:.2f} RPM'
        )


def main(args=None):
    rclpy.init(args=args)

    node = CmdVelToRPM()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()