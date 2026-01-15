#!/usr/bin/env python3
"""
B3M Neck Calibration Script
ネックの0度位置を設定するキャリブレーション専用スクリプト

使用方法:
    python b3m_calibrate.py --port /dev/ttyUSB0 --baudrate 1500000

実行後:
    b3m_calibration.txt にオフセットが保存されます
"""

import argparse
import time
from b3m_controller import B3MController


class B3MCalibrator:
    """B3M Neck Calibration Tool"""

    def __init__(self, serial_port: str = "/dev/ttyUSB0", baudrate: int = 1500000):
        """
        Initialize B3M Calibrator

        Args:
            serial_port: B3M用シリアルポート
            baudrate: 通信速度（1.5Mbps推奨）
        """
        print("=" * 60)
        print("  🎯 B3M Neck Calibration")
        print("=" * 60)
        print(f"Serial port: {serial_port}")
        print(f"Baudrate: {baudrate}\n")

        # B3M controller初期化
        print("Initializing B3M controller...")
        self.controller = B3MController(serial_port, baudrate)

        # Motor IDs
        self.YAW_MOTOR_ID = 0
        self.PITCH_MOTOR_ID = 1

        # Calibration offsets
        self.yaw_offset = 0.0
        self.pitch_offset = 0.0

        # Initialize motors
        self._initialize_motors()

        print("✅ B3M Calibrator initialized!\n")

    def _initialize_motors(self):
        """Initialize motors with torque enabled"""
        print("🔧 Initializing motors (torque ON)...")

        # Enable torque
        self.controller.enable_torque(self.YAW_MOTOR_ID)
        self.controller.enable_torque(self.PITCH_MOTOR_ID)

        print("✅ Motors initialized with torque ON\n")

    def calibrate(self):
        """
        キャリブレーションモード
        現在のモーター位置を0度基準として設定
        """
        print("=" * 60)
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

    def cleanup(self):
        """Cleanup and disable torque"""
        print("\n🔌 Disabling torque...")
        self.controller.disable_torque(self.YAW_MOTOR_ID)
        self.controller.disable_torque(self.PITCH_MOTOR_ID)
        self.controller.close()
        print("✅ Calibration complete.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="B3M Neck Calibration - ネックの0度位置を設定"
    )
    parser.add_argument(
        "--port", type=str, default="/dev/ttyUSB0", help="Serial port for B3M"
    )
    parser.add_argument(
        "--baudrate", type=int, default=1500000, help="Baud rate (1.5Mbps)"
    )

    args = parser.parse_args()

    # Initialize calibrator
    calibrator = B3MCalibrator(serial_port=args.port, baudrate=args.baudrate)

    try:
        # Run calibration
        calibrator.calibrate()
    except KeyboardInterrupt:
        print("\n\n⏹️  Calibration interrupted.")
    finally:
        calibrator.cleanup()
