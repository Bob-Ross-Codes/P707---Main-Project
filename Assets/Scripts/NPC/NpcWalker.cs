using UnityEngine;

/// <summary>
/// Walks an NPC along a route and back again, pausing at each end.
/// The walk clip's root motion moves the NPC, so the feet do not slide; this script only steers.
/// shortcut: flat ground and no obstacle avoidance. Switch to a NavMeshAgent if routes must dodge things.
/// </summary>
[RequireComponent(typeof(Animator))]
public class NpcWalker : MonoBehaviour
{
    [Tooltip("Parent object whose children are the waypoints, in walking order. Put the first and last out of sight.")]
    [SerializeField] private Transform route;

    [Tooltip("Waypoint the NPC heads for first, so walkers can start in the middle of a route.")]
    [Min(0)] [SerializeField] private int firstWaypoint = 0;

    [Tooltip("Degrees per second. Too low for the walk speed and the NPC circles a waypoint instead of reaching it.")]
    [SerializeField] private float turnSpeed = 240f;

    [Tooltip("Metres from a waypoint at which it counts as reached.")]
    [SerializeField] private float arriveDistance = 0.5f;

    [Tooltip("Seconds to wait at each end of the route, picked at random between the two values.")]
    [SerializeField] private Vector2 pauseSeconds = new Vector2(3f, 10f);

    [Tooltip("Animation speed, picked at random between the two values, so walkers do not move in step. The pack's walk clip covers 1.9 m/s at speed 1, so 0.7 is a 1.3 m/s stroll.")]
    [SerializeField] private Vector2 speedVariation = new Vector2(0.65f, 0.78f);

    private static readonly int Walking = Animator.StringToHash("Walking");

    private Animator animator;
    private int waypoint;
    private int direction = 1;
    private float pauseUntil;

    private void Awake()
    {
        animator = GetComponent<Animator>();
    }

    private void Start()
    {
        if (route == null || route.childCount < 2)
        {
            Debug.LogError($"{name}: NpcWalker needs a route with at least two waypoints.", this);
            enabled = false;
            return;
        }
        animator.applyRootMotion = true;
        animator.speed = Random.Range(speedVariation.x, speedVariation.y);
        waypoint = Mathf.Min(firstWaypoint, route.childCount - 1);
    }

    private void Update()
    {
        bool paused = Time.time < pauseUntil;
        animator.SetBool(Walking, !paused);
        if (paused) return;

        Vector3 toWaypoint = route.GetChild(waypoint).position - transform.position;
        toWaypoint.y = 0f;
        if (toWaypoint.sqrMagnitude < arriveDistance * arriveDistance)
        {
            Arrive();
            return;
        }
        transform.rotation = Quaternion.RotateTowards(
            transform.rotation, Quaternion.LookRotation(toWaypoint), turnSpeed * Time.deltaTime);
    }

    private void Arrive()
    {
        bool atEnd = waypoint == (direction > 0 ? route.childCount - 1 : 0);
        if (atEnd)
        {
            direction = -direction;
            pauseUntil = Time.time + Random.Range(pauseSeconds.x, pauseSeconds.y);
        }
        waypoint += direction;
    }
}
