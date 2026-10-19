using System;
using System.Collections.Generic;
using UnityEngine;

[RequireComponent(typeof(Camera))]
public class FOVZoom : MonoBehaviour
{
    [System.Serializable]
    public class ZTargetPoint
    {
        [Tooltip("Reference Transform whose Z coordinate determines the FOV.")]
        public Transform pointTransform;

        [Range(10f, 160f)]
        [Tooltip("The camera FOV to apply when at this target's Z position.")]
        public float targetFOV = 60f;
    }

    [Header("References")]
    [SerializeField] private Camera targetCamera;

    [Tooltip("The object whose Z coordinate is measured (leave empty to use this camera).")]
    [SerializeField] private Transform trackedObject;

    [Header("FOV Points (Sorted along Z)")]
    [Tooltip("Add your reference points. They will be evaluated by world Z coordinate.")]
    [SerializeField] private List<ZTargetPoint> fovPoints = new List<ZTargetPoint>();

    [Header("Smoothing")]
    [Tooltip("Enable smooth transitions rather than instantaneous FOV adjustment.")]
    [SerializeField] private bool smoothTransition = true;
    [SerializeField] private float smoothSpeed = 5f;

    private void Reset()
    {
        targetCamera = GetComponent<Camera>();
        trackedObject = transform;
    }

    private void Awake()
    {
        if (targetCamera == null)
            targetCamera = GetComponent<Camera>();

        if (trackedObject == null)
            trackedObject = transform;
    }

    private void Update()
    {
        if (targetCamera == null || trackedObject == null || fovPoints == null || fovPoints.Count == 0)
            return;

        float calculatedFOV = CalculateFOVAtZ(trackedObject.position.z);

        if (smoothTransition)
        {
            targetCamera.fieldOfView = Mathf.Lerp(targetCamera.fieldOfView, calculatedFOV, Time.deltaTime * smoothSpeed);
        }
        else
        {
            targetCamera.fieldOfView = calculatedFOV;
        }
    }

    private float CalculateFOVAtZ(float currentZ)
    {
        // Filter out null references and sort valid entries by Z ascending
        List<ZTargetPoint> validPoints = new List<ZTargetPoint>();
        for (int i = 0; i < fovPoints.Count; i++)
        {
            if (fovPoints[i].pointTransform != null)
            {
                validPoints.Add(fovPoints[i]);
            }
        }

        if (validPoints.Count == 0) return targetCamera.fieldOfView;
        if (validPoints.Count == 1) return validPoints[0].targetFOV;

        validPoints.Sort((a, b) => a.pointTransform.position.z.CompareTo(b.pointTransform.position.z));

        // Clamp before the first point
        if (currentZ <= validPoints[0].pointTransform.position.z)
            return validPoints[0].targetFOV;

        // Clamp beyond the last point
        if (currentZ >= validPoints[validPoints.Count - 1].pointTransform.position.z)
            return validPoints[validPoints.Count - 1].targetFOV;

        // Interpolate between the two bounding points along the Z axis
        for (int i = 0; i < validPoints.Count - 1; i++)
        {
            float zStart = validPoints[i].pointTransform.position.z;
            float zEnd = validPoints[i + 1].pointTransform.position.z;

            if (currentZ >= zStart && currentZ <= zEnd)
            {
                float t = Mathf.InverseLerp(zStart, zEnd, currentZ);
                return Mathf.Lerp(validPoints[i].targetFOV, validPoints[i + 1].targetFOV, t);
            }
        }

        return targetCamera.fieldOfView;
    }

    private void OnDrawGizmosSelected()
    {
        if (fovPoints == null) return;

        Gizmos.color = Color.cyan;
        foreach (var point in fovPoints)
        {
            if (point.pointTransform != null)
            {
                Vector3 pos = point.pointTransform.position;
                Gizmos.DrawWireSphere(pos, 0.5f);
                Gizmos.DrawLine(new Vector3(pos.x - 5f, pos.y, pos.z), new Vector3(pos.x + 5f, pos.y, pos.z));
            }
        }
    }
}