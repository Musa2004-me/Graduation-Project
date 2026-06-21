#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32


class RPMCommander(Node):

    def __init__(self):
        super().__init__('rpm_commander')

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

    def send_rpm(self, left_rpm, right_rpm):

        left_msg = Float32()
        left_msg.data = float(left_rpm)

        right_msg = Float32()
        right_msg.data = float(right_rpm)

        self.left_pub.publish(left_msg)
        self.right_pub.publish(right_msg)

        self.get_logger().info(
            f'Left RPM={left_rpm:.1f}  Right RPM={right_rpm:.1f}'
        )


def main():

    rclpy.init()
    node = RPMCommander()

    try:

        while rclpy.ok():

            text = input("\nEnter: left_rpm right_rpm > ")

            # الجديد: أمر التوقف السريع
            if text.strip().lower() == 'q':
                node.send_rpm(0.0, 0.0)
                print("STOP sent (0 0)")
                continue

            parts = text.split()

            if len(parts) != 2:
                print("Example: 100 50 (or 'q' to stop)")
                continue

            try:
                left_rpm = float(parts[0])
                right_rpm = float(parts[1])

            except ValueError:
                print("Please enter numbers only (or 'q')")
                continue

            node.send_rpm(left_rpm, right_rpm)

            rclpy.spin_once(node, timeout_sec=0)

    except KeyboardInterrupt:
        print("\nExiting RPM Commander...")

    finally:

        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()