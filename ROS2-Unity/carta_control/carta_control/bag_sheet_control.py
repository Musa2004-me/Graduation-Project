#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import sys
import tty
import termios
import threading

MSG = """
Bag Sheet Teleop Control
------------------------
Controls:
  a / d  : rotate left / right (angular.x)
  s      : stop rotation
  q      : quit

Hold key to increase velocity (step: 0.1 rad/s)
Current velocity will be printed on change.
"""

STEP = 0.1
MAX_VEL = 2.0


def get_key(settings):
    tty.setraw(sys.stdin.fileno())
    key = sys.stdin.read(1)
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


class BagSheetTeleop(Node):
    def __init__(self):
        super().__init__('bag_sheet_teleop')
        self.publisher_ = self.create_publisher(Twist, '/bag_vel', 10)
        self.velocity = 0.0
        self.get_logger().info(MSG)

    def publish_velocity(self, vel: float):
        msg = Twist()
        msg.angular.x = vel
        self.publisher_.publish(msg)
        self.get_logger().info(f'angular.x velocity: {vel:.2f} rad/s')

    def run(self):
        settings = termios.tcgetattr(sys.stdin)
        try:
            while rclpy.ok():
                key = get_key(settings)

                if key == 'a':
                    self.velocity = max(-MAX_VEL, self.velocity - STEP)
                elif key == 'd':
                    self.velocity = min(MAX_VEL, self.velocity + STEP)
                elif key == 's':
                    self.velocity = 0.0
                elif key == 'q':
                    self.publish_velocity(0.0)
                    self.get_logger().info('Stopping and quitting...')
                    break
                else:
                    continue

                self.publish_velocity(self.velocity)

        except Exception as e:
            self.get_logger().error(f'Error: {e}')
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)


def main(args=None):
    rclpy.init(args=args)
    node = BagSheetTeleop()

    # Spin in background thread so publisher works
    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    try:
        node.run()
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()