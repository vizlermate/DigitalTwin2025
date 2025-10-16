using UnityEngine;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System;
using CustomClasses;
using System.Globalization;
using XCharts.Runtime;
using UnityEngine.Networking;
using UnityEngine.InputSystem;




// CSV READING ADAPTED FROM https://www.youtube.com/watch?v=xwnL4meq-j8
public class RideController : MonoBehaviour
{
    private int y_axis_point = 0;
    private GameObject tempObject;
    public LineChart total_trips_chart;
    public LineChart active_trips_chart;
    public Station hovering_station;
    public SelectionText station_name_text;
    public SpeedText speed_text;

    private CultureInfo cultureInfo = CultureInfo.CreateSpecificCulture("en-EN");
    private List<TripData> started_trips = new List<TripData>();
    private List<TripData> ended_trips = new List<TripData>();
    public List<int> nr_of_completed = new List<int>();
    public List<int> nr_of_active = new List<int>();
   
    private DateTime dt = new DateTime(2024, 1, 1);
    private List<string> csvLines = new List<string>();
    private List<int> times = new List<int>();
    private StreamReader fileReader = new StreamReader("C:\\Users\\jaime\\Desktop\\Digital Twin Engineering Group 3\\Assets\\Data\\Event_Data.csv");
    
    
    private StreamWriter fileWriter;  

    bool EOF = false;
    public List<Station> stations;
    public Station unsupported_station;
    [SerializeField] public Station selected_station = null;

    [SerializeField] int speedup = 1;
    [SerializeField] int len_x_axis;
    [SerializeField] int len_y_axis;
    [SerializeField] GameObject StationSpawn;

    void Start()
    {
        station_name_text = FindFirstObjectByType<SelectionText>();
        station_name_text.setText("Overall");
        speed_text = FindFirstObjectByType<SpeedText>();
        speed_text.setText("1");
        fileWriter = File.CreateText("C:\\Users\\jaime\\Desktop\\Digital Twin Engineering Group 3\\Assets\\Data\\historical_data.csv");
        fileWriter.AutoFlush = true;
        fileWriter.WriteLine("ride_id,rideable_type,started_at,ended_at,start_station_name,start_station_id,end_station_name,end_station_id,start_lat,start_lng,end_lat,end_lng,member_casual");
        
        //fileWriter.WriteLine("ride_id,rideable_type,started_at,ended_at,start_station_name,start_station_id,end_station_name,end_station_id,start_lat,start_lng,end_lat,end_lng,member_casual");
        tempObject = GameObject.FindWithTag("total trips");
        total_trips_chart = tempObject.GetComponent<LineChart>();
        Title title = total_trips_chart.EnsureChartComponent<Title>();
        title.text = "Completed Trips";
        total_trips_chart.RemoveData();
        total_trips_chart.AddSerie<Line>("line");

        tempObject = GameObject.FindWithTag("active trips");
        active_trips_chart = tempObject.GetComponent<LineChart>();
        title = active_trips_chart.EnsureChartComponent<Title>();
        title.text = "Active Trips";
        active_trips_chart.RemoveData();
        active_trips_chart.AddSerie<Line>("line");

        InvokeRepeating("updateState", 0.0f, 60f);
        fileReader.ReadLine();
    }
    void updateState()
    {
        y_axis_point = y_axis_point + this.speedup;
        times.Add(y_axis_point);
        dt = dt.AddMinutes(this.speedup);
        while (!EOF)
        {
            string data_String = fileReader.ReadLine();
            if (data_String == null)
            {
                EOF = true;
                break;
            }
            TripData new_trip = new TripData(data_String);
            Station station = searchStation(new_trip.station_id);
            if (station.station_name.Equals("EMPTY"))
            {
                GameObject newStation = Instantiate(StationSpawn, new Vector3(-13 + len_x_axis * new_trip.longtitude, -7 + len_y_axis * new_trip.latitude, 0), Quaternion.identity);
                station = newStation.GetComponent<Station>();
                station.station_name = new_trip.station_name;
                station.station_ID = new_trip.station_id;
                stations.Add(station);

            }

            if (new_trip.state)
            {
                station.finalized_trips.Add(new_trip);
                this.ended_trips.Add(new_trip);
                TripData old_trip = findTrip(new_trip.ride_id);
                //Debug.Log(new_trip.time.ToString(cultureInfo));
                //Debug.Log(old_trip.time.ToString(cultureInfo));
                fileWriter.WriteLine($"{new_trip.ride_id},{new_trip.rideable_type},{old_trip.time.ToString("yyyy-MM-dd HH:mm:ss.fff")},{new_trip.time.ToString("yyyy-MM-dd HH:mm:ss.fff")},{old_trip.station_name},{old_trip.station_id},{new_trip.station_name},{new_trip.station_id},{calc_latitude(old_trip.latitude).ToString(cultureInfo)},{calc_longtitude(old_trip.longtitude).ToString(cultureInfo)},{calc_latitude(new_trip.latitude).ToString(cultureInfo)},{calc_longtitude(new_trip.longtitude).ToString(cultureInfo)},{new_trip.has_membership}");
            }
            else
            {
                station.started_trips.Add(new_trip);
                this.started_trips.Add(new_trip);
            }
            if (new_trip.time.Ticks >= dt.Ticks)
            {
                break;
            }

        }
        nr_of_completed.Add(ended_trips.Count);
        nr_of_active.Add(started_trips.Count - ended_trips.Count);
        if(selected_station.station_name.Equals("EMPTY")){
            total_trips_chart.AddXAxisData(y_axis_point.ToString());
            total_trips_chart.AddData(0, ended_trips.Count);

            active_trips_chart.AddXAxisData(y_axis_point.ToString());
            active_trips_chart.AddData(0, started_trips.Count - ended_trips.Count);
        }
        else{
            total_trips_chart.AddXAxisData(y_axis_point.ToString());
            total_trips_chart.AddData(0, selected_station.finalized_trips.Count);

            active_trips_chart.AddXAxisData(y_axis_point.ToString());
            active_trips_chart.AddData(0, selected_station.started_trips.Count - selected_station.finalized_trips.Count);
        }
        //Debug.Log("Started Trips:" + started_trips.Count);
        //Debug.Log("Finalized Trips:" + ended_trips.Count);
        //Debug.Log("Trips in Progress:" + (started_trips.Count - ended_trips.Count));
    }

    public void cleanGraphs()
    {
        total_trips_chart.RemoveData();
        total_trips_chart.AddSerie<Line>("line");
        active_trips_chart.RemoveData();
        active_trips_chart.AddSerie<Line>("line");
    }
    float calc_latitude(float latitude_percent)
    {
        return 40.633385f + (0.252915f * latitude_percent);
    }

    float calc_longtitude(float longtitude_percent)
    {
        return -74.050656f + (0.200876f * longtitude_percent);
    }

    TripData findTrip(string search_ride_id)
    {
        foreach (TripData possible_start_trip in started_trips)
        {
            if (possible_start_trip.ride_id.Equals(search_ride_id))
            {
                return possible_start_trip;
            }
        }
        return new TripData("0,0,12/31/2023 11:44:35 PM,0,0,0,0,0,0");
    }

    Station searchStation(string search_station_ID)
    {
        foreach (Station station in stations)
        {
            if (station.station_ID.Equals(search_station_ID))
            {
                return station;
            }
        }
        
        return unsupported_station.GetComponent<Station>();
    }

    public Station findStation(string search_station_name)
    {
        foreach (Station station in stations)
        {
            if (station.station_name.Equals(search_station_name))
            {
                return station;
            }
        }
        
        return unsupported_station.GetComponent<Station>();
    }

    public void increaseSpeed(int speed)
    {
        if(this.speedup < 625){
            this.speedup = this.speedup * speed;
        }
        speed_text.setText(this.speedup.ToString());
    }
    public void decreaseSpeed(int speed)
    {
        if (this.speedup > 1)
        {
            this.speedup = this.speedup / speed;
        }
        speed_text.setText(this.speedup.ToString());
    }
    public int return_day_of_month(){
        return dt.Day;
    }
    public int return_hour(){
        return dt.Hour;
    }
    public void appendGraphs(List<int> nr_of_completed, List<int> nr_of_active){
        for(int i = 0; i < nr_of_completed.Count; i++)
        {
            total_trips_chart.AddXAxisData(times[i].ToString());
            total_trips_chart.AddData(0, nr_of_completed[i]);

            active_trips_chart.AddXAxisData(times[i].ToString());
            active_trips_chart.AddData(0, nr_of_active[i]);
        }
    }
    
}