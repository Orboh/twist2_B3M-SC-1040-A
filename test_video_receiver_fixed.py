#!/usr/bin/env python3
"""
OrinVideoSender用のテストレシーバー
4バイトの長さプレフィックスを処理して、H.264ストリームをffplayに渡す
"""

import socket
import struct
import subprocess
import sys

def receive_video_stream(host='0.0.0.0', port=12345):
    # TCPソケットを作成
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(1)

    print(f"Listening on {host}:{port}")
    print("Waiting for connection from OrinVideoSender...")

    conn, addr = server_socket.accept()
    print(f"Connected from {addr}")

    # ffplayプロセスを起動
    ffplay_cmd = [
        'ffplay',
        '-f', 'h264',
        '-framerate', '60',
        '-video_size', '2560x720',  # 解像度を明示的に指定
        '-i', '-',
        '-vf', 'setpts=N/60/TB'  # タイムスタンプを調整
    ]

    print("Starting ffplay...")
    ffplay_process = subprocess.Popen(
        ffplay_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    frame_count = 0
    total_bytes = 0

    try:
        while True:
            # 4バイトの長さプレフィックスを読み取る
            length_data = conn.recv(4)
            if len(length_data) < 4:
                print("Connection closed or incomplete length prefix")
                break

            # ビッグエンディアンで長さを取得
            frame_length = struct.unpack('>I', length_data)[0]

            if frame_length == 0 or frame_length > 10000000:  # 10MB以上は異常
                print(f"Invalid frame length: {frame_length}")
                break

            # H.264フレームデータを読み取る
            h264_data = b''
            remaining = frame_length
            while remaining > 0:
                chunk = conn.recv(min(remaining, 65536))
                if not chunk:
                    print("Connection closed while reading frame data")
                    break
                h264_data += chunk
                remaining -= len(chunk)

            if len(h264_data) != frame_length:
                print(f"Incomplete frame: expected {frame_length}, got {len(h264_data)}")
                break

            # ffplayにH.264データを送る（長さプレフィックスなし）
            try:
                ffplay_process.stdin.write(h264_data)
                ffplay_process.stdin.flush()
            except BrokenPipeError:
                print("ffplay process terminated")
                break

            frame_count += 1
            total_bytes += frame_length

            if frame_count % 60 == 0:  # 1秒ごとに表示
                print(f"Frames: {frame_count}, Total data: {total_bytes/1024/1024:.2f} MB")

    except KeyboardInterrupt:
        print("\nStopping...")

    finally:
        print(f"\nTotal frames received: {frame_count}")
        print(f"Total data received: {total_bytes/1024/1024:.2f} MB")
        conn.close()
        server_socket.close()
        ffplay_process.terminate()
        ffplay_process.wait()

if __name__ == '__main__':
    receive_video_stream()
