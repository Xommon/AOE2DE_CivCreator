using System.Collections;
using UnityEngine;
using UnityEngine.UI;

public class AddCar : MonoBehaviour
{
    public GameObject prefab;

    public void Add()
    {
        Transform container = transform.parent;

        GameObject go = Instantiate(prefab, container);

        int myIndex = transform.GetSiblingIndex();
        go.transform.SetSiblingIndex(myIndex + 1);

        var rt = go.GetComponent<RectTransform>();
        if (rt != null)
        {
            rt.localScale = Vector3.one;
            rt.anchoredPosition3D = Vector3.zero;
        }

        StartCoroutine(RebuildLayout(container));
    }

    private IEnumerator RebuildLayout(Transform container)
    {
        // wait one frame so TMP/layout can compute preferred sizes
        yield return null;

        Canvas.ForceUpdateCanvases();

        // Rebuild container and its parent (common when ContentSizeFitter is on parent)
        var c = container as RectTransform;
        if (c != null) LayoutRebuilder.ForceRebuildLayoutImmediate(c);

        if (container.parent is RectTransform p)
            LayoutRebuilder.ForceRebuildLayoutImmediate(p);
    }
}
