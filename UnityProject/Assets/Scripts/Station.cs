using UnityEngine;
using CustomClasses;
using System.Collections.Generic;
using System.Collections;
using TMPro;
using UnityEngine.Networking;
using UnityEngine.EventSystems;


public class Station : MonoBehaviour, IPointerEnterHandler, IPointerExitHandler ,  IPointerDownHandler 
{
    [SerializeField] public string station_name;
    [SerializeField] public string station_ID;
    [SerializeField] Color32 yellow = new Color32(240, 230, 0, 255);
    [SerializeField] Color32 red = new Color32(255, 0, 0, 255);
    [SerializeField] Color32 black = new Color32(0, 0, 0, 255);
    [SerializeField] GameObject pop_up_spawn;
    private bool is_selected = false;
    string temp;
   
    private GameObject pop_up = null;
    private RideController controller;
    private SpriteRenderer sprite; 
    public List<int> nr_of_completed = new List<int>();
    public List<int> nr_of_active = new List<int>();
    public List<TripData> finalized_trips =  new List<TripData>();
    public List<TripData> started_trips = new List<TripData>();
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
       
        sprite =  GetComponent<SpriteRenderer>();
        controller = FindFirstObjectByType<RideController>();
        if (this.station_name.Equals("EMPTY")) {
            controller.unsupported_station = this;
        }
        InvokeRepeating("updateNrOfTrips", 0.0f, 60f);
    }

    void updateNrOfTrips(){
        nr_of_completed.Add(finalized_trips.Count);
        nr_of_active.Add(finalized_trips.Count - started_trips.Count);
    }
    // Update is called once per frame
    void Update()
    {
     
        //Debug.Log(this.station_name + " Finalized Trips:" + this.finalized_trips.Count);
        
        if (this.finalized_trips.Count > 5) {
            sprite.color = red;
        }
        else if (this.finalized_trips.Count > 2) { 
            sprite.color = yellow;
        }
        
    }

    public void proccess_click(PointerEventData eventData) {
        Debug.Log("mousepressed");
        if (is_selected) {
            Debug.Log($"Selected station:{station_name}");
            controller.selected_station = this;
            controller.cleanGraphs();
            controller.appendGraphs(nr_of_completed, nr_of_active);
        }
        if (!is_selected) {
            is_selected = false;
            Debug.Log($"Deselected station:{station_name}");
            controller.selected_station = null;
            controller.cleanGraphs();
            controller.appendGraphs(controller.nr_of_completed, controller.nr_of_active);
        }
    }
    
    public void OnPointerEnter(PointerEventData eventData){
        controller.hovering_station = this;
        server_predict();
    }
    public void OnPointerExit(PointerEventData eventData)
    {
        Destroy(pop_up, 0.25f);
        pop_up = null;
        Debug.Log("EXITING");
    }

    public void OnPointerDown(PointerEventData eventData)
    {

        controller.cleanGraphs();
        controller.appendGraphs(nr_of_completed, nr_of_active);
        controller.selected_station = controller.hovering_station;
        controller.station_name_text.setText(controller.selected_station.station_name);
    }
    
    
    void server_predict(){
        StartCoroutine(predict());
    }

    IEnumerator predict()
    {
        pop_up = Instantiate(pop_up_spawn, transform.position, Quaternion.Euler(0, 0, 90));
        TMP_Text text = pop_up.GetComponentInChildren<TMP_Text>();
        string data= $"{controller.return_day_of_month()}||{controller.return_hour()}||{station_name}";
        UnityWebRequest www = UnityWebRequest.Put("http://127.0.0.1:5000/predict",data);
        yield return www.SendWebRequest();
        temp = www.downloadHandler.text.Split(":")[1];
        temp = temp.Substring(0,temp.Length - 2);
        text.text = $"Name: {station_name} \n ID: {station_ID} \n Bikes next hour:{temp} ";
    }
}
