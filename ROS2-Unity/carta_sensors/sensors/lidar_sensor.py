#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool
import math

class ObstacleDetector(Node):
    """
    Node that reads LiDAR and sets obstacle flags in 8 directions:
    front, front-left, left, back-left, back, back-right, right, front-right
    """

    def __init__(self):
        super().__init__('obstacle_detector')

        # Subscription
        self.sub = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10
        )

        # Publishers for visualization
        self.pub_dict = {}
        directions = ['front', 'front_left', 'left', 'back_left', 
                      'back', 'back_right', 'right', 'front_right']
        for d in directions:
            self.pub_dict[d] = self.create_publisher(Bool, f'/obstacle_{d}', 10)

        # Thresholds
        self.front_thresh = 3.0
        self.side_thresh  = 1.5
        self.back_thresh  = 1.0  # optional, usually closer

        # Store last scan
        self.obstacles = {d: False for d in directions}

    def scan_callback(self, msg: LaserScan):
        ranges = msg.ranges
        angle_min = msg.angle_min
        angle_inc = msg.angle_increment

        # Reset obstacles
        for key in self.obstacles:
            self.obstacles[key] = False

        for i, r in enumerate(ranges):
            if r < msg.range_min or r > msg.range_max:
                continue

            angle = angle_min + i * angle_inc
            deg = math.degrees(angle)

            # Normalize angle to [-180, 180]
            deg = (deg + 180) % 360 - 180

            # Check sectors
            if -22.5 <= deg <= 22.5 and r < self.front_thresh:
                self.obstacles['front'] = True
            elif 22.5 < deg <= 67.5 and r < self.side_thresh:
                self.obstacles['front_left'] = True
            elif 67.5 < deg <= 112.5 and r < self.side_thresh:
                self.obstacles['left'] = True
            elif 112.5 < deg <= 157.5 and r < self.side_thresh:
                self.obstacles['back_left'] = True
            elif deg > 157.5 or deg < -157.5 and r < self.back_thresh:
                self.obstacles['back'] = True
            elif -157.5 < deg <= -112.5 and r < self.side_thresh:
                self.obstacles['back_right'] = True
            elif -112.5 < deg <= -67.5 and r < self.side_thresh:
                self.obstacles['right'] = True
            elif -67.5 < deg <= -22.5 and r < self.side_thresh:
                self.obstacles['front_right'] = True

        # Publish for visualization
        for key, pub in self.pub_dict.items():
            pub.publish(Bool(data=self.obstacles[key]))


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
