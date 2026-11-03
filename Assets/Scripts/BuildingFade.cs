
using UnityEngine;

public class BuildingFade : MonoBehaviour
{
    private TimelineController m_TimelineController;

    [Header("Building Renderers")]
    public Renderer[] renderers;

    [Header("Fade Settings")]
    [Min(0.01f)]
    public float fadeDuration = 2f;

    [Range(0f, 2f)]
    public float fade = 0f;

    [Header("Timeline Trigger")]
    public bool useTimelineTrigger = true;

    public float signalTime = 10f;

    private MaterialPropertyBlock block;

    private static readonly int FadeID =
        Shader.PropertyToID("_Fade");

    private void Awake()
    {
        block = new MaterialPropertyBlock();
        ApplyFade();
    }

    private void Start()
    {
        m_TimelineController =
            FindFirstObjectByType<TimelineController>();
    }

    private void Update()
    {
        if (useTimelineTrigger && m_TimelineController != null)
        {
            float timelineValue = m_TimelineController.timelineValue;

            // Calculate fade based directly on timeline position
            fade = Mathf.Clamp(
                (timelineValue - signalTime) / fadeDuration,
                0f,
                2f
            );

            ApplyFade();
        }
    }

    private void ApplyFade()
    {
        foreach (Renderer r in renderers)
        {
            if (r == null) continue;

            r.GetPropertyBlock(block);
            block.SetFloat(FadeID, fade);
            r.SetPropertyBlock(block);
        }
    }
}
