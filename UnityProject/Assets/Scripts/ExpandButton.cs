using UnityEngine;
using UnityEngine.UI;
using System.Collections;

public class ExpandButton : MonoBehaviour
{
    GameObject baseUI;
    GameObject fullUI;
    Button button;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        button = gameObject.GetComponent<Button>();
        button.onClick.AddListener(showFullUI);
        baseUI = GameObject.FindWithTag("baseUI");
        fullUI = GameObject.FindWithTag("fullUI");
        StartCoroutine(passivegraph(10f));
    }

    IEnumerator passivegraph(float miliseconds)
    {
        yield return new WaitForSeconds(miliseconds/1000);
        fullUI.SetActive(false);
    }
    public void showFullUI()
    {
        baseUI.SetActive(false);
        fullUI.SetActive(true);
    }
}
