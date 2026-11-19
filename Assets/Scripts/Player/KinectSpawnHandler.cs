using System.Collections;
using UnityEngine;
using UnityEngine.SceneManagement;

public class KinectSpawnHandler : MonoBehaviour
{
    [Header("Spawn Settings")]
    [Tooltip("The tag of the GameObject in the new scene where the Kinect/Player should be placed.")]
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
        // Start a short routine to ensure the scene is fully initialized before moving
        StartCoroutine(RelocateRoutine());
    }

    private IEnumerator RelocateRoutine()
    {
        // Wait one frame to let the new scene finish setting up its objects
        yield return null;

        GameObject spawnPoint = GameObject.FindWithTag(spawnPointTag);

        if (spawnPoint != null)
        {
            // 1. Temporarily disable CharacterController or Rigidbody if they exist so position changes aren't blocked
            CharacterController charController = GetComponentInChildren<CharacterController>();
            Rigidbody rb = GetComponentInChildren<Rigidbody>();

            if (charController != null) charController.enabled = false;
            if (rb != null) rb.isKinematic = true;

            // 2. Move to the spawn point
            transform.position = spawnPoint.transform.position;
            transform.rotation = spawnPoint.transform.rotation;

            // 3. Re-enable physics/controllers
            if (charController != null) charController.enabled = true;
            if (rb != null) rb.isKinematic = false;

            Debug.Log($"[KinectSpawnHandler] Successfully relocated to spawn point: {spawnPoint.name} at {spawnPoint.transform.position}");
        }
        else
        {
            Debug.LogWarning($"[KinectSpawnHandler] No GameObject with tag '{spawnPointTag}' found in the active scene!");
        }
    }
}