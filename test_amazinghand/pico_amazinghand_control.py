#!/usr/bin/env python3
"""
Pico Controller → AmazingHand Simple Control
G1本体なしでPicoコントローラーからAmazingHandを制御

使用方法:
1. ターミナル1: xrobot_teleop_to_robot_w_hand.py --robot amazing_hand
2. ターミナル2: このスクリプト
"""

import sys
import os
import time
import json

# Add TWIST2 to path
sys.path.insert(0, '/home/kota-ueda/TWIST2/deploy_real')

import redis
import numpy as np
from robot_control.amazing_hand_wrapper import AmazingHandController


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Pico → AmazingHand Simple Control')
    parser.add_argument('--serial_port', type=str, default='/dev/ttyACM0',
                       help='Serial port for AmazingHand')
    parser.add_argument('--baudrate', type=int, default=1000000,
                       help='Baudrate for AmazingHand')
    parser.add_argument('--redis_ip', type=str, default='localhost',
                       help='Redis server IP')
    args = parser.parse_args()

    print("=" * 70)
    print("Pico Controller → AmazingHand Simple Control")
    print("=" * 70)
    print(f"Serial port: {args.serial_port}")
    print(f"Baudrate: {args.baudrate}")
    print(f"Redis IP: {args.redis_ip}")
    print()

    # Connect to Redis
    print("Step 1: Connecting to Redis...")
    try:
        redis_client = redis.Redis(host=args.redis_ip, port=6379, db=0)
        redis_client.ping()
        print("✅ Redis connected\n")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("\nPlease start Redis server: redis-server &")
        print("And start teleop: python xrobot_teleop_to_robot_w_hand.py --robot amazing_hand")
        return

    # Initialize AmazingHand controller
    print("Step 2: Initializing AmazingHand...")
    try:
        hand_ctrl = AmazingHandController(
            serial_port=args.serial_port,
            baudrate=args.baudrate,
            re_init=True
        )
    except Exception as e:
        print(f"❌ AmazingHand initialization failed: {e}")
        return

    print()
    print("=" * 70)
    print("🎮 Ready! Control AmazingHand with Pico controller:")
    print("   - Press index_trig to CLOSE hand (gradually)")
    print("   - Press grip to OPEN hand (gradually)")
    print("   - Press Ctrl+C to exit")
    print("=" * 70)
    print()

    # Control loop
    last_left_cmd = None
    last_right_cmd = None
    loop_count = 0

    try:
        while True:
            loop_count += 1

            # Read hand commands from Redis (sent by xrobot_teleop)
            try:
                left_data = redis_client.get("action_hand_left_unitree_g1_with_hands")
                right_data = redis_client.get("action_hand_right_unitree_g1_with_hands")

                if left_data and right_data:
                    left_cmd = np.array(json.loads(left_data), dtype=np.float32)
                    right_cmd = np.array(json.loads(right_data), dtype=np.float32)

                    # Check if command changed
                    if (last_left_cmd is None or
                        not np.allclose(left_cmd, last_left_cmd, atol=0.01) or
                        not np.allclose(right_cmd, last_right_cmd, atol=0.01)):

                        # Send to AmazingHand
                        hand_ctrl.ctrl_dual_hand(left_cmd, right_cmd)

                        # Print status every 10th update
                        if loop_count % 10 == 0:
                            left_norm = np.linalg.norm(left_cmd)
                            right_norm = np.linalg.norm(right_cmd)
                            print(f"[{loop_count:5d}] Left: {left_norm:5.2f} rad  Right: {right_norm:5.2f} rad")

                        last_left_cmd = left_cmd.copy()
                        last_right_cmd = right_cmd.copy()

                else:
                    # No data yet from teleop
                    if loop_count == 1:
                        print("⏳ Waiting for commands from xrobot_teleop...")
                        print("   Make sure xrobot_teleop is running with --robot amazing_hand")

            except Exception as e:
                print(f"⚠️ Error reading Redis: {e}")

            # Control frequency: ~50Hz
            time.sleep(0.02)

    except KeyboardInterrupt:
        print("\n\n🛑 Stopping...")

    finally:
        # Cleanup
        print("Returning to default pose...")
        hand_ctrl.initialize()
        hand_ctrl.close()
        print("✅ AmazingHand control stopped")
        print()


if __name__ == '__main__':
    main()
