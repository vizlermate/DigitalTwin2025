using UnityEngine;
using System.Collections;
using UnityEngine.InputSystem;
using Unity.Cinemachine;

public class MouseController : MonoBehaviour
{
    [SerializeField] InputActionAsset zoom;
    [SerializeField] CinemachineCamera virtualcamera;
    GameObject mouseobject;
    GameObject mousetriggerer;

    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        mouseobject = GameObject.FindWithTag("Mouse");
        Cursor.visible = true;
    }

    // Update is called once per frame
    void Update()
    {
        float x = Camera.main.ScreenToWorldPoint(Mouse.current.position.ReadValue()).x;
        float y = Camera.main.ScreenToWorldPoint(Mouse.current.position.ReadValue()).y;
        //Debug.Log($"mouse x: {x} \n mouse y: {y} ");
        if (x < 8 && x > -8 && y < 5 && y > -5)
        {
            mouseobject.transform.position = new Vector3(x, y, 0);
        }
        InputAction action = zoom.FindAction("ScrollWheel");
        Vector2 z = action.ReadValue<Vector2>();
        //Debug.Log($"actionx:{z.x},actiony:{z.y}");
        if (z.y > 0)
        {
            Debug.Log("Scroll UP");
            zoomPlus();
        }
        else if (z.y < 0)
        {
            Debug.Log("Scroll DOWN");
            zoomMin();
        }
    }
    public void zoomPlus()
    {
        if(virtualcamera.Lens.OrthographicSize > 1)
        {
            virtualcamera.Lens.OrthographicSize = virtualcamera.Lens.OrthographicSize - 1;
        }
    }
    public void zoomMin()
    {
        if(virtualcamera.Lens.OrthographicSize < 6)
        {
            virtualcamera.Lens.OrthographicSize = virtualcamera.Lens.OrthographicSize + 1;
        }
    }
}
