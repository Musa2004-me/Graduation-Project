using UnityEngine;

public class LeftEncoderLaser : MonoBehaviour
{
    public Transform emitter;
    public Transform receiver;
    public LayerMask diskLayer;

    public event System.Action OnPulse;
    private bool wasBlocked = false;

    void Update()
    {
        Vector3 dir = (receiver.position - emitter.position).normalized;
        float dist = Vector3.Distance(emitter.position, receiver.position);
        bool isBlocked = Physics.Raycast(emitter.position, dir, dist, diskLayer);

        if (wasBlocked && !isBlocked)
        {
            OnPulse?.Invoke();
        }

        wasBlocked = isBlocked;
        Debug.DrawLine(emitter.position, receiver.position,
                       isBlocked ? Color.red : Color.green);
    }
}
