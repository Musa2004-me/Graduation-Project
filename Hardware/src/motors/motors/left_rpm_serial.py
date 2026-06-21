#!/usr/bin/env python3
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
import serial

import threading

class SerialBridge(Node):
    def __init__(self):
        super().__init__('left_serial_bridge')

        self.sub = self.create_subscription(
            Float32, '/left_rpm_setpoint', self.setpoint_callback, 10)

        self.pub = self.create_publisher(Float32, '/left_rpm_feedback', 10)

        self.declare_parameter("port", "/dev/serial/by-id/usb-Arduino__www.arduino.cc__0042_55834323832351106180-if00")
        self.port = self.get_parameter("port").value
        self.ser = serial.Serial(self.port, 115200, timeout=0.5)
        time.sleep(2)  # Arduino reset after serial open
        self.ser.reset_input_buffer()

        self.running = True
        self.thread = threading.Thread(target=self.read_serial_loop)
        self.thread.daemon = True
        self.thread.start()

    def setpoint_callback(self, msg):
        line = f"{msg.data}\n"
        self.ser.write(line.encode())

    def read_serial_loop(self):
        while self.running and rclpy.ok():
            try:
                line = self.ser.readline().decode(errors='ignore').strip()
                if line:
                    rpm = float(line)
                    msg = Float32()
                    msg.data = rpm
                    self.pub.publish(msg)
            except ValueError:
                pass
            except Exception as e:
                # Avoid flooding logs if node is shutting down
                if self.running:
                    self.get_logger().error(f"Serial read error: {e}")
                    time.sleep(0.1)

    def destroy_node(self):
        self.running = False
        try:
            self.ser.close()
        except:
            pass
        super().destroy_node()

def main():
    rclpy.init()
    node = SerialBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()