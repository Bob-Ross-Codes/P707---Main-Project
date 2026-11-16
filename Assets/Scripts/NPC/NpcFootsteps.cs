using UnityEngine;

/// <summary>
/// Posts a Wwise footstep event each time a foot lands in the walk animation.
/// The event is posted on this NPC, so Wwise pans it and fades it with distance as the NPC moves.
/// </summary>
[RequireComponent(typeof(Animator))]
public class NpcFootsteps : MonoBehaviour
{
    [SerializeField] private string footstepEvent = "Play_Footstep";

    [Tooltip("Name of the Animator state that is the walk.")]
    [SerializeField] private string walkState = "Walk";

    [Tooltip("Points in the walk cycle (0 to 1) where a foot lands. Measured from the Kevin Iglesias walk clips.")]
    [SerializeField] private float[] footfalls = { 0.0f, 0.5f };

    private Animator animator;
    private int walkStateHash;
    private float lastCycle = -1f;

    private void Awake()
    {
        animator = GetComponent<Animator>();
        walkStateHash = Animator.StringToHash(walkState);
    }

    private void Update()
    {
        AnimatorStateInfo state = animator.GetCurrentAnimatorStateInfo(0);
        if (state.shortNameHash != walkStateHash)
        {
            lastCycle = -1f;
            return;
        }

        float cycle = Mathf.Repeat(state.normalizedTime, 1f);
        if (lastCycle >= 0f)
        {
            foreach (float footfall in footfalls)
            {
                if (Passed(lastCycle, cycle, footfall))
                    AkUnitySoundEngine.PostEvent(footstepEvent, gameObject);
            }
        }
        lastCycle = cycle;
    }

    // True when the cycle moved past the point this frame, including across the loop from 1 back to 0.
    private static bool Passed(float from, float to, float point)
    {
        return from <= to ? from < point && point <= to : point > from || point <= to;
    }
}
