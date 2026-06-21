from setuptools import find_packages, setup

package_name = 'carta_control'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
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
            'diff_drive_node = carta_control.diff_drive_node:main',
            'diff_drive_teleop = carta_control.diff_drive_teleop:main',
            'bag_sheet_teleop = carta_control.bag_sheet_control:main',
            'sstf_publisher = carta_control.sstf_publisher:main',

        ],
    },
)
