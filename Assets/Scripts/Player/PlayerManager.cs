using UnityEngine;

public class PlayerManager : MonoBehaviour
{
    [Header("Target Settings")]
    [Tooltip("The GameObject whose global position/rotation to match.")]
    [SerializeField] private Transform target;

    [Header("Auto-Find Settings")]
    [Tooltip("Name of the bone to look for automatically if target is unassigned (e.g., 'pelvis' or 'head').")]
    [SerializeField] private string autoFindBoneName = "";

    public Transform Target => target;

    [Header("Options")]
    [SerializeField] private bool matchRotation = true;
    [SerializeField] private bool updateEveryFrame = false;

    [Header("Position Smoothing")]
    public bool useSmoothing = true;

    public bool smoothX = true;
    public bool smoothY = true;
    public bool smoothZ = true;

    [Min(0.01f)] public float smoothSpeedX = 5f;
    [Min(0.01f)] public float smoothSpeedY = 5f;
    [Min(0.01f)] public float smoothSpeedZ = 5f;

    [Header("Distance-Based Smoothing (Kinect)")]
    [Tooltip("If enabled, applies heavier smoothing the further the target is from the Kinect.")]
    public bool scaleSmoothingByDistance = true;

    [Tooltip("Transform representing the Kinect sensor's position. Defaults to world origin (0,0,0) if unassigned.")]
    [SerializeField] private Transform kinectOrigin;

    [Tooltip("Distance from the Kinect (in meters) where nearSmoothingFactor begins.")]
    [Min(0f)] public float minDistance = 1.0f;

    [Tooltip("Distance from the Kinect (in meters) where farSmoothingFactor is reached.")]
    [Min(0.01f)] public float maxDistance = 5.0f;

    [Tooltip("Speed multiplier near the Kinect (1 = full base speed / lighter smoothing).")]
    [Range(0.01f, 3f)] public float nearSmoothingFactor = 1.0f;

    [Tooltip("Speed multiplier far from the Kinect (lower values = heavier smoothing).")]
    [Range(0.01f, 3f)] public float farSmoothingFactor = 0.25f;

    [Tooltip("Also scale rotation smoothing speed by distance from the Kinect.")]
    public bool scaleRotationWithDistance = true;

    [Header("Rotation Smoothing")]
    public bool smoothRotation = true;
    [Min(0.01f)] public float rotationSmoothSpeed = 5f;

    private void Awake()
    {
        CheckAndFindTarget();
    }

    private void OnEnable()
    {
        // Re-check when the scene finishes loading or object is enabled
        CheckAndFindTarget();
    }

    private void Start()
    {
        SnapToTarget();
    }

    private void Update()
    {
        if (target == null)
        {
            CheckAndFindTarget();
        }

        if (updateEveryFrame)
        {
            SnapToTarget();
        }
    }

    private void CheckAndFindTarget()
    {
        if (target != null) return;

        if (!string.IsNullOrEmpty(autoFindBoneName))
        {
            // Search all transforms in the scene for one matching the bone name
            Transform[] allTransforms = FindObjectsByType<Transform>(FindObjectsSortMode.None);
            foreach (Transform t in allTransforms)
            {
                if (t.name.Equals(autoFindBoneName, System.StringComparison.OrdinalIgnoreCase))
                {
                    target = t;
                    Debug.Log($"[{gameObject.name}] Automatically re-linked target to bone: {t.name}");
                    break;
                }
            }
        }
    }

    private float GetDistanceSmoothingMultiplier(Vector3 targetPosition)
    {
        if (!scaleSmoothingByDistance)
            return 1f;

        Vector3 kinectPos = kinectOrigin != null ? kinectOrigin.position : Vector3.zero;
        float distance = Vector3.Distance(targetPosition, kinectPos);

        float denom = Mathf.Max(0.01f, maxDistance - minDistance);
        float t = Mathf.Clamp01((distance - minDistance) / denom);

        // Smoothstep gives a natural ease between near and far ranges
        float easedT = Mathf.SmoothStep(0f, 1f, t);
        return Mathf.Lerp(nearSmoothingFactor, farSmoothingFactor, easedT);
    }

    private static float DampFactor(float speed, float deltaTime)
    {
        // Frame-rate independent exponential smoothing (avoids overshoot if speed * dt > 1)
        return 1f - Mathf.Exp(-Mathf.Max(0f, speed) * deltaTime);
    }

    [ContextMenu("Snap to Target Now")]
    public void SnapToTarget()
    {
        if (target == null)
        {
            CheckAndFindTarget();
            if (target == null) return;
        }

        Vector3 currentPosition = transform.position;
        Vector3 targetPosition = target.position;

        if (!useSmoothing)
        {
            transform.position = targetPosition;

            if (matchRotation)
                transform.rotation = target.rotation;

            return;
        }

        float distanceMultiplier = GetDistanceSmoothingMultiplier(targetPosition);

        float x = smoothX
            ? Mathf.Lerp(currentPosition.x, targetPosition.x, DampFactor(smoothSpeedX * distanceMultiplier, Time.deltaTime))
            : targetPosition.x;

        float y = smoothY
            ? Mathf.Lerp(currentPosition.y, targetPosition.y, DampFactor(smoothSpeedY * distanceMultiplier, Time.deltaTime))
            : targetPosition.y;

        float z = smoothZ
            ? Mathf.Lerp(currentPosition.z, targetPosition.z, DampFactor(smoothSpeedZ * distanceMultiplier, Time.deltaTime))
            : targetPosition.z;

        transform.position = new Vector3(x, y, z);

        if (matchRotation)
        {
            if (smoothRotation)
            {
                float rotMultiplier = scaleRotationWithDistance ? distanceMultiplier : 1f;
                transform.rotation = Quaternion.Slerp(
                    transform.rotation,
                    target.rotation,
                    DampFactor(rotationSmoothSpeed * rotMultiplier, Time.deltaTime)
                );
            }
            else
            {
                transform.rotation = target.rotation;
            }
        }
    }
}