using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Sensor;

public class CameraPublisher : MonoBehaviour
{
    public CameraImageGenerator imageGenerator;
    public string topicName = "camera/image_raw";
    ROSConnection ros;

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.RegisterPublisher<ImageMsg>(topicName);
    }

    void Update()
    {
        Texture2D tex = imageGenerator.CaptureImage();
        byte[] imageBytes = tex.EncodeToJPG(); // or EncodeToPNG
        ImageMsg msg = new ImageMsg
        {
            height = (uint)tex.height,
            width = (uint)tex.width,
            encoding = "rgb8",
            step = (uint)(tex.width * 3),
            data = imageBytes
        };
        ros.Publish(topicName, msg);
    }
}

