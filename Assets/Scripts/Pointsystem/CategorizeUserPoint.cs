using UnityEngine;
using System.Collections;

public class CategorizeUserPoint : MonoBehaviour
{
    [Header("Dwelltime point count")]
    [Tooltip("Amount of current loops")]
    public int loopCount;
    [Tooltip("Max amount of loops in logic")]
    public int maxLoops;
    [Tooltip("Loops aqquired before penalty")]
    public int EarlyExitThreshhold;
 
    [Header("Penalty/Rewardtriggers")]
    [Tooltip("Player left interestpoint early")]
    public bool Exitearly;
    [Tooltip("Player have visited current interestpoint")]
    public bool HasVisitedInterestpoint;
    [Tooltip("Player has recieved bonuspoint for revisiting")]
    public bool HasReceivedRevisitBonus;
    [Tooltip("Player have visited the time before")]
    public bool HasVisitedAgeSection;

    [Header("TestValues")]
    public bool Test;

    private Coroutine standCoroutine;

    private PlayerStats playerStats;

    private void Start()
    {
        playerStats = FindFirstObjectByType<PlayerStats>();
    }

    //On First Time Enter. Found interest point, gives 1 point subtracted from the penalty. 
    public void GainInteractionPoint()
    {
        GainPoints(1);
        HasVisitedInterestpoint = true;
    }

    //On First Time Enter. Check if this current age has been visited
    public void SceneShiftTrigger()
    {
        HasVisitedAgeSection = true;
    }

    //On Player Enter. Visit again bous;
    public void RevisitBonus()
    {
        if (HasVisitedInterestpoint && !HasReceivedRevisitBonus)
        {
            GainPoints(1);
            HasReceivedRevisitBonus = true;
        }
    }

    //On Player Exit. cooldown period for when leaving interest point and returning to acctually ge tthe points.
    public void Cooldownperiod()
    {
  
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
            if (loopCount < EarlyExitThreshhold)
            {
                Exitearly = true;
            }
            else if (loopCount > EarlyExitThreshhold)
            {
                Exitearly = false;
            }
                yield return new WaitForSeconds(10f);

            GainPoints(1);
            loopCount++;
        }
    }

    //OnplayerExit. Penalty check
    public void OnexitPenalty()
    {
        if (Exitearly ==true)
        {
            LosePoints(1);
            Exitearly = false;
        }
    }

    //The regular point gain call
    public void GainPoints(int amountGain)
    {
        playerStats.Playerpoints += amountGain;
    }

    //The regular point loss call
    public void LosePoints(int amountLose)
    {
        playerStats.Playerpoints -= amountLose;
    }
}
