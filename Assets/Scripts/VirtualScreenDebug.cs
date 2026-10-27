
using UnityEngine;

[ExecuteAlways]
public class VirtualScreenDebug : MonoBehaviour
{
    [Header("References")]
    public Transform virtualScreen;
    public Transform headPosition;

    [Header("Screen Size (meters)")]
    public float screenWidth = 0.60f;
    public float screenHeight = 0.34f;

    [Header("Debug Settings")]
    public bool showScreen = true;
    public bool showGrid = true;
    public bool showFrustum = true;
    public bool showHead = true;
    public bool showDimensions = true;
    public bool showScreenNormal = true;

    [Range(1, 20)]
    public int gridDivisions = 6;

    [Header("Colors")]
    public Color screenColor = Color.green;
    public Color gridColor = Color.yellow;
    public Color frustumColor = Color.red;

    [Range(0f, 1f)]
    public float screenOpacity = 0.12f;

    private void OnDrawGizmos()
    {
        if (virtualScreen == null)
            return;

        Vector3 center = virtualScreen.position;
        Vector3 right = virtualScreen.right;
        Vector3 up = virtualScreen.up;

        float halfWidth = screenWidth * 0.5f;
        float halfHeight = screenHeight * 0.5f;

        Vector3 BL = center - right * halfWidth - up * halfHeight;
        Vector3 BR = center + right * halfWidth - up * halfHeight;
        Vector3 TL = center - right * halfWidth + up * halfHeight;
        Vector3 TR = center + right * halfWidth + up * halfHeight;

        // 1. Screen area and outer frame
        if (showScreen)
        {
            Gizmos.color = new Color(
                screenColor.r,
                screenColor.g,
                screenColor.b,
                screenOpacity
            );

            Gizmos.DrawCube(
                center,
                Vector3.zero
            );

            DrawTransparentScreen(BL, BR, TL, TR);

            Gizmos.color = screenColor;
            Gizmos.DrawLine(BL, BR);
            Gizmos.DrawLine(BR, TR);
            Gizmos.DrawLine(TR, TL);
            Gizmos.DrawLine(TL, BL);

            // Corner markers
            float markerSize = 0.012f;

            Gizmos.DrawSphere(BL, markerSize);
            Gizmos.DrawSphere(BR, markerSize);
            Gizmos.DrawSphere(TL, markerSize);
            Gizmos.DrawSphere(TR, markerSize);
        }

        // 2. Screen grid
        if (showGrid)
        {
            Gizmos.color = gridColor;

            for (int i = 1; i < gridDivisions; i++)
            {
                float t = i / (float)gridDivisions;

                Vector3 verticalBottom = Vector3.Lerp(BL, BR, t);
                Vector3 verticalTop = Vector3.Lerp(TL, TR, t);

                Gizmos.DrawLine(verticalBottom, verticalTop);

                Vector3 horizontalLeft = Vector3.Lerp(BL, TL, t);
                Vector3 horizontalRight = Vector3.Lerp(BR, TR, t);

                Gizmos.DrawLine(horizontalLeft, horizontalRight);
            }
        }

        // 3. Eye-to-screen frustum
        if (showFrustum && headPosition != null)
        {
            Gizmos.color = frustumColor;

            Vector3 eye = headPosition.position;

            Gizmos.DrawLine(eye, BL);
            Gizmos.DrawLine(eye, BR);
            Gizmos.DrawLine(eye, TL);
            Gizmos.DrawLine(eye, TR);
        }

        // 4. Head position
        if (showHead && headPosition != null)
        {
            Gizmos.color = Color.yellow;
            Gizmos.DrawWireSphere(
                headPosition.position,
                0.035f
            );
        }

        // 5. Screen normal
        if (showScreenNormal)
        {
            Gizmos.color = Color.cyan;
            Gizmos.DrawLine(
                center,
                center + virtualScreen.forward * 0.25f
            );
        }

#if UNITY_EDITOR
        if (showDimensions)
        {
            UnityEditor.Handles.color = Color.white;

            UnityEditor.Handles.Label(
                center + up * (halfHeight + 0.06f),
                $"SCREEN: {screenWidth * 100:F1} x {screenHeight * 100:F1} cm"
            );

            UnityEditor.Handles.Label(
                center + right * (halfWidth + 0.05f),
                $"{screenHeight * 100:F1} cm"
            );

            UnityEditor.Handles.Label(
                center - up * (halfHeight + 0.05f),
                $"{screenWidth * 100:F1} cm"
            );
        }
#endif
    }

    private void DrawTransparentScreen(
        Vector3 BL,
        Vector3 BR,
        Vector3 TL,
        Vector3 TR)
    {
#if UNITY_EDITOR
        UnityEditor.Handles.color = new Color(
            0.1f, 0.5f, 1f, screenOpacity
        );

        UnityEditor.Handles.DrawAAConvexPolygon(
            BL, TL, TR, BR
        );
#endif
    }
}
