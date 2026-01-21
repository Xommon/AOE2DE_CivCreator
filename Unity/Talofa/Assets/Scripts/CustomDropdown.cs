using System;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

public class CustomDropdown : MonoBehaviour
{
    [Header("Mode")]
    public bool multiChoice = false;

    [Header("Wiring")]
    public Button headerButton;
    public TMP_Text headerLabel;

    public RectTransform panel;          // dropdown list panel
    public GameObject overlay;           // full-screen overlay (inactive by default)
    public Button overlayButton;         // button on overlay (click outside to close)

    [Header("Option UI")]
    public Toggle togglePrefab;          // template toggle (can be prefab asset OR inactive scene object)
    public Transform toggleParent;       // where toggles are created

    [Header("Options (auto rebuilds when changed)")]
    [SerializeField] public string[] options = Array.Empty<string>();

    // Single-choice state
    [SerializeField] private int selectedIndex = -1;

    // Multi-choice state
    private readonly HashSet<int> selectedSet = new HashSet<int>();

    // Internals
    private readonly List<Toggle> builtToggles = new List<Toggle>();
    private ToggleGroup singleGroup;
    private int optionsHash;

    void Awake()
    {
        if (overlay != null) overlay.SetActive(false);
        if (panel != null) panel.gameObject.SetActive(false);

        if (headerButton != null) headerButton.onClick.AddListener(ToggleDropdown);
        if (overlayButton != null) overlayButton.onClick.AddListener(CloseDropdown);

        Rebuild(force: true);
        UpdateHeader();
    }

    void OnEnable()
    {
        // Editor + playmode safety
        Rebuild(force: true);
        UpdateHeader();
    }

#if UNITY_EDITOR
    void OnValidate()
    {
        // Automatically rebuild in-editor when you edit the options array or toggle multiChoice
        if (!UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode)
        {
            Rebuild(force: true);
            UpdateHeader();
        }
    }
#endif

    void Update()
    {
        // Auto rebuild at runtime if someone replaces/modifies the options array in code
        int h = ComputeOptionsHash(options);
        if (h != optionsHash)
        {
            Rebuild(force: true);
            UpdateHeader();
        }
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

        // Overlay behind panel
        if (overlay != null) overlay.transform.SetAsLastSibling();
        if (panel != null) panel.transform.SetAsLastSibling();
    }

    public void CloseDropdown()
    {
        if (panel != null) panel.gameObject.SetActive(false);
        if (overlay != null) overlay.SetActive(false);
    }

    public void Rebuild(bool force)
    {
        int h = ComputeOptionsHash(options);
        if (!force && h == optionsHash) return;
        optionsHash = h;

        // Clear existing toggles
        for (int i = toggleParent.childCount - 1; i >= 0; i--)
        {
            var child = toggleParent.GetChild(i);
            // If the template toggle lives under toggleParent, keep it (inactive) instead of destroying it.
            if (togglePrefab != null && child == togglePrefab.transform) continue;
            DestroyImmediateOrRuntime(child.gameObject);
        }

        builtToggles.Clear();

        // Ensure we have/clear ToggleGroup depending on mode
        if (!multiChoice)
        {
            singleGroup = toggleParent.GetComponent<ToggleGroup>();
            if (singleGroup == null) singleGroup = toggleParent.gameObject.AddComponent<ToggleGroup>();
            singleGroup.allowSwitchOff = true;
        }
        else
        {
            singleGroup = toggleParent.GetComponent<ToggleGroup>();
            if (singleGroup != null) singleGroup.enabled = false;
        }

        // Re-create toggles
        int count = options != null ? options.Length : 0;
        for (int i = 0; i < count; i++)
        {
            int idx = i;

            Toggle t = Instantiate(togglePrefab, toggleParent);
            t.gameObject.SetActive(true);

            // Assign/clear group
            if (!multiChoice)
            {
                if (singleGroup != null) singleGroup.enabled = true;
                t.group = singleGroup;
            }
            else
            {
                t.group = null;
            }

            // Label
            var tmp = t.GetComponentInChildren<TMP_Text>();
            if (tmp != null) tmp.text = options[i];

            // Initial state
            if (multiChoice)
                t.isOn = selectedSet.Contains(idx);
            else
                t.isOn = (selectedIndex == idx);

            // Listener
            t.onValueChanged.RemoveAllListeners();
            t.onValueChanged.AddListener(on =>
            {
                if (multiChoice)
                {
                    if (on) selectedSet.Add(idx);
                    else selectedSet.Remove(idx);

                    UpdateHeader();
                }
                else
                {
                    if (on) selectedIndex = idx;
                    else if (selectedIndex == idx) selectedIndex = -1;

                    // Enforce radio behavior (ToggleGroup helps, but this is extra safety)
                    if (on)
                    {
                        for (int k = 0; k < builtToggles.Count; k++)
                        {
                            if (k != idx && builtToggles[k] != null && builtToggles[k].isOn)
                                builtToggles[k].SetIsOnWithoutNotify(false);
                        }
                    }

                    UpdateHeader();
                    CloseDropdown(); // normal dropdown behavior
                }
            });

            builtToggles.Add(t);
        }

        // If template toggle is an in-scene object, keep it hidden
        if (togglePrefab != null && togglePrefab.transform.parent == toggleParent)
            togglePrefab.gameObject.SetActive(false);
    }

    private void UpdateHeader()
    {
        if (headerLabel == null) return;

        if (!multiChoice)
        {
            headerLabel.text = (selectedIndex >= 0 && options != null && selectedIndex < options.Length)
                ? options[selectedIndex]
                : "";
            return;
        }

        int c = selectedSet.Count;

        if (c == 0)
        {
            headerLabel.text = "";
        }
        else if (c == 1)
        {
            int only = -1;
            foreach (var v in selectedSet) { only = v; break; }
            headerLabel.text = (only >= 0 && options != null && only < options.Length) ? options[only] : "";
        }
        else
        {
            headerLabel.text = $"{c} Selected";
        }
    }

    // Optional helpers
    public int GetSelectedIndex() => selectedIndex;

    public List<int> GetSelectedIndices()
    {
        var list = new List<int>(selectedSet);
        list.Sort();
        return list;
    }

    public List<string> GetSelectedOptions()
    {
        var idxs = GetSelectedIndices();
        var list = new List<string>(idxs.Count);
        for (int i = 0; i < idxs.Count; i++)
        {
            int idx = idxs[i];
            if (options != null && idx >= 0 && idx < options.Length) list.Add(options[idx]);
        }
        return list;
    }

    // If you change options via code, prefer this (guaranteed rebuild)
    public void SetOptions(string[] newOptions)
    {
        options = newOptions ?? Array.Empty<string>();
        Rebuild(force: true);
        UpdateHeader();
    }

    private static int ComputeOptionsHash(string[] arr)
    {
        unchecked
        {
            int h = 17;
            if (arr == null) return h;

            h = h * 31 + arr.Length;
            for (int i = 0; i < arr.Length; i++)
            {
                h = h * 31 + (arr[i]?.GetHashCode() ?? 0);
            }
            return h;
        }
    }

    private static void DestroyImmediateOrRuntime(GameObject go)
    {
#if UNITY_EDITOR
        if (!Application.isPlaying) DestroyImmediate(go);
        else Destroy(go);
#else
        Destroy(go);
#endif
    }
}
