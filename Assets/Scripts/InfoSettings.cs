using UnityEngine;

public class InfoSettings : MonoBehaviour
{
    private Animator animator;

    public bool test;
    public bool test2;
    void Start()
    {
        animator = GetComponent<Animator>();
    }

    void Update()
    {
        if (test)
        {
            animator.SetTrigger("FadeIN");
            test = false;
        }

        if (test2)
        {
            animator.SetTrigger("FadeOUT");
            test2 = false;
        }
    }
}
