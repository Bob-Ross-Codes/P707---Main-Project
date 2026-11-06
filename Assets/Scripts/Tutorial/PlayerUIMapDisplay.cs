using UnityEngine;

[ExecuteAlways]
public class PlayerUIMapDisplay : MonoBehaviour
{
    [Header("References")]
    [Tooltip("Reference to your PlayerAreaTracker script.")]
    [SerializeField] private PlayerAreaTracker areaTracker;

    [Tooltip("The UI Panel/RectTransform that acts as the background map container.")]
    [SerializeField] private RectTransform mapContainer;

    [Tooltip("The UI RectTransform representing the player's dot inside the map.")]
    [SerializeField] private RectTransform playerDotUI;

    [Header("Auto-Aspect Ratio Settings")]
    [Tooltip("Automatically resize the UI map container to match the 3D area's width/depth ratio.")]
    [SerializeField] private bool autoMatchAspect = true;

    [Tooltip("The base pixel dimension (width or height) used when scaling the container.")]
    [SerializeField] private float basePixelSize = 400f;

    [Header("Display Settings")]
    [Tooltip("Hide the player dot when they step outside the 3D tracked area.")]
    [SerializeField] private bool hideWhenOutside = true;

    private void Update()
    {
        if (areaTracker == null) return;

        // 1. Automatically match the UI map container size to the 3D area's aspect ratio
        if (autoMatchAspect && mapContainer != null)
        {
            ApplyAspectRatio();
        }

        if (mapContainer == null || playerDotUI == null) return;

        // 2. Track player position percentages
        float percentX = areaTracker.RelativeXPercent;
        float percentZ = areaTracker.RelativeZPercent;

        bool isInside = (percentX >= 0f && percentX <= 100f && percentZ >= 0f && percentZ <= 100f);

        if (hideWhenOutside)
        {
            playerDotUI.gameObject.SetActive(isInside);
        }

        if (!isInside && hideWhenOutside) return;

        // 3. Convert 0-100% to local anchored pixel positions inside the map container
        float normX = Mathf.Clamp01(percentX / 100f);
        float normZ = Mathf.Clamp01(percentZ / 100f);

        Vector2 containerSize = mapContainer.rect.size;

        float posX = normX * containerSize.x;
        float posY = normZ * containerSize.y;

        playerDotUI.anchoredPosition = new Vector2(posX, posY);
    }

    private void ApplyAspectRatio()
    {
        float widthMeters = areaTracker.AreaWidthX;
        float depthMeters = areaTracker.AreaDepthZ;

        if (depthMeters <= 0f) return;

        // Calculate 3D ratio (e.g., 5.5m width / 4.0m depth = 1.375)
        float areaAspectRatio = widthMeters / depthMeters;

        Vector2 size = mapContainer.sizeDelta;

        if (areaAspectRatio >= 1f)
        {
            // Area is wider than it is deep
            size.x = basePixelSize;
            size.y = basePixelSize / areaAspectRatio;
        }
        else
        {
            // Area is deeper than it is wide
            size.y = basePixelSize;
            size.x = basePixelSize * areaAspectRatio;
        }

        mapContainer.sizeDelta = size;
    }
}