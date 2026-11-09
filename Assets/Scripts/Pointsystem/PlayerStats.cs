
using UnityEngine;
using System.Collections;

public class PlayerStats : MonoBehaviour
{
    public float Playerspeed;
    public float timeThreshold;

    private Coroutine speedCoroutine;

    void Start()
    {
        //Playerspeed = Hvad end speed er
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
