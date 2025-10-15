using UnityEngine;
using UnityEngine.UI;
using System;

public class HistoryVisuallisation : MonoBehaviour
{
    Button button;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        button = GetComponent<Button>();
        button.onClick.AddListener(startVisualisation);
    }

    void startVisualisation()
    {
        System.Diagnostics.Process.Start("CMD.exe","/C python Python\\final_version_visual.py");
    }

    // Update is called once per frame
    void Update()
    {
        
    }
}