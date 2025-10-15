using UnityEngine;
using TMPro;

public class SpeedText: MonoBehaviour
{
    TMP_Text text;
    void Start()
    {
        text = GetComponent<TMP_Text>();
    }
    public void setText(string name)
    {
        text.text = name;
    }
}
