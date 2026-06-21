using UnityEngine;

public class CameraImageGenerator : MonoBehaviour
{
    public Camera sensorCamera;
    public RenderTexture renderTexture;

    void Start()
    {
        if(sensorCamera == null)
            sensorCamera = GetComponent<Camera>();

        if(renderTexture == null)
        {
            renderTexture = new RenderTexture(640, 480, 24);
            sensorCamera.targetTexture = renderTexture;
        }
    }

    public Texture2D CaptureImage()
    {
        Texture2D tex = new Texture2D(renderTexture.width, renderTexture.height, TextureFormat.RGB24, false);
        RenderTexture.active = renderTexture;
        tex.ReadPixels(new Rect(0, 0, renderTexture.width, renderTexture.height), 0, 0);
        tex.Apply();
        RenderTexture.active = null;
        return tex;
    }
}

