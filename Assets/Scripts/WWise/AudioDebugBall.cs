
using UnityEngine;
using UnityEditor;

[ExecuteAlways]
public class AudioDebugBall : MonoBehaviour
{
    [Header("Debug Appearance")]
    public float ballRadius = 0.25f;
    public Color ballColor = Color.cyan;

    [Header("Listener")]
    public Transform listener;
    public float maxDistance = 30f;

    [Header("Illustrative dB Range")]
    public float maxDb = 0f;
    public float minDb = -60f;

    private void OnDrawGizmos()
    {
        // Solid ball at the actual sound source position
        Gizmos.color = ballColor;
        Gizmos.DrawSphere(transform.position, ballRadius);

        // White outline
        Gizmos.color = Color.white;
        Gizmos.DrawWireSphere(transform.position, ballRadius);

        // Find listener if not assigned
        Transform activeListener = listener;

        if (activeListener == null && Camera.main != null)
            activeListener = Camera.main.transform;

        if (activeListener == null)
            return;

        float distance = Vector3.Distance(
            transform.position,
            activeListener.position
        );

        float normalizedDistance = Mathf.Clamp01(distance / maxDistance);

        float estimatedDb = Mathf.Lerp(
            maxDb,
            minDb,
            normalizedDistance
        );

        // Connection to listener
        Gizmos.color = Color.yellow;
        Gizmos.DrawLine(transform.position, activeListener.position);

        #if UNITY_EDITOR
        GUIStyle style = new GUIStyle();
        style.normal.textColor = ballColor;
        style.fontSize = 13;
        style.fontStyle = FontStyle.Bold;

        Handles.Label(
            transform.position + Vector3.up * (ballRadius + 0.2f),
            $"{gameObject.name}\n{estimatedDb:F1} dB\n{distance:F1} m",
            style
        );
        #endif
    }
}
