
using UnityEngine;
using UnityEngine.Playables;

public class TimelineController : MonoBehaviour
{
    public PlayableDirector director;

    [Range(0, 100)]
    public int timelineValue;

    void Update()
    {
        if (director == null) return;

        // Prevent reaching the exact end
        director.time = Mathf.Min(timelineValue, 99.9f);

        director.Evaluate();
    }
}
