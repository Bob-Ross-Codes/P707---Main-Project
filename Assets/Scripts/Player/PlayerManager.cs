using UnityEngine;

public class PlayerManager : MonoBehaviour
{
    [Header("Target Settings")]
    [Tooltip("The GameObject whose global position/rotation to match.")]
    [SerializeField] private Transform target;

    [Header("Options")]
    [SerializeField] private bool matchRotation = true;
    [SerializeField] private bool updateEveryFrame = false;

    private void Start()
    {
        SnapToTarget();
    }

    private void Update()
    {
        if (updateEveryFrame)
        {
            SnapToTarget();
        }
    }

    [ContextMenu("Snap to Target Now")]
    public void SnapToTarget()
    {
        if (target == null)
        {
            Debug.LogWarning($"[{nameof(PlayerManager)}] No target assigned on {gameObject.name}.", this);
            return;
        }

        // Setting world position via transform.position
        transform.position = target.position;

        if (matchRotation)
        {
            transform.rotation = target.rotation;
        }
    }
}