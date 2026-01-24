using UnityEngine;
using UnityEngine.UI;
using TMPro;
using System.IO;
using System.Linq;

public class GameManager : MonoBehaviour
{
    // General
    public GameObject[] tabs;

    // Graphics
    public int graphicMode;
    public Button[] graphicDisplayButtons;
    public Button[] graphicOptionButtons;
    public Transform graphicButtonsHolder;
    private Sprite[] loadedGraphics;
    public TextMeshProUGUI title;
    public string[] graphicsTitles = { "Architecture", "Castle", "Wonder", "Monk", "Monastery", "Trade Cart", "Ship", "King" };

    // Sounds
    public CustomDropdown languageDropdown;

    // Tech tree
    public Color[] techTreeColours;

    public void RepopulateGraphicButtons()
    {
        loadedGraphics = Resources.LoadAll<Sprite>($"Sprites/{graphicsTitles[graphicMode]}/");

        int buttonCount = graphicOptionButtons != null ? graphicOptionButtons.Length : 0;

        for (int i = 0; i < buttonCount; i++)
        {
            bool active = i < loadedGraphics.Length;
            graphicOptionButtons[i].gameObject.SetActive(active);
            if (!active) continue;

            var tmp = graphicOptionButtons[i].GetComponentInChildren<TextMeshProUGUI>();

            string raw = loadedGraphics[i].name;

            int us = raw.IndexOf('_');
            if (us >= 0 && us < raw.Length - 1) raw = raw.Substring(us + 1);

            string label = raw.Replace('_', ' ').Replace('-', ' ').Trim();
            while (label.Contains("  ")) label = label.Replace("  ", " ");

            string[] words = label.Split(' ', System.StringSplitOptions.RemoveEmptyEntries);
            label = "";
            for (int w = 0; w < words.Length; w++)
            {
                string word = words[w];
                if (word.Length > 0)
                    word = char.ToUpperInvariant(word[0]) + (word.Length > 1 ? word.Substring(1).ToLowerInvariant() : "");

                if (w > 0) label += " ";
                label += word;
            }

            tmp.text = label.Replace(" 0", "");
            graphicOptionButtons[i].GetComponent<GraphicOptionButton>().sprite = loadedGraphics[i];
        }
    }

    public void OpenMod()
    {
    }

    // Scan raw .wem files from StreamingAssets/Sounds
    public void ScanSoundsFolder()
    {
        string folderPath = Path.Combine(Application.streamingAssetsPath, "Sounds");

        if (!Directory.Exists(folderPath))
        {
            Debug.LogError("Folder not found: " + folderPath);
            languageDropdown.options = System.Array.Empty<string>();
            return;
        }

        string[] results = Directory.EnumerateFiles(folderPath, "*.wem", SearchOption.TopDirectoryOnly)
            .Select(Path.GetFileNameWithoutExtension)
            .Where(n => !string.IsNullOrWhiteSpace(n))
            .Select(n => n.Split('_')[0])
            .Distinct()
            .OrderBy(s => s)
            .ToArray();

        Debug.Log("Found " + results.Length + " unique prefixes.");
        languageDropdown.options = results;
    }

    public void Start()
    {
        RepopulateGraphicButtons();
        ScanSoundsFolder();
    }

    public void ChangeTab(int index)
    {
        for (int i = 0; i < tabs.Length; i++)
        {
            tabs[i].SetActive(index == i);
        }
    }
}
