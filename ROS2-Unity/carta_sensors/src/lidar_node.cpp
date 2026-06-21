#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/laser_scan.hpp>
#include <cmath>
#include <vector>
#include <limits>
// تقسيم الاتجاهات من غير 
// Front / Left / Right obstacles
class LidarProcessor : public rclcpp::Node
{
public:
    LidarProcessor() : Node("lidar_processor")
    {
        subscription_ = this->create_subscription<sensor_msgs::msg::LaserScan>(
            "/scan",
            10,
            std::bind(&LidarProcessor::scanCallback, this, std::placeholders::_1)
        );

        RCLCPP_INFO(this->get_logger(), "LiDAR Processor Node Started");
    }

private:
    void scanCallback(const sensor_msgs::msg::LaserScan::SharedPtr msg)
    {
        const float angle_min = msg->angle_min;
        const float angle_increment = msg->angle_increment;

        float closest_distance = std::numeric_limits<float>::max();
        float closest_angle = 0.0;

        for (size_t i = 0; i < msg->ranges.size(); i++)
        {
            float range = msg->ranges[i];

            // ignore invalid readings
            if (std::isinf(range) || std::isnan(range))
                continue;

            float angle = angle_min + i * angle_increment;

            // print (optional - heavy if enabled)
            // RCLCPP_INFO(this->get_logger(), "Angle: %.2f, Distance: %.2f", angle, range);

            // find closest obstacle
            if (range < closest_distance)
            {
                closest_distance = range;
                closest_angle = angle;
            }
        }

        RCLCPP_INFO(this->get_logger(),
                    "Closest obstacle -> Distance: %.2f m | Angle: %.2f rad (%.2f deg)",
                    closest_distance,
                    closest_angle,
                    closest_angle * 180.0 / M_PI);
    }

    rclcpp::Subscription<sensor_msgs::msg::LaserScan>::SharedPtr subscription_;
};

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<LidarProcessor>());
    rclcpp::shutdown();
    return 0;
}