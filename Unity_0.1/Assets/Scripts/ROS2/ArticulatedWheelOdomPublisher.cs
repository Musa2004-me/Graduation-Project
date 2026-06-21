using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Nav;
using RosMessageTypes.Geometry;
using RosMessageTypes.Tf2;
using RosMessageTypes.BuiltinInterfaces; 
using RosMessageTypes.Std;
using System.Collections.Generic;

public class ArticulatedWheelOdomPublisher : MonoBehaviour
{
    [Header("Robot Body & Wheels")]
    public Transform baseLink; // اسحب الـ base_link هنا
    public ArticulationBody leftWheelJoint; 
    public ArticulationBody rightWheelJoint;
    
    [Header("Sensors to Sync")]
    public Transform[] sensorTransforms; 

    [Header("Measurements")]
    public float wheelRadius = 0.18415f; 
    public float trackWidth = 0.405f;
    
    [Header("Frame IDs")]
    public string odomFrameId = "odom";
    public string baseFrameId = "base_link";

    private double x, y, theta; 
    private ROSConnection ros;

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.RegisterPublisher<OdometryMsg>("odom");
        ros.RegisterPublisher<TFMessageMsg>("/tf");
        
        x = 0; y = 0; theta = 0;
    }

    void FixedUpdate()
    {
        if (leftWheelJoint == null || rightWheelJoint == null || baseLink == null) return;

        float v_l = (float)leftWheelJoint.jointVelocity[0] * wheelRadius;
        float v_r = (float)rightWheelJoint.jointVelocity[0] * wheelRadius;

        float linearV = (v_r + v_l) / 2f;
        float angularV = (v_r - v_l) / trackWidth;

        float dt = Time.fixedDeltaTime;
        theta += angularV * dt;
        x += linearV * Mathf.Cos((float)theta) * dt;
        y += linearV * Mathf.Sin((float)theta) * dt;

        PublishAllData(linearV, angularV);
    }

    void PublishAllData(float linearV, float angularV)
    {
        uint sec = (uint)Time.time;
        uint nanosec = (uint)((Time.time - sec) * 1e9);
        TimeMsg rosTime = new TimeMsg { sec = (int)sec, nanosec = nanosec };

        Quaternion rotation = Quaternion.Euler(0, 0, (float)(theta * Mathf.Rad2Deg));
        QuaternionMsg quatMsg = new QuaternionMsg { 
            x = rotation.x, y = rotation.y, z = rotation.z, w = rotation.w 
        };

        List<TransformStampedMsg> tfList = new List<TransformStampedMsg>();

        // 1. TF: odom -> base_link (تعديل الارتفاع Z هنا)
        tfList.Add(new TransformStampedMsg {
            header = new HeaderMsg { stamp = rosTime, frame_id = odomFrameId },
            child_frame_id = baseFrameId,
            transform = new TransformMsg {
                translation = new Vector3Msg { 
                    x = (float)x, 
                    y = (float)y, 
                    z = baseLink.localPosition.y // بياخد ارتفاع العربية من يونيتي ويرفعه في RViz
                },
                rotation = quatMsg
            }
        });

        // 2. معالجة الحساسات (Lidar, Camera, IMU) بالنسبة للـ base_link
        foreach (Transform sensor in sensorTransforms)
        {
            if (sensor == null) continue;

            // حساب الموقع النسبي
            Vector3 relativePos = baseLink.InverseTransformPoint(sensor.position);
            Quaternion relativeRot = Quaternion.Inverse(baseLink.rotation) * sensor.rotation;

            tfList.Add(new TransformStampedMsg {
                header = new HeaderMsg { stamp = rosTime, frame_id = baseFrameId },
                child_frame_id = sensor.name, 
                transform = new TransformMsg {
                    translation = new Vector3Msg { 
                        x = relativePos.z, 
                        y = -relativePos.x, 
                        z = relativePos.y 
                    },
                    rotation = new QuaternionMsg { 
                        x = -relativeRot.z, 
                        y = relativeRot.x, 
                        z = -relativeRot.y, 
                        w = relativeRot.w 
                    }
                }
            });
        }

        // نشر الأودومتري
        OdometryMsg odom = new OdometryMsg {
            header = new HeaderMsg { stamp = rosTime, frame_id = odomFrameId },
            child_frame_id = baseFrameId,
            pose = new PoseWithCovarianceMsg {
                pose = new PoseMsg {
                    position = new PointMsg { x = x, y = y, z = baseLink.localPosition.y },
                    orientation = quatMsg
                }
            },
            twist = new TwistWithCovarianceMsg {
                twist = new TwistMsg {
                    linear = new Vector3Msg { x = linearV, y = 0, z = 0 },
                    angular = new Vector3Msg { x = 0, y = 0, z = angularV }
                }
            }
        };

        ros.Publish("odom", odom);
        ros.Publish("/tf", new TFMessageMsg { transforms = tfList.ToArray() });
    }
}
