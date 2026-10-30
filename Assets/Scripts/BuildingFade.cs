
using UnityEngine;

public class BuildingFade : MonoBehaviour
{
    public Renderer[] renderers;

    [Range(0f, 2f)]
    public float fade = 2f;

    private MaterialPropertyBlock block;

    private static readonly int FadeID =
        Shader.PropertyToID("_Fade");

    void Awake()
    {
        block = new MaterialPropertyBlock();
    }

    void Update()
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
