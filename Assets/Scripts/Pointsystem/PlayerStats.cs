
using System.Collections;
using UnityEngine;
using UnityEngine.ProBuilder.MeshOperations;
using UnityEngine.SceneManagement;
using UnityEngine.SocialPlatforms.Impl;
using static UnityEngine.Rendering.HighDefinition.ScalableSettingLevelParameter;

public class PlayerStats : MonoBehaviour
{
    [Header("Playerstats and Categorization")]
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

    public bool test;

    [Header("Playerspeed")]
    public float speed;
    public float smoothing = 5f;
    private Vector3 lastPosition;
    private float smoothSpeed;
    public bool isLowSpeed;



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

        // Calculate raw speed
        float rawSpeed = distance / Time.deltaTime;

        // Smooth the speed
        smoothSpeed = Mathf.Lerp(
            smoothSpeed,
            rawSpeed,
            Time.deltaTime * smoothing
        );

        // Apply deadzone
        if (smoothSpeed < 0.001f)
        {
            smoothSpeed = 0f;
        }

        speed = Mathf.Max(0f, smoothSpeed);

        // Remember position
        lastPosition = transform.position;

        //Savepoints depending on scene
        string currentScene = SceneManager.GetActiveScene().name;

        if (test == true)
        {
            //SavePoint
            SaveSystem.SaveStat1(Playerpoints);
            //Save WHOLE FILE AS NEW
            SaveSystem.SaveAsNewFile();
            //Show path
            Debug.Log(Application.persistentDataPath + "/save.json");
            test = false;
        }

        if (currentScene == "MainMenu")
        {
            SaveSystem.SaveStat1(Playerpoints);
        }
        else if (currentScene == "Level1")
        {
            SaveSystem.SaveStat2(Playerpoints);
        }
        else if (currentScene == "Level2")
        {
            SaveSystem.SaveStat3(Playerpoints);
        }
    }
    IEnumerator CheckPlayerSpeed()
    {
        float timer = 0f;
        
        while (true)
        {
            if (speed < 1f)
            {
                timer += Time.deltaTime;

                if (timer >= timeThreshold && !isLowSpeed)
                {
                    isLowSpeed = true;
                    OnLowSpeed();
                }
            }
            else
            {
                timer = 0f;

                if (isLowSpeed)
                {
                    isLowSpeed = false;
                    OnSpeedRecovered();
                }
            }

            yield return null;
        }
    }

    private void OnLowSpeed()
    {
        Debug.Log("Lower speed achieved");
    }

    private void OnSpeedRecovered()
    {
        Debug.Log("Speed recovered");
    }
}
