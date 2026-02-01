#!/usr/bin/env python3
"""
B3M Neck Controller for G1 (Redis版)
PC側のxrobot_teleopからRedis経由でNeckデータを受信してB3Mサーボを制御

使用方法（G1上で実行）:
    python b3m_neck_controller_redis.py \
        --redis_ip 192.168.123.222 \
        --port /dev/ttyUSB0
"""

import time
import json
import redis
import numpy as np

# B3M Controller
from b3m_controller import B3MController


class B3MNeckControllerRedis:
    """Redis経由でNeckデータを受信してB3Mサーボを制御"""

    def __init__(
        self,
        redis_ip: str = "192.168.123.222",
        redis_port: int = 6379,
        serial_port: str = "/dev/ttyUSB0",
        baudrate: int = 1500000,
    ):
        """
        Initialize B3M Neck Controller (Redis版)

        Args:
            redis_ip: RedisサーバーのIPアドレス（PC側）
            redis_port: Redisポート
            serial_port: B3M用シリアルポート
            baudrate: 通信速度（1.5Mbps推奨）
        """
        print("=" * 60)
        print("  B3M Neck Controller (Redis版)")
        print("  PC (Redis) → G1 → B3M Neck")
        print("=" * 60)
        print(f"\nRedis server: {redis_ip}:{redis_port}")
        print(f"Serial port: {serial_port}")
        print(f"Baudrate: {baudrate}\n")

        # Redis接続
        print("Step 1: Connecting to Redis...")
        try:
            self.redis_client = redis.Redis(host=redis_ip, port=redis_port, db=0)
            self.redis_client.ping()
            print("✅ Redis connected\n")
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            print("\nPlease check:")
            print(f"  1. Redis server is running on PC ({redis_ip})")
            print("  2. Firewall allows connection")
            print("  3. PC and G1 are on same network (Ethernet)")
            raise

        # B3M controller初期化
        print("Step 2: Initializing B3M controller...")
        self.controller = B3MController(serial_port, baudrate)

        # Motor IDs
        self.YAW_MOTOR_ID = 0
        self.PITCH_MOTOR_ID = 1

        # B3M angle range (degrees)
        self.YAW_RANGE = (-80, 80)
        self.PITCH_RANGE = (-60, 60)

        # Calibration offsets
        self.yaw_offset = 0.0
        self.pitch_offset = 0.0

        # Load calibration if exists
        self._load_calibration()

        # Initialize motors
        self._initialize_motors()

        print()
        print("=" * 60)
        print("✅ B3M Neck Controller initialized!")
        print("=" * 60)
        print()

    def _initialize_motors(self):
        """Initialize yaw and pitch motors."""
        print("🔧 Initializing B3M motors...")

        # Enable torque
        self.controller.enable_torque(self.YAW_MOTOR_ID)
        self.controller.enable_torque(self.PITCH_MOTOR_ID)

        # Move to center
        self.controller.set_position(self.YAW_MOTOR_ID, 0)
        self.controller.set_position(self.PITCH_MOTOR_ID, 0)

        print("✅ B3M motors initialized and centered\n")

    def _load_calibration(self):
        """キャリブレーションデータをファイルから読み込み"""
        try:
            with open("b3m_calibration.txt", "r") as f:
                self.yaw_offset = float(f.readline().strip())
                self.pitch_offset = float(f.readline().strip())
            print(f"📂 Calibration loaded:")
            print(f"   Yaw offset: {self.yaw_offset:+.2f}°")
            print(f"   Pitch offset: {self.pitch_offset:+.2f}°")
            return True
        except FileNotFoundError:
            print("📂 No calibration file found (using zero offset)")
            return False
        except Exception as e:
            print(f"⚠️ Calibration load failed: {e}")
            return False

    def set_neck_position(self, yaw_deg, pitch_deg):
        """
        Set neck position with calibration offset applied.

        Args:
            yaw_deg: Yaw angle in degrees
            pitch_deg: Pitch angle in degrees
        """
        try:
            # Apply offset
            yaw_with_offset = -yaw_deg - self.yaw_offset
            pitch_with_offset = -pitch_deg - self.pitch_offset

            # Clamp to safe range
            yaw_with_offset = np.clip(yaw_with_offset, self.YAW_RANGE[0], self.YAW_RANGE[1])
            pitch_with_offset = np.clip(pitch_with_offset, self.PITCH_RANGE[0], self.PITCH_RANGE[1])

            # Send to motors
            self.controller.set_position(self.YAW_MOTOR_ID, yaw_with_offset)
            time.sleep(0.001)  # Daisy-chain delay
            self.controller.set_position(self.PITCH_MOTOR_ID, pitch_with_offset)

            return True
        except Exception as e:
            print(f"⚠️ Error setting position: {e}")
            return False

    def run(self, freq=50):
        """
        Main control loop - read from Redis and control B3M.

        Args:
            freq: Control frequency in Hz (default: 50Hz)
        """
        print(f"🎮 Starting neck control @ {freq}Hz...")
        print("📡 Waiting for neck data from PC (Redis)...")
        print("Press Ctrl+C to stop.\n")

        dt = 1.0 / freq
        last_yaw = 0.0
        last_pitch = 0.0
        loop_count = 0

        try:
            while True:
                start_time = time.time()
                loop_count += 1

                # Read neck data from Redis
                try:
                    neck_data = self.redis_client.get("action_neck_unitree_g1_with_hands")

                    if neck_data:
                        # Parse neck data
                        # Format: [yaw_rad, pitch_rad] (from xrobot_teleop)
                        neck_angles = json.loads(neck_data)

                        if len(neck_angles) >= 2:
                            # Convert radians to degrees
                            yaw_deg = np.rad2deg(neck_angles[0])
                            pitch_deg = np.rad2deg(neck_angles[1])

                            # Update only if change > 0.5 degrees
                            if abs(yaw_deg - last_yaw) > 0.5 or abs(pitch_deg - last_pitch) > 0.5:
                                success = self.set_neck_position(yaw_deg, pitch_deg)
                                if success:
                                    last_yaw = yaw_deg
                                    last_pitch = pitch_deg

                                    # Print status every 10th update
                                    if loop_count % 10 == 0:
                                        print(f"Neck: Yaw={yaw_deg:+6.1f}°, Pitch={pitch_deg:+6.1f}°")
                    else:
                        # No data yet from PC
                        if loop_count == 1:
                            print("⏳ Waiting for neck commands from PC...")
                            print("   Make sure xrobot_teleop is running on PC")

                except Exception as e:
                    print(f"⚠️ Error reading Redis: {e}")

                # Maintain frequency
                elapsed = time.time() - start_time
                sleep_time = max(0, dt - elapsed)
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping neck control...")
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup and return to center."""
        print("🔄 Returning to center position...")
        self.controller.set_position(self.YAW_MOTOR_ID, 0)
        self.controller.set_position(self.PITCH_MOTOR_ID, 0)
        time.sleep(0.5)

        print("🔌 Disabling torque...")
        self.controller.disable_torque(self.YAW_MOTOR_ID)
        self.controller.disable_torque(self.PITCH_MOTOR_ID)

        self.controller.close()
        print("✅ B3M Neck Controller stopped.\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="B3M Neck Controller (Redis版) - G1上で実行"
    )
    parser.add_argument("--redis_ip", type=str, default="192.168.123.222",
                       help="Redis server IP (PC側)")
    parser.add_argument("--redis_port", type=int, default=6379,
                       help="Redis port")
    parser.add_argument("--port", type=str, default="/dev/ttyUSB0",
                       help="Serial port for B3M")
    parser.add_argument("--baudrate", type=int, default=1500000,
                       help="Baud rate (1.5Mbps)")
    parser.add_argument("--freq", type=int, default=50,
                       help="Control frequency (Hz)")

    args = parser.parse_args()

    # Initialize controller
    controller = B3MNeckControllerRedis(
        redis_ip=args.redis_ip,
        redis_port=args.redis_port,
        serial_port=args.port,
        baudrate=args.baudrate
    )

    # Run
    controller.run(freq=args.freq)
