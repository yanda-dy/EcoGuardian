from airsim_wrapper import *
import airsim
import json


def setup(aw, color=None, thickness=5):
    if color is None:
        color = [0, 0, 1]
    aw.client.simSetTraceLine(color, thickness=thickness)

    start_x, start_y, start_z = 78, -13, -5
    # print(aw.client.simListAssets())
    # print(aw.client.simListSceneObjects())
    aw.client.simSetTimeOfDay(True, start_datetime="2024-03-30 13:52")

    object_names = ["African_Poacher_1_WalkwRifleLow_Anim2_2", "African_Poacher_1_WalkwRifleLow_Anim3_11", "African_Poacher_1_WalkwRifleLow_Anim_11",
                    "African_Poacher_2_WalkwRifle_Anim2_5", "African_Poacher_2_WalkwRifle_Anim3_14", "African_Poacher_2_WalkwRifle_Anim_14",
                    "African_Poacher_3_WalkwRifleSlung_Anim2_8", "African_Poacher_3_WalkwRifleSlung_Anim3_17", "African_Poacher_3_WalkwRifleSlung_Anim_2"]
    
    offset = (60, -25, 6)
    for idx, object in enumerate(object_names):
        pose = airsim.Pose(position_val=airsim.Vector3r(start_x + offset[0] + idx//3, start_y + offset[1] + idx%3, start_z + offset[2]),
                           orientation_val=airsim.to_quaternion(0, 0, 3.5))
        aw.client.simSetObjectPose(object, pose)
    