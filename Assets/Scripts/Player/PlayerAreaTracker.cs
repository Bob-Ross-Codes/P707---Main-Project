using UnityEngine;

[ExecuteAlways]
public class PlayerAreaTracker : MonoBehaviour
{
    [Header("References")]
    [Tooltip("The Kinect sensor transform (forward direction is Z+).")]
    [SerializeField] private Transform kinectTransform;

    [Tooltip("The BoxCollider attached to the tracked body/player.")]
    [SerializeField] private BoxCollider playerCollider;

    [Header("Area Configuration (Meters)")]
    [Tooltip("Distance (D) from the Kinect to the center of the tracked area along Kinect's forward Z axis.")]
    [Min(0f)]
    [SerializeField] private float centerDistanceD = 3f;

    [Tooltip("Total width of the area (X axis in meters).")]
    [Min(0.1f)]
    [SerializeField] private float areaWidthX = 4f;

    [Tooltip("Total depth of the area (Z axis in meters).")]
    [Min(0.1f)]
    [SerializeField] private float areaDepthZ = 3f;

    [Header("Display Settings")]
    [Tooltip("When checked: sliders show 0% to 100%. When unchecked: sliders show meters.")]
    [SerializeField] private bool showAsPercentage = true;

    [Header("Live Coordinates (Read Only)")]
    [Range(0f, 100f)]
    [SerializeField] private float relativeX_Percent;
    [Range(0f, 100f)]
    [SerializeField] private float relativeZ_Percent;

    [Space(5)]
    [SerializeField] private float relativeX_Meters;
    [SerializeField] private float relativeZ_Meters;

    [Header("Gizmo Settings")]
    [SerializeField] private Color areaGizmoColor = Color.green;
    [SerializeField] private Color playerGizmoColor = Color.red;

    public float RelativeXPercent => relativeX_Percent;
    public float RelativeZPercent => relativeZ_Percent;
    public float RelativeXMeters => relativeX_Meters;
    public float RelativeZMeters => relativeZ_Meters;
    public bool IsInsideArea { get; private set; }


    private void Update()
    {
        CalculateRelativeCoordinates();
    }

    private void CalculateRelativeCoordinates()
    {
        if (kinectTransform == null || playerCollider == null)
        {
            IsInsideArea = false;
            return;
        }

        Vector3 playerWorldPos = playerCollider.bounds.center;
        Vector3 localToKinect = kinectTransform.InverseTransformPoint(playerWorldPos);

        float minX = -areaWidthX * 0.5f;
        float maxX = areaWidthX * 0.5f;

        float minZ = centerDistanceD - (areaDepthZ * 0.5f);
        float maxZ = centerDistanceD + (areaDepthZ * 0.5f);

        // Check the actual position before clamping the coordinates.
        IsInsideArea =
            localToKinect.x >= minX &&
            localToKinect.x <= maxX &&
            localToKinect.z >= minZ &&
            localToKinect.z <= maxZ;

        // Keep the existing coordinate calculations.
        relativeX_Meters = Mathf.Clamp(localToKinect.x - minX, 0f, areaWidthX);
        relativeZ_Meters = Mathf.Clamp(localToKinect.z - minZ, 0f, areaDepthZ);

        relativeX_Percent =
            Mathf.Clamp01((localToKinect.x - minX) / areaWidthX) * 100f;

        relativeZ_Percent =
            Mathf.Clamp01((localToKinect.z - minZ) / areaDepthZ) * 100f;
    }

    private void OnDrawGizmos()
    {
        if (kinectTransform == null) return;

        // Calculate the center of the area in world space
        Vector3 localAreaCenter = new Vector3(0f, 0f, centerDistanceD);
        Vector3 worldAreaCenter = kinectTransform.TransformPoint(localAreaCenter);

        // Draw area outline aligned to the Kinect's orientation
        Matrix4x4 originalMatrix = Gizmos.matrix;
        Gizmos.matrix = Matrix4x4.TRS(worldAreaCenter, kinectTransform.rotation, Vector3.one);

        Gizmos.color = areaGizmoColor;
        Gizmos.DrawWireCube(Vector3.zero, new Vector3(areaWidthX, 0.05f, areaDepthZ));

        Gizmos.matrix = originalMatrix;

        // Draw line from Kinect to Area center (Distance D)
        Gizmos.color = Color.magenta;
        Gizmos.DrawLine(kinectTransform.position, worldAreaCenter);

        // Draw point and vertical pin on player collider center
        if (playerCollider != null)
        {
            Gizmos.color = playerGizmoColor;
            Vector3 playerCenter = playerCollider.bounds.center;
            Gizmos.DrawSphere(playerCenter, 0.15f);
            Gizmos.DrawLine(playerCenter, new Vector3(playerCenter.x, worldAreaCenter.y, playerCenter.z));
        }
    }
}