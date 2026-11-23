using UnityEngine;

public class SceneEventManager : MonoBehaviour
{
    public static SceneEventManager Instance;

    private void Awake()
    {
        if (Instance == null)
        {
            Instance = this;
            // Uncomment if your technical setup persists across scenes:
            // DontDestroyOnLoad(transform.root.gameObject);
        }
        else
        {
            Destroy(gameObject);
        }
    }

    public void ActivateZone(string zoneID)
    {
        // Pass 'true' so it can find objects even if they start disabled in the scene!
        ZoneReceiver[] receivers = FindObjectsOfType<ZoneReceiver>(true);
        foreach (var receiver in receivers)
        {
            if (receiver.zoneID == zoneID)
            {
                receiver.SetActiveState(true);
            }
        }
    }

    public void DeactivateZone(string zoneID)
    {
        ZoneReceiver[] receivers = FindObjectsOfType<ZoneReceiver>(true);
        foreach (var receiver in receivers)
        {
            if (receiver.zoneID == zoneID)
            {
                receiver.SetActiveState(false);
            }
        }
    }
}