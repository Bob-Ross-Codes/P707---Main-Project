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

    [ContextMenu("Snap to Target Now")]
    public void SnapToTarget()
    {
        if (target == null)
        {
            CheckAndFindTarget();
            if (target == null) return;
        }

        if (!useSmoothing)
        {
            transform.position = target.position;

            if (matchRotation)
                transform.rotation = target.rotation;

            return;
        }

        Vector3 currentPosition = transform.position;
        Vector3 targetPosition = target.position;

        float x = smoothX
            ? Mathf.Lerp(currentPosition.x, targetPosition.x, smoothSpeedX * Time.deltaTime)
            : targetPosition.x;

        float y = smoothY
            ? Mathf.Lerp(currentPosition.y, targetPosition.y, smoothSpeedY * Time.deltaTime)
            : targetPosition.y;

        float z = smoothZ
            ? Mathf.Lerp(currentPosition.z, targetPosition.z, smoothSpeedZ * Time.deltaTime)
            : targetPosition.z;

        transform.position = new Vector3(x, y, z);

        if (matchRotation)
        {
            if (smoothRotation)
            {
                transform.rotation = Quaternion.Slerp(
                    transform.rotation,
                    target.rotation,
                    rotationSmoothSpeed * Time.deltaTime
                );
            }
            else
            {
                transform.rotation = target.rotation;
            }
        }
    }
}