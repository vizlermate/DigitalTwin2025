using UnityEngine;
using UnityEngine.UI;
using System.Collections;

public class SpeedDown : MonoBehaviour
{
    RideController rc;
    Button button;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        rc = FindFirstObjectByType<RideController>();
        button = gameObject.GetComponent<Button>();
        button.onClick.AddListener(speedDown);

    }

    public void speedDown()
    {
        rc.decreaseSpeed(5);
    }
}
