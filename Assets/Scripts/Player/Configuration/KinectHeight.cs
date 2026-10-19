using UnityEngine;

public class KinectHeight : MonoBehaviour
{
    [Tooltip("The GameObject whose height you want to modify.")]
    [SerializeField] private Transform target;

    [Tooltip("The world Y position (height) to set.")]
    [SerializeField] private float height = 0f;

    private void Start()
    {
        ApplyHeight();
    }

    [ContextMenu("Apply Height Now")]
    public void ApplyHeight()   
    {
        if (target == null) return;

        Vector3 pos = target.localPosition;
        pos.y = height;
        target.localPosition = pos;
    }
}