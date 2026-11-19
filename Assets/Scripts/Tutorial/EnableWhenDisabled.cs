using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Events;

public class EnableWhenDisabled : MonoBehaviour
{
    [Header("Watch These (Must Activate, Then Disable)")]
    [Tooltip("Objects are ignored until active at least once, then count as complete once disabled.")]
    [SerializeField] private List<GameObject> watchObjects = new List<GameObject>();

    [Header("Enable These When Complete")]
    [Tooltip("GameObjects to activate once all watched objects have been active and then disabled.")]
    [SerializeField] private List<GameObject> enableOnComplete = new List<GameObject>();

    [Header("Behavior")]
    [Tooltip("If checked, only triggers once per enable cycle rather than re-applying every frame.")]
    [SerializeField] private bool triggerOnce = true;

    [Tooltip("Optional: also disable the enabled objects again if a watched object becomes active later.")]
    [SerializeField] private bool revertIfReactivated = false;

    [Tooltip("Optional event fired when the condition is met (e.g., for UI, audio, or animations).")]
    public UnityEvent onCompleted;

    private readonly HashSet<GameObject> activatedObjects = new HashSet<GameObject>();
    private bool hasTriggered;

    private void Update()
    {
        if (watchObjects == null || watchObjects.Count == 0)
            return;

        RecordActiveObjects();

        if (triggerOnce && hasTriggered)
            return;

        if (AreAllWatchedObjectsComplete())
        {
            SetEnabledObjectsActive(true);

            if (!hasTriggered)
            {
                hasTriggered = true;
                onCompleted?.Invoke();
            }
        }
        else if (revertIfReactivated && !triggerOnce)
        {
            SetEnabledObjectsActive(false);
        }
    }

    private void RecordActiveObjects()
    {
        for (int i = 0; i < watchObjects.Count; i++)
        {
            GameObject obj = watchObjects[i];
            if (obj != null && obj.activeInHierarchy)
            {
                activatedObjects.Add(obj);
            }
        }
    }

    private bool AreAllWatchedObjectsComplete()
    {
        bool anyValidWatchedObject = false;

        for (int i = 0; i < watchObjects.Count; i++)
        {
            GameObject obj = watchObjects[i];
            if (obj == null)
                continue;

            anyValidWatchedObject = true;

            // Must have been active at least once, and must now be inactive
            if (!activatedObjects.Contains(obj) || obj.activeInHierarchy)
            {
                return false;
            }
        }

        return anyValidWatchedObject;
    }

    private void SetEnabledObjectsActive(bool state)
    {
        for (int i = 0; i < enableOnComplete.Count; i++)
        {
            if (enableOnComplete[i] != null && enableOnComplete[i].activeSelf != state)
            {
                enableOnComplete[i].SetActive(state);
            }
        }
    }

    [ContextMenu("Reset Trigger")]
    public void ResetTrigger()
    {
        hasTriggered = false;
        activatedObjects.Clear();
    }
}