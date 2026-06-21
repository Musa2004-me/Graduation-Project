from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():

    diff_drive_node = Node(
        package='carta_control',
        executable='diff_drive_node',
        name='diff_drive_node',
        output='screen'
    )

    return LaunchDescription([
        diff_drive_node
    ])
