
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

    

    void Start()
    {
        //Find Amount of interest points in scene
        PlayerZoneTrigger[] triggers = FindObjectsByType<PlayerZoneTrigger>(FindObjectsSortMode.None);
        Debug.Log("Number of hit colliders: " + triggers.Length);

        // Give penalty depending of amount of interest points in the scene
        Playerpoints = Playerpoints - triggers.Length;
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
