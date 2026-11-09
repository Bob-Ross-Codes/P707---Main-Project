using UnityEngine;
using UnityEngine.UI;

public class ZoneProgressBarUI : MonoBehaviour
{
    [Header("UI References")]
    [Tooltip("Drag the specific Image object with the Filled property here.")]
    [SerializeField] private Image circularFillImage;

    private bool isFilling = false;
    private float currentTime = 0f;
    private float targetDuration = 10f;

    private void Start()
    {
        ResetProgress();
    }

    private void Update()
    {
        if (!isFilling) return;

        currentTime += Time.deltaTime;
        float currentDuration = Mathf.Max(targetDuration, 0.001f);
        float progress = Mathf.Clamp01(currentTime / currentDuration);

        UpdateVisuals(progress);

        if (progress >= 1f)
        {
            isFilling = false;
        }
    }

    /// <summary>
    /// Call this from the On Player Enter event. 
    /// Pass the PlayerZoneTrigger component directly so it reads its specific threshold!
    /// </summary>
    public void StartFillingFromTrigger(PlayerZoneTrigger zoneTrigger)
    {
        if (zoneTrigger != null)
        {
            // Read the exact duration configured on this specific hitbox
            targetDuration = zoneTrigger.DurationThreshold;
            Debug.Log($"[ZoneProgressBarUI] Started filling for hitbox. Target duration: {targetDuration}s");
        }
        else
        {
            Debug.LogWarning("[ZoneProgressBarUI] PlayerZoneTrigger reference was null! Using default duration.");
        }

        currentTime = 0f;
        isFilling = true;

        if (circularFillImage != null)
        {
            circularFillImage.gameObject.SetActive(true);
        }
    }

    public void StopAndResetFilling()
    {
        isFilling = false;
        ResetProgress();
    }

    private void UpdateVisuals(float progress0to1)
    {
        if (circularFillImage != null)
        {
            circularFillImage.fillAmount = progress0to1;
        }
    }

    private void ResetProgress()
    {
        currentTime = 0f;
        UpdateVisuals(0f);

        if (circularFillImage != null)
        {
            circularFillImage.gameObject.SetActive(false);
        }
    }
}