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

   
}
