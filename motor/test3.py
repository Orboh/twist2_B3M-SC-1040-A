
# -*- coding: utf-8 -*-
import serial
import time
from pynput import mouse

# --- B3M通信設定 ---
PORT_NAME = '/dev/ttyUSB0'
BAUD_RATE = 1500000
SERVO_ID = 0x00  # 動作したIDに合わせて変更してください

# シリアルポートのオープン
try:
    b3m = serial.Serial(PORT_NAME, baudrate=BAUD_RATE, timeout=0.1)
    b3m.flush()
except Exception as e:
    print(f"Error: {e}")
    exit()

def B3M_Write_CMD(servo_id, TxData, Address):
    txCmd = [0x08, 0x04, 0x00, servo_id, TxData, Address, 0x01]
    txCmd.append(sum(txCmd) & 0xff)
    b3m.write(txCmd)
    return b3m.read(5)

def B3M_setPos_CMD(servo_id, pos):
    # MoveTimeはとりあえず0（最速）で設定
    txCmd = [0x09, 0x06, 0x00, servo_id, pos & 0xff, pos >> 8 & 0xff, 0x00, 0x00]
    txCmd.append(sum(txCmd) & 0xff)
    b3m.write(txCmd)

# --- 初期設定 (トルクON) ---
B3M_Write_CMD(SERVO_ID, 0x02, 0x28) # Free
B3M_Write_CMD(SERVO_ID, 0x00, 0x28) # Normal (Torque ON)
print("トルクON！マウスを動かしてみてください。終了は右クリックです。")

# --- マウスイベントの処理 ---
def on_move(x, y):
    # 画面のX座標(例: 0~1920)をB3Mの角度(-8000 ~ 8000)に変換
    # ※画面サイズに合わせて1920の部分は調整してください
    screen_width = 1920 
    target_pos = int((x / screen_width) * 16000 - 8000)
    
    # 範囲制限（安全のため）
    target_pos = max(-8000, min(8000, target_pos))
    
    # サーボに命令を送信
    B3M_setPos_CMD(SERVO_ID, target_pos)

def on_click(x, y, button, pressed):
    if button == mouse.Button.right:
        # 右クリックで終了
        return False

# マウスの監視を開始
with mouse.Listener(on_move=on_move, on_click=on_click) as listener:
    listener.join()

# 終了処理
B3M_Write_CMD(SERVO_ID, 0x02, 0x28) # 脱力
b3m.close()
print("終了しました。")