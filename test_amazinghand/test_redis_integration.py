#!/usr/bin/env python3
"""
Test 3: Redis Integration Test
Tests Redis communication with 8D hand arrays
"""

import sys
import os

# Add TWIST2 to path
sys.path.insert(0, '/home/kota-ueda/TWIST2/deploy_real')

import redis
import json
import time
import numpy as np


def test_redis_hand_communication():
    """Test Redis integration with AmazingHand 8D arrays"""

    print("=" * 70)
    print("TEST 3: Redis Integration with 8D Hand Arrays")
    print("=" * 70)
    print()

    # Connect to Redis
    print("Step 1: Connecting to Redis...")
    print("-" * 70)
    try:
        redis_client = redis.Redis(host='localhost', port=6379, db=0)
        redis_client.ping()
        print("✅ Redis connected\n")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Start Redis: redis-server &")
        print("  2. Check if running: redis-cli ping")
        print("=" * 70)
        return False

    # Test poses (8D arrays)
    test_poses = {
        "open": np.array([-0.61, 0.61, -0.61, 0.61, -0.61, 0.61, -0.61, 0.61]),
        "close": np.array([1.57, -1.57, 1.57, -1.57, 1.57, -1.57, 1.57, -1.57]),
        "half": np.array([0.48, -0.48, 0.48, -0.48, 0.48, -0.48, 0.48, -0.48])
    }

    print("Step 2: Testing Redis write/read for hand poses...")
    print("-" * 70)

    for pose_name, pose in test_poses.items():
        print(f"\nTesting '{pose_name}' pose...")

        # Send to Redis (simulating xrobot_teleop)
        redis_client.set(
            "action_hand_left_unitree_g1_with_hands",
            json.dumps(pose.tolist())
        )
        redis_client.set(
            "action_hand_right_unitree_g1_with_hands",
            json.dumps(pose.tolist())
        )
        redis_client.set("t_action", int(time.time() * 1000))

        # Read back (simulating server_low_level)
        left_data = json.loads(
            redis_client.get("action_hand_left_unitree_g1_with_hands")
        )
        right_data = json.loads(
            redis_client.get("action_hand_right_unitree_g1_with_hands")
        )
        timestamp = int(redis_client.get("t_action"))

        # Validate
        assert len(left_data) == 8, f"Expected 8 DOF, got {len(left_data)}"
        assert len(right_data) == 8, f"Expected 8 DOF, got {len(right_data)}"
        assert np.allclose(left_data, pose, atol=0.001), "Left data mismatch"
        assert np.allclose(right_data, pose, atol=0.001), "Right data mismatch"

        print(f"  Left:  {left_data}")
        print(f"  Right: {right_data}")
        print(f"  Timestamp: {timestamp}")
        print(f"  ✅ {pose_name} pose verified (8 DOF)")

        time.sleep(0.2)

    # Test dimension compatibility check
    print("\nStep 3: Testing dimension validation...")
    print("-" * 70)

    # Test 7D array (should be detected)
    wrong_dim_array = [0, 0, 0, 0, 0, 0, 0]  # 7 DOF
    redis_client.set(
        "action_hand_left_unitree_g1_with_hands",
        json.dumps(wrong_dim_array)
    )

    read_back = json.loads(
        redis_client.get("action_hand_left_unitree_g1_with_hands")
    )
    print(f"  7D array test: {len(read_back)} DOF")
    if len(read_back) != 8:
        print(f"  ⚠️  WARNING: Non-8D array detected (expected for compatibility test)")
    else:
        print(f"  ✅ Dimension check working")

    # Cleanup
    print("\nStep 4: Cleaning up Redis keys...")
    print("-" * 70)
    redis_client.delete("action_hand_left_unitree_g1_with_hands")
    redis_client.delete("action_hand_right_unitree_g1_with_hands")
    redis_client.delete("t_action")
    print("✅ Redis keys cleaned up")

    print("\n" + "=" * 70)
    print("✅ TEST 3 PASSED - Redis integration working correctly!")
    print("=" * 70)
    return True


if __name__ == '__main__':
    success = test_redis_hand_communication()
    sys.exit(0 if success else 1)
