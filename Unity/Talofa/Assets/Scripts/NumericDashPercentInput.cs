using TMPro;
using UnityEngine;

[RequireComponent(typeof(TMP_InputField))]
public class NumericDashPercentInput : MonoBehaviour
{
    void Awake()
    {
        var input = GetComponent<TMP_InputField>();
        input.onValidateInput += Validate;
    }

    private char Validate(string text, int charIndex, char addedChar)
    {
        if (char.IsDigit(addedChar)) return addedChar;

        if (addedChar == '-' && !text.Contains("-") && charIndex == 0)
            return addedChar; // only at start, only once

        if (addedChar == '%' && !text.Contains("%"))
            return addedChar; // only once

        return '\0';
    }
}
