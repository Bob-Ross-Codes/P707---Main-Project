using UnityEngine;
using UnityEngine.SceneManagement;

public class CategorizeUserPoint : MonoBehaviour
{
    // This class stores all the variables that belong to ONE specific scene.
    [System.Serializable]
    public class ScenePointState
    {
        [Header("Scene State")]

        // The current score multiplier for this element, Starts at 0.5 and can increase up to 2.0.
        public float ScoreMult = 0.5f;

        // The revisit timer for THIS scene in this element.
        public float timer;

        // Has the player already received the revisit bonus?
        public bool HasReceivedRevisitBonus = false;

        // Has the player already visited the Interestpoint?
        public bool HasVisited = false;

        // Is this scene currently in cooldown?
        public bool Cooldown;

        [Header("Private Runtime Values")]

        // Used to make sure the multiplier is only reset
        // once when entering an interest point.
        public bool Scoremultreset;

        // Can be used to track whether the multiplier is running.
        public bool ScoreMultIsRunning;

        // Determines whether the revisit timer is currently counting.
        public bool timerRunning;

        // Tracks how long the player has been inside the
        // interest point before the multiplier increases.
        public float DwellTimer;

        // Is the player currently inside the interest point?
        public bool IsInside;
    }

    [Header("Scene Setup")]

    // Names of the scenes that this script should recognize.
    public string[] SceneNames;


    // Stores one ScenePointState for every scene.
    public ScenePointState[] SceneStates;


    // A reference to the state belonging to the scene we are CURRENTLY inside.
    private ScenePointState CurrentState;

    // Stores the index of the scene we are currently using. (-1 is no scene)
    private int CurrentSceneIndex = -1;

    [Header("Dwelltime point count")]

    // How often the multiplier increases.( 1 = 0.01)
    public float ScoreMultTimerLoop = 1f;

    // If the multiplier is equal to or below this value when the player exits, a penalty is applied.
    public float ScoreLowPenaltyThreshold = 0.6f;

    // How many points the player loses if the multiplier is below the penalty threshold when exiting.
    public float Penalty;

    // How many points the player gains when entering an InterestPoint
    public float EnterBonus;

    [Header("Revisit Bonus")]
    // A separate public timer variable.
    // (This timer is not the same as the timer stored inside ScenePointState)
    public float timer;

    public float RevisitPoints;

    // How long the revisit timer should count before finishing.
    public int TimerReturn = 30;

    [Header("Test Values")]
    public bool Test;

    private PlayerStats playerStats;

    private void Start()
    {
        playerStats = FindFirstObjectByType<PlayerStats>();

        // Find out which scene we are currently in.
        UpdateSceneState();
    }

    private void Update()
    {
        // Check which scene we are currently in.
        UpdateSceneState();

        // Check if scene is real
        if (CurrentState == null)
            return;

        if (CurrentState.timerRunning)
        {
            // Increase time
            CurrentState.timer += Time.deltaTime;

            if (CurrentState.timer >= TimerReturn)
            {
                // Make sure the timer doesn't go above max time
                CurrentState.timer = TimerReturn;

                // Stop the timer.
                CurrentState.timerRunning = false;

                // Mark this scene/trigger as being in cooldown.
                CurrentState.Cooldown = true;
            }
        }

        // Only run the dwell timer if the player is currently inside the interest point.
        if (CurrentState.IsInside)
        {
            UpdateDwellTimer();
        }

    }

    //Find current scene
    private void UpdateSceneState()
    {
        // Get the name of the scene currently loaded in Unity.
        string sceneName = SceneManager.GetActiveScene().name;

        // Scene check
        int sceneIndex = -1;

        // Go through all scene names in array
        for (int i = 0; i < SceneNames.Length; i++)
        {
            // Compare the current scene name with the scene names in our array.
            if (SceneNames[i] == sceneName)
            {
                // Match found then Store the index of the matching scene.
                sceneIndex = i;
                break;
            }
        }

        // If the scene isn't in our SceneNames array,no state  
        if (sceneIndex == -1)
        {
            // Clear the current state.
            CurrentState = null;

            // Stop the function here.
            return;
        }

        // Statecheck
        if (sceneIndex == CurrentSceneIndex)
            return;

        // Switch CurrentState to the state belonging to the new scene in array.
        CurrentState = SceneStates[sceneIndex];

        // Store the index of the new active scene.
        CurrentSceneIndex = sceneIndex;


        // Switch CurrentState to the state belonging to the new scene in array.
        CurrentState = SceneStates[sceneIndex];

        // Print a message of what state
        Debug.Log(gameObject.name + " is now using state for scene: " + sceneName);
    }

    //Function first time a scene is entered minus playerpoints from the Enterbonus Minus the amount of states in each scene (3)
    private void FirstTimeSceneEnter()
    {
        playerStats.Playerpoints = playerStats.Playerpoints - (EnterBonus * 3);
    }

    //On exit
    public void RevisitBonus()
    {
        // No valid scene state, no timer
        if (CurrentState == null)
            return;

        // Reset the timer to 0
        CurrentState.timer = 0f;

        // Start the timer.
        CurrentState.timerRunning = true;

        // Remove the cooldown state.
        CurrentState.Cooldown = false;
    }

    // On Exit.
    public void Cooldownperiod()
    {
        float Scoremulpoint;

        // no valid scene state, then stop the function.
        if (CurrentState == null)
            return;

        // reset multiplier
        CurrentState.Scoremultreset = false;

        // Stop the multiplier-running flag.
        CurrentState.ScoreMultIsRunning = false;

        // Player is no longer inside
        CurrentState.IsInside = false;


        // Reset dwell timer
        CurrentState.DwellTimer = 0f;

        //Penalty if score is low
        if (CurrentState.ScoreMult <= ScoreLowPenaltyThreshold)
        {
            // Subtract the global penalty amount from the player's points.
            LosePoints(Penalty);
            // Subtract the scoremult from the points also
            Scoremulpoint = -CurrentState.ScoreMult;
        }
        else
        {
            // Calculation of points given if over penalty
            Scoremulpoint = CurrentState.ScoreMult;
        }

        //apply multiplierpoint to current points
        playerStats.Playerpoints += CurrentState.ScoreMult;
    }

    //On player enter
    public void WithinInterestPoint()
    {
        // If no scene state exists, stop.
        if (CurrentState == null)
            return;

        if (CurrentState.HasVisited == false)
        {
            GainPoints(EnterBonus);
            CurrentState.HasVisited = true;
        }
        

        // Mark that the player is currently inside the interest point.
        CurrentState.IsInside = true;

        if (!CurrentState.Scoremultreset)
        {
            // Set the multiplier back to its starting value.
            CurrentState.ScoreMult = 0.5f;

            // Mark that the multiplier has now been reset.
            CurrentState.Scoremultreset = true;

            // Reset the dwell timer.
            CurrentState.DwellTimer = 0f;
        }

        //If the cooldown has expired and they revisit gain points
        if (CurrentState.Cooldown == true && CurrentState.HasReceivedRevisitBonus == false)
        {
            GainPoints(RevisitPoints);
            CurrentState.HasReceivedRevisitBonus = true;
        }
    }

    private void UpdateDwellTimer()
    {
        //Stop scoremultiplier at 2 if reached
        if (CurrentState.ScoreMult >= 2.0f)
            return;

        // Count up
        CurrentState.DwellTimer += Time.deltaTime;
        if (CurrentState.DwellTimer >= ScoreMultTimerLoop)
        {

            // This starts counting towards the next increase.
            CurrentState.DwellTimer = 0f;

            // Increase the multiplier by 0.01.
            CurrentState.ScoreMult += 0.01f;

            // Make sure the multiplier never exceeds 2.0.
            CurrentState.ScoreMult = Mathf.Min(
                CurrentState.ScoreMult,
                2.0f
            );
        }
    }

    //Gain x amount of points
    public void GainPoints(float amountGain)
    {
        playerStats.Playerpoints += amountGain;
    }

    //Lose x amount of points
    public void LosePoints(float amountLose)
    {
        playerStats.Playerpoints -= amountLose;
    }
}