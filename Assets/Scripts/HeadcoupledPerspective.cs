
using UnityEngine;

[ExecuteAlways]
[RequireComponent(typeof(Camera))]
public class HeadcoupledPerspective : MonoBehaviour
{
    [Header("References")]
    public Transform headPosition;
    public Transform virtualScreen;

    [Header("Physical Screen Size (meters)")]
    [Min(0.01f)] public float screenWidth = 0.60f;
    [Min(0.01f)] public float screenHeight = 0.34f;

    [Header("Projection")]
    public bool enableHeadCoupledPerspective = true;

    [Header("Debug Gizmos")]
    public bool showGizmos = true;
    public bool showGrid = true;
    public bool showFrustum = true;
    public bool showDirection = true;

    public Color screenColor = Color.green;
    public Color frustumColor = Color.red;

    private Camera cam;

    private void OnEnable()
    {
        cam = GetComponent<Camera>();
    }

    private void LateUpdate()
    {
        if (cam == null)
            cam = GetComponent<Camera>();

        if (!enableHeadCoupledPerspective ||
            headPosition == null ||
            virtualScreen == null)
        {
            cam.ResetProjectionMatrix();
            return;
        }

        UpdateProjection();
    }

    private void UpdateProjection()
    {
        Vector3 eye = headPosition.position;

        Vector3 screenRight = virtualScreen.right;
        Vector3 screenUp = virtualScreen.up;

        // +Z points INTO the virtual world.
        Vector3 screenForward = virtualScreen.forward;

        Vector3 center = virtualScreen.position;

        float halfW = screenWidth * 0.5f;
        float halfH = screenHeight * 0.5f;

        Vector3 bottomLeft =
            center - screenRight * halfW
                   - screenUp * halfH;

        Vector3 bottomRight =
            center + screenRight * halfW
                   - screenUp * halfH;

        Vector3 topLeft =
            center - screenRight * halfW
                   + screenUp * halfH;

        // Eye to screen corner vectors
        Vector3 va = bottomLeft - eye;
        Vector3 vb = bottomRight - eye;
        Vector3 vc = topLeft - eye;

        // Distance from eye to screen plane
        float distance = Vector3.Dot(
            center - eye,
            screenForward
        );

        // Eye must be on the viewing side
        if (distance <= 0.01f)
        {
            cam.ResetProjectionMatrix();
            return;
        }

        // Move camera to tracked head position
        transform.position = eye;

        // Camera local X/Y now match screen X/Y
        transform.rotation = Quaternion.LookRotation(
            screenForward,
            screenUp
        );

        float near = Mathf.Max(cam.nearClipPlane, 0.001f);
        float far = Mathf.Max(cam.farClipPlane, near + 0.01f);

        // Asymmetric frustum bounds
        float left = Vector3.Dot(
            screenRight, va
        ) * near / distance;

        float right = Vector3.Dot(
            screenRight, vb
        ) * near / distance;

        float bottom = Vector3.Dot(
            screenUp, va
        ) * near / distance;

        float top = Vector3.Dot(
            screenUp, vc
        ) * near / distance;

        cam.projectionMatrix = Matrix4x4.Frustum(
            left, right,
            bottom, top,
            near, far
        );
    }

    private void OnDisable()
    {
        if (cam == null)
            cam = GetComponent<Camera>();

        if (cam != null)
            cam.ResetProjectionMatrix();
    }

    private void OnDrawGizmos()
    {
        if (!showGizmos || virtualScreen == null)
            return;

        Vector3 center = virtualScreen.position;
        Vector3 sr = virtualScreen.right;
        Vector3 su = virtualScreen.up;
        Vector3 sf = virtualScreen.forward;

        float hw = screenWidth * 0.5f;
        float hh = screenHeight * 0.5f;

        Vector3 bl = center - sr * hw - su * hh;
        Vector3 br = center + sr * hw - su * hh;
        Vector3 tl = center - sr * hw + su * hh;
        Vector3 tr = center + sr * hw + su * hh;

        // Screen outline
        Gizmos.color = screenColor;
        Gizmos.DrawLine(bl, br);
        Gizmos.DrawLine(br, tr);
        Gizmos.DrawLine(tr, tl);
        Gizmos.DrawLine(tl, bl);

        // Corners
        float cornerSize = 0.012f;
        Gizmos.DrawSphere(bl, cornerSize);
        Gizmos.DrawSphere(br, cornerSize);
        Gizmos.DrawSphere(tl, cornerSize);
        Gizmos.DrawSphere(tr, cornerSize);

        // Grid
        if (showGrid)
        {
            Gizmos.color = new Color(
                1f, 0.9f, 0f, 0.65f
            );

            int divisions = 6;

            for (int i = 1; i < divisions; i++)
            {
                float t = i / (float)divisions;

                Gizmos.DrawLine(
                    Vector3.Lerp(bl, br, t),
                    Vector3.Lerp(tl, tr, t)
                );

                Gizmos.DrawLine(
                    Vector3.Lerp(bl, tl, t),
                    Vector3.Lerp(br, tr, t)
                );
            }
        }

        // Viewing direction
        if (showDirection)
        {
            Gizmos.color = Color.blue;
            Gizmos.DrawRay(center, sf * 0.4f);
        }

        // Actual screen frustum
        if (showFrustum && headPosition != null)
        {
            Vector3 eye = headPosition.position;

            Gizmos.color = Color.yellow;
            Gizmos.DrawWireSphere(eye, 0.025f);

            Gizmos.color = frustumColor;
            Gizmos.DrawLine(eye, bl);
            Gizmos.DrawLine(eye, br);
            Gizmos.DrawLine(eye, tl);
            Gizmos.DrawLine(eye, tr);
        }

#if UNITY_EDITOR
        UnityEditor.Handles.color = Color.white;
        UnityEditor.Handles.Label(
            center + su * (hh + 0.05f),
            $"SCREEN: {screenWidth * 100:F1} x " +
            $"{screenHeight * 100:F1} cm"
        );

        if (headPosition != null)
        {
            float signedDistance = Vector3.Dot(
                center - headPosition.position,
                sf
            );

            UnityEditor.Handles.Label(
                headPosition.position + Vector3.up * 0.08f,
                $"Eye distance: {signedDistance:F2} m"
            );
        }
#endif
    }
}
