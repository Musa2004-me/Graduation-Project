using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Sensor;
using RosMessageTypes.Std;

public class LidarROS2Publisher : MonoBehaviour
{
    public Lidar2D lidar; 
    public string topicName = "/scan";
    public float scanFrequency = 20f; 

    private ROSConnection ros;
    private float timer;

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.RegisterPublisher<LaserScanMsg>(topicName);
    }

    void Update()
    {
        // استخدام Time.deltaTime ممتاز هنا لأنه بيتحجم تلقائياً مع وقت المحاكاة
        timer += Time.deltaTime;
        if (timer >= 1f / scanFrequency)
        {
            timer = 0f;
            PublishLaserScan();
        }
    }

    void PublishLaserScan()
    {
        if (lidar == null || lidar.distances == null || lidar.distances.Length == 0) return;

        LaserScanMsg scan = new LaserScanMsg();
        scan.header = new HeaderMsg();
        scan.header.frame_id = "lidar_sensor"; 

        // 🔥 التعديل الجوهري: مزامنة الوقت بناءً على ساعة المحاكاة (Simulation Time) ليتطابق مع الـ TF
        double simTime = Time.timeAsDouble;
        int sec = (int)simTime;
        uint nanosec = (uint)((simTime - sec) * 1e9);

        scan.header.stamp.sec = sec;
        scan.header.stamp.nanosec = nanosec;

        scan.angle_min = 0f;
        scan.angle_max = 2f * Mathf.PI;
        scan.angle_increment = scan.angle_max / lidar.numRays;
        
        scan.time_increment = 0f;
        scan.scan_time = 1f / scanFrequency;
        scan.range_min = lidar.minDistance > 0 ? lidar.minDistance : 0.1f;
        scan.range_max = lidar.maxDistance > 0 ? lidar.maxDistance : 30f;

        scan.ranges = new float[lidar.distances.Length];
        
        for (int i = 0; i < lidar.distances.Length; i++)
        {
            float dist = lidar.distances[i];
            if (float.IsNaN(dist) || float.IsInfinity(dist) || dist <= scan.range_min)
            {
                scan.ranges[i] = scan.range_max; 
            }
            else
            {
                scan.ranges[i] = dist;
            }
        }

        ros.Publish(topicName, scan);
    }
}
