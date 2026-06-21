#!/usr/bin/env python3
import sys
import socket
import threading
import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu

class PhoneImuNode(Node):
    def __init__(self):
        super().__init__('phone_imu_node')
        
        # 1. Declare parameters (easily configurable via launch files or CLI)
        self.declare_parameter('port', 5555)
        self.declare_parameter('frame_id', 'imu_link')
        self.declare_parameter('imu_topic', 'imu/data')
        
        self.port = self.get_parameter('port').value
        self.frame_id = self.get_parameter('frame_id').value
        self.imu_topic = self.get_parameter('imu_topic').value
        
        # 2. Publisher
        self.imu_pub = self.create_publisher(Imu, self.imu_topic, 10)
        
        self.get_logger().info(f"Phone IMU Node initialized.")
        self.get_logger().info(f"Listening on UDP port: {self.port}")
        self.get_logger().info(f"Publishing to topic: {self.imu_topic}")
        self.get_logger().info(f"IMU Frame ID: {self.frame_id}")
        
        # 3. Thread control and socket setup
        self.running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.sock.bind(('0.0.0.0', self.port))
            # Set timeout so blocking recvfrom calls don't hang shutdown
            self.sock.settimeout(1.0)
        except Exception as e:
            self.get_logger().error(f"Failed to bind socket on port {self.port}: {e}")
            sys.exit(1)
            
        self.recv_thread = threading.Thread(target=self.receive_loop)
        self.recv_thread.daemon = True
        self.recv_thread.start()

    def receive_loop(self):
        while self.running and rclpy.ok():
            try:
                data, addr = self.sock.recvfrom(1024)
                packet_str = data.decode('utf-8').strip()
                self.parse_and_publish(packet_str)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.get_logger().warn(f"Error receiving UDP packet: {e}")

    def parse_and_publish(self, packet_str):
        # Clean packet data
        parts = [p.strip() for p in packet_str.split(',') if p.strip()]
        if not parts:
            return

        try:
            values = [float(p) for p in parts]
        except ValueError:
            self.get_logger().warn(f"Failed to parse CSV values: {packet_str}")
            return

        # Initialize sensor data variables
        ax, ay, az = None, None, None
        gx, gy, gz = None, None, None
        q_x, q_y, q_z, q_w = None, None, None, None
        
        # Parse depending on data size
        # Format 1: 3 orientation values (Rotation Vector components x, y, z)
        # Quaternion w component is mathematically reconstructed: w = sqrt(1 - x^2 - y^2 - z^2)
        if len(values) == 3:
            q_x, q_y, q_z = values
            val = 1.0 - (q_x**2 + q_y**2 + q_z**2)
            q_w = math.sqrt(max(0.0, val))
            
        # Format 2: 4 orientation values (Quaternion x, y, z, w directly)
        elif len(values) == 4:
            q_x, q_y, q_z, q_w = values

        # Format 3: 6 values (Linear Acceleration [3] + Rotation Vector [3])
        elif len(values) == 6:
            ax, ay, az = values[0], values[1], values[2]
            q_x, q_y, q_z = values[3], values[4], values[5]
            val = 1.0 - (q_x**2 + q_y**2 + q_z**2)
            q_w = math.sqrt(max(0.0, val))

        # Format 4: 7 values (Linear Acceleration [3] + Quaternion [4])
        elif len(values) == 7:
            ax, ay, az = values[0], values[1], values[2]
            q_x, q_y, q_z, q_w = values[3], values[4], values[5], values[6]
            
        # Format 5: 9 values (Linear Acceleration [3] + Gyroscope [3] + Rotation Vector [3])
        elif len(values) == 9:
            ax, ay, az = values[0], values[1], values[2]
            gx, gy, gz = values[3], values[4], values[5]
            q_x, q_y, q_z = values[6], values[7], values[8]
            val = 1.0 - (q_x**2 + q_y**2 + q_z**2)
            q_w = math.sqrt(max(0.0, val))

        # Format 6: 10 values (Linear Acceleration [3] + Gyroscope [3] + Quaternion [4])
        elif len(values) == 10:
            ax, ay, az = values[0], values[1], values[2]
            gx, gy, gz = values[3], values[4], values[5]
            q_x, q_y, q_z, q_w = values[6], values[7], values[8], values[9]
            
        else:
            self.get_logger().warn(f"Unsupported packet size ({len(values)} values): {packet_str}")
            return

        # 4. Construct the standard ROS 2 Imu message
        imu_msg = Imu()
        imu_msg.header.stamp = self.get_clock().now().to_msg()
        imu_msg.header.frame_id = self.frame_id

        # Orientation population
        if q_x is not None:
            imu_msg.orientation.x = q_x
            imu_msg.orientation.y = q_y
            imu_msg.orientation.z = q_z
            imu_msg.orientation.w = q_w
            # Standard covariance for Rotation Vector
            imu_msg.orientation_covariance = [
                0.01, 0.0, 0.0,
                0.0, 0.01, 0.0,
                0.0, 0.0, 0.01
            ]
        else:
            # -1 in the first element indicates orientation is invalid/not measured
            imu_msg.orientation_covariance[0] = -1.0

        # Linear Acceleration population
        if ax is not None:
            imu_msg.linear_acceleration.x = ax
            imu_msg.linear_acceleration.y = ay
            imu_msg.linear_acceleration.z = az
            # Standard covariance for accelerometer
            imu_msg.linear_acceleration_covariance = [
                0.1, 0.0, 0.0,
                0.0, 0.1, 0.0,
                0.0, 0.0, 0.1
            ]
        else:
            imu_msg.linear_acceleration_covariance[0] = -1.0

        # Angular Velocity population
        if gx is not None:
            imu_msg.angular_velocity.x = gx
            imu_msg.angular_velocity.y = gy
            imu_msg.angular_velocity.z = gz
            # Standard covariance for gyroscope
            imu_msg.angular_velocity_covariance = [
                0.02, 0.0, 0.0,
                0.0, 0.02, 0.0,
                0.0, 0.0, 0.02
            ]
        else:
            # -1 in the first element indicates angular velocity is invalid/not measured
            imu_msg.angular_velocity_covariance[0] = -1.0

        # Publish the complete message to the imu/data topic
        self.imu_pub.publish(imu_msg)

    def destroy_node(self):
        self.running = False
        try:
            self.sock.close()
        except:
            pass
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = PhoneImuNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()