# TWIST2 ZED Mini → Pico VR ビデオストリーミング システム概要

## 試したアプローチと結果

### 1. OrinVideoSender (Jetson Orin用) - ❌ 白い画面
- **場所**: `/home/kota-ueda/XRoboToolkit-Orin-Video-Sender/`
- **用途**: 本来はJetson Orin用（ロボット側）
- **設定**: `pico_video_source_actual.yml` (PICO4U/ZEDMINI プロファイル)
- **結果**: 
  - Picoから接続なし（"Waiting for a new client connection..."）
  - 白い画面

### 2. zed_camera_server.py (ZeroMQ方式) - ❌ 白い画面
- **場所**: `/home/kota-ueda/TWIST2/zed-mini/zed_camera_server.py`
- **通信**: ZeroMQ (tcp://*:5556) + JPEG圧縮
- **結果**: サーバーは正常動作（30fps配信）だが、Pico側で受信できず

### 3. XRoboToolkit-RobotVision-PC - ❌ Linuxでビルド不可
- **場所**: `/home/kota-ueda/XRoboToolkit-RobotVision-PC/`
- **用途**: PC用の正式なビデオ送信プログラム
- **問題**: Windows専用（windows.h依存）、Linuxでコンパイル不可

## ファイル一覧

### 設定ファイル
```
/home/kota-ueda/TWIST2/
├── pico_video_source_actual.yml          # Picoの完全な設定（PICO4U + ZEDMINI）
├── B3M/video_source.yml                   # PICO4U用の簡易設定
└── zed-mini/video_source.yml             # ZED Mini用の簡易設定（ZeroMQ URL形式）
```

### サーバープログラム
```
/home/kota-ueda/
├── XRoboToolkit-Orin-Video-Sender/       # Jetson Orin用（PCで動作中だが本来の用途ではない）
│   └── OrinVideoSender
├── TWIST2/zed-mini/
│   └── zed_camera_server.py              # ZeroMQ + JPEG ストリーミングサーバー
└── XRoboToolkit-RobotVision-PC/          # PC用正式版（Windowsのみ）
    └── VideoTransferPC/RobotVisionTest/
        └── RobotVisionConsole (未ビルド)
```

### テストスクリプト
```
/home/kota-ueda/TWIST2/
├── test_orin_sender.sh                   # OrinVideoSender起動スクリプト
├── test_video_receiver.sh                # 簡易ビデオ受信テスト
└── test_video_receiver_fixed.py          # H.264ストリーム受信テスト
```

## 根本的な問題

**全てのアプローチで「白い画面」= Pico側でビデオデコーダーが起動していない**

可能性：
1. Unity Clientアプリ自体の問題
2. Pico側の設定や権限の問題
3. ネットワーク接続の問題（接続はできているがデータが流れていない）
4. ビデオフォーマット/プロトコルの不一致

## 次に確認すべきこと

1. Pico側のXRoboToolkit Unity Clientアプリのバージョン確認
2. アプリの権限設定確認
3. 実際にネットワークでデータが流れているかの確認
4. 他のPico VRデバイスやテスト環境での動作確認
