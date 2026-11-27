using TMPro;
using UnityEngine;

// The text and photo of one interest point. It sits on the zone root (next to ZoneReceiver) and writes its content
// into every look below it, so switching which variant child is active keeps the content. Updates live in edit mode.
// Each variant's page holds TMP texts named Title, Body and Caption and a PhotoArea (scaled to the photo-and-caption
// column) with a Photo quad inside; the photo is fitted to the top of the column and the caption fills the rest.
[ExecuteAlways]
public class InfoPage : MonoBehaviour
{
    public string title;
    [TextArea(6, 20)] public string body;
    [TextArea(2, 6)] public string caption;
    public Texture2D photo;

    const float CaptionGap = 0.04f, PhotoShare = 0.7f, BodyMin = 0.36f, BodyMax = 0.46f;
    static readonly int BaseMap = Shader.PropertyToID("_BaseColorMap"); // HDRP/Lit name; URP used _BaseMap
    MaterialPropertyBlock block;

    void OnEnable() => Apply();

#if UNITY_EDITOR
    // TMP and renderers can't be touched inside OnValidate itself
    void OnValidate() => UnityEditor.EditorApplication.delayCall += () => { if (this) Apply(); };
#endif

    public void Apply()
    {
        foreach (var t in GetComponentsInChildren<TMP_Text>(true))
        {
            if (t.name == "Title") t.text = title;
            else if (t.name == "Body") { t.text = body; FitBody(t); }
            else if (t.name == "Caption") t.text = caption;
        }
        foreach (var area in GetComponentsInChildren<Transform>(true))
            if (area.name == "PhotoArea") FitPhoto(area);
    }

    // the largest body size up to BodyMax that fits the column; TMP's own auto-size steps too coarsely at world sizes
    void FitBody(TMP_Text t)
    {
        t.enableAutoSizing = false;
        var box = ((RectTransform)t.transform).rect.size;
        float lo = BodyMin, hi = BodyMax;
        for (int i = 0; i < 8; i++)
        {
            t.fontSize = (lo + hi) / 2;
            if (t.GetPreferredValues(body, box.x, 0).y <= box.y) lo = t.fontSize; else hi = t.fontSize;
        }
        t.fontSize = lo;
    }

    void FitPhoto(Transform area)
    {
        var quad = area.Find("Photo");
        var cap = area.parent.Find("Caption");
        if (quad == null) return;
        var r = quad.GetComponent<Renderer>();
        r.enabled = photo != null;
        // the area is the photo-and-caption column; the photo gets up to PhotoShare of its height, the caption the rest
        float w = area.localScale.x, h = area.localScale.y, qw = 0, qh = 0;
        if (photo != null)
        {
            block ??= new MaterialPropertyBlock();
            r.GetPropertyBlock(block);
            block.SetTexture(BaseMap, photo);
            r.SetPropertyBlock(block);
            float aspect = (float)photo.width / photo.height;
            qw = w; qh = w / aspect;
            if (qh > h * PhotoShare) { qh = h * PhotoShare; qw = qh * aspect; }
        }
        quad.localScale = new Vector3(Mathf.Max(qw, 0.001f) / w, Mathf.Max(qh, 0.001f) / h, 1);
        quad.localPosition = new Vector3(0, 0.5f - qh / h / 2, 0);
        if (cap == null) return;
        float top = area.localPosition.y + h / 2 - qh - (photo ? CaptionGap : 0);
        cap.localPosition = new Vector3(area.localPosition.x - w / 2, top, 0);
        ((RectTransform)cap).sizeDelta = new Vector2(w, Mathf.Max(0.1f, top - (area.localPosition.y - h / 2)));
    }
}
