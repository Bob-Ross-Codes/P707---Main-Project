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

        float normalizedTime = timelineValue / 100f;

        director.time = normalizedTime * director.duration;

        director.Evaluate();
    }
}