
using UnityEngine;
using TMPro;
using UnityEngine.SceneManagement;

public class NumberCounter : MonoBehaviour
{
    [Header("Settings")]
    public TextMeshProUGUI counterText;
    public TextMeshProUGUI FVT_text;
    public int currentValue;
    public int targetValue;
    public float duration = 3f;

    [Header("Trigger")]
    public bool testBool = false;

    private bool hastriggered4000;
    private bool hastriggered1620;

    int startValue;
    float timer = 0f;
    bool isCounting = false;
    bool previousTestBool = false;

    void Awake()
    {
        counterText = transform.Find("Canvas/Number").GetComponent<TextMeshProUGUI>();

        FVT_text = transform.Find("Canvas/FVT").GetComponent<TextMeshProUGUI>();
    }

    void Start()
    {
        FVT_text.gameObject.SetActive(true);
        counterText.text = currentValue.ToString();
    }

    void Update()
    {
        if (SceneManager.GetActiveScene().buildIndex == 1 && hastriggered4000 == false)
        {
            targetValue = 4000;
            hastriggered4000 = true;
            hastriggered1620 = false;
            StartCounting();
        }

        if (SceneManager.GetActiveScene().buildIndex == 2 && hastriggered1620 == false)
        {
            targetValue = 1620;
            hastriggered1620 = true;
            hastriggered4000 = false;
            StartCounting();
        }

        // Detect when testBool is enabled
        if (testBool && !previousTestBool)
        {
            StartCounting();
            testBool = false;
        }

        if (currentValue == 4000)
        {
            FVT_text.alpha = Mathf.MoveTowards(
                FVT_text.alpha, 1f, Time.deltaTime * 2f
            );
        }
        else
        {
            FVT_text.alpha = Mathf.MoveTowards(
                FVT_text.alpha, 0f, Time.deltaTime * 2f
            );
        }

        previousTestBool = testBool;

        if (!isCounting)
            return;

        timer += Time.deltaTime;

        float progress = duration <= 0f ? 1f : Mathf.Clamp01(timer / duration);

        currentValue = Mathf.RoundToInt(
            Mathf.Lerp(startValue, targetValue, progress)
        );

        counterText.text = currentValue.ToString();

        if (progress >= 1f)
        {
            currentValue = targetValue;
            counterText.text = currentValue.ToString();
            isCounting = false;
        }
    }

    public void StartCounting()
    {
        startValue = currentValue;
        timer = 0f;
        isCounting = true;
    }
}
