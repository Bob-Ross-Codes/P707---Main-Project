using UnityEngine;
using UnityEngine.Events;

public class PlayerZoneTrigger : MonoBehaviour
{
    [Header("Target Configuration")]
    [Tooltip("Drag the specific Player Collider here from the Inspector.")]
    [SerializeField] private Collider targetPlayerCollider;

    [Header("Timing Configuration")]
    [Tooltip("Time in seconds the player must stay inside before the 10s event fires.")]
    [SerializeField] private float durationThreshold = 10f;

    [Header("Standard Events")]
    public UnityEvent onPlayerEnter;
    public UnityEvent onPlayerExit;

    [Header("Duration Event")]
    [Tooltip("Fires once after the player has been inside continuously for the specified duration.")]
    public UnityEvent onPlayerStayDurationMet;

    [Header("While inside collider Event")]
    [Tooltip("Fires every frame while the player is inside the zone.")]
    public UnityEvent onPlayerStay;

    [Header("First Time Events")]
    [Tooltip("Fires only the very first time the player enters this zone.")]
    public UnityEvent onFirstTimeEnter;
    [Tooltip("Fires only the very first time the player exits this zone.")]
    public UnityEvent onFirstTimeExit;

    // Runtime state tracking
    private bool isPlayerInside = false;
    private float timeInsideZone = 0f;
    private bool hasTriggeredDuration = false;

    private bool hasEnteredEver = false;
    private bool hasExitedEver = false;

    private void OnTriggerEnter(Collider other)
    {
        // Check if the colliding object matches the designated player collider
        if (targetPlayerCollider != null && other == targetPlayerCollider)
        {
            HandlePlayerEnter();
        }
    }

    private void OnTriggerStay(Collider other)
    {
        if (isPlayerInside && targetPlayerCollider != null && other == targetPlayerCollider)
        {
            // Scenario 3: While collider in (Stay)
            Debug.Log($"[PlayerZoneTrigger] ({gameObject.name}) Player is inside collider.");
            onPlayerStay?.Invoke();

            // Scenario 2: Timer tracking for 10s (or custom duration)
            if (!hasTriggeredDuration)
            {
                timeInsideZone += Time.deltaTime;
                if (timeInsideZone >= durationThreshold)
                {
                    hasTriggeredDuration = true;
                    Debug.Log($"[PlayerZoneTrigger] ({gameObject.name}) stay duration threshold met!");
                    onPlayerStayDurationMet?.Invoke();
                }
            }
        }
    }

    private void OnTriggerExit(Collider other)
    {
        if (targetPlayerCollider != null && other == targetPlayerCollider)
        {
            HandlePlayerExit();
        }
    }

    private void HandlePlayerEnter()
    {
        isPlayerInside = true;
        timeInsideZone = 0f;
        hasTriggeredDuration = false;

        // Scenario 1: Standard Enter
        Debug.Log($"[PlayerZoneTrigger] ({gameObject.name}) Player entered the collider.");
        onPlayerEnter?.Invoke();

        // Scenario 5: Unique First Enter
        if (!hasEnteredEver)
        {
            hasEnteredEver = true;
            Debug.Log($"[PlayerZoneTrigger] ({gameObject.name}) FIRST TIME enter triggered!");
            onFirstTimeEnter?.Invoke();
        }
    }

    private void HandlePlayerExit()
    {
        if (!isPlayerInside) return;

        isPlayerInside = false;

        // Scenario 4: Standard Exit
        Debug.Log($"[PlayerZoneTrigger] ({gameObject.name}) Player exited the collider.");
        onPlayerExit?.Invoke();

        // Scenario 6: Unique First Exit
        if (!hasExitedEver)
        {
            hasExitedEver = true;
            Debug.Log($"PlayerZoneTrigger] ({gameObject.name}) FIRST TIME exit triggered");
            onFirstTimeExit?.Invoke();
        }
    }
}