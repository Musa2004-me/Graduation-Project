using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Geometry;

public class BagMotor : MonoBehaviour
{
    [SerializeField] private ArticulationBody bagBody;
    [SerializeField] private float forceLimit = 100f;

    private ROSConnection ros;
    private float currentVelocity = 0f;

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.Subscribe<TwistMsg>("/bag_vel", OnVelocityReceived);
    }

    private void OnVelocityReceived(TwistMsg msg)
    {
        currentVelocity = (float)msg.angular.x;
    }

    void FixedUpdate()
    {
        if (bagBody == null) return;

        ArticulationDrive drive = bagBody.xDrive;
        drive.targetVelocity = currentVelocity * Mathf.Rad2Deg;
        drive.forceLimit = forceLimit;
        bagBody.xDrive = drive;
    }
}
