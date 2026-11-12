using UnityEngine;
using UnityEngine.SceneManagement;

public class SceneSwitcher : MonoBehaviour
{
    /// <summary>
    /// Loads the next scene in the Build Settings (+1 index).
    /// </summary>
    public void LoadNextScene()
    {
        int currentSceneIndex = SceneManager.GetActiveScene().buildIndex;
        int nextSceneIndex = currentSceneIndex + 1;

        // Check if the next scene exists in Build Settings before loading
        if (nextSceneIndex < SceneManager.sceneCountInBuildSettings)
        {
            SceneManager.LoadScene(nextSceneIndex);
        }
        else
        {
            Debug.LogWarning("[SceneSwitcher] You are already at the last scene in Build Settings!");
        }
    }

    /// <summary>
    /// Loads the previous scene in the Build Settings (-1 index).
    /// </summary>
    public void LoadPreviousScene()
    {
        int currentSceneIndex = SceneManager.GetActiveScene().buildIndex;
        int prevSceneIndex = currentSceneIndex - 1;

        // Check if the previous scene index is valid (>= 0)
        if (prevSceneIndex >= 0)
        {
            SceneManager.LoadScene(prevSceneIndex);
        }
        else
        {
            Debug.LogWarning("[SceneSwitcher] You are already at the first scene in Build Settings!");
        }
    }

    /// <summary>
    /// Loads a specific scene by its exact name.
    /// </summary>
    public void LoadSceneByName(string sceneName)
    {
        SceneManager.LoadScene(sceneName);
    }
}