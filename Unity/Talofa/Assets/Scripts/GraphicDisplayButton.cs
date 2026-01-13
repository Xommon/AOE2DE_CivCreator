using UnityEngine;
using UnityEngine.UI;

public class GraphicDisplayButton : MonoBehaviour
{
    private Image image;
    public int index;
    private GameManager gameManager;
    private Button button;

    private void Update()
    {
        if (image == null)
        {
            image = GetComponent<Image>();
        }

        if (gameManager == null)
        {
            gameManager = Object.FindObjectOfType<GameManager>();
        }

        if (button == null)
        {
            button = GetComponent<Button>();
        }

        // Change the selection
        button.interactable = gameManager.graphicMode != index;
    }

    public void SwitchMode()
    {
        if (gameManager.graphicMode != index)
        {
            // Switch graphic mode
            gameManager.graphicMode = index;

            // Change graphic title
            gameManager.title.text = gameManager.graphicsTitles[index];

            // Repopulate graphic buttons
            gameManager.RepopulateGraphicButtons();
        }
    }
}
