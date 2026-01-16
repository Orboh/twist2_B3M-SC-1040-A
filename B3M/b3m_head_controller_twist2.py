#!/usr/bin/env python3
"""
B3M Head Controller for TWIST2 (完全独立版)
近藤科学 B3M-SB-1040-A サーボモーター版

依存関係を最小化 - xrobotoolkit_sdkのみ必要
"""

import time
import numpy as np
from scipy.spatial.transform import Rotation as R

# XRoboToolkit SDK（TWIST2に含まれる）
# キャリブレーションモードでは不要
try:
    import xrobotoolkit_sdk as xrt
    XRT_AVAILABLE = True
except ImportError:
    xrt = None
    XRT_AVAILABLE = False

# B3M Controller
from b3m_controller import B3MController


def human_head_to_robot_neck(smplx_data=None):
    """
    Extract neck angle from headset pose (TWIST2の関数をコピー)

    Args:
        smplx_data: Dict with 'Spine3' and 'Head' poses

    Returns:
        (neck_yaw_rad, neck_pitch_rad): Neck angles in radians
    """
    if smplx_data is None:
        return 0.0, 0.0

    spine_rotation_wxyz = smplx_data['Spine3'][1]  # [w, x, y, z]
    head_rotation_wxyz = smplx_data['Head'][1]  # [w, x, y, z]

    # Convert from [w, x, y, z] to [x, y, z, w] for scipy (old version)
    spine_rotation_xyzw = [spine_rotation_wxyz[1], spine_rotation_wxyz[2],
                           spine_rotation_wxyz[3], spine_rotation_wxyz[0]]
    head_rotation_xyzw = [head_rotation_wxyz[1], head_rotation_wxyz[2],
                          head_rotation_wxyz[3], head_rotation_wxyz[0]]

    # Convert to rotation objects
    spine_rotation = R.from_quat(spine_rotation_xyzw)
    head_rotation = R.from_quat(head_rotation_xyzw)

    # Compute head rotation relative to spine
    relative_rotation = spine_rotation.inv() * head_rotation

    # Convert to Euler angles (roll, pitch, yaw)
    roll, pitch, yaw = relative_rotation.as_euler('xyz', degrees=True)

    # Map to neck angles
    neck_yaw = -pitch
    neck_pitch = roll

    # Convert to radians
    neck_yaw = np.deg2rad(neck_yaw)
    neck_pitch = np.deg2rad(neck_pitch)

    return neck_yaw, neck_pitch


class B3MHeadControllerTWIST2:
    """PICO VR headset tracking with B3M servo motors - 完全独立版"""

    def __init__(
        self,
        port: str = "/dev/ttyUSB0",
        baudrate: int = 1500000,
    ):
        """
        Initialize B3M Head Controller

        Args:
            port: Serial port for B3M communication
            baudrate: Communication speed (1.5Mbps recommended)
        """
        print("=" * 60)
        print("  B3M Head Controller for TWIST2")
        print("  PICO VR Headset → B3M Neck Motors")
        print("=" * 60)
        print("\n🚀 Initializing...")

        # XRoboToolkit SDK初期化（キャリブレーションモードでは不要）
        if XRT_AVAILABLE:
            try:
                xrt.init()
                print("✅ XRoboToolkit SDK initialized (PICO VR connected)")
            except Exception as e:
                print(f"⚠️ Failed to initialize XRoboToolkit: {e}")
                print("Note: XRoboToolkit is not required for calibration mode")
        else:
            print("ℹ️ XRoboToolkit SDK not available (OK for calibration mode)")

        # B3M controller初期化
        self.controller = B3MController(port, baudrate)

        # Motor IDs
        self.YAW_MOTOR_ID = 0
        self.PITCH_MOTOR_ID = 1

        # B3M angle range (degrees)
        self.YAW_RANGE = (-80, 80)
        self.PITCH_RANGE = (-60, 60)

        # Scale factor
        self.scale = 1.5

        # Calibration offsets
        self.yaw_offset = 0.0
        self.pitch_offset = 0.0

        # Debug mode
        self.debug = False

        # Initialize motors
        self._initialize_motors()

    def _initialize_motors(self):
        """Initialize yaw and pitch motors."""
        print("\n🔧 Initializing B3M motors...")

        # Enable torque
        self.controller.enable_torque(self.YAW_MOTOR_ID)
        self.controller.enable_torque(self.PITCH_MOTOR_ID)

        # Move to center
        self.controller.set_position(self.YAW_MOTOR_ID, 0)
        self.controller.set_position(self.PITCH_MOTOR_ID, 0)

        print("✅ B3M motors initialized and centered\n")

    def calibrate(self):
        """
        キャリブレーションモード
        現在のモーター位置を0度基準として設定
        """
        print("\n" + "=" * 60)
        print("  🎯 CALIBRATION MODE")
        print("=" * 60)
        print("\n手順:")
        print("1. 現在のモーター位置を確認します（トルクONのまま）")
        print("2. 手動でロボットの首を物理的に0度の位置に合わせてください")
        print("   （モーターを手で優しく動かしてください）")
        print("3. 位置が決まったらEnterキーを押してください\n")

        # まず現在位置を読み取ってテスト（トルクON状態）
        print("📏 テスト: トルクON状態で位置読み取り...")
        test_yaw = self.controller.read_position(self.YAW_MOTOR_ID, debug=True)
        test_pitch = self.controller.read_position(self.PITCH_MOTOR_ID, debug=True)

        if test_yaw is not None:
            print(f"✅ 現在のYaw位置: {test_yaw:+.2f}°")
        if test_pitch is not None:
            print(f"✅ 現在のPitch位置: {test_pitch:+.2f}°")
        print()

        input("首を0度の位置に合わせたらEnterキーを押してください...")

        # 現在位置を読み取り（キャリブレーション基準）
        print("\n📏 0度基準位置を読み取り中...")
        print("\n--- Yaw Motor (ID 0) ---")
        yaw_current = self.controller.read_position(self.YAW_MOTOR_ID, debug=True)
        print("\n--- Pitch Motor (ID 1) ---")
        pitch_current = self.controller.read_position(self.PITCH_MOTOR_ID, debug=True)

        if yaw_current is not None and pitch_current is not None:
            self.yaw_offset = yaw_current
            self.pitch_offset = pitch_current

            print(f"\n✅ キャリブレーション完了!")
            print(f"   Yaw offset: {self.yaw_offset:+.2f}°")
            print(f"   Pitch offset: {self.pitch_offset:+.2f}°")
            print(f"\n   この位置を0度基準として記録しました。")

            # オフセットをファイルに保存
            self._save_calibration()
        else:
            print("\n❌ キャリブレーション失敗")
            print("   モーターから位置情報を読み取れませんでした。")
            print("   B3Mモーターの通信を確認してください。")
            self.yaw_offset = 0.0
            self.pitch_offset = 0.0

        print()

    def _save_calibration(self):
        """キャリブレーションデータをファイルに保存"""
        try:
            with open("b3m_calibration.txt", "w") as f:
                f.write(f"{self.yaw_offset}\n")
                f.write(f"{self.pitch_offset}\n")
            print("💾 キャリブレーションデータを保存しました (b3m_calibration.txt)")
        except Exception as e:
            print(f"⚠️ 保存失敗: {e}")

    def _load_calibration(self):
        """キャリブレーションデータをファイルから読み込み"""
        try:
            with open("b3m_calibration.txt", "r") as f:
                self.yaw_offset = float(f.readline().strip())
                self.pitch_offset = float(f.readline().strip())
            print(f"📂 キャリブレーションデータを読み込みました")
            print(f"   Yaw offset: {self.yaw_offset:+.2f}°")
            print(f"   Pitch offset: {self.pitch_offset:+.2f}°")
            return True
        except FileNotFoundError:
            print("📂 キャリブレーションファイルが見つかりません（初回起動またはキャリブレーション未実施）")
            return False
        except Exception as e:
            print(f"⚠️ 読み込み失敗: {e}")
            return False

    def get_neck_angles_from_headset(self):
        """
        Get neck angles from PICO VR headset.

        Returns:
            (yaw_deg, pitch_deg): Neck angles in degrees
        """
        try:
            # Get headset pose from XRoboToolkit
            headset_pose = xrt.get_headset_pose()
            # headset_pose: [x, y, z, qx, qy, qz, qw]

            # Convert to numpy array for easier indexing
            headset_pose = np.array(headset_pose)

            # 🔍 デバッグ: 生データを表示
            if self.debug:
                print(f"\n📊 Raw headset_pose: {headset_pose}")
                print(f"   Position (x,y,z): [{headset_pose[0]:.3f}, {headset_pose[1]:.3f}, {headset_pose[2]:.3f}]")
                print(f"   Quaternion (qx,qy,qz,qw): [{headset_pose[3]:.3f}, {headset_pose[4]:.3f}, {headset_pose[5]:.3f}, {headset_pose[6]:.3f}]")

            # Convert to TWIST2's smplx_data format
            smplx_data = {
                'Spine3': ([0, 0, 0], [1, 0, 0, 0]),  # Dummy spine
                'Head': (
                    headset_pose[:3].tolist(),  # Position
                    [headset_pose[6], headset_pose[3], headset_pose[4], headset_pose[5]]  # Quaternion [w, x, y, z]
                )
            }

            # Use TWIST2's neck retarget function
            neck_yaw_rad, neck_pitch_rad = human_head_to_robot_neck(smplx_data)

            # 🔍 デバッグ: 計算結果を表示
            if self.debug:
                print(f"   Neck angles (rad): yaw={neck_yaw_rad:.3f}, pitch={neck_pitch_rad:.3f}")

            # Convert to degrees and apply scale
            neck_yaw_deg = np.rad2deg(neck_yaw_rad) * self.scale
            neck_pitch_deg = np.rad2deg(neck_pitch_rad) * self.scale

            # 🔍 デバッグ: スケール適用後
            if self.debug:
                print(f"   After scale (×{self.scale}): yaw={neck_yaw_deg:.1f}°, pitch={neck_pitch_deg:.1f}°")

            # Clamp to safe range
            neck_yaw_deg = np.clip(neck_yaw_deg, self.YAW_RANGE[0], self.YAW_RANGE[1])
            neck_pitch_deg = np.clip(neck_pitch_deg, self.PITCH_RANGE[0], self.PITCH_RANGE[1])

            # 🔍 デバッグ: 範囲制限後
            if self.debug:
                print(f"   Final (clamped): yaw={neck_yaw_deg:.1f}°, pitch={neck_pitch_deg:.1f}°")

            return neck_yaw_deg, neck_pitch_deg

        except Exception as e:
            print(f"⚠️ Error getting headset pose: {e}")
            import traceback
            if self.debug:
                traceback.print_exc()
            return 0.0, 0.0

    def set_neck_position(self, yaw_deg, pitch_deg):
        """
        Set neck position with calibration offset applied.

        Args:
            yaw_deg: Yaw angle in degrees (before calibration)
            pitch_deg: Pitch angle in degrees (before calibration)
        """
        try:
            # オフセットを適用（キャリブレーション後の基準からの角度）
            yaw_with_offset = -yaw_deg - self.yaw_offset
            pitch_with_offset = -pitch_deg - self.pitch_offset

            # 🔍 デバッグ: モーターに送信する値を表示
            if self.debug:
                print(f"   >>> Before offset: Yaw={-yaw_deg:.1f}°, Pitch={-pitch_deg:.1f}°")
                print(f"   >>> Offset: Yaw={self.yaw_offset:+.1f}°, Pitch={self.pitch_offset:+.1f}°")
                print(f"   >>> Sending to motors: Yaw(ID={self.YAW_MOTOR_ID})={yaw_with_offset:.1f}°, "
                      f"Pitch(ID={self.PITCH_MOTOR_ID})={pitch_with_offset:.1f}°")

            self.controller.set_position(self.YAW_MOTOR_ID, yaw_with_offset)

            # デイジーチェーン通信のため、コマンド間に短い遅延を追加（1ms）
            time.sleep(0.001)

            self.controller.set_position(self.PITCH_MOTOR_ID, pitch_with_offset)
            return True
        except Exception as e:
            print(f"⚠️ Error setting position: {e}")
            return False

    def run(self, freq=100):
        """
        Main control loop.

        Args:
            freq: Control frequency in Hz (default: 100Hz)
        """
        print(f"🎮 Starting head tracking @ {freq}Hz...")
        print("📹 Your head movements will control the B3M neck!")
        print("Press Ctrl+C to stop.\n")

        dt = 1.0 / freq
        last_yaw = 0.0
        last_pitch = 0.0

        try:
            while True:
                start_time = time.time()

                # Get neck angles from headset
                yaw_deg, pitch_deg = self.get_neck_angles_from_headset()

                # Deadband: Update only if change > 0.5 degrees
                if abs(yaw_deg - last_yaw) > 0.5 or abs(pitch_deg - last_pitch) > 0.5:
                    success = self.set_neck_position(yaw_deg, pitch_deg)
                    if success:
                        last_yaw = yaw_deg
                        last_pitch = pitch_deg
                        print(f"Neck: Yaw={yaw_deg:+6.1f}°, Pitch={pitch_deg:+6.1f}°", end="\r")

                # Maintain frequency
                elapsed = time.time() - start_time
                sleep_time = max(0, dt - elapsed)
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping head tracking...")
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
        print("✅ B3M Head Controller stopped.\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="B3M Head Controller for TWIST2 (PICO VR連動)"
    )
    parser.add_argument("--port", type=str, default="/dev/ttyUSB0",
                       help="Serial port for B3M")
    parser.add_argument("--baudrate", type=int, default=1500000,
                       help="Baud rate (1.5Mbps)")
    parser.add_argument("--freq", type=int, default=100,
                       help="Control frequency (Hz)")
    parser.add_argument("--scale", type=float, default=1.5,
                       help="Neck movement scale factor")
    parser.add_argument("--debug", action="store_true",
                       help="Enable debug mode (show detailed data)")
    parser.add_argument("--calibrate", action="store_true",
                       help="Run calibration mode before starting")

    args = parser.parse_args()

    # Initialize controller
    controller = B3MHeadControllerTWIST2(
        port=args.port,
        baudrate=args.baudrate
    )
    controller.scale = args.scale
    controller.debug = args.debug

    # キャリブレーション実行
    if args.calibrate:
        controller.calibrate()
    else:
        # 保存されたキャリブレーションを読み込み
        controller._load_calibration()

    if args.debug:
        print("\n🔍 DEBUG MODE ENABLED")
        print("Detailed headset data will be displayed\n")

    # Run
    controller.run(freq=args.freq)
