#!/usr/bin/env python3
"""
B3M Controller for Kondo Kagaku B3M-SB-1040-A
動作確認済み（test3.pyベース）
  このプログラムは以下の動作をします：

  1. モーターID 0（Yaw）とID 1（Pitch）のトルクON
  2. 中心位置（0度）に移動
  3. 左に回転（Yaw -30度）
  4. 右に回転（Yaw +30度）
  5. 上を向く（Pitch +20度）
  6. 下を向く（Pitch -20度）
  7. 中心に戻る
  8. トルクOFF

"""

import serial
import time


class B3MController:
    """B3M servo controller using pyserial - 実装完了版"""

    def __init__(self, port="/dev/ttyUSB0", baudrate=1500000):
        """
        Initialize B3M controller.

        Args:
            port: Serial port
            baudrate: Communication speed (1.5Mbps recommended)
        """
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.1
            )
            self.ser.flush()
            print(f"✅ B3M Controller initialized on {port} @ {baudrate}bps")
        except Exception as e:
            print(f"❌ B3M Connection Failed: {e}")
            raise

    def write_command(self, servo_id, tx_data, address):
        """
        B3M基本書き込みコマンド

        Args:
            servo_id: モーターID (0 or 1)
            tx_data: 送信データ
            address: レジスタアドレス
        """
        txCmd = [0x08, 0x04, 0x00, servo_id, tx_data, address, 0x01]
        txCmd.append(sum(txCmd) & 0xff)
        self.ser.write(bytes(txCmd))
        return self.ser.read(5)

    def enable_torque(self, servo_id):
        """
        トルクON（モーターを有効化）

        Args:
            servo_id: モーターID (0 or 1)
        """
        self.write_command(servo_id, 0x02, 0x28)  # Free
        time.sleep(0.1)
        self.write_command(servo_id, 0x00, 0x28)  # Normal (Torque ON)
        print(f"  Motor ID {servo_id}: Torque ON")

    def disable_torque(self, servo_id):
        """
        トルクOFF（モーターを脱力）

        Args:
            servo_id: モーターID (0 or 1)
        """
        self.write_command(servo_id, 0x02, 0x28)  # Free
        print(f"  Motor ID {servo_id}: Torque OFF")

    def set_position(self, motor_id, position_deg):
        """
        モーター位置を設定（度単位）

        Args:
            motor_id: モーターID (0 or 1)
            position_deg: 目標位置（度）
        """
        # 度を0.01度単位に変換
        position_value = int(position_deg * 100)

        # 範囲制限（安全のため）
        position_value = max(-8000, min(8000, position_value))

        # 位置設定コマンド（MoveTime=0で最速）
        txCmd = [
            0x09, 0x06, 0x00, motor_id,
            position_value & 0xff,
            (position_value >> 8) & 0xff,
            0x00, 0x00
        ]
        txCmd.append(sum(txCmd) & 0xff)
        self.ser.write(bytes(txCmd))

    def read_position(self, servo_id, debug=False):
        """
        モーターの現在位置を読み取る（度単位）

        Args:
            servo_id: モーターID (0 or 1)
            debug: デバッグ情報を表示

        Returns:
            float: 現在位置（度）、エラー時はNone
        """
        # シリアルバッファをクリア
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()

        # 位置読み取りコマンド（レジスタ0x2C-0x2D: 現在位置）
        # 注意: 0x2Aは目標位置、0x2Cが現在位置！
        # フォーマット: SIZE, COMMAND, OPTION, ID, ADDRESS, LENGTH, SUM
        txCmd = [0x07, 0x03, 0x00, servo_id, 0x2C, 0x02]
        txCmd.append(sum(txCmd) & 0xff)

        if debug:
            print(f"[DEBUG] Sending read command: {[hex(x) for x in txCmd]}")

        self.ser.write(bytes(txCmd))
        time.sleep(0.05)  # 応答待ちを長めに

        response = self.ser.read(12)  # より多くのバイトを読む

        if debug:
            print(f"[DEBUG] Response length: {len(response)}")
            if len(response) > 0:
                print(f"[DEBUG] Response data: {[hex(x) for x in response]}")

        # READコマンドの応答は7バイト (SIZE, COMMAND, STATUS, ID, DATA1, DATA2, SUM)
        if len(response) >= 7:
            # 位置データは4,5バイト目（インデックス0始まり）（リトルエンディアン、符号付き16bit）
            position_raw = response[4] | (response[5] << 8)
            # 符号付き16bitに変換
            if position_raw >= 32768:
                position_raw -= 65536
            # 0.01度単位から度に変換
            position_deg = position_raw / 100.0

            if debug:
                print(f"[DEBUG] Position raw: {position_raw}, Position deg: {position_deg:.2f}°")

            return position_deg
        else:
            print(f"⚠️ Failed to read position from motor ID {servo_id} (response length: {len(response)})")
            if len(response) > 0:
                print(f"   Response: {[hex(x) for x in response]}")
            return None

    def close(self):
        """シリアル接続を閉じる"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("B3M Controller closed.")


if __name__ == "__main__":
    """テスト用メイン"""
    print("B3M Controller Test")
    print("2つのモーターを動かします...")

    # コントローラー初期化
    controller = B3MController("/dev/ttyUSB0", 1500000)

    # 2つのモーターのトルクON
    controller.enable_torque(0)  # Yaw
    controller.enable_torque(1)  # Pitch

    try:
        # テスト動作
        print("\n中心位置に移動...")
        controller.set_position(0, 0)    # Yaw: 0度
        controller.set_position(1, 0)    # Pitch: 0度
        time.sleep(2)

        print("左に回転...")
        controller.set_position(0, -30)  # Yaw: -30度
        time.sleep(2)

        print("右に回転...")
        controller.set_position(0, 30)   # Yaw: 30度
        time.sleep(2)

        print("上を向く...")
        controller.set_position(1, 20)   # Pitch: 20度
        time.sleep(2)

        print("下を向く...")
        controller.set_position(1, -20)  # Pitch: -20度
        time.sleep(2)

        print("中心に戻る...")
        controller.set_position(0, 0)
        controller.set_position(1, 0)
        time.sleep(1)

    except KeyboardInterrupt:
        print("\n中断されました")

    finally:
        # トルクOFF
        controller.disable_torque(0)
        controller.disable_torque(1)
        controller.close()
        print("終了しました。")
