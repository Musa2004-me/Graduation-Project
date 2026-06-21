using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using Unity.Robotics.ROSTCPConnector.ROSGeometry; // مهم جداً للتحويلات التلقائية للمحاور
using RosMessageTypes.Sensor;
using RosMessageTypes.Std; // تم إضافتها لإنشاء الـ Header

public class IMUPublisher : MonoBehaviour
{
    public string topicName = "imu/data";
    public string frameId = "imu_link"; // ربطه بفريم الـ TF الصحيح
    public float publishRate = 50f;

    private ROSConnection ros;
    private float timer;
    public IMUSensor imuSensor;

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.RegisterPublisher<ImuMsg>(topicName);

        if (imuSensor == null)
            imuSensor = GetComponent<IMUSensor>();
    }

    void FixedUpdate()
    {
        timer += Time.fixedDeltaTime;
        if (timer >= 1f / publishRate)
        {
            timer = 0f;
            PublishIMU();
        }
    }

    void PublishIMU()
    {
        if (imuSensor == null) return;

        ImuMsg msg = new ImuMsg();
        
        // 1. إعداد الـ Header وإضافة الـ frame_id والـ Timestamp
        msg.header = new HeaderMsg();
        msg.header.frame_id = frameId;
        msg.header.stamp.sec = (int)Time.time;
        msg.header.stamp.nanosec = (uint)((Time.time % 1f) * 1e9f);

        // 2. تحويل المحاور من الـ Left-Handed (Unity) إلى الـ Right-Handed FLU (ROS) تلقائياً وبدقة
        msg.orientation = imuSensor.orientation.To<FLU>();
        msg.angular_velocity = imuSensor.angularVelocity.To<FLU>();
        msg.linear_acceleration = imuSensor.linearAcceleration.To<FLU>();

        ros.Publish(topicName, msg);
    }
}
