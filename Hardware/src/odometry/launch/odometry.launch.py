import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # Declare the launch arguments
    wheel_radius_arg = DeclareLaunchArgument(
        'wheel_radius',
        default_value='0.18415',
        description='Wheel radius in meters'
    )

    track_width_arg = DeclareLaunchArgument(
        'track_width',
        default_value='0.405',
        description='Track width (distance between wheels) in meters'
    )

    use_imu_arg = DeclareLaunchArgument(
        'use_imu',
        default_value='true',
        description='Whether to use IMU data to fuse yaw/orientation'
    )

    publish_tf_arg = DeclareLaunchArgument(
        'publish_tf',
        default_value='true',
        description='Whether to publish tf transform (odom -> base_link)'
    )

    publish_rate_arg = DeclareLaunchArgument(
        'publish_rate',
        default_value='20.0',
        description='Rate at which to compute and publish odometry (Hz)'
    )

    left_rpm_topic_arg = DeclareLaunchArgument(
        'left_rpm_topic',
        default_value='/left_rpm_feedback',
        description='Topic name for left wheel RPM feedback'
    )

    right_rpm_topic_arg = DeclareLaunchArgument(
        'right_rpm_topic',
        default_value='/right_rpm_feedback',
        description='Topic name for right wheel RPM feedback'
    )

    imu_topic_arg = DeclareLaunchArgument(
        'imu_topic',
        default_value='imu/data',
        description='Topic name for IMU feedback'
    )

    odom_topic_arg = DeclareLaunchArgument(
        'odom_topic',
        default_value='odom',
        description='Topic name for published odometry'
    )

    odom_frame_arg = DeclareLaunchArgument(
        'odom_frame',
        default_value='odom',
        description='Odom frame ID'
    )

    base_frame_arg = DeclareLaunchArgument(
        'base_frame',
        default_value='base_link',
        description='Base link frame ID'
    )

    rpm_timeout_arg = DeclareLaunchArgument(
        'rpm_timeout',
        default_value='0.6',
        description='Timeout for RPM feedback in seconds'
    )

    # Node configuration
    odometry_node = Node(
        package='odometry',
        executable='odometry_node',
        name='odometry_node',
        output='screen',
        parameters=[{
            'wheel_radius': LaunchConfiguration('wheel_radius'),
            'track_width': LaunchConfiguration('track_width'),
            'use_imu': LaunchConfiguration('use_imu'),
            'publish_tf': LaunchConfiguration('publish_tf'),
            'publish_rate': LaunchConfiguration('publish_rate'),
            'left_rpm_topic': LaunchConfiguration('left_rpm_topic'),
            'right_rpm_topic': LaunchConfiguration('right_rpm_topic'),
            'imu_topic': LaunchConfiguration('imu_topic'),
            'odom_topic': LaunchConfiguration('odom_topic'),
            'odom_frame': LaunchConfiguration('odom_frame'),
            'base_frame': LaunchConfiguration('base_frame'),
            'rpm_timeout': LaunchConfiguration('rpm_timeout'),
        }]
    )

    return LaunchDescription([
        wheel_radius_arg,
        track_width_arg,
        use_imu_arg,
        publish_tf_arg,
        publish_rate_arg,
        left_rpm_topic_arg,
        right_rpm_topic_arg,
        imu_topic_arg,
        odom_topic_arg,
        odom_frame_arg,
        base_frame_arg,
        rpm_timeout_arg,
        odometry_node
    ])
