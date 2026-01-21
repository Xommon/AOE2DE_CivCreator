using System;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

public class MultiSelectDropdown : MonoBehaviour
{
    [Header("Wiring")]
    public Button headerButton;
    public TMP_Text headerLabel;

    public RectTransform panel;          // dropdown list panel
    public Toggle togglePrefab;
    public Transform toggleParent;

    [Header("Modal overlay (blocks clicks + closes on outside click)")]
    public GameObject overlay;           // full-screen panel GameObject (inactive by default)
    public Button overlayButton;         // Button on the overlay (clicking it closes)

    [Header("Options")]
    public List<string> options = new List<string>();

    // NEW: subscribe to this from other scripts to know when selection changes
    public event Action<List<int>, List<string>> OnSelectionChanged;

    private readonly HashSet<int> selected = new HashSet<int>();

    void Awake()
    {
        if (overlay != null) overlay.SetActive(false);
        if (panel != null) panel.gameObject.SetActive(false);

        if (headerButton != null)
            headerButton.onClick.AddListener(ToggleDropdown);

        if (overlayButton != null)
            overlayButton.onClick.AddListener(CloseDropdown);

        Build();
        UpdateHeader();
        NotifySelectionChanged(); // NEW
    }

    public void ToggleDropdown()
    {
        bool opening = panel != null && !panel.gameObject.activeSelf;
        if (opening) OpenDropdown();
        else CloseDropdown();
    }

    public void OpenDropdown()
    {
        if (overlay != null) overlay.SetActive(true);
        if (panel != null) panel.gameObject.SetActive(true);

        // overlay behind panel
        if (overlay != null) overlay.transform.SetAsLastSibling();
        if (panel != null) panel.transform.SetAsLastSibling();
    }

    public void CloseDropdown()
    {
        if (panel != null) panel.gameObject.SetActive(false);
        if (overlay != null) overlay.SetActive(false);
    }

    public void Build()
    {
        for (int i = toggleParent.childCount - 1; i >= 0; i--)
            Destroy(toggleParent.GetChild(i).gameObject);

        selected.Clear();

        for (int i = 0; i < options.Count; i++)
        {
            int idx = i;
            Toggle t = Instantiate(togglePrefab, toggleParent);
            t.isOn = false;

            var tmp = t.GetComponentInChildren<TMP_Text>();
            if (tmp != null) tmp.text = options[i];

            t.onValueChanged.AddListener(on =>
            {
                if (on) selected.Add(idx);
                else selected.Remove(idx);

                UpdateHeader();
                NotifySelectionChanged(); // NEW: actively updates whenever added/removed
            });
        }
    }

    private void UpdateHeader()
    {
        if (headerLabel == null) return;

        if (selected.Count == 0) { headerLabel.text = ""; return; }

        if (selected.Count == 1)
        {
            foreach (int i in selected) { headerLabel.text = options[i]; break; }
            return;
        }

        var idxs = new List<int>(selected);
        idxs.Sort();

        string acronym = "";
        foreach (int i in idxs)
        {
            string opt = options[i];
            if (!string.IsNullOrWhiteSpace(opt))
                acronym += char.ToUpperInvariant(opt.Trim()[0]);
        }

        headerLabel.text = acronym + " Ages";
    }

    // NEW: helper to send selection state out
    private void NotifySelectionChanged()
    {
        if (OnSelectionChanged == null) return;

        var idxs = new List<int>(selected);
        idxs.Sort();

        var names = new List<string>(idxs.Count);
        for (int i = 0; i < idxs.Count; i++)
            names.Add(options[idxs[i]]);

        OnSelectionChanged.Invoke(idxs, names);
    }

    // Optional helpers other scripts can call:
    public List<int> GetSelectedIndices()
    {
        var idxs = new List<int>(selected);
        idxs.Sort();
        return idxs;
    }

    public List<string> GetSelectedOptions()
    {
        var idxs = GetSelectedIndices();
        var list = new List<string>(idxs.Count);
        for (int i = 0; i < idxs.Count; i++)
            list.Add(options[idxs[i]]);
        return list;
    }
}
