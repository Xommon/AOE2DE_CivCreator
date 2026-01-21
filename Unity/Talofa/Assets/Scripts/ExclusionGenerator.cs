using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class ExclusionGenerator : MonoBehaviour
{
    public MultiSelectDropdown exclusionDropdown;
    public TMP_Dropdown dropdown;

    public void OnDropdownChange()
    {
        // Clear options
        exclusionDropdown.options.Clear();
        Debug.Log(dropdown.options[dropdown.value].text);

        // Repopulate options
        if (dropdown.options[dropdown.value].text == "Archer-line")
        {
            exclusionDropdown.options.Add("Archer");
            exclusionDropdown.options.Add("Crossbowman");
            exclusionDropdown.options.Add("Arbalester");
        }
        if (dropdown.options[dropdown.value].text == "Skirmishers")
        {
            exclusionDropdown.options.Add("Skirmisher");
            exclusionDropdown.options.Add("Elite Skirmisher");
            exclusionDropdown.options.Add("Imperial Skirmisher");
        }
        if (dropdown.options[dropdown.value].text == "Cavalry archers")
        {
            exclusionDropdown.options.Add("Cavalry archer");
            exclusionDropdown.options.Add("Heavy Cavalry archer");
        }
    }
}
