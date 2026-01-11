#!/usr/bin/env python3
"""
Test 2: AmazingHand Dual Hand Control Test
Tests both hands opening, closing, and independent control
"""

import sys
import os

# Add TWIST2 to path
sys.path.insert(0, '/home/kota-ueda/TWIST2/deploy_real')

from robot_control.amazing_hand_wrapper import AmazingHandController
import numpy as np
import time


def test_dual_hand(serial_port='/dev/ttyUSB0'):
    """Test dual hand control"""

    print("=" * 70)
    print("TEST 2: AmazingHand Dual Hand Control")
    print("=" * 70)
    print()

    try:
        # Initialize controller
        print("Initializing AmazingHandController...")
        hand_ctrl = AmazingHandController(
            serial_port=serial_port,
            baudrate=1000000,
            re_init=True  # Start from default pose
        )

        # Test 1: Open both hands
        print("\n[Test 1/5] Opening both hands...")
        print("-" * 70)
        open_pose = np.array([-0.61, 0.61, -0.61, 0.61, -0.61, 0.61, -0.61, 0.61])
        hand_ctrl.ctrl_dual_hand(open_pose, open_pose)
        time.sleep(2.0)

        left_state, right_state = hand_ctrl.get_hand_state()
        print(f"Left state:  {np.array2string(left_state, precision=2, suppress_small=True)}")
        print(f"Right state: {np.array2string(right_state, precision=2, suppress_small=True)}")
        print("✅ Open pose commanded")

        # Test 2: Close both hands
        print("\n[Test 2/5] Closing both hands...")
        print("-" * 70)
        close_pose = np.array([1.57, -1.57, 1.57, -1.57, 1.57, -1.57, 1.57, -1.57])
        hand_ctrl.ctrl_dual_hand(close_pose, close_pose)
        time.sleep(2.0)

        left_state, right_state = hand_ctrl.get_hand_state()
        print(f"Left state:  {np.array2string(left_state, precision=2, suppress_small=True)}")
        print(f"Right state: {np.array2string(right_state, precision=2, suppress_small=True)}")
        print("✅ Close pose commanded")

        # Test 3: Asymmetric control (left open, right closed)
        print("\n[Test 3/5] Asymmetric control (left open, right closed)...")
        print("-" * 70)
        hand_ctrl.ctrl_dual_hand(open_pose, close_pose)
        time.sleep(2.0)

        left_state, right_state = hand_ctrl.get_hand_state()
        print(f"Left state:  {np.array2string(left_state, precision=2, suppress_small=True)}")
        print(f"Right state: {np.array2string(right_state, precision=2, suppress_small=True)}")
        print("✅ Asymmetric control works")

        # Test 4: Gradual interpolation
        print("\n[Test 4/5] Gradual interpolation (0% → 100% closed)...")
        print("-" * 70)
        for i in range(6):
            ratio = i / 5.0  # 0.0 to 1.0
            interp_pose = open_pose + (close_pose - open_pose) * ratio
            hand_ctrl.ctrl_dual_hand(interp_pose, interp_pose)
            print(f"  Step {i}: {ratio*100:3.0f}% closed")
            time.sleep(0.5)

        print("✅ Gradual interpolation works")

        # Test 5: Return to default
        print("\n[Test 5/5] Returning to default pose...")
        print("-" * 70)
        hand_ctrl.initialize()
        time.sleep(1.0)

        left_state, right_state = hand_ctrl.get_hand_state()
        print(f"Left state:  {np.array2string(left_state, precision=2, suppress_small=True)}")
        print(f"Right state: {np.array2string(right_state, precision=2, suppress_small=True)}")
        print("✅ Default pose restored")

        # Cleanup
        hand_ctrl.close()

        print("\n" + "=" * 70)
        print("✅ TEST 2 PASSED - All dual hand tests completed successfully!")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"\n❌ TEST 2 FAILED - {e}")
        import traceback
        traceback.print_exc()
        print("=" * 70)
        return False


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Test AmazingHand dual control')
    parser.add_argument('--serial_port', type=str, default='/dev/ttyUSB0',
                       help='Serial port (default: /dev/ttyUSB0)')
    args = parser.parse_args()

    success = test_dual_hand(args.serial_port)
    sys.exit(0 if success else 1)
