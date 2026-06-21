using UnityEngine;

public class Lidar2D : MonoBehaviour
{
    [Header("LiDAR Settings")]
    public int numRays = 360;          // Number of rays in one scan
    public float horizontalFOV = 360f; // Horizontal field of view (degrees)
    public float minDistance = 0.1f;   // Minimum detectable distance
    public float maxDistance = 5f;    // Maximum detectable distance
    public LayerMask obstacleMask;     // Which layers LiDAR can hit

    [Header("Visualization")]
    public bool showRays = true;
    public Color hitColor = Color.red;
    public Color missColor = Color.green;

    // Array to store distances
    [HideInInspector]
    public float[] distances;

    void Start()
    {
        distances = new float[numRays];
    }

    void Update()
    {
        float angleStep = horizontalFOV / numRays;

        for (int i = 0; i < numRays; i++)
        {
            float angle = -horizontalFOV / 2 + i * angleStep;
            Vector3 direction = Quaternion.Euler(0, angle, 0) * transform.forward;

            if (Physics.Raycast(transform.position, direction, out RaycastHit hit, maxDistance, obstacleMask))
            {
                distances[i] = hit.distance;
                if (showRays) Debug.DrawLine(transform.position, hit.point, hitColor);
            }
            else
            {
                distances[i] = maxDistance;
                if (showRays) Debug.DrawRay(transform.position, direction * maxDistance, missColor);
            }
        }
    }
}

