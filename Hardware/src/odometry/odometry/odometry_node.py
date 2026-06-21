#!/usr/bin/env python3

import math
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
from sensor_msgs.msg import Imu
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
import tf2_ros

def euler_to_quaternion(roll, pitch, yaw):
    """
    Convert roll, pitch, yaw to a quaternion.
    """
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)

    qw = cr * cp * cy + sr * sp * sy
    qx = sr * cp * cy - cr * sp * sy
    qy = cr * sp * cy + sr * cp * sy
    qz = cr * cp * sy - sr * sp * sy

    return qx, qy, qz, qw

def quaternion_to_yaw(x, y, z, w):
    """
    Extract yaw from quaternion representation.
    """
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    return math.atan2(siny_cosp, cosy_cosp)

def normalize_angle(angle):
    """
    Normalize angle to be within [-pi, pi].
    """
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle

class OdometryNode(Node):
    def __init__(self):
        super().__init__('odometry_node')

        # 1. Declare and get parameters
        self.declare_parameter("wheel_radius", 0.3683 / 2.0)
        self.declare_parameter("track_width", 0.405)
        self.declare_parameter("publish_rate", 20.0) # Hz
        self.declare_parameter("use_imu", False)
        self.declare_parameter("publish_tf", True)
        self.declare_parameter("odom_frame", "odom")
        self.declare_parameter("base_frame", "base_link")
        self.declare_parameter("rpm_timeout", 0.6) # seconds
        self.declare_parameter("left_rpm_topic", "/left_rpm_feedback")
        self.declare_parameter("right_rpm_topic", "/right_rpm_feedback")
        self.declare_parameter("imu_topic", "imu/data")
        self.declare_parameter("odom_topic", "odom")

        self.R = self.get_parameter("wheel_radius").value
        self.L = self.get_parameter("track_width").value
        self.publish_rate = self.get_parameter("publish_rate").value
        self.use_imu = self.get_parameter("use_imu").value
        self.publish_tf = self.get_parameter("publish_tf").value
        self.odom_frame = self.get_parameter("odom_frame").value
        self.base_frame = self.get_parameter("base_frame").value
        self.rpm_timeout = self.get_parameter("rpm_timeout").value
        self.left_rpm_topic = self.get_parameter("left_rpm_topic").value
        self.right_rpm_topic = self.get_parameter("right_rpm_topic").value
        self.imu_topic = self.get_parameter("imu_topic").value
        self.odom_topic = self.get_parameter("odom_topic").value

        # Log parameters
        self.get_logger().info("Odometry Node Initialized with parameters:")
        self.get_logger().info(f" - Wheel Radius: {self.R} m")
        self.get_logger().info(f" - Track Width (L): {self.L} m")
        self.get_logger().info(f" - Publish Rate: {self.publish_rate} Hz")
        self.get_logger().info(f" - Use IMU: {self.use_imu}")
        self.get_logger().info(f" - Publish TF (odom->base_link): {self.publish_tf}")
        self.get_logger().info(f" - Odom Frame: {self.odom_frame}")
        self.get_logger().info(f" - Base Frame: {self.base_frame}")

        # 2. Robot state variables
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0

        # Latest motor readings
        self.left_rpm = 0.0
        self.right_rpm = 0.0
        self.left_rpm_recv_time = self.get_clock().now()
        self.right_rpm_recv_time = self.get_clock().now()

        # IMU state variables
        self.imu_yaw = 0.0
        self.imu_yaw_rate = 0.0
        self.imu_yaw_offset = None
        self.last_imu_yaw = 0.0
        self.imu_received = False

        # Covariances for the Odometry message
        # Pose covariance: x, y, z, roll, pitch, yaw
        self.pose_covariance = [
            0.005, 0.0,   0.0,   0.0,   0.0,   0.0,
            0.0,   0.005, 0.0,   0.0,   0.0,   0.0,
            0.0,   0.0,   999.0, 0.0,   0.0,   0.0,
            0.0,   0.0,   0.0,   999.0, 0.0,   0.0,
            0.0,   0.0,   0.0,   0.0,   999.0, 0.0,
            0.0,   0.0,   0.0,   0.0,   0.0,   0.03
        ]

        # Twist covariance: vx, vy, vz, v_roll, v_pitch, v_yaw
        self.twist_covariance = [
            0.002, 0.0,   0.0,   0.0,   0.0,   0.0,
            0.0,   0.002, 0.0,   0.0,   0.0,   0.0,
            0.0,   0.0,   999.0, 0.0,   0.0,   0.0,
            0.0,   0.0,   0.0,   999.0, 0.0,   0.0,
            0.0,   0.0,   0.0,   0.0,   999.0, 0.0,
            0.0,   0.0,   0.0,   0.0,   0.0,   0.01
        ]

        # Adjust covariance values if IMU is used
        if self.use_imu:
            self.pose_covariance[35] = 0.001  # Yaw variance is much smaller
            self.twist_covariance[35] = 0.0005 # Yaw rate variance is smaller

        # 3. Subscribers and Publishers
        self.left_rpm_sub = self.create_subscription(
            Float32, self.left_rpm_topic, self.left_rpm_callback, 10)
        self.right_rpm_sub = self.create_subscription(
            Float32, self.right_rpm_topic, self.right_rpm_callback, 10)
        
        if self.use_imu:
            self.imu_sub = self.create_subscription(
                Imu, self.imu_topic, self.imu_callback, 10)

        self.odom_pub = self.create_publisher(Odometry, self.odom_topic, 10)

        # 4. TF Broadcaster
        if self.publish_tf:
            self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)

        # 5. Timer for odometry computation loop
        self.last_time = self.get_clock().now()
        dt_timer = 1.0 / self.publish_rate
        self.timer = self.create_timer(dt_timer, self.update_odometry)

    def left_rpm_callback(self, msg):
        self.left_rpm = msg.data
        self.left_rpm_recv_time = self.get_clock().now()

    def right_rpm_callback(self, msg):
        self.right_rpm = msg.data
        self.right_rpm_recv_time = self.get_clock().now()

    def imu_callback(self, msg):
        # Extract yaw from quaternion
        qx = msg.orientation.x
        qy = msg.orientation.y
        qz = msg.orientation.z
        qw = msg.orientation.w
        
        raw_yaw = quaternion_to_yaw(qx, qy, qz, qw)
        
        if self.imu_yaw_offset is None:
            self.imu_yaw_offset = raw_yaw
            self.get_logger().info(f"First IMU reading received. Setting initial yaw offset: {self.imu_yaw_offset:.4f} rad")
            self.last_imu_yaw = 0.0
        
        self.imu_yaw = normalize_angle(raw_yaw - self.imu_yaw_offset)
        self.imu_yaw_rate = msg.angular_velocity.z
        self.imu_received = True

    def update_odometry(self):
        current_time = self.get_clock().now()
        dt = (current_time - self.last_time).nanoseconds / 1e9

        # Handle dt abnormalities (e.g. startup or simulation resets)
        if dt <= 0.0:
            self.last_time = current_time
            return
        if dt > 1.0:
            self.get_logger().warn(f"Large time step detected (dt = {dt:.4f}s). Skipping state update.")
            self.last_time = current_time
            return

        # Check for sensor timeout (motor RPM data loss)
        t_now = self.get_clock().now()
        left_elapsed = (t_now - self.left_rpm_recv_time).nanoseconds / 1e9
        right_elapsed = (t_now - self.right_rpm_recv_time).nanoseconds / 1e9

        active_left_rpm = max(0.0, self.left_rpm)
        active_right_rpm = max(0.0, self.right_rpm)

        if left_elapsed > self.rpm_timeout:
            active_left_rpm = 0.0
        if right_elapsed > self.rpm_timeout:
            active_right_rpm = 0.0

        # Convert RPM to linear wheel velocities (m/s)
        # RPM * 2 * pi * R / 60
        v_left = (active_left_rpm * 2.0 * math.pi * self.R) / 60.0
        v_right = (active_right_rpm * 2.0 * math.pi * self.R) / 60.0

        # Differential kinematics
        v = (v_right + v_left) / 2.0
        w_wheel = (v_right - v_left) / self.L

        # Compute heading change and current heading
        if self.use_imu and self.imu_received:
            # Heading from IMU
            d_theta = normalize_angle(self.imu_yaw - self.last_imu_yaw)
            self.theta = normalize_angle(self.theta + d_theta)
            self.last_imu_yaw = self.imu_yaw
            # Use gyroscope reading for angular velocity if available, otherwise estimate it
            w = self.imu_yaw_rate
        else:
            # Pure wheel odometry heading
            d_theta = w_wheel * dt
            self.theta = normalize_angle(self.theta + d_theta)
            w = w_wheel

        # Update position using average heading during the interval
        theta_mid = self.theta - (d_theta / 2.0)
        dx = v * math.cos(theta_mid) * dt
        dy = v * math.sin(theta_mid) * dt

        self.x += dx
        self.y += dy

        # Convert heading to quaternion
        qx, qy, qz, qw = euler_to_quaternion(0.0, 0.0, self.theta)

        # 6. Publish Odometry message
        odom_msg = Odometry()
        odom_msg.header.stamp = current_time.to_msg()
        odom_msg.header.frame_id = self.odom_frame
        odom_msg.child_frame_id = self.base_frame

        # Set the pose
        odom_msg.pose.pose.position.x = self.x
        odom_msg.pose.pose.position.y = self.y
        odom_msg.pose.pose.position.z = 0.0
        odom_msg.pose.pose.orientation.x = qx
        odom_msg.pose.pose.orientation.y = qy
        odom_msg.pose.pose.orientation.z = qz
        odom_msg.pose.pose.orientation.w = qw
        odom_msg.pose.covariance = self.pose_covariance

        # Set the twist (velocities)
        odom_msg.twist.twist.linear.x = v
        odom_msg.twist.twist.linear.y = 0.0
        odom_msg.twist.twist.linear.z = 0.0
        odom_msg.twist.twist.angular.x = 0.0
        odom_msg.twist.twist.angular.y = 0.0
        odom_msg.twist.twist.angular.z = w
        odom_msg.twist.covariance = self.twist_covariance

        self.odom_pub.publish(odom_msg)

        # 7. Publish TF transform
        if self.publish_tf:
            t = TransformStamped()
            t.header.stamp = current_time.to_msg()
            t.header.frame_id = self.odom_frame
            t.child_frame_id = self.base_frame

            t.transform.translation.x = self.x
            t.transform.translation.y = self.y
            t.transform.translation.z = 0.0
            t.transform.rotation.x = qx
            t.transform.rotation.y = qy
            t.transform.rotation.z = qz
            t.transform.rotation.w = qw

            self.tf_broadcaster.sendTransform(t)

        self.last_time = current_time

def main(args=None):
    rclpy.init(args=args)
    node = OdometryNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
