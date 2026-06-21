# Odometry Package

This ROS 2 package calculates the odometry for a differential drive robot with two traction wheels and two casters. It subscribes to feedback from the two motors (RPMs) and optionally fuses the heading with IMU orientation and angular velocity readings to provide a robust, drift-resistant state estimate suitable for SLAM and Nav2.

## How it Works

### 1. Differential Kinematics
The node reads the wheel speed feedbacks on topics `/left_rpm_feedback` and `/right_rpm_feedback` (in RPM). 
The linear velocity of each wheel is computed using the wheel radius $R$:
$$v_{\text{left}} = \frac{RPM_{\text{left}} \times 2\pi R}{60}$$
$$v_{\text{right}} = \frac{RPM_{\text{right}} \times 2\pi R}{60}$$

Using standard differential drive kinematics:
- Robot linear velocity ($v$):
$$v = \frac{v_{\text{right}} + v_{\text{left}}}{2}$$
- Robot angular velocity ($w_{\text{wheel}}$) calculated from wheels:
$$w_{\text{wheel}} = \frac{v_{\text{right}} - v_{\text{left}}}{L}$$
where $L$ is the track width (distance between wheels).

### 2. IMU Fusion (Optional)
If `use_imu` is set to `True`, the node subscribes to the `/imu/data` topic. It extracts the orientation (quaternion) and converts it to yaw. To prevent orientation offsets at startup, it defines the first received yaw angle as an offset and calculates a relative yaw:
$$\theta_{\text{imu\_relative}} = \theta_{\text{imu}} - \theta_{\text{imu\_offset}}$$

At each iteration, the heading update $\Delta\theta$ is calculated from the IMU yaw change (properly normalized) rather than from the wheels, which eliminates drift caused by wheel slippage and caster drag. The angular velocity $w$ in the published twist is taken directly from the IMU's gyroscope reading (`angular_velocity.z`).

### 3. Pose Integration
The position is integrated using average heading during the interval:
$$\theta_{\text{mid}} = \theta_{\text{prev}} + \frac{\Delta\theta}{2}$$
$$\Delta x = v \cos(\theta_{\text{mid}}) \Delta t$$
$$\Delta y = v \sin(\theta_{\text{mid}}) \Delta t$$

The updated pose and velocity are published to the `odom` topic (`nav_msgs/msg/Odometry`) and, if configured, broadcasted via `tf` as a transform from the `odom` frame to the `base_link` frame.

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `wheel_radius` | float | `0.18415` | Radius of the traction wheels (meters). |
| `track_width` | float | `0.405` | Distance between wheels (meters). |
| `publish_rate` | float | `20.0` | Output publishing rate (Hz). |
| `use_imu` | bool | `False` | Enable/disable IMU yaw integration. |
| `publish_tf` | bool | `True` | Publish the `odom -> base_link` tf transform. (Disable if using EKF/robot_localization). |
| `odom_frame` | string | `"odom"` | Frame ID of the odometry. |
| `base_frame` | string | `"base_link"` | Frame ID of the robot's base link. |
| `rpm_timeout` | float | `0.2` | Time (s) before setting a wheel speed to 0.0 if feedback is lost. |
| `left_rpm_topic` | string | `"/left_rpm_feedback"` | Subscription topic for left wheel RPM. |
| `right_rpm_topic` | string | `"/right_rpm_feedback"` | Subscription topic for right wheel RPM. |
| `imu_topic` | string | `"imu/data"` | Subscription topic for IMU data. |
| `odom_topic` | string | `"odom"` | Topic name for published odometry. |

## Quick Start

### Build the Package
From the root of your workspace:
```bash
colcon build --packages-select odometry
```

### Run Node with pure Wheel Odometry
```bash
ros2 run odometry odometry_node
```

### Run Node with IMU Fusion Enabled
```bash
ros2 run odometry odometry_node --ros-args -p use_imu:=True
```

### Launch via Launch File
A launch file is provided in the `launch/` folder. Run it with:
```bash
ros2 launch odometry odometry.launch.py use_imu:=True
```
