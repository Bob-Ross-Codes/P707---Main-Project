using UnityEngine;
using UnityEngine.InputSystem;

[DefaultExecutionOrder(-100)]
public class PlayerModeController : MonoBehaviour
{
    public enum ControlMode
    {
        KinectTracking,
        ManualDebug
    }

    [Header("Mode Selection")]
    [SerializeField] private ControlMode currentMode = ControlMode.KinectTracking;

    [Header("Tracked Positions")]
    [Tooltip("Optional tracked player visual/root to move alongside the head while debugging.")]
    [SerializeField] private Transform playerTransform;

    [Tooltip("Tracked head output used by the projection camera. Its PlayerManager target is the live Kinect position.")]
    [SerializeField] private Transform cameraPosition;

    [Header("Movement Speeds (Meters per Second)")]
    [SerializeField] private float keyboardSpeed = 3f;
    [SerializeField] private float verticalSpeed = 2f;
    [SerializeField] private float mouseButtonSpeed = 3f;
    [Tooltip("Change in WASD speed per scroll notch, in meters per second.")]
    [SerializeField] private float scrollWheelSensitivity = 0.5f;

    [Header("WASD Movement Limits (Meters from live Kinect position)")]
    [Min(0f)] public float maxLeftMeters = 1f;
    [Min(0f)] public float maxRightMeters = 1f;
    [Tooltip("Maximum W movement along world +Z.")]
    [Min(0f)] public float maxUpMeters = 1f;
    [Tooltip("Maximum S movement along world -Z.")]
    [Min(0f)] public float maxDownMeters = 1f;

    [Header("Scene View Limits")]
    public bool showMovementLimits = true;
    public Color movementLimitColor = Color.cyan;

    [Header("Mode Indicator")]
    [SerializeField] private bool showModeIndicator = true;

    // Preserve references serialized by existing scenes. Debug mode leaves Kinect tracking enabled.
    [HideInInspector] [SerializeField] private MonoBehaviour[] kinectComponents;
    [HideInInspector] [SerializeField] private GameObject[] kinectGameObjects;

    private PlayerManager playerPositionManager;
    private PlayerManager cameraPositionManager;
    private Vector3 debugOffset;
    private Vector3 playerPositionWithoutTracking;
    private Vector3 cameraPositionWithoutTracking;

    private const float MinimumKeyboardSpeed = 0.05f;
    private const float MaximumKeyboardSpeed = 10f;

    private void Start()
    {
        playerPositionManager = playerTransform != null
            ? playerTransform.GetComponent<PlayerManager>()
            : null;
        cameraPositionManager = cameraPosition != null
            ? cameraPosition.GetComponent<PlayerManager>()
            : null;

        SaveUntrackedPositions();
    }

    private void Update()
    {
        Keyboard keyboard = Keyboard.current;
        if (keyboard == null || !keyboard.tabKey.wasPressedThisFrame)
            return;

        currentMode = currentMode == ControlMode.KinectTracking
            ? ControlMode.ManualDebug
            : ControlMode.KinectTracking;

        debugOffset = Vector3.zero;

        if (currentMode == ControlMode.ManualDebug)
        {
            SaveUntrackedPositions();
        }
        else
        {
            ApplyTrackedPositions();
            SaveUntrackedPositions();
        }
    }

    private void LateUpdate()
    {
        if (currentMode != ControlMode.ManualDebug)
            return;

        Keyboard keyboard = Keyboard.current;
        if (keyboard != null)
            debugOffset += ReadMovement(keyboard, Mouse.current);

        debugOffset = ClampDebugOffset(debugOffset);

        // Rebuild from the live Kinect targets each frame so tracking stays active under the offset.
        ApplyTrackedPositions();
    }

    private Vector3 ClampDebugOffset(Vector3 offset)
    {
        float leftLimit = Mathf.Max(0f, maxLeftMeters);
        float rightLimit = Mathf.Max(0f, maxRightMeters);
        float upLimit = Mathf.Max(0f, maxUpMeters);
        float downLimit = Mathf.Max(0f, maxDownMeters);

        return new Vector3(
            Mathf.Clamp(offset.x, -leftLimit, rightLimit),
            offset.y,
            Mathf.Clamp(offset.z, -downLimit, upLimit)
        );
    }

    private void SaveUntrackedPositions()
    {
        if (playerTransform != null)
            playerPositionWithoutTracking = playerTransform.position;

        if (cameraPosition != null)
            cameraPositionWithoutTracking = cameraPosition.position;
    }

    private void ApplyTrackedPositions()
    {
        ApplyOffset(playerTransform, playerPositionManager, playerPositionWithoutTracking);
        ApplyOffset(cameraPosition, cameraPositionManager, cameraPositionWithoutTracking);
    }

    private void ApplyOffset(Transform output, PlayerManager manager, Vector3 fallbackPosition)
    {
        if (output == null)
            return;

        Transform trackedTarget = manager != null ? manager.Target : null;
        Vector3 trackedPosition = trackedTarget != null && trackedTarget != output
            ? trackedTarget.position
            : fallbackPosition;

        output.position = trackedPosition + debugOffset;
    }

    private Vector3 ReadMovement(Keyboard keyboard, Mouse mouse)
    {
        float moveX = 0f;
        float moveY = 0f;
        float moveZ = 0f;

        if (keyboard.wKey.isPressed || keyboard.upArrowKey.isPressed) moveZ += 1f;
        if (keyboard.sKey.isPressed || keyboard.downArrowKey.isPressed) moveZ -= 1f;
        if (keyboard.aKey.isPressed || keyboard.leftArrowKey.isPressed) moveX -= 1f;
        if (keyboard.dKey.isPressed || keyboard.rightArrowKey.isPressed) moveX += 1f;
        if (keyboard.eKey.isPressed) moveY += 1f;
        if (keyboard.qKey.isPressed) moveY -= 1f;

        Vector3 planarInput = new Vector3(moveX, 0f, moveZ);
        if (planarInput.sqrMagnitude > 1f)
            planarInput.Normalize();

        float scrollY = mouse != null ? mouse.scroll.ReadValue().y : 0f;
        if (Mathf.Abs(scrollY) > 0.01f)
        {
            keyboardSpeed = Mathf.Clamp(
                keyboardSpeed + Mathf.Sign(scrollY) * scrollWheelSensitivity,
                MinimumKeyboardSpeed,
                MaximumKeyboardSpeed
            );
        }

        Vector3 movement = planarInput * (keyboardSpeed * Time.deltaTime);
        movement.y = moveY * (verticalSpeed * Time.deltaTime);

        if (mouse != null)
        {
            float mouseMoveX = 0f;
            if (mouse.leftButton.isPressed) mouseMoveX -= 1f;
            if (mouse.rightButton.isPressed) mouseMoveX += 1f;
            movement.x += mouseMoveX * (mouseButtonSpeed * Time.deltaTime);
        }

        return movement;
    }

    private void OnGUI()
    {
        if (!showModeIndicator || currentMode != ControlMode.ManualDebug)
            return;

        GUI.Box(
            new Rect(12f, 12f, 500f, 28f),
            $"DEBUG OFFSET  |  Kinect live  |  WASD {keyboardSpeed:0.00} m/s  |  scroll speed  |  TAB exit"
        );
    }

    private void OnDrawGizmos()
    {
        if (!showMovementLimits)
            return;

        Vector3 center = GetTrackedHeadPosition();
        float left = Mathf.Max(0f, maxLeftMeters);
        float right = Mathf.Max(0f, maxRightMeters);
        float up = Mathf.Max(0f, maxUpMeters);
        float down = Mathf.Max(0f, maxDownMeters);

        Vector3 lowerLeft = center + Vector3.left * left + Vector3.back * down;
        Vector3 lowerRight = center + Vector3.right * right + Vector3.back * down;
        Vector3 upperRight = center + Vector3.right * right + Vector3.forward * up;
        Vector3 upperLeft = center + Vector3.left * left + Vector3.forward * up;

        Gizmos.color = movementLimitColor;
        Gizmos.DrawLine(lowerLeft, lowerRight);
        Gizmos.DrawLine(lowerRight, upperRight);
        Gizmos.DrawLine(upperRight, upperLeft);
        Gizmos.DrawLine(upperLeft, lowerLeft);
        Gizmos.DrawWireSphere(center, 0.025f);

#if UNITY_EDITOR
        UnityEditor.Handles.color = movementLimitColor;
        UnityEditor.Handles.Label(
            upperLeft + Vector3.up * 0.05f,
            $"WASD limits (XZ)  L:{left:0.00}  R:{right:0.00}  U:{up:0.00}  D:{down:0.00} m"
        );
#endif
    }

    private Vector3 GetTrackedHeadPosition()
    {
        PlayerManager manager = cameraPositionManager;
        if (manager == null && cameraPosition != null)
            manager = cameraPosition.GetComponent<PlayerManager>();

        Transform trackedTarget = manager != null ? manager.Target : null;
        if (trackedTarget != null && trackedTarget != cameraPosition)
            return trackedTarget.position;

        return cameraPosition != null ? cameraPosition.position : transform.position;
    }
}
