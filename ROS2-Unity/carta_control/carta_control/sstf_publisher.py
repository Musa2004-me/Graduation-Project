import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TransformStamped
from tf2_ros import StaticTransformBroadcaster

class LidarTFPublisher(Node):

    def __init__(self):
        super().__init__('lidar_tf_publisher')

        self.broadcaster = StaticTransformBroadcaster(self)

        t = TransformStamped()

        t.header.stamp = self.get_clock().now().to_msg()

        t.header.frame_id = 'base_link'
        t.child_frame_id = 'lidar_sensor'

        # عدل القيم حسب مكان الليدار
        t.transform.translation.x = 0.0
        t.transform.translation.y = 0.0
        t.transform.translation.z = 0.30

        # no rotation
        t.transform.rotation.x = 0.0
        t.transform.rotation.y = 0.0
        t.transform.rotation.z = 0.0
        t.transform.rotation.w = 1.0

        self.broadcaster.sendTransform(t)

        self.get_logger().info('Published base_link -> lidar_link static TF')


def main():
    rclpy.init()

    node = LidarTFPublisher()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()