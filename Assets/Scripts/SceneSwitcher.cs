using UnityEngine;
using UnityEngine.SceneManagement;

public class SceneSwitcher : MonoBehaviour
{
    [Header("Scene Lock Settings")]
    [Tooltip("Build index of the tutorial scene (usually 0).")]
    [SerializeField] private int tutorialSceneBuildIndex = 0;

    [Tooltip("Once leaving this build index (e.g., 1 for Scene 1), players cannot go back to it.")]
    [SerializeField] private int lockGoingBackFromBuildIndex = 1;

    // Lowest build index the player is currently allowed to load
    private int minAllowedBuildIndex = 0;

    private void Awake()
    {
        int currentIndex = SceneManager.GetActiveScene().buildIndex;
        UpdateMinimumAllowedIndex(currentIndex);
    }

    private void OnEnable()
    {
        SceneManager.sceneLoaded += OnSceneLoaded;
    }

    private void OnDisable()
    {
        SceneManager.sceneLoaded -= OnSceneLoaded;
    }

    private void OnSceneLoaded(Scene scene, LoadSceneMode mode)
    {
        UpdateMinimumAllowedIndex(scene.buildIndex);
    }

    private void UpdateMinimumAllowedIndex(int currentBuildIndex)
    {
        // Once past Tutorial (index 0), block going back to index 0, but keep index 1 accessible
        if (currentBuildIndex > tutorialSceneBuildIndex)
        {
            minAllowedBuildIndex = Mathf.Max(minAllowedBuildIndex, tutorialSceneBuildIndex + 1);
        }
    }

    /// <summary>
    /// Loads the next scene in the Build Settings (+1 index).
    /// </summary>
    public void LoadNextScene()
    {
        int currentSceneIndex = SceneManager.GetActiveScene().buildIndex;
        int nextSceneIndex = currentSceneIndex + 1;

        if (nextSceneIndex < SceneManager.sceneCountInBuildSettings)
        {
            UpdateMinimumAllowedIndex(nextSceneIndex);
            SceneManager.LoadScene(nextSceneIndex);
        }
        else
        {
            Debug.LogWarning("[SceneSwitcher] You are already at the last scene in Build Settings!");
        }
    }

    /// <summary>
    /// Loads the previous scene in the Build Settings (-1 index), respecting locked earlier scenes.
    /// </summary>
    public void LoadPreviousScene()
    {
        int currentSceneIndex = SceneManager.GetActiveScene().buildIndex;
        int prevSceneIndex = currentSceneIndex - 1;

        if (prevSceneIndex >= minAllowedBuildIndex && prevSceneIndex >= 0)
        {
            SceneManager.LoadScene(prevSceneIndex);
        }
        else
        {
            Debug.Log($"[SceneSwitcher] Going back to build index {prevSceneIndex} is blocked (minimum allowed: {minAllowedBuildIndex}).");
        }
    }

    /// <summary>
    /// Loads a specific scene by its exact name, unless it is earlier than the allowed minimum index.
    /// </summary>
    public void LoadSceneByName(string sceneName)
    {
        int targetIndex = SceneUtility.GetBuildIndexByScenePath(sceneName);

        // SceneUtility.GetBuildIndexByScenePath returns -1 if only the scene name (not path) was passed
        if (targetIndex < 0)
        {
            for (int i = 0; i < SceneManager.sceneCountInBuildSettings; i++)
            {
                string path = SceneUtility.GetScenePathByBuildIndex(i);
                string nameWithoutExt = System.IO.Path.GetFileNameWithoutExtension(path);
                if (nameWithoutExt == sceneName)
                {
                    targetIndex = i;
                    break;
                }
            }
        }

        if (targetIndex >= 0 && targetIndex < minAllowedBuildIndex)
        {
            Debug.Log($"[SceneSwitcher] Blocked loading '{sceneName}' (index {targetIndex}) because minimum allowed index is {minAllowedBuildIndex}.");
            return;
        }

        if (targetIndex >= 0)
        {
            UpdateMinimumAllowedIndex(targetIndex);
        }

        SceneManager.LoadScene(sceneName);
    }
   
    public void LoadLastAllowedScene()
    {
        int sceneCount = SceneManager.sceneCountInBuildSettings;
        if (sceneCount <= 0) return;

        int minAllowed = Mathf.Clamp(minAllowedBuildIndex, 0, sceneCount - 1);
        int currentIndex = SceneManager.GetActiveScene().buildIndex;

        int targetIndex;
        if (currentIndex > minAllowed)
        {
            targetIndex = minAllowed;
        }
        else
        {
            targetIndex = currentIndex - 1;
        }

        if (targetIndex >= minAllowed && targetIndex >= 0 && targetIndex != currentIndex)
        {
            SceneManager.LoadScene(targetIndex);
        }
        else
        {
            Debug.Log($"[SceneSwitcher] Cannot go earlier than build index {minAllowed} from scene index {currentIndex}.");
        }
    }
}