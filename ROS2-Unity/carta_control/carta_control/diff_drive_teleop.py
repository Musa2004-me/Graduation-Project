#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import sys
import termios
import tty

class KeyboardTeleop(Node):

    def __init__(self):
        super().__init__('keyboard_teleop')

        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)

        self.linear_speed = 0.5
        self.angular_speed = 2.5
        self.linear_step = 0.1
        self.angular_step = 0.1

        self.get_logger().info("Keyboard Teleop Started")
        self.print_help()

        self.settings = termios.tcgetattr(sys.stdin)
        self.run()

    def print_help(self):
        print("""
==============================
Keyboard Teleop Controls:

w : Forward
d : Left wheel Faster
a : Right wheel Faster

+ : Increase speed
- : Decrease speed

space : Stop
q : Quit
==============================
        """)

    def get_key(self):
        tty.setraw(sys.stdin.fileno())
        key = sys.stdin.read(1)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        return key

    def run(self):
        while rclpy.ok():
            key = self.get_key()
            msg = Twist()
            direction = "STOP"

            if key == 'w':
                msg.linear.x = -self.linear_speed
                direction = "FORWARD"

            # Left wheel faster
            elif key == 'd':
                msg.linear.x = -self.linear_speed
                msg.angular.z = self.angular_speed
                direction = "LEFT WHEEL Faster"

            # Right wheel Faster
            elif key == 'a':
                msg.linear.x = -self.linear_speed
                msg.angular.z = -self.angular_speed
                direction = "RIGHT WHEEL Faster"

            elif key == '+':
                self.linear_speed += self.linear_step
                self.angular_speed += self.angular_step
                self.print_status("SPEED INCREASED")
                continue

            elif key == '-':
                self.linear_speed = max(0.0, self.linear_speed - self.linear_step)
                self.angular_speed = max(0.0, self.angular_speed - self.angular_step)
                self.print_status("SPEED DECREASED")
                continue

            elif key == ' ':
                direction = "STOP"

            elif key == 'q':
                print("Exiting Teleop...")
                break

            self.pub.publish(msg)
            self.print_status(direction)

    def print_status(self, direction):
        print(
            f"\rSpeed: linear={self.linear_speed:.2f} | angular={self.angular_speed:.2f} | Direction: {direction}   ",
            end=""
        )


def main():
    rclpy.init()
    node = KeyboardTeleop()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
