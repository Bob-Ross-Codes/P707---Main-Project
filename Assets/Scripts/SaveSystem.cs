
using UnityEngine;
using System.IO;

[System.Serializable]
public class SaveData
{
    public int value1;
    public int value2;
    public int value3;
    public int value4;
}

public static class SaveSystem
{
    private static string SavePath =>
        Application.persistentDataPath + "/save.json";

    // LOAD ALL DATA
    public static SaveData Load()
    {
        if (File.Exists(SavePath))
        {
            string json = File.ReadAllText(SavePath);
            return JsonUtility.FromJson<SaveData>(json);
        }

        return new SaveData();
    }

    // SAVE ALL DATA
    private static void SaveAll(SaveData data)
    {
        string json = JsonUtility.ToJson(data, true);
        File.WriteAllText(SavePath, json);
    }

    // SAVE INDIVIDUAL VALUES
    public static void SaveStat1(int value)
    {
        SaveData data = Load();
        data.value1 = value;
        SaveAll(data);
    }

    public static void SaveStat2(int value)
    {
        SaveData data = Load();
        data.value2 = value;
        SaveAll(data);
    }

    public static void SaveStat3(int value)
    {
        SaveData data = Load();
        data.value3 = value;
        SaveAll(data);
    }

    public static void SaveStat4(int value)
    {
        SaveData data = Load();
        data.value4 = value;
        SaveAll(data);
    }

    public static void SaveAsNewFile()
    {
        // Load current values
        SaveData data = Load();

        // Convert to JSON
        string json = JsonUtility.ToJson(data, true);

        // Create unique filename using timestamp
        string fileName = "save_" +
            System.DateTime.Now.ToString("yyyy-MM-dd_HHmmss")
            + ".json";

        // Create folder if it doesn't exist
        Directory.CreateDirectory(
            Path.GetDirectoryName(SavePath)
        );

        // Save as a new file
        string newPath = Path.Combine(
            Path.GetDirectoryName(SavePath),
            fileName
        );

        File.WriteAllText(newPath, json);

        Debug.Log("New save created: " + newPath);
    }
}
