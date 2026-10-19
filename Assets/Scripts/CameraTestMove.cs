using UnityEngine;
using UnityEngine.InputSystem;

public class CameraTestMove : MonoBehaviour
{
    [SerializeField] private float moveSpeed = 5f;
    [SerializeField] private bool useLocalSpace = true;

    void Update()
    {
        // Guard against null if no keyboard is connected
        if (Keyboard.current == null) return;

        float horizontal = 0f;

        if (Keyboard.current.dKey.isPressed)
        {
            horizontal += 1f;
        }

        if (Keyboard.current.aKey.isPressed)
        {
            horizontal -= 1f;
        }

        if (horizontal != 0f)
        {
            Vector3 direction = useLocalSpace ? transform.right : Vector3.right;
            transform.position += direction * (horizontal * moveSpeed * Time.deltaTime);
        }
    }
}