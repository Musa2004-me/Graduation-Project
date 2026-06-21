using UnityEngine;
using UnityEngine.UI;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;

public class MessageReceiver : MonoBehaviour
{
    [Header("UI")]
    public Text messageText;       // assign a UI Text in Inspector
    public ScrollRect scrollRect;  // optional scroll view

    private TcpListener listener;
    private Thread listenerThread;
    private string pendingMessage = null;
    private readonly object msgLock = new object();

    void Start()
    {
        listenerThread = new Thread(Listen) { IsBackground = true };
        listenerThread.Start();
        Debug.Log("Unity Subscriber listening on port 9001...");
    }

    void Listen()
    {
        listener = new TcpListener(IPAddress.Any, 9001);
        listener.Start();
        while (true)
        {
            using var client = listener.AcceptTcpClient();
            var buf = new byte[4096];
            int n = client.GetStream().Read(buf, 0, buf.Length);
            string msg = Encoding.UTF8.GetString(buf, 0, n).Trim();
            lock (msgLock) { pendingMessage = msg; }
        }
    }

    void Update()
    {
        string msg;
        lock (msgLock)
        {
            if (pendingMessage == null) return;
            msg = pendingMessage;
            pendingMessage = null;
        }
        Debug.Log("[Subscriber] " + msg);
        if (messageText) messageText.text += "\n" + msg;
    }

    void OnDestroy() => listener?.Stop();
}
