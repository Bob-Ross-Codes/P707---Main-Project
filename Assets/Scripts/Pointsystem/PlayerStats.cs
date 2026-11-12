
using UnityEngine;
using System.Collections;
using UnityEngine.ProBuilder.MeshOperations;

public class PlayerStats : MonoBehaviour
{
    [Header("Playerstats and Categorization")]
    [Tooltip("Current speed of player")]
    public float Playerspeed;
    [Tooltip("Amount of points")]
    public int Playerpoints;
    [Tooltip("How long the player needs to stand still for lowspeed")]
    public float timeThreshold;
    [Tooltip("Threshold between the two types")]
    public int CategorizationDivitionThreshold;
    [Tooltip("Player is classified as a Looker")]
    public bool Lookercategorization;
    [Tooltip("Player is classified as a Cooker")]
    public bool Cookercategorization;

    //Coroutine for 
    private Coroutine speedCoroutine;

    [Header("Playerspeed")]
    public float speed;
    public float smoothing = 5f;
    private Vector3 lastPosition;
    private float smoothSpeed;



    void Start()
    {
        //Find Amount of interest points in scene
        PlayerZoneTrigger[] triggers = FindObjectsByType<PlayerZoneTrigger>(FindObjectsSortMode.None);
        Debug.Log("Number of hit colliders: " + triggers.Length);

        // Give penalty depending of amount of interest points in the scene
        Playerpoints = Playerpoints - triggers.Length;

        // Speed position
        lastPosition = transform.position;
    }

    private void Update()
    {
        speedCoroutine = StartCoroutine(CheckPlayerSpeed());

        if (Playerpoints < CategorizationDivitionThreshold)
        {
            Lookercategorization = true;
            Cookercategorization = false;
        }
        else if (Playerpoints > CategorizationDivitionThreshold)
        {
            Lookercategorization = false;
            Cookercategorization = true;
        }

        // Calculate distance moved this frame
        float distance = Vector3.Distance(
            transform.position,
            lastPosition
        );

        if (distance < 0.001f)
        {
            distance = 0f;
        }

        // Calculate raw speed (units per second)
        float rawSpeed = distance / Time.deltaTime;

        // Smooth the speed to prevent jitter
        smoothSpeed = Mathf.Lerp(
            smoothSpeed,
            rawSpeed,
            Time.deltaTime * smoothing
        );

        speed = Mathf.Max(0f, smoothSpeed);

        // Remember position for next frame
        lastPosition = transform.position;
    }

    IEnumerator CheckPlayerSpeed()
    {
        float timer = 0f;

        while (true)
        {
            if (Playerspeed < 1f)
            {
                timer += Time.deltaTime;

                if (timer >= timeThreshold)
                {
                    OnLowSpeed();
                    timer = 0f;
                }
            }
            else
            {
                timer = 0f;
            }

            yield return null;
        }
    }

    private void OnLowSpeed()
    {
        Debug.Log("Lower speed achieved");
    }
}
