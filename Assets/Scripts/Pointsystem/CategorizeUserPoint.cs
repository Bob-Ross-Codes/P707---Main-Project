using UnityEngine;
using System.Collections;

public class CategorizeUserPoint : MonoBehaviour
{
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

    private PlayerStats playerStats;

    private void Start()
    {
        playerStats = FindFirstObjectByType<PlayerStats>();

        if (HasVisitedAgeSection == true)
        {
            playerStats.Playerpoints++;
        }
    }

    //On First Time Enter. Found interest point, gives 1 point subtracted from the penalty. 
    public void GainInteractionPoint()
    {
        playerStats.Playerpoints++;
        HasVisitedInterestpoint = true;
    }

    //On First Time Enter. Check if this current age has been visited
    public void SceneShiftTrigger()
    {
        HasVisitedAgeSection = true;
    }

    //On Player Enter. Visit again bous;
    public void Revisitbsonus()
    {
        if (HasVisitedInterestpoint)
        {
            playerStats.Playerpoints++;
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
            playerStats.Playerpoints--;
            Exitearly = false;
        }
    }

    //The regular 1 point call
    public void DwellTimePoint()
    {
        playerStats.Playerpoints++;
    }


    public void GainReturnPointInterestPoint()
    {
        playerStats.Playerpoints += 2;
    }

    public void GainReturnPointScene()
    {
        playerStats.Playerpoints +=3;
    }
}
