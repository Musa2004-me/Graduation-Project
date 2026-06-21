from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():

    left_bridge = Node(
        package='motors',
        executable='left_rpm_serial',
        name='left_serial_bridge',
        output='screen'
    )

    right_bridge = Node(
        package='motors',
        executable='right_rpm_serial',
        name='right_serial_bridge',
        output='screen'
    )

    return LaunchDescription([
        left_bridge,
        right_bridge
    ])