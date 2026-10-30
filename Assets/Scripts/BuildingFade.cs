
using System.Collections;
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
    public float fade = 2f;

    public bool Fadestate = false;

    [Header("Manual Triggers")]
    public bool fadeInTrigger;
    public bool fadeOutTrigger;

    [Header("Timeline Trigger")]
    public bool useTimelineTrigger = true;
    public float signalTime;

    private MaterialPropertyBlock block;
    private Coroutine currentFade;

    private static readonly int FadeID =
        Shader.PropertyToID("_Fade");

    private void Awake()
    {
        block = new MaterialPropertyBlock();
        ApplyFade();
    }

    private void Start()
    {
        m_TimelineController = FindFirstObjectByType<TimelineController>();
    }

    private void Update()
    {
        // Manual triggers
        if (fadeInTrigger)
        {
            fadeInTrigger = false;
            FadeIn();
        }

        if (fadeOutTrigger)
        {
            fadeOutTrigger = false;
            FadeOut();
        }

        // Timeline trigger
        if (useTimelineTrigger && m_TimelineController != null)
        {
            if (m_TimelineController.timelineValue < signalTime)
            {
                FadeOut();
            }
            else
            {
                FadeIn();
            }
        }
    }

    public void FadeOut()
    {
        if (Fadestate)
        {
            StartFade(0f);
            Fadestate = false;
        }
    }

    public void FadeIn()
    {
        if (!Fadestate)
        {
            StartFade(2f);
            Fadestate = true;
        }
    }

    private void StartFade(float target)
    {
        if (currentFade != null)
        {
            StopCoroutine(currentFade);
        }

        currentFade = StartCoroutine(FadeRoutine(target));
    }

    private IEnumerator FadeRoutine(float target)
    {
        float startValue = fade;
        float elapsed = 0f;

        while (elapsed < fadeDuration)
        {
            elapsed += Time.deltaTime;

            float t = Mathf.Clamp01(elapsed / fadeDuration);

            fade = Mathf.Lerp(startValue, target, t);

            ApplyFade();

            yield return null;
        }

        fade = target;
        ApplyFade();

        currentFade = null;
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
