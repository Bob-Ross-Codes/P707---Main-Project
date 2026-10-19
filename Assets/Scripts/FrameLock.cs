using UnityEngine;

public class FrameLock : MonoBehaviour
{
    [Tooltip("Target frames per second (-1 = uncapped).")]
    [Range(-1, 300)]
    [SerializeField] private int targetFPS = 60;

    [Tooltip("Disable VSync so targetFrameRate takes effect.")]
    [SerializeField] private bool disableVSync = true;

    private void Awake()
    {
        ApplyFrameRate();
    }

    private void OnValidate()
    {
        // Allows you to change the frame rate live from the Inspector during Play Mode
        if (Application.isPlaying)
        {
            ApplyFrameRate();
        }
    }

    private void ApplyFrameRate()
    {
        if (disableVSync)
        {
            // When vSyncCount is non-zero, targetFrameRate is ignored by Unity
            QualitySettings.vSyncCount = 0;
        }

        Application.targetFrameRate = targetFPS;
    }
}