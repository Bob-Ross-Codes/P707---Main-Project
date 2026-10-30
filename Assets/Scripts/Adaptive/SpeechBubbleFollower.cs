using UnityEngine;

public class SpeechBubbleFollower : MonoBehaviour
{
    [Header("References")]
    [SerializeField] private Transform character;
    [SerializeField] private Transform visitorHead;

    [Header("Position")]
    [SerializeField]
    private Vector3 characterOffset =
        new Vector3(0f, 2f, 0f);

    private Camera mainCamera;

    private void Awake()
    {
        mainCamera = Camera.main;
    }

    private void LateUpdate()
    {
        if (character == null)
            return;

        // Follow the character without inheriting its scale.
        transform.position = character.position + characterOffset;

        // Face the camera so the text remains readable.
        if (mainCamera != null)
        {
            transform.rotation = mainCamera.transform.rotation;
        }
    }
}