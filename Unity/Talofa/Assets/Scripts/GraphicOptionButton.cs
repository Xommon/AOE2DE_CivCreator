using UnityEngine;
using UnityEngine.UI;

public class GraphicOptionButton : MonoBehaviour
{
    public Sprite sprite;
    private GameManager gameManager;

    private void Update()
    {
        if (gameManager == null)
        {
            gameManager = Object.FindObjectOfType<GameManager>();
        }
    }

    public void SetSprite()
    {
        if (sprite != null)
        {
            Image selectedImage = gameManager.graphicDisplayButtons[gameManager.graphicMode].GetComponent<Image>();
            selectedImage.sprite = sprite;
            selectedImage.SetNativeSize();
        }
    }
}
