using UnityEngine;
using System.Collections;

public class CategorizeUserPoint : MonoBehaviour
{
    [Header("User Point Value")]
    [Tooltip("Total amout of UserPoints.")]
    public int UserPointTotalValue;

    [Header("Loop point counts")]
    [Tooltip("Amount of current loops")]
    public int loopCount;
    [Tooltip("Max amount of loops in logic")]
    public int maxLoops;

    [Header("Penalty/Rewardtriggers")]
    public bool Exitearly;
    public bool HasVisitedInterestpoint;
    public bool HasVisitedAgeSection;

    [Header("TestValues")]
    public bool Test;

    private Coroutine standCoroutine;

    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        //Find Amount of interest points in scene
        PlayerZoneTrigger[] triggers = FindObjectsByType<PlayerZoneTrigger>(FindObjectsSortMode.None);
        Debug.Log("Number of hit colliders: " + triggers.Length);

        // Give penalty depending of amount of interest points in the scene
        UserPointTotalValue = UserPointTotalValue - triggers.Length;
    }

    //On First Time Enter. Found interest point, gives 1 point subtracted from the penalty. 
    public void GainInteractionPoint()
    {
        UserPointTotalValue++;
        HasVisitedInterestpoint = true;
    }

    //On First Time Enter. Check if this current age has been visited
    public void SceneShiftTrigger()
    {

    }

    //On Player Enter. Visit again bous;
    public void Revisitbsonus()
    {
        if (HasVisitedInterestpoint)
        {
            UserPointTotalValue++;
        } 
    }
    

    

    //While inside colider Event. Dwell cheker.
    public void WithinInterestPoint()
    {
        standCoroutine = StartCoroutine(DwellTimer());
    }

    IEnumerator DwellTimer()
    {
        while (loopCount < maxLoops)
        {
            //Alter this if another penalty is required
            int EarlyExitLoopThreshhold = 0;

            if (loopCount < EarlyExitLoopThreshhold)
            {
                Exitearly = true;
            }
            else if (loopCount > EarlyExitLoopThreshhold)
            {
                Exitearly = false;
            }
                yield return new WaitForSeconds(10f);

            DwellTimePoint();
            loopCount++;
        }
    }

    //OnplayerExit. Penalty check
    public void OnexitPenalty()
    {
        if (Exitearly ==true)
        {
            UserPointTotalValue--;
            Exitearly = false;
        }
    }

    //The regular 1 point call
    public void DwellTimePoint()
    {
        UserPointTotalValue++;
    }


    public void GainReturnPointInterestPoint()
    {
        UserPointTotalValue += 2;
    }

    public void GainReturnPointScene()
    {
        UserPointTotalValue += 3;
    }
}
