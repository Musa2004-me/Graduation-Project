#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import serial
import threading

class MotorBridge(Node):
    def __init__(self):
        super().__init__('motor_serial_bridge')
        
        self.pub = self.create_publisher(String, '/bag_state', 10)
        self.sub = self.create_subscription(String, '/motor_command', self.command_callback, 10)
        
        self.port = "/dev/serial/by-id/usb-Arduino__www.arduino.cc__0043_24238313635351910130-if00"
        self.ser = serial.Serial(self.port, 9600, timeout=0.1)
        
        self.thread = threading.Thread(target=self.read_serial_loop, daemon=True)
        self.thread.start()

    def command_callback(self, msg):
        cmd = '1' if msg.data == '1' else 's'
        self.ser.write(cmd.encode())

    def read_serial_loop(self):
        while rclpy.ok():
            if self.ser.in_waiting > 0:
                line = self.ser.readline().decode('utf-8').strip()
                if line in ["OPEN", "CLOSED", "STARTED", "STOPPED"]:
                    msg = String()
                    msg.data = line
                    self.pub.publish(msg)
                    self.get_logger().info(f"Bag Status: {line}")

def main():
    rclpy.init()
    node = MotorBridge()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()