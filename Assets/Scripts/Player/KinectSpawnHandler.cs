using UnityEngine;
using UnityEngine.SceneManagement;

public class KinectSpawnHandler : MonoBehaviour
{
    [Header("Spawn Settings")]
    [Tooltip("The tag or name of the GameObject in the new scene where the Kinect should be placed.")]
    [SerializeField] private string spawnPointTag = "KinectSpawnPoint";

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
        RelocateToSpawnPoint(scene.name);
    }

    public void RelocateToSpawnPoint(string sceneName = "")
    {
        GameObject spawnPoint = GameObject.FindWithTag(spawnPointTag);

        if (spawnPoint != null)
        {
            transform.position = spawnPoint.transform.position;
            transform.rotation = spawnPoint.transform.rotation;

            Debug.Log($"[KinectSpawnHandler] Relocated Kinect to spawn point in scene: {sceneName}");
        }
        else
        {
            Debug.LogWarning($"[KinectSpawnHandler] No GameObject with tag '{spawnPointTag}' found in scene '{SceneManager.GetActiveScene().name}'. Keeping previous position.");
        }
    }
}