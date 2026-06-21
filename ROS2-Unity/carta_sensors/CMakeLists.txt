cmake_minimum_required(VERSION 3.8)
project(carta_sensors)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# ── Dependencies ──────────────────────────────────────────────────────────────
find_package(ament_cmake REQUIRED)
find_package(rclpy       REQUIRED)
find_package(rclcpp      REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs    REQUIRED)
find_package(std_srvs    REQUIRED)
find_package(cv_bridge   REQUIRED)

# ── C++ encoder node ──────────────────────────────────────────────────────────
add_executable(left_encoder_node
  src/left_encoder_node.cpp
)
add_executable(right_encoder_node
  src/right_encoder_node.cpp
)


target_compile_features(right_encoder_node PUBLIC cxx_std_17)
target_compile_features(left_encoder_node PUBLIC cxx_std_17)

ament_target_dependencies(left_encoder_node
  rclcpp
  std_msgs
  std_srvs
)

ament_target_dependencies(right_encoder_node
  rclcpp
  std_msgs
  std_srvs
)

install(TARGETS left_encoder_node right_encoder_node
  DESTINATION lib/${PROJECT_NAME}
)
# ── LiDAR node ─────────────────────────────────────────────
add_executable(lidar_node
  src/lidar_node.cpp
)

target_compile_features(lidar_node PUBLIC cxx_std_17)

ament_target_dependencies(lidar_node
  rclcpp
  sensor_msgs
)

install(TARGETS lidar_node
  DESTINATION lib/${PROJECT_NAME}
)
# ── Python nodes ──────────────────────────────────────────────────────────────
install(
  PROGRAMS
    sensors/camera_sensor.py
    sensors/lidar_sensor.py
    sensors/imu_sensor.py
  DESTINATION lib/${PROJECT_NAME}
)

# ── Testing ───────────────────────────────────────────────────────────────────
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()