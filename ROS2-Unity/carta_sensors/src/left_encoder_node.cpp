#include <atomic>
#include <chrono>
#include <mutex>
#include <cmath>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/bool.hpp"
#include "std_msgs/msg/int32.hpp"
#include "std_msgs/msg/float64.hpp"
#include "std_srvs/srv/trigger.hpp"

class LeftEncoderNode : public rclcpp::Node
{
public:
  LeftEncoderNode() : Node("left_encoder_node")
  {
    this->declare_parameter<double>("pulses_per_revolution", 90.0/2.0);
    this->declare_parameter<double>("publish_rate_hz",       20.0);
    this->declare_parameter<std::string>("pulse_topic", "/encoder/left/pulse");
    this->declare_parameter<std::string>("count_topic", "/encoder/left/count");
    this->declare_parameter<std::string>("rpm_topic",   "/encoder/left/rpm");

    ppr_          = this->get_parameter("pulses_per_revolution").as_double();
    rate_hz_      = this->get_parameter("publish_rate_hz").as_double();
    pulse_topic_  = this->get_parameter("pulse_topic").as_string();
    count_topic_  = this->get_parameter("count_topic").as_string();
    rpm_topic_    = this->get_parameter("rpm_topic").as_string();

    // Subscriber: receives a Bool=true on every encoder pulse from Unity
    pulse_sub_ = this->create_subscription<std_msgs::msg::Bool>(
      pulse_topic_, rclcpp::QoS(10),
      [this](const std_msgs::msg::Bool::SharedPtr msg) {
        if (!msg->data) return;
        total_count_.fetch_add(1, std::memory_order_relaxed);
        std::lock_guard<std::mutex> lk(mtx_);
        ++window_count_;
      });

    count_pub_ = this->create_publisher<std_msgs::msg::Int32>(count_topic_, 10);
    rpm_pub_   = this->create_publisher<std_msgs::msg::Float64>(rpm_topic_, 10);

    last_time_ = this->now();

    auto period = std::chrono::duration_cast<std::chrono::nanoseconds>(
      std::chrono::duration<double>(1.0 / rate_hz_));

    publish_timer_ = this->create_wall_timer(period, [this]() { publish_tick(); });

    // Optional reset: ros2 service call /encoder/left/reset std_srvs/srv/Trigger {}
    reset_srv_ = this->create_service<std_srvs::srv::Trigger>(
      "/encoder/left/reset",
      [this](const std_srvs::srv::Trigger::Request::SharedPtr,
             std_srvs::srv::Trigger::Response::SharedPtr res) {
        total_count_.store(0, std::memory_order_relaxed);
        { std::lock_guard<std::mutex> lk(mtx_); window_count_ = 0; }
        res->success = true;
        res->message = "Encoder count reset to 0.";
        RCLCPP_INFO(this->get_logger(), "Encoder count reset.");
      });

    RCLCPP_INFO(this->get_logger(),
      "LeftEncoderNode ready  |  pulse: %s  |  PPR: %.0f  |  rate: %.1f Hz",
      pulse_topic_.c_str(), ppr_, rate_hz_);
  }

private:
  void publish_tick()
  {
    const rclcpp::Time now = this->now();
    const double dt = (now - last_time_).seconds();
    last_time_ = now;

    int32_t window = 0;
    { std::lock_guard<std::mutex> lk(mtx_); window = window_count_; window_count_ = 0; }

    // Cumulative count
    std_msgs::msg::Int32 cnt;
    cnt.data = total_count_.load(std::memory_order_relaxed);
    count_pub_->publish(cnt);

    // RPM = (pulses / PPR) * (60 / dt_seconds)
    std_msgs::msg::Float64 rpm;
    rpm.data = (dt > 0.0 && ppr_ > 0.0)
      ? (static_cast<double>(window) / ppr_) * (60.0 / dt)
      : 0.0;
    rpm_pub_->publish(rpm);
  }

  // Parameters
  double ppr_, rate_hz_;
  std::string pulse_topic_, count_topic_, rpm_topic_;

  // State
  std::atomic<int32_t> total_count_{0};
  int32_t window_count_{0};
  std::mutex mtx_;
  rclcpp::Time last_time_;

  // ROS interfaces
  rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr      pulse_sub_;
  rclcpp::Publisher<std_msgs::msg::Int32>::SharedPtr        count_pub_;
  rclcpp::Publisher<std_msgs::msg::Float64>::SharedPtr      rpm_pub_;
  rclcpp::TimerBase::SharedPtr                              publish_timer_;
  rclcpp::Service<std_srvs::srv::Trigger>::SharedPtr        reset_srv_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<LeftEncoderNode>());
  rclcpp::shutdown();
  return 0;
}