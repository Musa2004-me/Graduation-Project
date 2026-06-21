#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
import math

class ImuReader(Node):
    """
    Node that subscribes to a Unity-published IMU topic and prints orientation, angular velocity, and linear acceleration.
    Converts Unity coordinates (Y-up, left-handed) to ROS coordinates (Z-up, right-handed).
    """

    def __init__(self):
        super().__init__('imu_reader')

        # Subscription to Unity IMU topic
        self.sub = self.create_subscription(
            Imu,
            '/imu/data',  # Unity IMU topic
            self.imu_callback,
            10
        )

        # Optional: publisher for ROS-aligned IMU
        self.pub = self.create_publisher(Imu, '/imu/ros_aligned', 10)

    def imu_callback(self, msg: Imu):
        # --- Convert Unity coordinates to ROS coordinates ---
        # Unity: X-forward, Y-up, Z-right (left-handed)
        # ROS: X-forward, Y-left, Z-up (right-handed)

        # Orientation quaternion conversion
        ux, uy, uz, uw = msg.orientation.x, msg.orientation.y, msg.orientation.z, msg.orientation.w
        ros_orientation = self.unity_to_ros_quaternion(ux, uy, uz, uw)

        # Angular velocity conversion
        av = msg.angular_velocity
        ros_angular_velocity = [
            av.x,   # X stays
            -av.z,  # Y = -Z
            av.y    # Z = Y
        ]

        # Linear acceleration conversion
        la = msg.linear_acceleration
        ros_linear_acceleration = [
            la.x,    # X stays
            -la.z,   # Y = -Z
            la.y     # Z = Y
        ]

        # Convert orientation to Euler for logging
        roll, pitch, yaw = self.quaternion_to_euler(*ros_orientation)

        # Log data
        self.get_logger().info(
            f"Orientation (deg): roll={math.degrees(roll):.2f}, pitch={math.degrees(pitch):.2f}, yaw={math.degrees(yaw):.2f}\n"
            f"Angular Vel (rad/s): x={ros_angular_velocity[0]:.2f}, y={ros_angular_velocity[1]:.2f}, z={ros_angular_velocity[2]:.2f}\n"
            f"Linear Acc (m/s^2): x={ros_linear_acceleration[0]:.2f}, y={ros_linear_acceleration[1]:.2f}, z={ros_linear_acceleration[2]:.2f}"
        )

        # Optional: republish converted IMU
        ros_msg = Imu()
        ros_msg.header.stamp = msg.header.stamp
        ros_msg.header.frame_id = "imu_link"
        ros_msg.orientation.x = ros_orientation[0]
        ros_msg.orientation.y = ros_orientation[1]
        ros_msg.orientation.z = ros_orientation[2]
        ros_msg.orientation.w = ros_orientation[3]
        ros_msg.angular_velocity.x = ros_angular_velocity[0]
        ros_msg.angular_velocity.y = ros_angular_velocity[1]
        ros_msg.angular_velocity.z = ros_angular_velocity[2]
        ros_msg.linear_acceleration.x = ros_linear_acceleration[0]
        ros_msg.linear_acceleration.y = ros_linear_acceleration[1]
        ros_msg.linear_acceleration.z = ros_linear_acceleration[2]

        self.pub.publish(ros_msg)

    @staticmethod
    def unity_to_ros_quaternion(x, y, z, w):
        """
        Convert Unity quaternion (X-forward, Y-up, Z-right) to ROS quaternion (X-forward, Y-left, Z-up)
        """
        return (x, -z, y, w)

    @staticmethod
    def quaternion_to_euler(x, y, z, w):
        """
        Convert quaternion (x, y, z, w) to Euler angles (roll, pitch, yaw)
        """
        # Roll (x-axis rotation)
        t0 = +2.0 * (w * x + y * z)
        t1 = +1.0 - 2.0 * (x * x + y * y)
        roll = math.atan2(t0, t1)

        # Pitch (y-axis rotation)
        t2 = +2.0 * (w * y - z * x)
        t2 = +1.0 if t2 > +1.0 else t2
        t2 = -1.0 if t2 < -1.0 else t2
        pitch = math.asin(t2)

        # Yaw (z-axis rotation)
        t3 = +2.0 * (w * z + x * y)
        t4 = +1.0 - 2.0 * (y * y + z * z)
        yaw = math.atan2(t3, t4)

        return roll, pitch, yaw


def main(args=None):
    rclpy.init(args=args)
    node = ImuReader()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
