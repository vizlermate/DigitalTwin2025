using UnityEngine;
using System;
using System.Globalization;
using System.Collections;

namespace CustomClasses
{
    public class TripData 
    {
        private CultureInfo cultureInfo = CultureInfo.CreateSpecificCulture("en-EN");
        //"yyyy-MM-dd hh:mm:ss"
        string format = "yyyy-MM-dd HH:mm:ss.fff";

        //"2024-12-30 23:41:25.635" 
        //string test_string ="2024-12-30 23:41:25.635";
        public TripData(string csvEntry)

        
        {
            var data_values = csvEntry.Split(",");
            this.ride_id = data_values[0];
            this.rideable_type = data_values[1];
            this.time = DateTime.ParseExact(data_values[2],format,CultureInfo.InvariantCulture);
            this.station_name = data_values[3];
            this.station_id = data_values[4];
            this.has_membership = data_values[5];
            this.latitude = float.Parse(data_values[6],CultureInfo.InvariantCulture);
            this.longtitude = float.Parse(data_values[7],CultureInfo.InvariantCulture);
            this.state = (data_values[8] == "1");
            return;
        }
        public string ride_id;
        public string rideable_type;
        public DateTime time;
        public string station_name;
        public string station_id;
        public string has_membership;
        public float longtitude;
        public float latitude;
        public bool state;
    }
}