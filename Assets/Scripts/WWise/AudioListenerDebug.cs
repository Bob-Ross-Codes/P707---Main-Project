
using UnityEngine;

#if UNITY_EDITOR
using UnityEditor;
#endif

[ExecuteAlways]
public class AudioListenerDebug : MonoBehaviour
{
    [Header("Debug Display")]
    public bool showDebug = true;
    public string listenerLabel = "AUDIO LISTENER";
    public Color iconColor = Color.cyan;
    public float labelHeight = 0.5f;
    public float iconSize = 0.15f;

#if UNITY_EDITOR
    private void OnDrawGizmos()
    {
        if (!showDebug) return;

        Vector3 position = transform.position;

        // Draw listener position
        Gizmos.color = iconColor;
        Gizmos.DrawWireSphere(position, iconSize);

        // Draw direction indicator
        Gizmos.DrawLine(
            position,
            position + transform.forward * 0.4f
        );

        // Draw Scene View label
        Handles.color = iconColor;

        GUIStyle style = new GUIStyle();
        style.fontSize = 13;
        style.fontStyle = FontStyle.Bold;
        style.normal.textColor = iconColor;
        style.alignment = TextAnchor.MiddleCenter;

        Handles.Label(
            position + Vector3.up * labelHeight,
            "((  " + listenerLabel + "  ))",
            style
        );
    }
#endif
}
