using UnityEngine;
using UnityEngine.UI;
using System.Collections;

public class SpeedUp : MonoBehaviour
{
    RideController rc;
    Button button;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        rc = FindFirstObjectByType<RideController>();
        button = gameObject.GetComponent<Button>();
        button.onClick.AddListener(speedUp);

    }

    public void speedUp()
    {
        rc.increaseSpeed(5);
    }
}
