using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;

public class PlayerModeController : MonoBehaviour
{
    public enum ControlMode
    {
        KinectTracking,
        ManualDebug
    }

    [Header("Mode Selection")]
    [SerializeField] private ControlMode currentMode = ControlMode.KinectTracking;

    [Header("Target To Move")]
    [Tooltip("The GameObject or Player Transform that contains the colliders to move in debug mode.")]
    [SerializeField] private Transform playerTransform;
    [SerializeField] private Transform cameraPosition;

    [Header("Movement Speeds (Meters per Second)")]
    [SerializeField] private float keyboardSpeed = 3f;
    [SerializeField] private float verticalSpeed = 2f;
    [SerializeField] private float mouseButtonSpeed = 3f;
    [Tooltip("Sensitivity for scroll wheel Z movement.")]
    [SerializeField] private float scrollWheelSensitivity = 0.5f;

    [Header("Kinect Components To Toggle")]
    [Tooltip("Drag any Kinect-related scripts/components here to disable them during manual control.")]
    [SerializeField] private List<MonoBehaviour> kinectComponents = new List<MonoBehaviour>();

    [Tooltip("Optional: Entire Kinect GameObjects to deactivate completely when in manual mode.")]
    [SerializeField] private List<GameObject> kinectGameObjects = new List<GameObject>();

    private void Start()
    {
        ApplyMode(currentMode);
    }

    private void Update()
    {
        Keyboard keyboard = Keyboard.current;
        Mouse mouse = Mouse.current;

        if (keyboard == null) return;

        // 1. Toggle Mode with Tab key
        if (keyboard.tabKey.wasPressedThisFrame)
        {
            currentMode = (currentMode == ControlMode.KinectTracking)
                ? ControlMode.ManualDebug
                : ControlMode.KinectTracking;

            ApplyMode(currentMode);
        }

        // 2. Only process manual inputs when in Manual Debug Mode
        if (currentMode == ControlMode.ManualDebug)
        {
            HandleManualMovement(keyboard, mouse);
        }
    }

    private void OnValidate()
    {
        if (Application.isPlaying)
        {
            ApplyMode(currentMode);
        }
    }

    private void ApplyMode(ControlMode mode)
    {
        bool enableKinect = (mode == ControlMode.KinectTracking);

        foreach (var comp in kinectComponents)
        {
            if (comp != null)
            {
                comp.enabled = enableKinect;
            }
        }

        foreach (var go in kinectGameObjects)
        {
            if (go != null)
            {
                go.SetActive(enableKinect);
            }
        }
    }

    private void HandleManualMovement(Keyboard keyboard, Mouse mouse)
    {
        if (playerTransform == null) return;

        float moveX = 0f;
        float moveY = 0f;
        float moveZ = 0f;

        // Keyboard Controls: WASD & Arrow Keys (Horizontal Plane)
        if (keyboard.wKey.isPressed || keyboard.upArrowKey.isPressed) moveZ += 1f;
        if (keyboard.sKey.isPressed || keyboard.downArrowKey.isPressed) moveZ -= 1f;
        if (keyboard.aKey.isPressed || keyboard.leftArrowKey.isPressed) moveX -= 1f;
        if (keyboard.dKey.isPressed || keyboard.rightArrowKey.isPressed) moveX += 1f;

        // Vertical Controls: Q (Down) / E (Up)
        if (keyboard.eKey.isPressed) moveY += 1f;
        if (keyboard.qKey.isPressed) moveY -= 1f;

        // Mouse Button Controls: Left click = -X, Right click = +X
        if (mouse != null)
        {
            if (mouse.leftButton.isPressed)
            {
                moveX -= 1f;
            }
            if (mouse.rightButton.isPressed)
            {
                moveX += 1f;
            }
        }

        // Normalize planar horizontal movement to prevent speed boosting diagonally
        Vector3 planarInput = new Vector3(moveX, 0f, moveZ);
        if (planarInput.sqrMagnitude > 1f)
        {
            planarInput.Normalize();
        }

        Vector3 deltaPosition = planarInput * (keyboardSpeed * Time.deltaTime);

        // Apply vertical movement (scaled independently by verticalSpeed)
        deltaPosition.y = moveY * (verticalSpeed * Time.deltaTime);

        // Mouse Scroll Wheel Controls: Scroll up = +Z, Scroll down = -Z
        if (mouse != null)
        {
            float scrollY = mouse.scroll.ReadValue().y;
            if (Mathf.Abs(scrollY) > 0.01f)
            {
                deltaPosition.z += Mathf.Sign(scrollY) * scrollWheelSensitivity;
            }
        }

        // Apply movement
        playerTransform.position += deltaPosition;

        if (cameraPosition != null)
        {
            cameraPosition.position += deltaPosition;
        }
    }
}