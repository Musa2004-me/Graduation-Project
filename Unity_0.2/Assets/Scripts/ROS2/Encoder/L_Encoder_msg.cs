using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Std;

[RequireComponent(typeof(LeftEncoderLaser))]
public class LeftEncoderRosPublisher : MonoBehaviour
{
    public string topicName = "/encoder/left/pulse";

    private ROSConnection ros;
    private LeftEncoderLaser encoder;

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.RegisterPublisher<BoolMsg>(topicName);

        encoder = GetComponent<LeftEncoderLaser>();
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
