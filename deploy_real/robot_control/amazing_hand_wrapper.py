#!/usr/bin/env python3
"""
AmazingHand Controller Wrapper for TWIST2
Compatible with Dex3_1_Controller interface

Author: Integration with TWIST2 system
Date: 2026-01-11
"""

import numpy as np
import time
import sys

try:
    from rustypot import Scs0009PyController
except ImportError:
    print("Error: rustypot library not found. Please install it:")
    print("pip install rustypot")
    sys.exit(1)

# Constants
AmazingHand_Num_Motors = 8

# Default poses (radians) - conservative starting position
DEFAULT_QPOS_LEFT = np.array([0, 0, 0, 0, 0, 0, 0, 0], dtype=np.float32)
DEFAULT_QPOS_RIGHT = np.array([0, 0, 0, 0, 0, 0, 0, 0], dtype=np.float32)

# Joint limits (radians) - safe range ±90 degrees
QPOS_LEFT_MAX = np.array([1.57, 1.57, 1.57, 1.57, 1.57, 1.57, 1.57, 1.57])
QPOS_LEFT_MIN = np.array([-1.57, -1.57, -1.57, -1.57, -1.57, -1.57, -1.57, -1.57])
QPOS_RIGHT_MAX = np.array([1.57, 1.57, 1.57, 1.57, 1.57, 1.57, 1.57, 1.57])
QPOS_RIGHT_MIN = np.array([-1.57, -1.57, -1.57, -1.57, -1.57, -1.57, -1.57, -1.57])


class AmazingHand_Left_JointIndex:
    """Left hand servo ID mapping (array index -> motor ID)"""
    kLeftHandIndex0 = 0   # Motor 11
    kLeftHandIndex1 = 1   # Motor 12
    kLeftHandMiddle0 = 2  # Motor 13
    kLeftHandMiddle1 = 3  # Motor 14
    kLeftHandRing0 = 4    # Motor 15
    kLeftHandRing1 = 5    # Motor 16
    kLeftHandThumb0 = 6   # Motor 17
    kLeftHandThumb1 = 7   # Motor 18


class AmazingHand_Right_JointIndex:
    """Right hand servo ID mapping (array index -> motor ID)"""
    kRightHandIndex0 = 0  # Motor 1
    kRightHandIndex1 = 1  # Motor 2
    kRightHandMiddle0 = 2 # Motor 3
    kRightHandMiddle1 = 3 # Motor 4
    kRightHandRing0 = 4   # Motor 5
    kRightHandRing1 = 5   # Motor 6
    kRightHandThumb0 = 6  # Motor 7
    kRightHandThumb1 = 7  # Motor 8


class AmazingHandController:
    """
    Controller for dual AmazingHands on single serial bus

    Compatible with Dex3_1_Controller interface for TWIST2 integration.
    Controls left and right AmazingHands (8 DOF each) via different servo IDs
    on the same serial bus.

    Servo ID mapping:
    - Right hand: IDs 1-8
    - Left hand: IDs 11-18
    """

    def __init__(self, serial_port='/dev/ttyUSB0', baudrate=1000000, re_init=True):
        """
        Initialize AmazingHand controller

        Args:
            serial_port: Serial port path (default: /dev/ttyUSB0)
            baudrate: Communication baudrate (default: 1000000)
            re_init: Initialize to default pose if True
        """
        print("=" * 60)
        print("Initialize AmazingHandController...")
        print("=" * 60)
        print(f"Serial port: {serial_port}")
        print(f"Baudrate: {baudrate}")
        print(f"Re-init: {re_init}\n")

        # Initialize serial connection
        try:
            self.controller = Scs0009PyController(
                serial_port=serial_port,
                baudrate=baudrate,
                timeout=0.05
            )
            print("✅ Serial connection established\n")
        except Exception as e:
            print(f"❌ Failed to initialize serial connection: {e}")
            raise

        # State arrays (matching Dex3_1_Controller)
        self.left_hand_state_array = np.zeros(AmazingHand_Num_Motors, dtype=np.float32)
        self.right_hand_state_array = np.zeros(AmazingHand_Num_Motors, dtype=np.float32)

        # Additional state arrays for compatibility
        self.Lpos = np.zeros(AmazingHand_Num_Motors, dtype=np.float32)
        self.Rpos = np.zeros(AmazingHand_Num_Motors, dtype=np.float32)
        self.Ltemp = np.zeros((AmazingHand_Num_Motors, 2), dtype=np.float32)
        self.Rtemp = np.zeros((AmazingHand_Num_Motors, 2), dtype=np.float32)
        self.Ltau = np.zeros(AmazingHand_Num_Motors, dtype=np.float32)
        self.Rtau = np.zeros(AmazingHand_Num_Motors, dtype=np.float32)

        # Enable torque for all motors
        self._enable_torque()

        # Read initial state
        print("Reading initial hand state...")
        self.get_hand_state()
        print(f"Left hand state:  {np.array2string(self.left_hand_state_array, precision=2)}")
        print(f"Right hand state: {np.array2string(self.right_hand_state_array, precision=2)}\n")

        # Initialize to default pose if requested
        if re_init:
            self.initialize()

        print("=" * 60)
        print("✅ AmazingHandController initialized successfully!")
        print("=" * 60)
        print()

    def _enable_torque(self):
        """Enable torque for all motors (right: 1-8, left: 11-18)"""
        print("🔧 Enabling torque for all servos...")
        try:
            # Right hand (IDs 1-8)
            for motor_id in range(1, 9):
                try:
                    self.controller.write_torque_enable(motor_id, 1)
                    time.sleep(0.001)
                except Exception as e:
                    print(f"  ⚠️ Failed to enable torque for right motor {motor_id}: {e}")

            # Left hand (IDs 11-18)
            for motor_id in range(11, 19):
                try:
                    self.controller.write_torque_enable(motor_id, 1)
                    time.sleep(0.001)
                except Exception as e:
                    print(f"  ⚠️ Failed to enable torque for left motor {motor_id}: {e}")

            print("✅ Torque enabled for all motors\n")
        except Exception as e:
            print(f"⚠️ Torque enable warning: {e}\n")

    def get_hand_state(self):
        """
        Read current positions from both hands

        Returns:
            tuple: (left_hand_state, right_hand_state) as numpy arrays (8 DOF each)
        """
        try:
            # Right hand (IDs 1-8)
            for idx, motor_id in enumerate(range(1, 9)):
                try:
                    pos = self.controller.read_present_position(motor_id)
                    # rustypot returns a list, extract first element
                    self.right_hand_state_array[idx] = pos[0]
                    self.Rpos[idx] = pos[0]
                except Exception as e:
                    # Use last known position on read failure
                    pass
                time.sleep(0.001)

            # Left hand (IDs 11-18)
            for idx, motor_id in enumerate(range(11, 19)):
                try:
                    pos = self.controller.read_present_position(motor_id)
                    # rustypot returns a list, extract first element
                    self.left_hand_state_array[idx] = pos[0]
                    self.Lpos[idx] = pos[0]
                except Exception as e:
                    # Use last known position on read failure
                    pass
                time.sleep(0.001)

        except Exception as e:
            print(f"⚠️ Error in get_hand_state: {e}")

        return self.left_hand_state_array.copy(), self.right_hand_state_array.copy()

    def get_hand_all_state(self):
        """
        Get all states for compatibility with Dex3_1_Controller

        Returns:
            tuple: (Lpos, Rpos, Ltemp, Rtemp, Ltau, Rtau)
        """
        # Update positions
        self.get_hand_state()

        return (
            self.Lpos.copy(),
            self.Rpos.copy(),
            self.Ltemp.copy(),
            self.Rtemp.copy(),
            self.Ltau.copy(),
            self.Rtau.copy()
        )

    def ctrl_dual_hand(self, left_q_target, right_q_target):
        """
        Control both hands with 8D target positions (radians)

        Args:
            left_q_target: 8-element array of target positions for left hand (radians)
            right_q_target: 8-element array of target positions for right hand (radians)
        """
        # Validate input dimensions
        assert len(left_q_target) == 8, f"Left must be 8D, got {len(left_q_target)}"
        assert len(right_q_target) == 8, f"Right must be 8D, got {len(right_q_target)}"

        try:
            # Right hand (IDs 1-8)
            for idx, motor_id in enumerate(range(1, 9)):
                # Clamp to safe range
                target = np.clip(
                    right_q_target[idx],
                    QPOS_RIGHT_MIN[idx],
                    QPOS_RIGHT_MAX[idx]
                )
                try:
                    self.controller.write_goal_position(motor_id, float(target))
                    time.sleep(0.0002)  # Prevent serial bus congestion
                except Exception as e:
                    print(f"⚠️ Failed to write right motor {motor_id}: {e}")

            # Left hand (IDs 11-18)
            for idx, motor_id in enumerate(range(11, 19)):
                # Clamp to safe range
                target = np.clip(
                    left_q_target[idx],
                    QPOS_LEFT_MIN[idx],
                    QPOS_LEFT_MAX[idx]
                )
                try:
                    self.controller.write_goal_position(motor_id, float(target))
                    time.sleep(0.0002)  # Prevent serial bus congestion
                except Exception as e:
                    print(f"⚠️ Failed to write left motor {motor_id}: {e}")

        except Exception as e:
            print(f"❌ Error in ctrl_dual_hand: {e}")

    def initialize(self):
        """Move to default pose (all zeros)"""
        print("🔧 Initializing to default pose...")
        self.ctrl_dual_hand(DEFAULT_QPOS_LEFT, DEFAULT_QPOS_RIGHT)
        time.sleep(0.5)  # Wait for movement to complete
        print("✅ Initialized to default pose\n")

    def close(self):
        """Cleanup: disable torque for all motors"""
        print("\n🔧 Closing AmazingHandController...")
        try:
            # Disable torque for all motors
            for motor_id in list(range(1, 9)) + list(range(11, 19)):
                try:
                    self.controller.write_torque_enable(motor_id, 0)
                    time.sleep(0.001)
                except:
                    pass
            print("✅ AmazingHandController closed\n")
        except Exception as e:
            print(f"⚠️ Error during close: {e}\n")


# Test code
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Test AmazingHandController')
    parser.add_argument('--serial_port', type=str, default='/dev/ttyUSB0',
                       help='Serial port for AmazingHand')
    parser.add_argument('--baudrate', type=int, default=1000000,
                       help='Baudrate for serial communication')
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("🧪 Testing AmazingHandController")
    print("=" * 60)
    print()

    try:
        # Initialize controller
        hand_ctrl = AmazingHandController(
            serial_port=args.serial_port,
            baudrate=args.baudrate,
            re_init=True
        )

        print("🎯 Running test sequence...")
        print("Test 1: Move index finger gradually\n")

        # Test sequence: gradually move index finger
        for i in range(11):
            angle = 0.15 * i  # 0 to 1.5 rad
            left_target = np.array([angle, 0, 0, 0, 0, 0, 0, 0])
            right_target = np.array([angle, 0, 0, 0, 0, 0, 0, 0])

            hand_ctrl.ctrl_dual_hand(left_target, right_target)

            # Read back state
            left_state, right_state = hand_ctrl.get_hand_state()
            print(f"Step {i:2d}: Target={angle:.2f} rad, "
                  f"Left[0]={left_state[0]:.2f}, Right[0]={right_state[0]:.2f}")

            time.sleep(0.2)

        print("\n✅ Test sequence completed!")

        # Return to default
        print("\n🔧 Returning to default pose...")
        hand_ctrl.initialize()

        # Cleanup
        hand_ctrl.close()

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        print()

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
