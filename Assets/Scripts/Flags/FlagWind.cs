using UnityEngine;

/// <summary>
/// The wind every flag responds to. Put one in the scene; it blows along its forward (blue) axis.
/// Changes to strength and direction reach the flags smoothly, so you can animate them.
/// </summary>
[ExecuteAlways]
public class FlagWind : MonoBehaviour
{
    [Tooltip("0 = still air, the flags hang. 1 = strong wind, the flags fly straight out.")]
    [Range(0f, 1f)] public float strength = 0.55f;
    [Tooltip("How much gusts rolling through the scene raise and drop the wind.")]
    [Range(0f, 1f)] public float gustiness = 0.5f;
    [Tooltip("Degrees the direction drifts slowly to either side of the forward axis.")]
    [Range(0f, 90f)] public float directionWander = 15f;
    [Tooltip("Seconds the flags take to follow a change in strength or direction.")]
    [Min(0.01f)] public float smoothing = 2f;

    private static readonly int WindId = Shader.PropertyToID("_FlagWind");
    private static readonly int ClockId = Shader.PropertyToID("_FlagWindClock");

    private Vector2 direction;
    private float currentStrength;
    private float clock;

    private void OnEnable()
    {
        direction = TargetDirection();
        currentStrength = strength;
        Push();
    }

    private void Update()
    {
        float dt = Time.deltaTime;
        float k = 1f - Mathf.Exp(-dt / smoothing);
        direction = Vector2.Lerp(direction, TargetDirection(), k).normalized;
        currentStrength = Mathf.Lerp(currentStrength, strength, k);
        // Ripples travel faster in strong wind; integrating keeps them continuous when the wind changes.
        clock += dt * Mathf.Lerp(1.2f, 5.5f, currentStrength);
        Push();
    }

    private Vector2 TargetDirection()
    {
        Vector3 f = transform.forward;
        float drift = directionWander * (Mathf.PerlinNoise(Time.time * 0.03f, 0.5f) * 2f - 1f);
        Vector3 d = Quaternion.Euler(0f, drift, 0f) * new Vector3(f.x, 0f, f.z);
        return d.sqrMagnitude > 1e-6f ? new Vector2(d.x, d.z).normalized : Vector2.right;
    }

    private void Push()
    {
        Shader.SetGlobalVector(WindId, new Vector4(direction.x, direction.y, currentStrength, gustiness));
        Shader.SetGlobalFloat(ClockId, clock);
    }

    private void OnDrawGizmos()
    {
        Gizmos.color = Color.cyan;
        Vector3 p = transform.position, f = transform.forward * 2f;
        Gizmos.DrawLine(p, p + f);
        Gizmos.DrawLine(p + f, p + f * 0.75f + transform.right * 0.4f);
        Gizmos.DrawLine(p + f, p + f * 0.75f - transform.right * 0.4f);
    }
}
