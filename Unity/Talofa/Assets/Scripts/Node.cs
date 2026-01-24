using UnityEngine;
using UnityEngine.UI;
using TMPro;
using System.Collections.Generic;
using UnityEngine.EventSystems;

[ExecuteAlways]
public class Node : MonoBehaviour, IPointerClickHandler
{
    [HideInInspector] public Image background;
    [HideInInspector] public Image icon;
    [HideInInspector] public TextMeshProUGUI label;
    [HideInInspector] public GameObject disabledDisplay;

    [Header("Data")]
    public string nodeName;
    [Range(1, 4)] public int age;
    public Sprite nodeSprite;

    public enum NodeType { Neutral, Unit, RegionalUnit, UniqueUnit, Tech, Building }
    public NodeType nodeType;

    public bool isEnabled = true;

    [Header("Child Layout")]
    public float siblingSpacingX = 45f;
    public float slotStep = 46.875f;
    public float ageStep = 97.5f;

    private GameManager gameManager;
    public Node[] substitutions;
    public GameObject specialBorder;

    private readonly List<Node> _nodeChildren = new List<Node>(8);

    private bool _lastIsEnabled;
    private static bool s_propagating = false;

    // ---------- NEW: deferred active switching ----------
    private struct PendingActive
    {
        public GameObject go;
        public bool active;
    }

    private static readonly List<PendingActive> s_pending = new List<PendingActive>(128);
    private static bool s_processingPending = false;

    private static void QueueSetActive(GameObject go, bool active)
    {
        if (go == null) return;
        if (go.activeSelf == active) return;

        // avoid duplicates (last write wins)
        for (int i = s_pending.Count - 1; i >= 0; i--)
        {
            if (s_pending[i].go == go)
            {
                s_pending[i] = new PendingActive { go = go, active = active };
                return;
            }
        }

        s_pending.Add(new PendingActive { go = go, active = active });
    }

    private static void FlushPending()
    {
        if (s_processingPending) return;
        if (s_pending.Count == 0) return;

        s_processingPending = true;
        try
        {
            for (int i = 0; i < s_pending.Count; i++)
            {
                var p = s_pending[i];
                if (p.go == null) continue;
                if (p.go.activeSelf != p.active)
                    p.go.SetActive(p.active);
            }
        }
        finally
        {
            s_pending.Clear();
            s_processingPending = false;
        }
    }
    // ----------------------------------------------------

    void Update()
    {
        if (gameManager == null)
        {
#if UNITY_2022_2_OR_NEWER
            gameManager = FindFirstObjectByType<GameManager>();
#else
            gameManager = FindFirstObjectOfType<GameManager>();
#endif
        }

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

        if (!s_propagating && isEnabled != _lastIsEnabled)
        {
            s_propagating = true;
            try
            {
                if (!isEnabled) SetDescendantsIsEnabled(false);
                else SetAncestorsIsEnabled(true);
            }
            finally { s_propagating = false; }
        }
        _lastIsEnabled = isEnabled;

        RepositionNodeChildren();

        if (specialBorder != null)
            specialBorder.SetActive(substitutions != null && substitutions.Length > 0);

        // Apply deferred SetActive safely after UI has settled this frame
        FlushPending();
    }

    // If you want it even safer, move FlushPending() to LateUpdate instead.
    void LateUpdate()
    {
        FlushPending();
    }

    public void OnPointerClick(PointerEventData eventData)
    {
        if (eventData == null) return;

        if (eventData.button == PointerEventData.InputButton.Left)
        {
            ToggleIsEnabled();
        }
        else if (eventData.button == PointerEventData.InputButton.Right)
        {
            if (substitutions != null && substitutions.Length > 0)
            {
                Node[] subs = gameObject.GetComponent<Node>().substitutions;
                foreach (Node sub in subs)
                {
                    sub.gameObject.SetActive(true);
                }
                gameObject.SetActive(false);
            }
        }
    }

    private void SetDescendantsIsEnabled(bool value)
    {
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
        if (!isEnabled) return;

        bool thisIsBottomSlot = false;
        if (transform.parent != null)
        {
            var pNode = transform.parent.GetComponent<Node>();
            if (pNode != null && pNode.age == age)
                thisIsBottomSlot = true;
        }

        _nodeChildren.Clear();

        for (int i = 0; i < transform.childCount; i++)
        {
            var childNode = transform.GetChild(i).GetComponent<Node>();
            if (childNode == null) continue;
            if (!childNode.gameObject.activeInHierarchy) continue;
            _nodeChildren.Add(childNode);
        }

        if (_nodeChildren.Count == 0) return;

        float parentY = parentRt.anchoredPosition.y;

        for (int i = 0; i < _nodeChildren.Count; i++)
        {
            Node ch = _nodeChildren[i];
            if (ch == null) continue;

            if (ch.age < age) ch.age = age;

            var chRt = ch.GetComponent<RectTransform>();
            if (chRt == null) continue;

            float targetY;

            if (ch.age == age) targetY = parentY - slotStep;
            else
            {
                int ageDelta = Mathf.Clamp(ch.age - age, 1, 3);
                float bottomComp = thisIsBottomSlot ? slotStep : 0f;
                targetY = parentY - (ageDelta * ageStep) + bottomComp;
            }

            float localX = siblingSpacingX * i;
            float localY = targetY - parentY;

            chRt.anchoredPosition = new Vector2(localX, localY);
        }
    }

    public void ToggleIsEnabled()
    {
        isEnabled = !isEnabled;
        if (disabledDisplay != null)
            disabledDisplay.SetActive(!isEnabled);
    }

    private void OnEnable()
    {
        // When THIS node becomes active:
        // 1) ensure all descendants are active (deferred)
        EnableAllDescendantsActive();

        // 2) force substitutions OFF (deferred)
        /*if (substitutions == null) return;
        for (int i = 0; i < substitutions.Length; i++)
        {
            var sub = substitutions[i];
            if (sub == null) continue;
            QueueSetActive(sub.gameObject, false);
        }*/
    }

    private void EnableAllDescendantsActive()
    {
        // Activate everything under this transform (children, grandchildren, etc.)
        // Uses deferred QueueSetActive to avoid Selectable.OnEnable timing issues.
        var stack = new Stack<Transform>();
        stack.Push(transform);

        while (stack.Count > 0)
        {
            var t = stack.Pop();
            for (int i = 0; i < t.childCount; i++)
            {
                var c = t.GetChild(i);
                stack.Push(c);

                // Turn on the whole child object
                QueueSetActive(c.gameObject, true);
            }
        }
    }

    private void OnDisable()
    {
        /*// When inactive: enable ALL substitutions (deferred)
        if (substitutions == null || substitutions.Length == 0) return;
        for (int i = 0; i < substitutions.Length; i++)
        {
            var sub = substitutions[i];
            if (sub == null) continue;
            QueueSetActive(sub.gameObject, true);
        }*/
    }
}
