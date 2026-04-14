# Camera Tuning for Nvblox




## A: Tuning Camera [Simulation]

### Step 1: Launch Camera Tuning [Docker]
```
ros2 launch movensys_perception camera_transform_tuning.launch.py use_sim_time:=true child_frame:=camera_top_color_optical_frame
```

### Step 2: Modify Transform Value
`movensys_perception/launch/camera_top_transform.launch.py`
`start_camera_top_transform_simulation`


