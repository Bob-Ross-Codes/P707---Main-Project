
using UnityEngine;
using UnityEngine.UI;

public class AdaptiveGuideController : MonoBehaviour
{
    private enum GuideState
    {
        Idle,
        Waiting,
        Approaching,
        Introducing,
        DetailedInformation
    }

    [Header("Visitor References")]
    [SerializeField] private PlayerAreaTracker playerAreaTracker;
    [SerializeField] private Transform visitorTransform;

    [Header("Guide References")]
    [SerializeField] private GameObject guideCharacter;
    [SerializeField] private Transform guideDestination;

    [Header("Speech Bubble")]
    [Tooltip("The SpeechBubbleCanvas GameObject.")]
    [SerializeField] private GameObject speechBubble;

    [Tooltip("The Text component inside the speech bubble.")]
    [SerializeField] private Text guideText;

    [Header("Timing")]
    [Min(0f)]
    [SerializeField] private float visitorWaitTime = 5f;

    [Min(0f)]
    [SerializeField] private float introductionDuration = 5f;

    [Min(0f)]
    [SerializeField] private float leaveGracePeriod = 2f;

    [Header("Movement")]
    [Min(0.01f)]
    [SerializeField] private float movementSpeed = 1f;

    [Min(0.01f)]
    [SerializeField] private float arrivalDistance = 0.1f;

    [Header("Information")]
    [TextArea(2, 5)]
    [SerializeField]
    private string waitingMessage =
        "Hello! One moment while I come over.";

    [TextArea(2, 5)]
    [SerializeField]
    private string introductionMessage =
        "Welcome! I can tell you more about this exhibit.";

    [TextArea(2, 5)]
    [SerializeField]
    private string detailedMessage =
        "Here is some more detailed information about the exhibit.";

    private GuideState currentState = GuideState.Idle;

    private float stateTimer;
    private float outsideAreaTimer;

    private Vector3 initialGuidePosition;
    private Quaternion initialGuideRotation;

    private bool initialPositionSaved;

    private void Awake()
    {
        if (guideCharacter != null)
        {
            initialGuidePosition = guideCharacter.transform.position;
            initialGuideRotation = guideCharacter.transform.rotation;
            initialPositionSaved = true;
        }
    }

    private void Start()
    {
        if (guideCharacter != null)
        {
            guideCharacter.SetActive(false);
        }

        SetSpeechBubble("");
        currentState = GuideState.Idle;
    }

    private void Update()
    {
        if (!ReferencesAreValid())
        {
            return;
        }

        bool visitorInside = playerAreaTracker.IsInsideArea;

        // Reset the outside-area timer while the visitor is inside.
        if (visitorInside)
        {
            outsideAreaTimer = 0f;
        }
        else
        {
            outsideAreaTimer += Time.deltaTime;

            // Allow a short grace period for position fluctuations.
            if (outsideAreaTimer >= leaveGracePeriod)
            {
                ResetExperience();
                return;
            }
        }

        switch (currentState)
        {
            case GuideState.Idle:
                if (visitorInside)
                {
                    stateTimer = 0f;
                    currentState = GuideState.Waiting;

                    SetSpeechBubble(waitingMessage);
                }
                break;

            case GuideState.Waiting:
                if (visitorInside)
                {
                    stateTimer += Time.deltaTime;

                    if (stateTimer >= visitorWaitTime)
                    {
                        guideCharacter.SetActive(true);

                        currentState = GuideState.Approaching;
                        SetSpeechBubble("");
                    }
                }
                break;

            case GuideState.Approaching:
                MoveGuideToDestination();

                if (HasReachedDestination())
                {
                    currentState = GuideState.Introducing;
                    stateTimer = 0f;

                    SetSpeechBubble(introductionMessage);
                }
                break;

            case GuideState.Introducing:
                stateTimer += Time.deltaTime;

                if (stateTimer >= introductionDuration)
                {
                    currentState = GuideState.DetailedInformation;

                    SetSpeechBubble(detailedMessage);
                }
                break;

            case GuideState.DetailedInformation:
                // Keep the detailed information visible while the
                // visitor remains in the interaction area.
                break;
        }
    }

    private bool ReferencesAreValid()
    {
        if (playerAreaTracker == null ||
            visitorTransform == null ||
            guideCharacter == null ||
            guideDestination == null ||
            speechBubble == null ||
            guideText == null)
        {
            return false;
        }

        return true;
    }

    private void MoveGuideToDestination()
    {
        Vector3 destination = guideDestination.position;

        guideCharacter.transform.position = Vector3.MoveTowards(
            guideCharacter.transform.position,
            destination,
            movementSpeed * Time.deltaTime
        );

        // Rotate the guide toward its destination on the horizontal plane.
        Vector3 direction =
            destination - guideCharacter.transform.position;

        direction.y = 0f;

        if (direction.sqrMagnitude > 0.001f)
        {
            Quaternion targetRotation = Quaternion.LookRotation(direction);

            guideCharacter.transform.rotation = Quaternion.Slerp(
                guideCharacter.transform.rotation,
                targetRotation,
                5f * Time.deltaTime
            );
        }
    }

    private bool HasReachedDestination()
    {
        return Vector3.Distance(
            guideCharacter.transform.position,
            guideDestination.position
        ) <= arrivalDistance;
    }

    private void SetSpeechBubble(string message)
    {
        if (speechBubble == null || guideText == null)
        {
            return;
        }

        bool shouldShow = !string.IsNullOrWhiteSpace(message);

        if (shouldShow)
        {
            guideText.text = message;
        }

        speechBubble.SetActive(shouldShow);
    }

    private void ResetExperience()
    {
        currentState = GuideState.Idle;

        stateTimer = 0f;
        outsideAreaTimer = 0f;

        SetSpeechBubble("");

        if (guideCharacter != null)
        {
            guideCharacter.SetActive(false);

            // Return the guide to its original starting position.
            if (initialPositionSaved)
            {
                guideCharacter.transform.position = initialGuidePosition;
                guideCharacter.transform.rotation = initialGuideRotation;
            }
        }
    }

    private void OnDisable()
    {
        SetSpeechBubble("");

        if (guideCharacter != null)
        {
            guideCharacter.SetActive(false);
        }
    }
}