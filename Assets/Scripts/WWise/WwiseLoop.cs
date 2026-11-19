using UnityEngine;

/// <summary>
/// Plays one Wwise event from this object for as long as the object is active, then stops it.
/// Use it for looping beds and for looping sounds placed in the world (the event decides 2D or 3D).
/// </summary>
public class WwiseLoop : MonoBehaviour
{
    [SerializeField] private string eventName = "Play_Town_Ambience";

    private uint playingId;

    // Start, not OnEnable: Wwise is initialised by another object's Awake/OnEnable.
    private void Start()
    {
        // Events posted by name don't load their auto-defined SoundBank; AK.Wwise.Event fields do.
        AkBankManager.LoadBank(eventName, false, false, AkBankTypeEnum.AkBankType_Event);
        playingId = AkUnitySoundEngine.PostEvent(eventName, gameObject);
        if (playingId == AkUnitySoundEngine.AK_INVALID_PLAYING_ID)
            Debug.LogWarning($"{name}: Wwise event '{eventName}' did not start. Is it in the SoundBanks?", this);
    }

    private void OnDisable()
    {
        if (playingId != AkUnitySoundEngine.AK_INVALID_PLAYING_ID)
            AkUnitySoundEngine.StopPlayingID(playingId);
    }
}
