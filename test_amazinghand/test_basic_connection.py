#!/usr/bin/env python3
"""
Test 1: AmazingHand Basic Connection Test
Verifies serial connection to AmazingHand and checks all 16 motors
"""

import sys
import os

# Add TWIST2 to path
sys.path.insert(0, '/home/kota-ueda/TWIST2/deploy_real')

from rustypot import Scs0009PyController
import time


def test_connection(serial_port='/dev/ttyUSB0', baudrate=1000000):
    """Test serial connection and motor communication"""

    print("=" * 70)
    print("TEST 1: AmazingHand Serial Connection and Motor Communication")
    print("=" * 70)
    print(f"Serial port: {serial_port}")
    print(f"Baudrate: {baudrate}\n")

    try:
        print("Step 1: Initializing serial controller...")
        controller = Scs0009PyController(
            serial_port=serial_port,
            baudrate=baudrate,
            timeout=0.5
        )
        print("✅ Serial connection established\n")

        # Test right hand motors (IDs 1-8)
        print("Step 2: Testing RIGHT hand motors (IDs 1-8)...")
        print("-" * 70)
        right_success_count = 0
        for motor_id in range(1, 9):
            try:
                pos = controller.read_present_position(motor_id)
                # rustypot returns a list, extract first element
                print(f"  Motor {motor_id:2d}: {pos[0]:7.3f} rad  ✅")
                right_success_count += 1
                time.sleep(0.01)
            except Exception as e:
                print(f"  Motor {motor_id:2d}: FAILED - {e}  ❌")

        print(f"\nRight hand: {right_success_count}/8 motors responding")

        # Test left hand motors (IDs 11-18)
        print("\nStep 3: Testing LEFT hand motors (IDs 11-18)...")
        print("-" * 70)
        left_success_count = 0
        for motor_id in range(11, 19):
            try:
                pos = controller.read_present_position(motor_id)
                # rustypot returns a list, extract first element
                print(f"  Motor {motor_id:2d}: {pos[0]:7.3f} rad  ✅")
                left_success_count += 1
                time.sleep(0.01)
            except Exception as e:
                print(f"  Motor {motor_id:2d}: FAILED - {e}  ❌")

        print(f"\nLeft hand: {left_success_count}/8 motors responding")

        # Summary
        print("\n" + "=" * 70)
        total_success = right_success_count + left_success_count
        print(f"Total: {total_success}/16 motors responding")

        if total_success == 16:
            print("✅ TEST 1 PASSED - All motors responding!")
            print("=" * 70)
            return True
        elif total_success >= 14:
            print("⚠️  TEST 1 PARTIAL - Most motors responding")
            print("   Check power supply and connections for failed motors")
            print("=" * 70)
            return True
        else:
            print("❌ TEST 1 FAILED - Too many motors not responding")
            print("   Check:")
            print("   1. Power supply connected (5V, 2A+)")
            print("   2. Waveshare adapter properly connected")
            print("   3. Motor IDs set correctly (right: 1-8, left: 11-18)")
            print("=" * 70)
            return False

    except Exception as e:
        print(f"\n❌ TEST 1 FAILED - Serial connection error")
        print(f"   Error: {e}")
        print("\n   Troubleshooting:")
        print(f"   1. Check if {serial_port} exists: ls -l {serial_port}")
        print("   2. Check permissions: sudo chmod 666 " + serial_port)
        print("   3. Try different port (might be /dev/ttyACM0)")
        print("=" * 70)
        return False


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Test AmazingHand connection')
    parser.add_argument('--serial_port', type=str, default='/dev/ttyUSB0',
                       help='Serial port (default: /dev/ttyUSB0)')
    parser.add_argument('--baudrate', type=int, default=1000000,
                       help='Baudrate (default: 1000000)')
    args = parser.parse_args()

    success = test_connection(args.serial_port, args.baudrate)
    sys.exit(0 if success else 1)
