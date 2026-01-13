using UnityEngine;
using TMPro;
using UnityEngine.UI;

[ExecuteAlways]
public class ButtonDim : MonoBehaviour
{
    public TextMeshProUGUI text;
    public Image icon;
    private Button button;
    private Dropdown dropdown;

    void Update()
    {
        if (button == null)
        {
            button = GetComponent<Button>();
        }
        if (dropdown == null)
        {
            dropdown = GetComponent<Dropdown>();
        }

        // Change colour of text and icon
        if (button != null)
        {
            if (text != null)
                text.color = (button.interactable) ? Color.white : Color.grey;

            if (icon != null)
                icon.color = (button.interactable) ? new Color(1, 0.8664268f, 0, 1) : new Color(0.5f, 0.5f, 0.2f, 1);
        }
        else if (dropdown != null)
        {
            if (text != null)
                text.color = (dropdown.interactable) ? Color.white : Color.grey;
            print(text.text);

            if (icon != null)
                icon.color = (dropdown.interactable) ? new Color(1, 0.8664268f, 0, 1) : new Color(0.5f, 0.5f, 0.2f, 1);
        }
    }
}
