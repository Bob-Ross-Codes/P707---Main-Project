using UnityEngine;

public class ZoneReceiver : MonoBehaviour
{
    public enum ZoneType
    {
        [InspectorName("FL Collider")] FL_Collider,
        [InspectorName("FM Collider")] FM_Collider,
        [InspectorName("FR Collider")] FR_Collider,
        [InspectorName("Custom...")] Custom
    }

    [Header("Zone Configuration")]
    public ZoneType zoneSelection;

    [Tooltip("Type your custom Zone ID here if 'Custom' is selected above.")]
    public string customZoneID;

    // Automatically returns the right string ID depending on your choice
    public string zoneID
    {
        get
        {
            switch (zoneSelection)
            {
                case ZoneType.FL_Collider: return "FL Collider";
                case ZoneType.FM_Collider: return "FM Collider";
                case ZoneType.FR_Collider: return "FR Collider";
                case ZoneType.Custom: return customZoneID;
                default: return "";
            }
        }
    }

    public void SetActiveState(bool isActive)
    {
        gameObject.SetActive(isActive);
    }
}