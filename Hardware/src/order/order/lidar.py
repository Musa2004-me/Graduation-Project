#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import LaserScan


class ScanRegions(Node):

    def __init__(self):
        super().__init__('scan_regions')

        self.threshold = 0.04  # 4 cm

        self.subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10
        )

        self.get_logger().info("Scan region detector started")

    def scan_callback(self, msg):

        regions = {
            'FRONT': [],
            'FRONT_LEFT': [],
            'LEFT': [],
            'BACK_LEFT': [],
            'BACK': [],
            'BACK_RIGHT': [],
            'RIGHT': [],
            'FRONT_RIGHT': []
        }

        for i, r in enumerate(msg.ranges):

            if math.isinf(r) or math.isnan(r):
                continue

            angle = msg.angle_min + i * msg.angle_increment
            angle_deg = math.degrees(angle)
            angle_deg = (angle_deg + 270) % 360   # shift frame so LiDAR forward = LEFT becomes FRONT

            if angle_deg < 0:
                angle_deg += 360

            if 337.5 <= angle_deg or angle_deg < 22.5:
                regions['FRONT'].append(r)

            elif 22.5 <= angle_deg < 67.5:
                regions['FRONT_LEFT'].append(r)

            elif 67.5 <= angle_deg < 112.5:
                regions['LEFT'].append(r)

            elif 112.5 <= angle_deg < 157.5:
                regions['BACK_LEFT'].append(r)

            elif 157.5 <= angle_deg < 202.5:
                regions['BACK'].append(r)

            elif 202.5 <= angle_deg < 247.5:
                regions['BACK_RIGHT'].append(r)

            elif 247.5 <= angle_deg < 292.5:
                regions['RIGHT'].append(r)

            elif 292.5 <= angle_deg < 337.5:
                regions['FRONT_RIGHT'].append(r)

        for name, values in regions.items():

            if not values:
                continue

            min_dist = min(values)

            if min_dist < self.threshold:
                self.get_logger().warn(
                    f'OBSTACLE IN {name} : {min_dist:.3f} m'
                )


def main(args=None):
    rclpy.init(args=args)

    node = ScanRegions()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()