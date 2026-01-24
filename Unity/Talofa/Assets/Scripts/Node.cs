using UnityEngine;
using UnityEngine.UI;
using TMPro;
using System.Collections.Generic;

[ExecuteAlways]
public class Node : MonoBehaviour
{
    [HideInInspector]
    public Image background;
    [HideInInspector]
    public Image icon;
    [HideInInspector]
    public TextMeshProUGUI label;
    [HideInInspector]
    public GameObject disabledDisplay; // red X overlay (visual only)

    [Header("Data")]
    public string nodeName;
    [Range(1, 4)] public int age;
    public Sprite nodeSprite;

    public enum NodeType { Neutral, Unit, RegionalUnit, UniqueUnit, Tech, Building }
    public NodeType nodeType;

    // Visual-only flag. Does NOT deactivate the GameObject.
    public bool isEnabled = true;

    [Header("Child Layout")]
    public float siblingSpacingX = 45f;  // 0, +45, +90...
    public float slotStep = 46.875f;     // distance between top & bottom slot centers within an age
    public float ageStep = 97.5f;        // distance between age zones

    private GameManager gameManager;
    public Node[] substitutions;
    public GameObject specialBorder;

    // Cache to avoid allocations every Update
    private readonly List<Node> _nodeChildren = new List<Node>(8);

    // Detect transitions
    private bool _lastIsEnabled;

    // Prevent recursive ping-pong in ExecuteAlways
    private static bool s_propagating = false;

    void Update()
    {
        // Find GameManager (works in edit mode too)
        if (gameManager == null)
        {
#if UNITY_2022_2_OR_NEWER
            gameManager = FindFirstObjectByType<GameManager>();
#else
            gameManager = FindFirstObjectOfType<GameManager>();
#endif
        }

        // ---------- UI ----------
        if (gameManager != null && background != null && gameManager.techTreeColours != null)
        {
            int idx = (int)nodeType;
            if (idx >= 0 && idx < gameManager.techTreeColours.Length)
                background.color = gameManager.techTreeColours[idx];
        }

        if (icon != null) icon.sprite = nodeSprite;
        if (label != null) label.text = nodeName;

        gameObject.name = !string.IsNullOrEmpty(nodeName) ? $"Node: {nodeName}" : "Node";

        if (disabledDisplay != null)
            disabledDisplay.SetActive(!isEnabled);

        // ---------- Propagation on change ----------
        if (!s_propagating && isEnabled != _lastIsEnabled)
        {
            s_propagating = true;
            try
            {
                if (!isEnabled)
                {
                    // If I became disabled -> disable ALL descendants
                    SetDescendantsIsEnabled(false);
                }
                else
                {
                    // If I became enabled -> enable ALL ancestors
                    SetAncestorsIsEnabled(true);
                }
            }
            finally
            {
                s_propagating = false;
            }
        }
        _lastIsEnabled = isEnabled;

        // ---------- Position children ----------
        RepositionNodeChildren();

        // Change substitution UI
        specialBorder.SetActive(substitutions.Length > 0);
    }

    private void SetDescendantsIsEnabled(bool value)
    {
        // Walk transform hierarchy and set isEnabled on Nodes (children, grandchildren, ...)
        var stack = new Stack<Transform>();
        stack.Push(transform);

        while (stack.Count > 0)
        {
            var t = stack.Pop();

            for (int i = 0; i < t.childCount; i++)
            {
                var c = t.GetChild(i);
                stack.Push(c);

                var n = c.GetComponent<Node>();
                if (n == null) continue;

                n.isEnabled = value;
                if (n.disabledDisplay != null)
                    n.disabledDisplay.SetActive(!n.isEnabled);
            }
        }
    }

    private void SetAncestorsIsEnabled(bool value)
    {
        // Walk upward through parents and set isEnabled on Nodes
        Transform t = transform.parent;
        while (t != null)
        {
            var n = t.GetComponent<Node>();
            if (n != null)
            {
                n.isEnabled = value;
                if (n.disabledDisplay != null)
                    n.disabledDisplay.SetActive(!n.isEnabled);
            }
            t = t.parent;
        }
    }

    private void RepositionNodeChildren()
    {
        var parentRt = GetComponent<RectTransform>();
        if (parentRt == null) return;

        // If this node is logically disabled, don't reposition its children.
        if (!isEnabled) return;

        // If this node has a Node parent in the same age, treat it as bottom-slot.
        bool thisIsBottomSlot = false;
        if (transform.parent != null)
        {
            var pNode = transform.parent.GetComponent<Node>();
            if (pNode != null && pNode.age == age)
                thisIsBottomSlot = true;
        }

        _nodeChildren.Clear();

        // ONLY direct children that have Node and are active in hierarchy
        for (int i = 0; i < transform.childCount; i++)
        {
            var childNode = transform.GetChild(i).GetComponent<Node>();
            if (childNode == null) continue;
            if (!childNode.gameObject.activeInHierarchy) continue;

            // NOTE: we do NOT skip based on childNode.isEnabled,
            // so disabled nodes still occupy their slot and don't cause overlaps.
            _nodeChildren.Add(childNode);
        }

        if (_nodeChildren.Count == 0) return;

        float parentY = parentRt.anchoredPosition.y;

        for (int i = 0; i < _nodeChildren.Count; i++)
        {
            Node ch = _nodeChildren[i];
            if (ch == null) continue;

            // Force child age up if needed
            if (ch.age < age)
                ch.age = age;

            var chRt = ch.GetComponent<RectTransform>();
            if (chRt == null) continue;

            float targetY;

            if (ch.age == age)
            {
                // Same age: directly below in the next slot
                targetY = parentY - slotStep;
            }
            else
            {
                // Later age: top slot of that age zone
                // If THIS node is already in the bottom slot, compensate by one slotStep
                int ageDelta = Mathf.Clamp(ch.age - age, 1, 3);
                float bottomComp = thisIsBottomSlot ? slotStep : 0f;
                targetY = parentY - (ageDelta * ageStep) + bottomComp;
            }

            // Subsequent children go to the right of the first
            float localX = siblingSpacingX * i;
            float localY = targetY - parentY;

            chRt.anchoredPosition = new Vector2(localX, localY);
        }
    }

    // Optional helper if you still want a click hook elsewhere:
    public void ToggleIsEnabled()
    {
        isEnabled = !isEnabled;
        if (disabledDisplay != null)
            disabledDisplay.SetActive(!isEnabled);
    }

    private void OnEnable()
    {
        // When this node is active in hierarchy, force all substitutions OFF
        if (substitutions == null) return;
        for (int i = 0; i < substitutions.Length; i++)
        {
            var sub = substitutions[i];
            if (sub == null) continue;
            if (sub.gameObject.activeSelf) sub.gameObject.SetActive(false);
        }
    }

    private void OnDisable()
    {
        // When this node becomes inactive in hierarchy, enable ALL substitutions
        if (substitutions == null || substitutions.Length == 0) return;

        for (int i = 0; i < substitutions.Length; i++)
        {
            var sub = substitutions[i];
            if (sub == null) continue;

            if (!sub.gameObject.activeSelf)
                sub.gameObject.SetActive(true);
        }
    }
}
