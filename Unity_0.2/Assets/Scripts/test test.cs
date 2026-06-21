using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Std;

public class ROSConnectionTest : MonoBehaviour
{
    ROSConnection ros;
    public string testTopic = "/unity_test";
    float timer = 0f;

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.RegisterPublisher<StringMsg>(testTopic);
        Debug.Log("✅ ROS Connection Started!");
    }

    void Update()
    {
        timer += Time.deltaTime;

        // بيبعت رسالة كل ثانية
        if (timer >= 1.0f)
        {
            timer = 0f;
            StringMsg msg = new StringMsg("Hello from Unity! Time: " + Time.time);
            ros.Publish(testTopic, msg);
            Debug.Log("📤 Message Sent: " + Time.time);
        }
    }
}
