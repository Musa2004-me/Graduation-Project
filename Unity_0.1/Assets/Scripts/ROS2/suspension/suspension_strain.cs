using UnityEngine;
#if UNITY_EDITOR
using UnityEditor;
#endif

// This attribute ensures the script runs in the Editor (Edit Mode) 
// as well as in Play Mode, allowing for real-time visualization 
// during scene setup and editing.
[ExecuteAlways]
public class LineDistanceDisplay : MonoBehaviour
{
    // --- Public Fields ---

    [Header("Articulation Bodies")]
    [Tooltip("The first Articulation Body (e.g., High Arm).")]
    public ArticulationBody bodyA;

    [Tooltip("The second Articulation Body (e.g., Low Arm).")]
    public ArticulationBody bodyB;

    [Header("Local points on bodies")]
    [Tooltip("The point's local offset from bodyA's transform.")]
    public Vector3 localPointA = Vector3.zero;

    [Tooltip("The point's local offset from bodyB's transform.")]
    public Vector3 localPointB = Vector3.zero;

    [Header("Distance info (read-only)")]
    [Tooltip("The calculated distance between the two points in world space.")]
    public float currentDistance;


    // --- Core Logic ---

    void Update()
    {
        // Safety check: ensure both bodies are assigned before proceeding.
        if (!bodyA || !bodyB) return;

        // 1. Convert local points to world space coordinates
        Vector3 posA = bodyA.transform.TransformPoint(localPointA);
        Vector3 posB = bodyB.transform.TransformPoint(localPointB);

        // 2. Calculate the distance between the two world points
        currentDistance = Vector3.Distance(posB, posA);
    }


    // --- Visualization (Gizmos) ---

    // This method is called by Unity to draw visualization helpers in the Scene view.
    void OnDrawGizmos()
    {
        // Safety check for visualization, same as Update().
        if (!bodyA || !bodyB) return;

        // Recalculate world positions for Gizmos drawing (Update may not run constantly in Edit Mode)
        Vector3 posA = bodyA.transform.TransformPoint(localPointA);
        Vector3 posB = bodyB.transform.TransformPoint(localPointB);

        // Draw a line between the two points
        Gizmos.color = Color.cyan;
        Gizmos.DrawLine(posA, posB);

        // Display the distance as a text label in the Scene view (Editor only)
        #if UNITY_EDITOR
        
        // Ensure distance is calculated before trying to draw the label
        // (This handles cases where Update might not have run immediately)
        if (Application.isPlaying == false)
        {
             currentDistance = Vector3.Distance(posB, posA);
        }

        Handles.color = Color.white;
        // Place the label at the midpoint for better visibility
        Handles.Label((posA + posB) / 2, $"Distance: {currentDistance:F3} m");
        #endif
    }
}
