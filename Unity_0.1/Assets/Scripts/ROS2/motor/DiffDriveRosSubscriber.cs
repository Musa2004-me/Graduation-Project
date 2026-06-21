using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Std;

public class DiffDriveRosArticulation : MonoBehaviour
{
    ROSConnection ros;

    [Header("ROS Topic")]
    public string wheelOmegaTopic = "/wheel_omega";

    [Header("Robot Wheels (ArticulationBody)")]
    public ArticulationBody leftWheel;
    public ArticulationBody rightWheel;

    [Header("Drive Parameters")]
    public float forceLimit = 5000f;
    public float damping = 1f;
    public float stiffness = 0f;
    public float rosTimeout = 1.0f; // seconds

    private float lastCmdTime = 0f;
    private double leftOmega = 0.0;
    private double rightOmega = 0.0;

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.Subscribe<Float64MultiArrayMsg>(wheelOmegaTopic, WheelOmegaCallback);

        SetupWheel(leftWheel);
        SetupWheel(rightWheel);
    }

    void WheelOmegaCallback(Float64MultiArrayMsg msg)
    {
        if (msg.data.Length < 2) return;
        leftOmega = msg.data[0];
        rightOmega = msg.data[1];
        lastCmdTime = Time.time;
    }

    void FixedUpdate()
    {
        if (Time.time - lastCmdTime > rosTimeout)
        {
            leftOmega = 0.0;
            rightOmega = 0.0;
        }

        // rad/s → deg/s
        float leftDeg = (float)(leftOmega * Mathf.Rad2Deg);
        float rightDeg = (float)(rightOmega * Mathf.Rad2Deg);

        ApplyVelocity(leftWheel, leftDeg);
        ApplyVelocity(rightWheel, rightDeg);
    }

    void SetupWheel(ArticulationBody wheel)
    {
        var drive = wheel.xDrive;
        drive.forceLimit = forceLimit;  // مهم: لازم كبير
        drive.stiffness = stiffness;
        drive.damping = damping;
        drive.targetVelocity = 0f;
        drive.lowerLimit = 0f;
        drive.upperLimit = 0f;
        wheel.xDrive = drive;

        // تأكد في Inspector:
        // Joint Type = RevoluteJoint
        // X Motion = Free
    }

    void ApplyVelocity(ArticulationBody wheel, float targetVelocity)
    {
        var drive = wheel.xDrive;
        drive.targetVelocity = targetVelocity;
        wheel.xDrive = drive;
    }
}

