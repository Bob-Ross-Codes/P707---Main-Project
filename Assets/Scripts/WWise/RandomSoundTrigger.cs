
using UnityEngine;
using System.Collections;

public class RandomSoundTrigger : MonoBehaviour
{
    [Header("Wwise")]
    public string eventName = "Play_Birds";

    [Header("Random Timing")]
    public float minInterval = 3f;
    public float maxInterval = 12f;

    private void Start()
    {
        // Events posted by name don't load their auto-defined SoundBank; AK.Wwise.Event fields do.
        AkBankManager.LoadBank(eventName, false, false, AkBankTypeEnum.AkBankType_Event);
        StartCoroutine(PlayRandomly());
    }

    private IEnumerator PlayRandomly()
    {
        while (true)
        {
            // Wait for a random amount of time
            float waitTime = Random.Range(
                minInterval,
                maxInterval
            );

            yield return new WaitForSeconds(waitTime);

            // Trigger Wwise event
            AkSoundEngine.PostEvent(eventName, gameObject);
        }
    }
}
