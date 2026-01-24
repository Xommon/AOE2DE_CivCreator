using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class TextCarousel : MonoBehaviour
{
    public Button leftButton;
    public Button rightButton;
    public Image referenceImage;
    public Image referenceImage2;
    public string[] textOptions;
    public Sprite[] spriteOptions;
    public Sprite[] spriteOptions2;
    public Color[] colourOptions;
    public int index = 0;
    public TextMeshProUGUI display;

    private void Update()
    {
        display.text = textOptions[index];
        if (referenceImage != null && spriteOptions.Length > 0)
        {
            referenceImage.sprite = spriteOptions[index];
        }
        if (referenceImage2 != null && spriteOptions2.Length > 0)
        {
            referenceImage2.sprite = spriteOptions2[index];
        }
        if (referenceImage != null && colourOptions.Length > 0)
        {
            referenceImage.color = colourOptions[index];
        }
    }

    public void LeftButton()
    {
        index = (index == 0) ? textOptions.Length-1 : index-1;
    }

    public void RightButton()
    {
        index = (index == textOptions.Length-1) ? 0 : index+1;
    }
}
