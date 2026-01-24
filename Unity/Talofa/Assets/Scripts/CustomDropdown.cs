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

    [Header("Option UI")]
    public Toggle togglePrefab;          // template toggle (prefab asset OR inactive scene object)
    public Transform toggleParent;       // where toggles are created

    [Header("Options (auto rebuilds when changed)")]
    [SerializeField] public string[] options = Array.Empty<string>();

    // ---------------- NEW: Auto width ----------------
    [Header("Auto Width")]
    public bool autoWidth = true;
    public float widthPadding = 24f;         // extra padding added to the widest child
    public float minWidth = 0f;              // 0 = no minimum
    public float maxWidth = 0f;              // 0 = no maximum
    public bool matchHeaderWidthToo = true;  // also apply to headerButton/headerLabel parent if desired
    // -------------------------------------------------

    // Single-choice state
    [SerializeField] private int selectedIndex = -1;

    // Multi-choice state
    private readonly HashSet<int> selectedSet = new HashSet<int>();

    // Internals
    private readonly List<Toggle> builtToggles = new List<Toggle>();
    private ToggleGroup singleGroup;
    private int optionsHash;

    // Runtime overlay + panel reparenting
    private GameObject runtimeOverlayGO;
    private Transform panelOriginalParent;
    private int panelOriginalSiblingIndex;
    private bool panelWasActive;

    void Awake()
    {
        if (panel != null) panel.gameObject.SetActive(false);

        if (headerButton != null) headerButton.onClick.AddListener(ToggleDropdown);

        Rebuild(force: true);
        UpdateHeader();
        UpdatePanelWidthFromChildren(); // NEW
    }

    void OnEnable()
    {
        Rebuild(force: true);
        UpdateHeader();
        UpdatePanelWidthFromChildren(); // NEW
    }

#if UNITY_EDITOR
    void OnValidate()
    {
        if (!UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode)
        {
            Rebuild(force: true);
            UpdateHeader();
            UpdatePanelWidthFromChildren(); // NEW
        }
    }
#endif

    void Update()
    {
        int h = ComputeOptionsHash(options);
        if (h != optionsHash)
        {
            Rebuild(force: true);
            UpdateHeader();
            UpdatePanelWidthFromChildren(); // NEW
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
        if (panel == null) return;

        EnsureRuntimeOverlay();
        BringPanelToFront();

        panel.gameObject.SetActive(true);

        // NEW: after it becomes active, rebuild layout and set width from children
        UpdatePanelWidthFromChildren();
    }

    public void CloseDropdown()
    {
        if (panel != null) panel.gameObject.SetActive(false);

        RestorePanelParentAndOrder();
        DestroyRuntimeOverlay();
    }

    private void EnsureRuntimeOverlay()
    {
        if (runtimeOverlayGO != null) return;

        Transform canvasRoot = GetCanvasRoot();
        if (canvasRoot == null)
        {
            Debug.LogError("CustomDropdown: Could not find a parent Canvas. Overlay cannot be created.");
            return;
        }

        runtimeOverlayGO = new GameObject("DropdownOverlay_Runtime", typeof(RectTransform), typeof(Image), typeof(Button));
        runtimeOverlayGO.transform.SetParent(canvasRoot, false);

        var rt = runtimeOverlayGO.GetComponent<RectTransform>();
        rt.anchorMin = Vector2.zero;
        rt.anchorMax = Vector2.one;
        rt.offsetMin = Vector2.zero;
        rt.offsetMax = Vector2.zero;

        var img = runtimeOverlayGO.GetComponent<Image>();
        img.color = new Color(0f, 0f, 0f, 0f);
        img.raycastTarget = true;

        var btn = runtimeOverlayGO.GetComponent<Button>();
        btn.onClick.RemoveAllListeners();
        btn.onClick.AddListener(CloseDropdown);

        runtimeOverlayGO.transform.SetAsLastSibling();
    }

    private void DestroyRuntimeOverlay()
    {
        if (runtimeOverlayGO == null) return;
        Destroy(runtimeOverlayGO);
        runtimeOverlayGO = null;
    }

    private void BringPanelToFront()
    {
        if (panel == null) return;

        Transform canvasRoot = GetCanvasRoot();
        if (canvasRoot == null) return;

        if (panelOriginalParent == null)
        {
            panelOriginalParent = panel.transform.parent;
            panelOriginalSiblingIndex = panel.transform.GetSiblingIndex();
            panelWasActive = panel.gameObject.activeSelf;
        }

        panel.transform.SetParent(canvasRoot, worldPositionStays: true);
        panel.transform.SetAsLastSibling();
    }

    private void RestorePanelParentAndOrder()
    {
        if (panel == null) return;
        if (panelOriginalParent == null) return;

        panel.transform.SetParent(panelOriginalParent, worldPositionStays: true);

        int maxIndex = panelOriginalParent.childCount - 1;
        int clampedIndex = Mathf.Clamp(panelOriginalSiblingIndex, 0, maxIndex);
        panel.transform.SetSiblingIndex(clampedIndex);

        panelOriginalParent = null;
        panelOriginalSiblingIndex = 0;
    }

    private Transform GetCanvasRoot()
    {
        Canvas c = null;

        if (panel != null) c = panel.GetComponentInParent<Canvas>();
        if (c == null) c = GetComponentInParent<Canvas>();

        if (c == null) return null;

        var root = c.rootCanvas != null ? c.rootCanvas : c;
        return root.transform;
    }

    public void Rebuild(bool force)
    {
        int h = ComputeOptionsHash(options);
        if (!force && h == optionsHash) return;
        optionsHash = h;

        if (toggleParent == null || togglePrefab == null)
        {
            builtToggles.Clear();
            return;
        }

        for (int i = toggleParent.childCount - 1; i >= 0; i--)
        {
            var child = toggleParent.GetChild(i);
            if (child == togglePrefab.transform) continue;
            DestroyImmediateOrRuntime(child.gameObject);
        }

        builtToggles.Clear();

        if (!multiChoice)
        {
            singleGroup = toggleParent.GetComponent<ToggleGroup>();
            if (singleGroup == null) singleGroup = toggleParent.gameObject.AddComponent<ToggleGroup>();
            singleGroup.allowSwitchOff = true;
            singleGroup.enabled = true;
        }
        else
        {
            singleGroup = toggleParent.GetComponent<ToggleGroup>();
            if (singleGroup != null) singleGroup.enabled = false;
        }

        int count = options != null ? options.Length : 0;
        for (int i = 0; i < count; i++)
        {
            int idx = i;

            Toggle t = Instantiate(togglePrefab, toggleParent);
            t.gameObject.SetActive(true);

            if (!multiChoice)
                t.group = singleGroup;
            else
                t.group = null;

            var tmp = t.GetComponentInChildren<TMP_Text>();
            if (tmp != null) tmp.text = options[i];

            if (multiChoice)
                t.isOn = selectedSet.Contains(idx);
            else
                t.isOn = (selectedIndex == idx);

            t.onValueChanged.RemoveAllListeners();
            t.onValueChanged.AddListener(on =>
            {
                if (multiChoice)
                {
                    if (on) selectedSet.Add(idx);
                    else selectedSet.Remove(idx);

                    UpdateHeader();
                    UpdatePanelWidthFromChildren(); // NEW (text can change, e.g. localization)
                }
                else
                {
                    if (on) selectedIndex = idx;
                    else if (selectedIndex == idx) selectedIndex = -1;

                    if (on)
                    {
                        for (int k = 0; k < builtToggles.Count; k++)
                        {
                            if (k != idx && builtToggles[k] != null && builtToggles[k].isOn)
                                builtToggles[k].SetIsOnWithoutNotify(false);
                        }
                    }

                    UpdateHeader();
                    UpdatePanelWidthFromChildren(); // NEW
                    CloseDropdown();
                }
            });

            builtToggles.Add(t);
        }

        if (togglePrefab != null && togglePrefab.transform.parent == toggleParent)
            togglePrefab.gameObject.SetActive(false);

        // NEW
        UpdatePanelWidthFromChildren();
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

    public void SetOptions(string[] newOptions)
    {
        options = newOptions ?? Array.Empty<string>();
        Rebuild(force: true);
        UpdateHeader();
        UpdatePanelWidthFromChildren(); // NEW
    }

    // ---------------- NEW: Width-from-children logic ----------------
    private void UpdatePanelWidthFromChildren()
    {
        if (!autoWidth) return;
        if (panel == null) return;
        if (toggleParent == null) return;

        // Ensure layout/text sizes are up-to-date before measuring
        Canvas.ForceUpdateCanvases();
        if (toggleParent is RectTransform tprt)
            LayoutRebuilder.ForceRebuildLayoutImmediate(tprt);

        float max = 0f;

        // Measure preferred width from TMP text where possible, otherwise RectTransform width
        foreach (var t in builtToggles)
        {
            if (t == null) continue;

            float w = 0f;

            var tmp = t.GetComponentInChildren<TMP_Text>();
            if (tmp != null)
            {
                // preferredWidth is great for TMP labels
                w = tmp.preferredWidth;
                // include toggle padding by reading toggle rect width as baseline
                var trt = t.GetComponent<RectTransform>();
                if (trt != null) w = Mathf.Max(w, trt.rect.width);
            }
            else
            {
                var trt = t.GetComponent<RectTransform>();
                if (trt != null) w = trt.rect.width;
            }

            max = Mathf.Max(max, w);
        }

        // If no toggles, fallback to parent width
        if (max <= 0.01f && toggleParent is RectTransform tp)
            max = tp.rect.width;

        float target = max + widthPadding;

        if (minWidth > 0f) target = Mathf.Max(minWidth, target);
        if (maxWidth > 0f) target = Mathf.Min(maxWidth, target);

        // Set ONLY width on panel
        panel.SetSizeWithCurrentAnchors(RectTransform.Axis.Horizontal, target);

        // Optionally also set header container width to match
        if (matchHeaderWidthToo)
        {
            var headerRt = headerButton != null ? headerButton.GetComponent<RectTransform>() : null;
            if (headerRt != null)
                headerRt.SetSizeWithCurrentAnchors(RectTransform.Axis.Horizontal, target);
        }
    }
    // ----------------------------------------------------------------

    private static int ComputeOptionsHash(string[] arr)
    {
        unchecked
        {
            int h = 17;
            if (arr == null) return h;

            h = h * 31 + arr.Length;
            for (int i = 0; i < arr.Length; i++)
                h = h * 31 + (arr[i]?.GetHashCode() ?? 0);

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
