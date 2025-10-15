using UnityEngine;
using UnityEngine.UI;

public class ExitButton : MonoBehaviour
{
    GameObject baseUI;
    GameObject fullUI;
    Button button;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        button = gameObject.GetComponent<Button>();
        button.onClick.AddListener(hideFullUI);
        baseUI = GameObject.FindWithTag("baseUI");
        fullUI = GameObject.FindWithTag("fullUI");
       
    }


    public void hideFullUI()
    {
        baseUI.SetActive(true);
        fullUI.SetActive(false);
    }
}
