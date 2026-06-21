using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using Unity.Robotics.ROSTCPConnector.ROSGeometry;

using RosMessageTypes.Nav;
using RosMessageTypes.Geometry;
using RosMessageTypes.Std;
using RosMessageTypes.Tf2;

public class tf : MonoBehaviour
{
    [Header("ROS Connection & Topics")]
    public string odomTopic = "/odom";
    public string tfTopic = "/tf";

    [Header("Robot Links & Articulation")]
    public Transform baseLink;
    public ArticulationBody baseArticulation; 
    
    [Header("Sensors & Wheels Links")]
    public Transform lidarLink;
    public Transform imuLink;
    public Transform leftWheel;
    public Transform rightWheel;

    private ROSConnection ros;

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.RegisterPublisher<OdometryMsg>(odomTopic);
        ros.RegisterPublisher<TFMessageMsg>(tfTopic);

        if (baseLink == null)
        {
            Debug.LogError("رجاءً قم بسحب الـ baseLink في الـ Inspector لتفادي الأخطاء!");
        }
    }

    void FixedUpdate()
    {
        if (baseLink == null) return;
        
        // حساب وقت موحد تماماً لهذه الـ Frame وضمان إرساله للأودومتري والـ TF معاً
        System.DateTimeOffset now = System.DateTimeOffset.UtcNow;
        int sec = (int)now.ToUnixTimeSeconds();
        uint nanosec = (uint)(now.Millisecond * 1_000_000);

        PublishOdom(sec, nanosec);
        PublishTF(sec, nanosec);
    }

    void PublishOdom(int sec, uint nanosec)
    {
        if (baseArticulation == null) return;

        OdometryMsg odom = new OdometryMsg();
        odom.header = new HeaderMsg();
        
        odom.header.stamp.sec = sec;
        odom.header.stamp.nanosec = nanosec;
        
        odom.header.frame_id = "odom";
        odom.child_frame_id = "base_link";

        odom.pose.pose.position = baseLink.position.To<FLU>();
        odom.pose.pose.orientation = baseLink.rotation.To<FLU>();

        if (baseArticulation != null)
        {
            odom.twist.twist.linear = baseArticulation.velocity.To<FLU>();
            odom.twist.twist.angular = baseArticulation.angularVelocity.To<FLU>();
        }
        else
        {
            odom.twist.twist.linear = new Vector3Msg();
            odom.twist.twist.angular = new Vector3Msg();
        }

        ros.Publish(odomTopic, odom);
    }

    void PublishTF(int sec, uint nanosec)
    {
        TransformStampedMsg[] transforms =
        {
            CreateWorldTF("odom", "base_link", baseLink, sec, nanosec),
            CreateRelativeTF("base_link", "lidar_sensor", lidarLink, sec, nanosec),
            CreateRelativeTF("base_link", "imu_link", imuLink, sec, nanosec),
            CreateRelativeTF("base_link", "left_wheel", leftWheel, sec, nanosec),
            CreateRelativeTF("base_link", "right_wheel", rightWheel, sec, nanosec)
        };

        TFMessageMsg tfMsg = new TFMessageMsg(transforms);
        ros.Publish(tfTopic, tfMsg);
    }

    TransformStampedMsg CreateWorldTF(string parent, string child, Transform tf, int sec, uint nanosec)
    {
        TransformStampedMsg msg = new TransformStampedMsg();
        msg.header = new HeaderMsg();
        
        msg.header.stamp.sec = sec;
        msg.header.stamp.nanosec = nanosec;
        
        msg.header.frame_id = parent;
        msg.child_frame_id = child;

        msg.transform.translation = tf.position.To<FLU>();
        msg.transform.rotation = tf.rotation.To<FLU>();

        return msg;
    }

    TransformStampedMsg CreateRelativeTF(string parent, string child, Transform tf, int sec, uint nanosec)
    {
        TransformStampedMsg msg = new TransformStampedMsg();
        msg.header = new HeaderMsg();
        
        msg.header.stamp.sec = sec;
        msg.header.stamp.nanosec = nanosec;
        
        msg.header.frame_id = parent;
        msg.child_frame_id = child;

        if (tf != null)
        {
            Vector3 relativePosition = baseLink.InverseTransformPoint(tf.position);
            Quaternion relativeRotation = Quaternion.Inverse(baseLink.rotation) * tf.rotation;

            msg.transform.translation = relativePosition.To<FLU>();
            msg.transform.rotation = relativeRotation.To<FLU>();
        }
        else
        {
            msg.transform.translation = new Vector3Msg();
            msg.transform.rotation = new QuaternionMsg(0, 0, 0, 1);
        }

        return msg;
    }
}
