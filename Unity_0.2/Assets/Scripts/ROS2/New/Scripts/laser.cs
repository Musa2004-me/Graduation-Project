using System;
using System.Collections.Generic;
using RosMessageTypes.Sensor;
using RosMessageTypes.Std;
using RosMessageTypes.BuiltinInterfaces;
using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using UnityEngine.Serialization;

public class LaserScanSensor : MonoBehaviour
{
    [Header("ROS")]
    public string topic = "/scan";
    public string FrameId = "lidar_sensor";

    [Header("Scan Settings")]
    public double PublishPeriodSeconds = 0.1;
    public float RangeMetersMin = 0.1f;
    public float RangeMetersMax = 12f;

    public float ScanAngleStartDegrees = -180f;
    public float ScanAngleEndDegrees = 180f;

    public float ScanOffsetAfterPublish = 0f;

    public int NumMeasurementsPerScan = 360;

    public float TimeBetweenMeasurementsSeconds = 0f;

    public string LayerMaskName = "Default";

    [Header("Visualization (like old Lidar2D)")]
    public bool showRays = true;
    public Color hitColor = Color.red;
    public Color missColor = Color.green;

    float m_CurrentScanAngleStart;
    float m_CurrentScanAngleEnd;

    ROSConnection m_Ros;

    double m_TimeNextScanSeconds = -1;
    double m_TimeLastScanBeganSeconds = -1;

    int m_NumMeasurementsTaken;
    int m_LayerMask;

    bool isScanning = false;

    readonly List<float> ranges = new List<float>();

    void Start()
    {
        m_Ros = ROSConnection.GetOrCreateInstance();
        m_Ros.RegisterPublisher<LaserScanMsg>(topic);

        m_CurrentScanAngleStart = ScanAngleStartDegrees;
        m_CurrentScanAngleEnd = ScanAngleEndDegrees;

        m_TimeNextScanSeconds = Time.timeAsDouble + PublishPeriodSeconds;

        m_LayerMask = LayerMask.GetMask(LayerMaskName);
    }

    void BeginScan()
    {
        isScanning = true;

        m_TimeLastScanBeganSeconds = Time.timeAsDouble;
        m_TimeNextScanSeconds = m_TimeLastScanBeganSeconds + PublishPeriodSeconds;

        m_NumMeasurementsTaken = 0;
        ranges.Clear();
    }

    void EndScan()
    {
        double simTime = Time.timeAsDouble;

        var stamp = new TimeMsg
        {
            sec = (int)simTime,
            nanosec = (uint)((simTime - (int)simTime) * 1e9)
        };

        float angleStartRos = -m_CurrentScanAngleStart * Mathf.Deg2Rad;
        float angleEndRos = -m_CurrentScanAngleEnd * Mathf.Deg2Rad;

        if (angleStartRos > angleEndRos)
        {
            float tmp = angleStartRos;
            angleStartRos = angleEndRos;
            angleEndRos = tmp;

            ranges.Reverse();
        }

        LaserScanMsg msg = new LaserScanMsg
        {
            header = new HeaderMsg
            {
                frame_id = FrameId,
                stamp = stamp
            },

            angle_min = angleStartRos,
            angle_max = angleEndRos,

            angle_increment =
                (angleEndRos - angleStartRos) /
                (NumMeasurementsPerScan - 1),

            time_increment = 0f,
            scan_time = (float)PublishPeriodSeconds,

            range_min = RangeMetersMin,
            range_max = RangeMetersMax,

            ranges = ranges.ToArray(),
            intensities = new float[ranges.Count]
        };

        m_Ros.Publish(topic, msg);

        isScanning = false;

        m_CurrentScanAngleStart += ScanOffsetAfterPublish;
        m_CurrentScanAngleEnd += ScanOffsetAfterPublish;
    }

    void Update()
    {
        if (!isScanning)
        {
            if (Time.timeAsDouble < m_TimeNextScanSeconds)
                return;

            BeginScan();
        }

        int measurementsSoFar =
            TimeBetweenMeasurementsSeconds <= 0f
            ? NumMeasurementsPerScan
            : Mathf.Min(
                NumMeasurementsPerScan,
                1 + Mathf.FloorToInt(
                    (float)(Time.timeAsDouble - m_TimeLastScanBeganSeconds)
                    / TimeBetweenMeasurementsSeconds));

        float yawBaseDegrees = transform.rotation.eulerAngles.y;

        while (m_NumMeasurementsTaken < measurementsSoFar)
        {
            float t = m_NumMeasurementsTaken / (float)(NumMeasurementsPerScan - 1);

            float yawSensorDegrees =
                Mathf.Lerp(
                    m_CurrentScanAngleStart,
                    m_CurrentScanAngleEnd,
                    t);

            float yawDegrees = yawBaseDegrees + yawSensorDegrees;

            Vector3 direction =
                Quaternion.Euler(0f, yawDegrees, 0f) *
                Vector3.forward;

            Vector3 rayStart =
                transform.position +
                direction * RangeMetersMin;

            Ray ray = new Ray(rayStart, direction);

            if (Physics.Raycast(ray, out RaycastHit hit, RangeMetersMax, m_LayerMask))
                ranges.Add(hit.distance);
            else
                ranges.Add(RangeMetersMax);

            m_NumMeasurementsTaken++;
        }

        if (m_NumMeasurementsTaken >= NumMeasurementsPerScan)
            EndScan();
    }

    // =========================
    // VISUALIZATION (LIKE OLD LIDAR2D)
    // =========================
    void LateUpdate()
    {
        if (!showRays)
            return;

        float yawBaseDegrees = transform.rotation.eulerAngles.y;

        for (int i = 0; i < NumMeasurementsPerScan; i++)
        {
            float t = i / (float)(NumMeasurementsPerScan - 1);

            float yawSensorDegrees =
                Mathf.Lerp(
                    m_CurrentScanAngleStart,
                    m_CurrentScanAngleEnd,
                    t);

            float yawDegrees = yawBaseDegrees + yawSensorDegrees;

            Vector3 direction =
                Quaternion.Euler(0f, yawDegrees, 0f) *
                Vector3.forward;

            Vector3 rayStart =
                transform.position +
                direction * RangeMetersMin;

            if (Physics.Raycast(rayStart, direction, out RaycastHit hit, RangeMetersMax, m_LayerMask))
            {
                Debug.DrawLine(rayStart, hit.point, hitColor);
            }
            else
            {
                Debug.DrawRay(rayStart, direction * RangeMetersMax, missColor);
            }
        }
    }
}
