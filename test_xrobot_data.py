#!/usr/bin/env python3
"""
Test script to check XRobot data availability
"""
import xrobotoolkit_sdk as xrt
import time

print("Initializing XRoboToolkit SDK...")
xrt.init()
print("SDK initialized")
time.sleep(1)

print("\nChecking data availability for 10 seconds...")
for i in range(20):
    body_available = xrt.is_body_data_available()
    print(f"[{i:2d}] Body data available: {body_available}")

    if body_available:
        body_poses = xrt.get_body_joints_pose()
        print(f"     Body poses length: {len(body_poses) if body_poses else 0}")
        if body_poses and len(body_poses) > 0:
            # Print first joint (Pelvis)
            print(f"     Pelvis: x={body_poses[0][0]:.3f}, y={body_poses[0][1]:.3f}, z={body_poses[0][2]:.3f}")

    time.sleep(0.5)

print("\nDone")
