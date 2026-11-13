using UnityEngine;

[DisallowMultipleComponent]
public class PersistentKinect : MonoBehaviour
{
    private static PersistentKinect instance;

    private void Awake()
    {
        // Check if another instance of the Kinect already exists
        if (instance != null && instance != this)
        {
            // If a persistent Kinect is already running, destroy this duplicate one in the new scene
            Debug.Log("[PersistentKinect] Duplicate Kinect prefab detected in new scene. Destroying duplicate.");
            Destroy(gameObject);
            return;
        }

        // Set this as the main instance and make it survive scene loads
        instance = this;
        DontDestroyOnLoad(gameObject);
    }
}