#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64MultiArray

class DiffDriveNode(Node):
    def __init__(self):
        super().__init__('diff_drive_node')

        # Parameters
        self.declare_parameter("wheel_radius", 0.3683/2.0)
        self.declare_parameter("track_width", 0.405)

        self.R = self.get_parameter("wheel_radius").value
        self.L = self.get_parameter("track_width").value

        # Publisher to Unity
        self.wheel_pub = self.create_publisher(
            Float64MultiArray, "/wheel_omega", 10)

        # Subscriber
        self.create_subscription(
            Twist, "/cmd_vel", self.cmd_vel_callback, 10)

        self.get_logger().info("Diff Drive Node started")

    def cmd_vel_callback(self, msg):
        v = msg.linear.x
        w = msg.angular.z

        omega_left  = (v - w * self.L / 2.0) / self.R
        omega_right = (v + w * self.L / 2.0) / self.R

        msg_out = Float64MultiArray()
        msg_out.data = [omega_left, omega_right]
        self.wheel_pub.publish(msg_out)


def main(args=None):
    rclpy.init(args=args)
    node = DiffDriveNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
