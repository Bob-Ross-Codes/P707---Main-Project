using UnityEngine;
using System.Collections;

public class CategorizeUserPoint : MonoBehaviour
{
    [Header("User Point Value")]
    public int UserPointValue = 0;
    public int UserPointPenaltyStart = 2;
    public int UserPointValueStart;

    [Header("PointGain Amounts")]
    public int PointAmount_InterestPoint;
    public int PointAmount_ScenePoint;

    [Header("TestValues")]
    public bool testpoint;

    private Coroutine standCoroutine;

    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        //Find Amount of interest points in scene
        PlayerZoneTrigger[] triggers = FindObjectsByType<PlayerZoneTrigger>(FindObjectsSortMode.None);
        Debug.Log("Number of hit colliders: " + triggers.Length);

        // Give penalty depending of amount of interest points in the scene
        UserPointValueStart = triggers.Length / UserPointPenaltyStart;
        UserPointValue = UserPointValue - UserPointValueStart;

        standCoroutine = StartCoroutine(DwellTimer());
    }

    // Update is called once per frame
    void Update()
    {
        if (testpoint)
        {
            GainInteractionPoint();
            testpoint = false;
        }
    }

    public void GainInteractionPoint()
    {
        UserPointValue++;
        
    }

    IEnumerator DwellTimer()
    {
        int loopCount = 0;
        int maxLoops = 5;

        while (loopCount < maxLoops)
        {
            yield return new WaitForSeconds(10f);

            DwellTimePoint();
            loopCount++;
        }
    }

    public void DwellTimePoint()
    {
        UserPointValue++;
    }


    public void GainReturnPointInterestPoint()
    {
        UserPointValue += 2;
    }

    public void GainReturnPointScene()
    {
        UserPointValue += 3;
    }
}
