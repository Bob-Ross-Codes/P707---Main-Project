using UnityEngine;
using System.Collections;
using System.Runtime.CompilerServices;
using Unity.VisualScripting;
using System;

public class OldVersion : MonoBehaviour
{
    [Header("Dwelltime point count")]

    [Tooltip("Private Values")]
    [SerializeField]
    private float ScoreMult;
    private bool ScoreMultIsRunning;

    [Tooltip("Time speed for how fast the scoremulitiplier counts up whitin interest point (in sec)")]
    public float ScoreMultTimerLoop;

    [Tooltip("What ScoreMult need to reach to miss penalty when leaving interest point (in sec)")]
    public float ScoreLowPenaltyThreshold;

    [Tooltip("Amount of points lost to penalty")]
    public float Penalty;

    [Tooltip("Time before revisit bonus")]
    public float timer;

    [Header("Penalty/Rewardtriggers")]

    [Tooltip("Player has recieved bonuspoint for revisiting")]
    public bool HasReceivedRevisitBonus;

    [Tooltip("Player have visited the time before")]
    public bool HasVisitedAgeSection;

    [Tooltip("return timer")]
    public int TimerReturn;

    [Tooltip("Cooldown trigger")]
    public bool Cooldown;

    [Header("TestValues")]
    public bool Test;
    private bool Scoremultreset;

    private bool timerRunning = false;

    private PlayerStats playerStats;

    private Coroutine standCoroutine;

    private void Start()
    {
        //Get Playerstats so we can alter points
        playerStats = FindFirstObjectByType<PlayerStats>();
    }

    private void Update()
    {
        if (Test)
        {
            RevisitBonus();
            Test = false;
        }

        if (timerRunning)
        {
            timer += Time.deltaTime;

            if (timer >= TimerReturn)
            {
                timer = TimerReturn;
                timerRunning = false;

                Cooldown = true;
            }
        }
    }

    //On Player Exit. Visit again bous;
    public void RevisitBonus()
    {
        timer = 0f;
        timerRunning = true;
    }

    //On Player Enter. 
    public void Bonuspoint()
    {

    }

    //On Player Exit. cooldown period for when leaving interest point and returning to acctually ge tthe points.
    public void Cooldownperiod()
    {
        //Reset Scoremult for each visit to interestpoint
        Scoremultreset = false;

        if (ScoreMult <= ScoreLowPenaltyThreshold)
        {
            LosePoints(Penalty);
        }

        playerStats.Playerpoints = playerStats.Playerpoints * ScoreMult;

    }

    //While inside colider Event. Dwell cheker.
    public void WithinInterestPoint()
    {
        if (!Scoremultreset)
        {
            ScoreMult = 0.5f;
            Scoremultreset = true;
        }

        if (!ScoreMultIsRunning)
        {
            standCoroutine = StartCoroutine(DwellTimer());
        }
    }

    IEnumerator DwellTimer()
    {
        ScoreMultIsRunning = true;

        while (ScoreMult < 2.0f)
        {
            ScoreMult += 0.01f;
            ScoreMult = Mathf.Min(ScoreMult, 2.0f);

            yield return new WaitForSeconds(ScoreMultTimerLoop);
        }

        ScoreMultIsRunning = false;
    }

    //The regular point gain call
    public void GainPoints(float amountGain)
    {
        playerStats.Playerpoints += amountGain;
    }

    //The regular point loss call
    public void LosePoints(float amountLose)
    {
        playerStats.Playerpoints -= amountLose;
    }
}
