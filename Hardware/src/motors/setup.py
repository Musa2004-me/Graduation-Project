from setuptools import find_packages, setup

package_name = 'motors'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch',
            ['launch/motors_serial.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='musa',
    maintainer_email='musaelshenawy5@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'left_rpm_serial = motors.left_rpm_serial:main',
            'right_rpm_serial = motors.right_rpm_serial:main',
            'velocity_to_RPM = motors.velocity_to_RPM:main',
            'fuzzy_w_control= motors.fuzzy_w_control:main',
            'fuzzy_cascaded_control= motors.fuzzy_cascaded_control:main',
            'rpm_commander = motors.rpm_commander:main',
            'motion_controller = motors.motion_controller:main',
            'rpm_wifi = motors.rpm_wifi:main',
        ],
    },
)
