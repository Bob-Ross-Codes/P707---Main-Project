using UnityEngine;
using UnityEngine.InputSystem;

public class SceneShortcutController : MonoBehaviour
{
    [Header("Scene Switcher Reference")]
    [SerializeField] private SceneSwitcher sceneSwitcher;

    [Header("First '0' Press Object States")]
    [Tooltip("GameObjects to turn OFF (SetActive(false)) on the first press of '0'.")]
    [SerializeField] private GameObject[] objectsToDisableOnFirstZero;

    [Tooltip("GameObjects to turn ON (SetActive(true)) on the first press of '0'.")]
    [SerializeField] private GameObject[] objectsToEnableOnFirstZero;

    [Tooltip("If true, persists whether the first '0' toggle has already happened across scene loads.")]
    [SerializeField] private bool rememberFirstZeroAcrossScenes = true;

    private static bool hasUsedFirstZeroGlobal = false;
    private bool hasUsedFirstZeroLocal = false;

    private void Awake()
    {
        if (sceneSwitcher == null)
        {
            sceneSwitcher = GetComponent<SceneSwitcher>();
            if (sceneSwitcher == null)
            {
                sceneSwitcher = GetComponentInChildren<SceneSwitcher>();
            }
        }
    }

    private void Update()
    {
        Keyboard keyboard = Keyboard.current;
        if (keyboard == null || sceneSwitcher == null)
            return;

        // Top-row '0' and numpad '0'
        bool zeroPressed = keyboard.digit0Key.wasPressedThisFrame || keyboard.numpad0Key.wasPressedThisFrame;
        // Top-row '9' and numpad '9'
        bool ninePressed = keyboard.digit9Key.wasPressedThisFrame || keyboard.numpad9Key.wasPressedThisFrame;

        if (zeroPressed)
        {
            HandleZeroKey();
        }
        else if (ninePressed)
        {
            sceneSwitcher.LoadLastAllowedScene();
        }
    }

    private void HandleZeroKey()
    {
        bool alreadyTriggered = rememberFirstZeroAcrossScenes
            ? hasUsedFirstZeroGlobal
            : hasUsedFirstZeroLocal;

        if (!alreadyTriggered)
        {
            ApplyFirstZeroObjectStates();

            if (rememberFirstZeroAcrossScenes)
                hasUsedFirstZeroGlobal = true;
            else
                hasUsedFirstZeroLocal = true;
        }

        sceneSwitcher.LoadNextScene();
    }

    private void ApplyFirstZeroObjectStates()
    {
        if (objectsToDisableOnFirstZero != null)
        {
            foreach (GameObject obj in objectsToDisableOnFirstZero)
            {
                if (obj != null)
                    obj.SetActive(false);
            }
        }

        if (objectsToEnableOnFirstZero != null)
        {
            foreach (GameObject obj in objectsToEnableOnFirstZero)
            {
                if (obj != null)
                    obj.SetActive(true);
            }
        }
    }
}