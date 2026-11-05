
using System.Collections;
using UnityEngine;

public class TreeFade : MonoBehaviour
{
    public float fadeDuration = 2f;
    public bool Fadeintrigger = false;
    public bool Fadeouttrigger = false;

    private Renderer[] renderers;
    private Material[][] materials;
    private Color[][] originalColors;
    private string[][] colorProperties;

    void Awake()
    {
        renderers = GetComponentsInChildren<Renderer>(true);

        materials = new Material[renderers.Length][];
        originalColors = new Color[renderers.Length][];
        colorProperties = new string[renderers.Length][];

        for (int i = 0; i < renderers.Length; i++)
        {
            materials[i] = renderers[i].materials;
            originalColors[i] = new Color[materials[i].Length];
            colorProperties[i] = new string[materials[i].Length];

            for (int j = 0; j < materials[i].Length; j++)
            {
                Material mat = materials[i][j];

                string prop = mat.HasProperty("_BaseColor")
                    ? "_BaseColor"
                    : mat.HasProperty("_Color") ? "_Color" : null;

                colorProperties[i][j] = prop;

                if (prop != null)
                    originalColors[i][j] = mat.GetColor(prop);
            }
        }
    }

    private void Update()
    {
        if (Fadeintrigger)
        {
            Fadeintrigger = false;
            FadeIn();
        }
        else if (Fadeouttrigger)
        {
            Fadeouttrigger = false;
            FadeOut();
        }
    }

    public void FadeOut()
    {
        StopAllCoroutines();
        StartCoroutine(Fade(0f));
    }

    public void FadeIn()
    {
        StopAllCoroutines();
        StartCoroutine(Fade(1f));
    }

    IEnumerator Fade(float targetAlpha)
    {
        float elapsed = 0f;
        float startAlpha = targetAlpha == 0f ? 1f : 0f;

        while (elapsed < fadeDuration)
        {
            elapsed += Time.deltaTime;
            float t = Mathf.Clamp01(elapsed / fadeDuration);
            SetAlpha(Mathf.Lerp(startAlpha, targetAlpha, t));
            yield return null;
        }

        SetAlpha(targetAlpha);
    }

    void SetAlpha(float alpha)
    {
        for (int i = 0; i < materials.Length; i++)
        {
            for (int j = 0; j < materials[i].Length; j++)
            {
                string prop = colorProperties[i][j];

                if (prop == null) continue;

                Color c = originalColors[i][j];
                c.a *= alpha;
                materials[i][j].SetColor(prop, c);
            }
        }
    }
}
