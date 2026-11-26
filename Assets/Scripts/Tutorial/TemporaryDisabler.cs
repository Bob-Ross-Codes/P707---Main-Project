using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class TemporaryDisabler : MonoBehaviour
{
    [Header("Targets to Temporarily Disable (Will Re-enable)")]
    [SerializeField] private List<GameObject> tempObjects = new List<GameObject>();
    [SerializeField] private List<Behaviour> tempComponents = new List<Behaviour>();

    [Header("Targets to Permanently Disable (Will NOT Re-enable)")]
    [SerializeField] private List<GameObject> permanentObjects = new List<GameObject>();
    [SerializeField] private List<Behaviour> permanentComponents = new List<Behaviour>();

    [Header("Timing")]
    [SerializeField] private float defaultDisableDuration = 2.5f;

    private Coroutine activeRoutine;

    /// <summary>
    /// Parameterless method so it can be called easily via Invoke(nameof(DisableTargets), delay)
    /// or UnityEvents.
    /// </summary>
    public void DisableTargets()
    {
        StartDisableRoutine(defaultDisableDuration);
    }

    /// <summary>
    /// Call this from another script when you need a custom duration for the temporary targets.
    /// </summary>
    public void DisableForDuration(float duration)
    {
        StartDisableRoutine(duration);
    }

    private void StartDisableRoutine(float duration)
    {
        if (activeRoutine != null)
        {
            StopCoroutine(activeRoutine);
        }

        activeRoutine = StartCoroutine(DisableRoutine(duration));
    }

    private IEnumerator DisableRoutine(float duration)
    {
        // 1. Disable permanent targets immediately (never added to re-enable lists)
        foreach (GameObject obj in permanentObjects)
        {
            if (obj != null)
            {
                obj.SetActive(false);
            }
        }

        foreach (Behaviour comp in permanentComponents)
        {
            if (comp != null)
            {
                comp.enabled = false;
            }
        }

        // 2. Disable temporary targets and track only those that were active/enabled
        List<GameObject> disabledTempObjects = new List<GameObject>();
        List<Behaviour> disabledTempComponents = new List<Behaviour>();

        foreach (GameObject obj in tempObjects)
        {
            if (obj != null && obj.activeSelf)
            {
                obj.SetActive(false);
                disabledTempObjects.Add(obj);
            }
        }

        foreach (Behaviour comp in tempComponents)
        {
            if (comp != null && comp.enabled)
            {
                comp.enabled = false;
                disabledTempComponents.Add(comp);
            }
        }

        yield return new WaitForSeconds(duration);

        // 3. Re-enable only the temporary targets that were active before
        foreach (GameObject obj in disabledTempObjects)
        {
            if (obj != null)
            {
                obj.SetActive(true);
            }
        }

        foreach (Behaviour comp in disabledTempComponents)
        {
            if (comp != null)
            {
                comp.enabled = true;
            }
        }

        activeRoutine = null;
    }
}