using UnityEngine;
using UnityEngine.SceneManagement;

public class CategorizeUserPoint : MonoBehaviour
{
    [System.Serializable]
    public class ScenePointState
    {
        [Header("Scene State")]

        public float ScoreMult = 0.5f;

        public float timer;

        public bool HasReceivedRevisitBonus;

        public bool HasVisitedAgeSection;

        public bool Cooldown;

        [Header("Private Runtime Values")]

        public bool Scoremultreset;

        public bool ScoreMultIsRunning;

        public bool timerRunning;

        public float DwellTimer;

        public bool IsInside;
    }

    [Header("Scene Setup")]

    [Tooltip("Scene names must match the actual Unity scene names")]
    public string[] SceneNames;

    [Tooltip("One separate state for each scene")]
    public ScenePointState[] SceneStates;

    private ScenePointState CurrentState;

    private int CurrentSceneIndex = -1;

    [Header("Dwelltime point count")]

    public float ScoreMultTimerLoop = 1f;

    public float ScoreLowPenaltyThreshold = 0.6f;

    public float Penalty = 5f;

    [Header("Revisit Bonus")]

    public float timer;

    public int TimerReturn = 10;

    [Header("Test Values")]

    public bool Test;

    private PlayerStats playerStats;

    private void Start()
    {
        playerStats = FindFirstObjectByType<PlayerStats>();

        UpdateSceneState();
    }

    private void Update()
    {
        UpdateSceneState();

        if (CurrentState == null)
            return;

        if (Test)
        {
            RevisitBonus();
            Test = false;
        }

        // Revisit timer
        if (CurrentState.timerRunning)
        {
            CurrentState.timer += Time.deltaTime;

            if (CurrentState.timer >= TimerReturn)
            {
                CurrentState.timer = TimerReturn;

                CurrentState.timerRunning = false;

                CurrentState.Cooldown = true;
            }
        }

        // Dwell timer
        if (CurrentState.IsInside)
        {
            UpdateDwellTimer();
        }
    }

    // Finds which scene we are currently in
    private void UpdateSceneState()
    {
        string sceneName = SceneManager.GetActiveScene().name;

        int sceneIndex = -1;

        for (int i = 0; i < SceneNames.Length; i++)
        {
            if (SceneNames[i] == sceneName)
            {
                sceneIndex = i;
                break;
            }
        }

        // Scene not found in our array
        if (sceneIndex == -1)
        {
            CurrentState = null;
            return;
        }

        // No need to update if we are already using the correct scene
        if (sceneIndex == CurrentSceneIndex)
            return;

        CurrentSceneIndex = sceneIndex;

        CurrentState = SceneStates[sceneIndex];

        Debug.Log(gameObject.name + " is now using state for scene: " + sceneName);
    }

    // On Player Exit - starts revisit timer
    public void RevisitBonus()
    {
        if (CurrentState == null)
            return;

        CurrentState.timer = 0f;

        CurrentState.timerRunning = true;

        CurrentState.Cooldown = false;
    }

    // On Player Enter
    public void Bonuspoint()
    {
        // Your bonus logic goes here
    }

    // On Player Exit
    public void Cooldownperiod()
    {
        if (CurrentState == null)
            return;

        // Reset multiplier for the next visit
        CurrentState.Scoremultreset = false;

        CurrentState.ScoreMultIsRunning = false;

        CurrentState.IsInside = false;

        CurrentState.DwellTimer = 0f;

        // Penalty
        if (CurrentState.ScoreMult <= ScoreLowPenaltyThreshold)
        {
            LosePoints(Penalty);
        }

        // Apply multiplier
        playerStats.Playerpoints *= CurrentState.ScoreMult;
    }

    // While inside collider
    public void WithinInterestPoint()
    {
        if (CurrentState == null)
            return;

        CurrentState.IsInside = true;

        if (!CurrentState.Scoremultreset)
        {
            CurrentState.ScoreMult = 0.5f;

            CurrentState.Scoremultreset = true;

            CurrentState.DwellTimer = 0f;
        }
    }

    // Dwell timer
    private void UpdateDwellTimer()
    {
        if (CurrentState.ScoreMult >= 2.0f)
            return;

        CurrentState.DwellTimer += Time.deltaTime;

        if (CurrentState.DwellTimer >= ScoreMultTimerLoop)
        {
            CurrentState.DwellTimer = 0f;

            CurrentState.ScoreMult += 0.01f;

            CurrentState.ScoreMult = Mathf.Min(
                CurrentState.ScoreMult,
                2.0f
            );
        }
    }

    // Regular point gain
    public void GainPoints(float amountGain)
    {
        playerStats.Playerpoints += amountGain;
    }

    // Regular point loss
    public void LosePoints(float amountLose)
    {
        playerStats.Playerpoints -= amountLose;
    }
}