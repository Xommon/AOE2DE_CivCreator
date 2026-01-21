using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class GameManager : MonoBehaviour
{
    // Graphics
    public int graphicMode;
    public Button[] graphicDisplayButtons;
    public Button[] graphicOptionButtons;
    public Transform graphicButtonsHolder;
    private Sprite[] loadedGraphics;
    public TextMeshProUGUI title;
    public string[] graphicsTitles = {"Architecture", "Castle", "Wonder", "Monk", "Monastery", "Trade Cart", "Ship", "King"};

    public void RepopulateGraphicButtons()
    {
        // Load graphics
        loadedGraphics = Resources.LoadAll<Sprite>($"Sprites/{graphicsTitles[graphicMode]}/");

        for (int i = 0; i < 100; i++)
        {
            graphicOptionButtons[i].gameObject.SetActive(i < loadedGraphics.Length);

            if (graphicOptionButtons[i].gameObject.activeInHierarchy)
            {
                // Create button label from sprite name
                var tmp = graphicOptionButtons[i].GetComponentInChildren<TextMeshProUGUI>();

                // Example input: "trade-cart_elite" / "unit_trade-cart" etc.
                string raw = loadedGraphics[i].name;

                // If you want to drop anything before the first underscore, uncomment:
                int us = raw.IndexOf('_');
                if (us >= 0 && us < raw.Length - 1) raw = raw.Substring(us + 1);

                // Turn separators into spaces
                string label = raw.Replace('_', ' ').Replace('-', ' ').Trim();

                // Collapse multiple spaces
                while (label.Contains("  ")) label = label.Replace("  ", " ");

                // Title-case each word safely
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

                // Load sprite into each graphic option button
                graphicOptionButtons[i].GetComponent<GraphicOptionButton>().sprite = loadedGraphics[i];
            }
        }
    }

    public void Start()
    {
        RepopulateGraphicButtons();
    }
}
