
using System.Collections;
using UnityEngine;
using UnityEngine.ProBuilder.MeshOperations;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;
using UnityEngine.SocialPlatforms.Impl;
using static UnityEngine.Rendering.HighDefinition.ScalableSettingLevelParameter;

public class PlayerStats : MonoBehaviour
{
    [Header("Playerstats and Categorization")]

    [Tooltip("Amount of points")]
    public float Playerpoints;

    [Tooltip("Bonus points from scene to scene")]
    public float PlayerpointsSceneBonus = 0;

    [Tooltip("Bonus point from scene divition")]
    public float PlayerpointsSceneDivition = 2;

    [Tooltip("How long the player needs to stand still for lowspeed")]
    public float timeThreshold;

    [Tooltip("Threshold between the two types")]
    public float CategorizationDivitionThreshold;

    [Tooltip("Player is classified as a Looker")]
    public bool Lookercategorization;

    [Tooltip("Player is classified as a Cooker")]
    public bool Cookercategorization;

    //Coroutine for 
    private Coroutine speedCoroutine;

    public bool test;
    private bool FirstTimeEnterScene2 = false;
    private bool FirstTimeEnterScene3 = false;
    private float PlayerpointsZero = 0;

    [Header("Playerspeed")]
    public float speed;
    public float smoothing = 5f;
    private Vector3 lastPosition;
    private float smoothSpeed;
    public bool isLowSpeed;
    private int previousSceneIndex;

    private void Awake()
    {
        // Remember the scene we start in
        previousSceneIndex = SceneManager.GetActiveScene().buildIndex;

        // Keep this manager alive between scenes
        DontDestroyOnLoad(gameObject);
    }

    void Start()
    {
        // Speed position
        lastPosition = transform.position;

    }

    void OnEnable()
    {
        SceneManager.sceneLoaded += OnSceneLoaded;
    }

    void OnDisable()
    {
        SceneManager.sceneLoaded -= OnSceneLoaded;
    }

    void OnSceneLoaded(Scene scene, LoadSceneMode mode)
    {
        int currentSceneIndex = scene.buildIndex;

        // Scene 1 -> Scene 2
        if (previousSceneIndex == 0 && currentSceneIndex == 1)
        {
            Scene2Forward();
        }

        // Scene 2 -> Scene 3
        else if (previousSceneIndex == 1 && currentSceneIndex == 2)
        {
            Scene3Forward();
        }

        // Scene 3 -> Scene 2
        else if (previousSceneIndex == 2 && currentSceneIndex == 1)
        {
            Scene2Backward();
        }

        // Scene 2 -> Scene 1
        else if (previousSceneIndex == 1 && currentSceneIndex == 0)
        {
            Scene1Backward();
        }

        previousSceneIndex = currentSceneIndex;
    }

    void Pointbonuscalculation()
    {
        PlayerpointsSceneBonus = Playerpoints / PlayerpointsSceneDivition;
    }

    void Scene2Forward()
    {
        Debug.Log("State: Scene 2 - Forward");

        //Save stats from scene 1
        SaveSystem.SaveStat1(Playerpoints);

        //Subtract point bonus or load stats
        if (FirstTimeEnterScene2 == true)
        {
            Playerpoints = SaveSystem.Load().value2;
        }
        else if (FirstTimeEnterScene2 == false)
        {
            //First time in scene call (otherwise load the value)
            Pointbonuscalculation();
            Playerpoints = PlayerpointsZero + PlayerpointsSceneBonus;
            FirstTimeEnterScene2 = true;
        }

        //Show save path 
        Debug.Log(Application.persistentDataPath + "/save.json");

    }

    void Scene3Forward()
    {
        Debug.Log("State: Scene 2 - Forward");

        //Save stats from scene 1
        SaveSystem.SaveStat2(Playerpoints);

        //Subtract point bonus or load stats
        if (FirstTimeEnterScene3 == true)
        {
            Playerpoints = SaveSystem.Load().value3;
        }
        else if (FirstTimeEnterScene3 == false)
        {
            //First time in scene call (otherwise load the value)
            Pointbonuscalculation();
            Playerpoints = PlayerpointsZero + PlayerpointsSceneBonus;
            FirstTimeEnterScene3 = true;
        }

        //Show save path 
        Debug.Log(Application.persistentDataPath + "/save.json");

    }

    void Scene2Backward()
    {
        Debug.Log("State: Scene 2 - Backward");
        Playerpoints = SaveSystem.Load().value2;
        //Show save path 
        Debug.Log(Application.persistentDataPath + "/save.json");
        
    }

    void Scene1Backward()
    {
        Debug.Log("State: Scene 2 - Backward");
        Playerpoints = SaveSystem.Load().value1;
        //Show save path 
        Debug.Log(Application.persistentDataPath + "/save.json");
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

        //ALL BELOW IS PLAYERSPEED
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
