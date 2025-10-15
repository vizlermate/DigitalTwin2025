using UnityEngine;
using UnityEngine.UI;


public class Reset : MonoBehaviour
{
    RideController rc;
    Button button;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        button = GetComponent<Button>();
        button.onClick.AddListener(resetDashboard);
        rc= FindFirstObjectByType<RideController>();
    }

    void resetDashboard()
    {
        rc.cleanGraphs();
        rc.appendGraphs(rc.nr_of_completed, rc.nr_of_active);
        rc.selected_station = rc.unsupported_station;
        rc.station_name_text.setText("Overall");
    }

    // Update is called once per frame
    void Update()
    {
        
    }
}
