using UnityEngine;

public class AddCar : MonoBehaviour
{
    public GameObject prefab; // drag your blue prefab here in Inspector

    public void Add()
    {
        // Parent is the object that currently holds ExclusionAddButton / AgeAddButton (likely UnitBonus)
        Transform container = transform.parent;

        // Create the new UI element under the same parent
        GameObject go = Instantiate(prefab, container);

        // Put it directly below this AddButton in the hierarchy
        int myIndex = transform.GetSiblingIndex();
        go.transform.SetSiblingIndex(myIndex + 1);

        // (Optional) reset UI transform so it appears correctly
        var rt = go.GetComponent<RectTransform>();
        if (rt != null)
        {
            rt.localScale = Vector3.one;
            rt.anchoredPosition3D = Vector3.zero;
        }
    }
}
