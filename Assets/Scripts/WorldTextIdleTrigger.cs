using System.Collections;
using UnityEngine;
using TMPro;

[RequireComponent(typeof(TextMeshPro))]
public class WorldTextIdleTrigger : MonoBehaviour
{
    [Header("Proximity Settings")]
    [Tooltip("Distance in world units within which this text will activate.")]
    [SerializeField] private float activationDistance = 5f;

    [Header("Idle Detection Settings")]
    [SerializeField] private float idleDurationRequired = 3f;
    [SerializeField] private float positionThreshold = 0.05f;
    [SerializeField] private float rotationThreshold = 0.5f;

    [Header("Fade Settings")]
    [SerializeField] private float fadeDuration = 0.5f;

    [Header("Debugging")]
    [SerializeField] private bool enableDebugLogs = true;

    private TextMeshPro _textMesh;
    private Transform _cameraTransform;
    private Vector3 _lastCamPos;
    private Quaternion _lastCamRot;
    private float _idleTimer;
    private bool _isVisible;
    private Coroutine _fadeCoroutine;

    // Track previous state flags to avoid spamming logs every frame
    private bool _wasCloseEnough;

    void Awake()
    {
        _textMesh = GetComponent<TextMeshPro>();

        // Ensure text starts completely invisible
        Color c = _textMesh.color;
        c.a = 0f;
        _textMesh.color = c;
    }

    void Start()
    {
        if (Camera.main != null)
        {
            _cameraTransform = Camera.main.transform;
            _lastCamPos = _cameraTransform.position;
            _lastCamRot = _cameraTransform.rotation;
            LogDebug($"Initialized. Watching for Camera within {activationDistance}m and idle for {idleDurationRequired}s.");
        }
        else
        {
            Debug.LogError($"[WorldTextIdleTrigger - {gameObject.name}] No Main Camera found! Ensure your camera has the 'MainCamera' tag.", this);
        }
    }

    void Update()
    {
        if (_cameraTransform == null) return;

        // 1. Proximity check
        float distToCamera = Vector3.Distance(transform.position, _cameraTransform.position);
        bool isCloseEnough = distToCamera <= activationDistance;

        // Log range enter/exit once
        if (isCloseEnough && !_wasCloseEnough)
        {
            LogDebug($"Camera entered range ({distToCamera:F2}m <= {activationDistance:F2}m).");
        }
        else if (!isCloseEnough && _wasCloseEnough)
        {
            LogDebug($"Camera left range ({distToCamera:F2}m > {activationDistance:F2}m).");
        }
        _wasCloseEnough = isCloseEnough;

        // 2. Camera motion deltas
        float posDelta = Vector3.Distance(_cameraTransform.position, _lastCamPos);
        float rotDelta = Quaternion.Angle(_cameraTransform.rotation, _lastCamRot);
        bool isCameraStill = posDelta <= positionThreshold && rotDelta <= rotationThreshold;

        // 3. Evaluate trigger conditions
        if (isCloseEnough && isCameraStill)
        {
            _idleTimer += Time.deltaTime;

            if (_idleTimer >= idleDurationRequired && !_isVisible)
            {
                LogDebug($"Idle threshold met ({_idleTimer:F1}s >= {idleDurationRequired:F1}s). Triggering FADE IN.");
                TriggerFade(true);
            }
        }
        else
        {
            // Only log if an active countdown or visible prompt was broken
            if (_idleTimer > 0f || _isVisible)
            {
                string reason = !isCloseEnough
                    ? $"Camera out of range ({distToCamera:F2}m)"
                    : (posDelta > positionThreshold
                        ? $"Camera position shifted (Δpos: {posDelta:F3} > threshold: {positionThreshold:F3})"
                        : $"Camera rotation shifted (Δrot: {rotDelta:F3}° > threshold: {rotationThreshold:F3}°)");

                LogDebug($"Conditions broken: {reason}. Resetting timer (was at {_idleTimer:F1}s).");
            }

            _idleTimer = 0f;

            if (_isVisible)
            {
                LogDebug("Fading text out because criteria were lost.");
                TriggerFade(false);
            }
        }

        // Snapshot camera transform for next frame's comparison
        _lastCamPos = _cameraTransform.position;
        _lastCamRot = _cameraTransform.rotation;
    }

    private void TriggerFade(bool show)
    {
        _isVisible = show;

        if (_fadeCoroutine != null)
        {
            LogDebug("Interrupting active fade coroutine.");
            StopCoroutine(_fadeCoroutine);
        }

        _fadeCoroutine = StartCoroutine(FadeRoutine(show ? 1f : 0f));
    }

    private IEnumerator FadeRoutine(float targetAlpha)
    {
        float startAlpha = _textMesh.color.a;
        float elapsed = 0f;

        LogDebug($"Fading alpha: {startAlpha:F2} -> {targetAlpha:F2} over {fadeDuration:F2}s.");

        while (elapsed < fadeDuration)
        {
            elapsed += Time.deltaTime;
            float currentAlpha = Mathf.Lerp(startAlpha, targetAlpha, elapsed / fadeDuration);

            Color c = _textMesh.color;
            c.a = currentAlpha;
            _textMesh.color = c;

            yield return null;
        }

        Color finalColor = _textMesh.color;
        finalColor.a = targetAlpha;
        _textMesh.color = finalColor;

        LogDebug($"Fade complete. Final alpha: {_textMesh.color.a:F2}.");
        _fadeCoroutine = null;
    }

    private void LogDebug(string message)
    {
        if (enableDebugLogs)
        {
            Debug.Log($"[WorldTextIdleTrigger - {gameObject.name}] {message}", this);
        }
    }

    private void OnDrawGizmosSelected()
    {
        Gizmos.color = new Color(1f, 0.92f, 0.016f, 0.35f);
        Gizmos.DrawWireSphere(transform.position, activationDistance);
    }
}