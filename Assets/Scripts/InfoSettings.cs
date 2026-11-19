using UnityEngine;
using UnityEngine.ProBuilder.Shapes;

public class InfoSettings : MonoBehaviour
{
    private Animator animator;

    public bool test;
    public bool test2;

    public UnityEngine.Sprite Info;

    private Material MaterialRender;


    private void OnEnable()
    {
        animator = GetComponent<Animator>();
        animator.SetTrigger("FadeIN");
    }

    void Start()
    {
       
        // Create material
        MaterialRender = new Material(Shader.Find("Universal Render Pipeline/Lit"));

        MaterialRender.mainTexture = Info.texture;

        // Set surface type to Transparent
        MaterialRender.SetFloat("_Surface", 1);

        // Disable alpha clipping
        MaterialRender.SetFloat("_AlphaClip", 0);

        // Set blending mode to Alpha
        MaterialRender.SetFloat("_Blend", 0);

        // Set source and destination blending
        MaterialRender.SetFloat("_SrcBlend", (float)UnityEngine.Rendering.BlendMode.SrcAlpha);
        MaterialRender.SetFloat("_DstBlend", (float)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);

        // Disable depth writing
        MaterialRender.SetFloat("_ZWrite", 0);

        // Set transparent render queue
        MaterialRender.renderQueue = 3000;

        // Enable transparency keyword
        MaterialRender.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");

        // Disable alpha clipping keyword
        MaterialRender.DisableKeyword("_ALPHATEST_ON");

        // Set alpha to 0
        Color color = MaterialRender.color;
        color.a = 0f;
        MaterialRender.color = color;

        // Apply material
        GetComponent<Renderer>().material = MaterialRender;
    }
}
