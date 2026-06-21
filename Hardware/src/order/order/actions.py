#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Float32
import threading


class CartController(Node):

    def __init__(self):
        super().__init__('cart_controller')

        # Subscribers
        self.cmd_sub = self.create_subscription(
            String,
            '/cart/command_state',
            self.cloud_command_callback,
            10
        )

        # Publishers
        self.bag_motor_pub = self.create_publisher(
            String,
            '/motor_command',
            10
        )

        self.left_rpm_pub = self.create_publisher(
            Float32,
            '/left_rpm_setpoint',
            10
        )

        self.right_rpm_pub = self.create_publisher(
            Float32,
            '/right_rpm_setpoint',
            10
        )

        self.lock_timer = None
        self.e_stop_active = False

        self.get_logger().info(
            "🛒 Central Cart Controller Coordinator Node online."
        )

    def cloud_command_callback(self, msg):
        command = msg.data.lower().strip()

        self.get_logger().info(
            f"📥 Processing Cloud Command: '{command}'"
        )

        if command == "unlock":
            self.handle_unlock()

        elif command == "emergency_stop":
            self.handle_emergency_stop()

        elif command == "resume_motion":
            self.handle_resume_motion()

        elif command == "dispatch":
            self.handle_dispatch()

        else:
            self.get_logger().warn(
                f"Unknown command: {command}"
            )

    def handle_unlock(self):
        """
        Send 1 immediately (OPEN)
        then send 1 again after 10 seconds (CLOSE)
        """

        if self.e_stop_active:
            self.get_logger().warn(
                "🚫 Unlock blocked. Emergency Stop active."
            )
            return

        self.get_logger().info(
            "🔓 Unlock sequence triggered: Opening bag motor..."
        )

        if self.lock_timer is not None:
            self.lock_timer.cancel()

        # OPEN
        bag_msg = String()
        bag_msg.data = '1'
        self.bag_motor_pub.publish(bag_msg)

        self.lock_timer = threading.Timer(
            10.0,
            self.close_bag_motor
        )

        self.lock_timer.start()

    def close_bag_motor(self):
        """
        Send 1 again after 10 sec to CLOSE.
        """

        if self.e_stop_active:
            self.get_logger().warn(
                "⚠️ Close cancelled due to Emergency Stop."
            )
            return

        self.get_logger().info(
            "🔒 10 seconds elapsed: Sending second toggle (1) to close bag."
        )

        bag_msg = String()
        bag_msg.data = '1'      # <-- THIS IS THE IMPORTANT CHANGE
        self.bag_motor_pub.publish(bag_msg)

    def handle_emergency_stop(self):

        self.get_logger().error(
            "🚨 EMERGENCY STOP RECEIVED!"
        )

        self.e_stop_active = True

        if self.lock_timer is not None:
            self.lock_timer.cancel()

        # stop bag motor
        bag_msg = String()
        bag_msg.data = 's'
        self.bag_motor_pub.publish(bag_msg)

        # stop wheels
        self.left_rpm_pub.publish(Float32(data=0.0))
        self.right_rpm_pub.publish(Float32(data=0.0))

        self.get_logger().info(
            "🛑 All motors stopped."
        )

    def handle_resume_motion(self):

        self.e_stop_active = False

        self.get_logger().info(
            "✅ Emergency Stop cleared."
        )

    def handle_dispatch(self):

        if self.e_stop_active:
            self.get_logger().warn(
                "🚫 Dispatch blocked by Emergency Stop."
            )
            return

        self.get_logger().info(
            "🚀 Dispatch command acknowledged."
        )

        self.left_rpm_pub.publish(Float32(data=50.0))
        self.right_rpm_pub.publish(Float32(data=50.0))

    def destroy_node(self):

        if self.lock_timer is not None:
            self.lock_timer.cancel()

        super().destroy_node()


def main(args=None):

    rclpy.init(args=args)

    node = CartController()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()

        try:
            rclpy.shutdown()
        except Exception:
            pass


if __name__ == '__main__':
    main()