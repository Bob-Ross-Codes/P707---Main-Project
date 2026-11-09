
using UnityEngine;
using System.Collections;

public class PlayerStats : MonoBehaviour
{
    public float Playerspeed;
    public float timeThreshold;

    public int Playerpoints; 

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
