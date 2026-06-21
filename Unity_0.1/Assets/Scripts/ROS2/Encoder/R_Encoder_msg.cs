using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Std;

[RequireComponent(typeof(RightEncoderLaser))]
public class RightEncoderRosPublisher : MonoBehaviour
{
    public string topicName = "/encoder/right/pulse";

    private ROSConnection ros;
    private RightEncoderLaser encoder;

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.RegisterPublisher<BoolMsg>(topicName);

        encoder = GetComponent<RightEncoderLaser>();
        encoder.OnPulse += HandlePulse;
    }

    void OnDestroy()
    {
        if (encoder != null)
            encoder.OnPulse -= HandlePulse;
    }

    private void HandlePulse()
    {
        ros.Publish(topicName, new BoolMsg { data = true });
    }
}
