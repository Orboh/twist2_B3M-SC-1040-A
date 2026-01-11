import numpy as np

DEFAULT_MIMIC_OBS_G1 = np.concatenate([
                    np.array([0, 0]), # xy velocity
                    np.array([0.8]), # z position
                    np.array([0, 0]), # roll/pitch
                    np.array([0]), # yaw angular velocity
                    # 29 dof
                    np.array([-0.2, 0.0, 0.0, 0.4, -0.2, 0.0,  # left leg (6)
                            -0.2, 0.0, 0.0, 0.4, -0.2, 0.0,  # right leg (6)
                            0.0, 0.0, 0.0, # torso (1)
                            0.0, 0.4, 0.0, 1.2, 0.0, 0.0, 0.0, # left arm (7)
                            0.0, -0.4, 0.0, 1.2, 0.0, 0.0, 0.0, # right arm (7)
                        ])
                ])

DEFAULT_MIMIC_OBS_G1_MIXED_MODE = np.concatenate([
                    np.array([0, 0]), # xy velocity
                    np.array([0.8]), # z position
                    np.array([0, 0]), # roll/pitch
                    np.array([0]), # yaw angular velocity
                    # 29 dof
                    np.array([-0.2, 0.0, 0.0, 0.4, -0.2, 0.0,  # left leg (6)
                            -0.2, 0.0, 0.0, 0.4, -0.2, 0.0,  # right leg (6)
                            0.0, 0.0, 0.0, # torso (1)
                            0.0, 0.4, 0.0, 1.2, 0.0, 0.0, 0.0, # left arm (7)
                            0.0, -0.4, 0.0, 1.2, 0.0, 0.0, 0.0, # right arm (7)
                        ]),
                    np.array([1.0, 0.0]) # mode indicator
                ])

DEFAULT_MIMIC_OBS_T1 = np.concatenate([
                    np.array([ 0.6]),
                    np.array([0, 0, 0]),
                    np.array([0, 0, 0]),
                    np.array([ 0.0]),
                    # 21 dof
                    np.array([
                        0.25, -1.4, 0.0, -0.5, # left arm
                        0.25, 1.4, 0.0, 0.5, # right arm
                        0.0, # waist
                        -0.1, 0.0, 0.0, 0.2, -0.1, 0.0, # left leg
                        -0.1, 0.0, 0.0, 0.2, -0.1, 0.0, # right leg
                    ])
                ])

DEFAULT_MIMIC_OBS_TODDY = np.concatenate([
                    np.array([ 0.3]),
                    np.array([0, 0, 0]),
                    np.array([0, 0, 0]),
                    np.array([ 0.0]),
                    # 21 dof
                    np.array([
                        0.0, 0.0, # waist (2)
                        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, # left leg (6)
                        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, # right leg (6)
                        0, -0.3, 0, 0.0, # left arm (4)
                        0, -0.3, 0, 0.0, # right arm (4)
                      
                    ])
                ])

DEFAULT_MIMIC_OBS = {
    "unitree_g1": DEFAULT_MIMIC_OBS_G1,
    "unitree_g1_mixed_mode": DEFAULT_MIMIC_OBS_G1_MIXED_MODE,
    "unitree_g1_with_hands": DEFAULT_MIMIC_OBS_G1,
    "amazing_hand": DEFAULT_MIMIC_OBS_G1,  # Use same as G1 with hands
    "booster_t1": DEFAULT_MIMIC_OBS_T1,
    "stanford_toddy": DEFAULT_MIMIC_OBS_TODDY,
}


DEFAULT_HAND_POSE = {
    "unitree_g1": 
    {
        "left": {
            "open": np.array([0, 0, 0, 0, 0, 0, 0]),
            "close": np.array([
                    # left (thumb, middle, index)
                    0, 1.0, 1.74, -1.57, -1.74, -1.57, -1.74,
                ]),
            # "open_pinch":
            #             np.array([0, 0, 0, -1.57, -1.74, 0, 0,]),
            # "close_pinch": np.array([
            #         # left (thumb, middle, index)
            #         -0.8, 0.7037, 0.2937, -1.57, -1.74, -1.2, -1.4,
            #     ])
            "open_pinch":
                        np.array([0, 0, 0, 0, 0, -1.57, -1.74]),
            "close_pinch": np.array([
                    # left (thumb, middle, index)
                    0.8, 0.7037, 0.2937,  -1.57, -1.74, -1.57, -1.74,
                ])
        },
        "right": {
            "open": np.array([0, 0, 0, 0, 0, 0, 0]),
            "close": np.array([
                    # right (thumb, middle, index)
                    0, -1.0, -1.74, 1.57, 1.74, 1.57, 1.74,
                ]),
            # "open_pinch":
            #             np.array([0, 0, 0, 1.57, 1.74, 0, 0,]),
            # "close_pinch": np.array([
            #         # right (thumb, middle, index)
            #         -0.8, -0.7037, -0.2937, 1.57, 1.74, 1.2, 1.4, 
            #     ])
            "open_pinch":
                        np.array([0, 0, 0, 0, 0, 1.57, 1.74]),
            "close_pinch": np.array([
                    # right (thumb, middle, index)
                    0.8, -0.7037, -0.2937, 1.57, 1.74, 1.57, 1.74
                ])
        },
    },
    "unitree_g1_with_hands": 
    {
        "left": {
            "open": np.array([0, 0, 0, 0, 0, 0, 0]),
            "close": np.array([
                    # left (thumb, index, middle)
                    0, 1.0, 1.74, -1.57, -1.74, -1.57, -1.74,
                ])
        },
        "right": {
            "open": np.array([0, 0, 0, 0, 0, 0, 0]),
            "close": np.array([
                    # right (thumb, index, middle)
                    0, -1.0, -1.74, 1.57, 1.74, 1.57, 1.74,
                ])
        },
    },
    "booster_t1": 
    {
        "left": {
            "open": np.array([0, 0]), # parallel gripper
            "close": np.array([0, 0]), # parallel gripper
        },
        "right": {
            "open": np.array([0, 0]), # parallel gripper
            "close": np.array([0, 0]), # parallel gripper
        },
    },
    "stanford_toddy":
    {
        "left": {
            "open": np.array([0, 0]), # parallel gripper
            "close": np.array([0, 0]), # parallel gripper
        },
        "right": {
            "open": np.array([0, 0]), # parallel gripper
            "close": np.array([0, 0]), # parallel gripper
        },
    },
    "amazing_hand":
    {
        "left": {
            # 8 DOF: [Index_0, Index_1, Middle_0, Middle_1, Ring_0, Ring_1, Thumb_0, Thumb_1]
            # Open pose: -35 to +35 degrees → -0.61 to +0.61 radians
            "open": np.array([-0.61, 0.61, -0.61, 0.61, -0.61, 0.61, -0.61, 0.61]),
            # Close pose: 90 to -90 degrees → 1.57 to -1.57 radians
            "close": np.array([1.57, -1.57, 1.57, -1.57, 1.57, -1.57, 1.57, -1.57]),
        },
        "right": {
            # 8 DOF: [Index_0, Index_1, Middle_0, Middle_1, Ring_0, Ring_1, Thumb_0, Thumb_1]
            "open": np.array([-0.61, 0.61, -0.61, 0.61, -0.61, 0.61, -0.61, 0.61]),
            "close": np.array([1.57, -1.57, 1.57, -1.57, 1.57, -1.57, 1.57, -1.57]),
        },
    },
}
