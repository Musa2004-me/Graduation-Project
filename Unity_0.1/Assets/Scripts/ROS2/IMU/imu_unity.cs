/*
using UnityEngine;

public class IMUSensor : MonoBehaviour
{
    private Rigidbody rb;

    public Quaternion Orientation { get; private set; }
    public Vector3 AngularVelocity { get; private set; }
    public Vector3 LinearAcceleration { get; private set; }

    private Vector3 lastVelocity = Vector3.zero;

    void Start()
    {
        rb = GetComponent<Rigidbody>();
    }

    void FixedUpdate()
    {
        // Orientation
        Orientation = transform.rotation;

        // Angular velocity (rad/s)
        AngularVelocity = rb.angularVelocity;

        // Linear acceleration (m/s²)
        LinearAcceleration = (rb.linearVelocity - lastVelocity) / Time.fixedDeltaTime;
        lastVelocity = rb.linearVelocity;
    }
}*/
using UnityEngine; 

public class IMUSensor : MonoBehaviour
{
    public ArticulationBody imuBody;
    [HideInInspector]
    public Vector3 linearAcceleration;
    [HideInInspector]
    public Vector3 angularVelocity;
    [HideInInspector]
    public Quaternion orientation;

    private Vector3 lastPosition;
    private Quaternion lastRotation;

    void Start()
    {
        if (imuBody == null)
            imuBody = GetComponent<ArticulationBody>();

        lastPosition = imuBody.transform.position;
        lastRotation = imuBody.transform.rotation;
    }

    void FixedUpdate()
    {
        // Orientation
        orientation = imuBody.transform.rotation;

        // Angular velocity (approx)
        Quaternion deltaRotation = imuBody.transform.rotation * Quaternion.Inverse(lastRotation);
        deltaRotation.ToAngleAxis(out float angle, out Vector3 axis);
        if (angle > 180f) angle -= 360f;
        angularVelocity = axis * angle * Mathf.Deg2Rad / Time.fixedDeltaTime;

        // Linear acceleration
        Vector3 velocity = (imuBody.transform.position - lastPosition) / Time.fixedDeltaTime;
        linearAcceleration = (velocity - ((lastPosition - imuBody.transform.position) / Time.fixedDeltaTime)) / Time.fixedDeltaTime;
        lastPosition = imuBody.transform.position;
        lastRotation = imuBody.transform.rotation;


    }
}
