# ZED Mini カメラ映像のPicoへのストリーミング手順

## 概要

このドキュメントでは、PCに接続されたZED MiniカメラからPico VRヘッドセットへステレオ映像をストリーミングする方法を説明します。

## システム構成

```
ZED Mini Camera (USB接続)
    ↓
PC (Ubuntu 22.04)
    ↓ WiFi経由 (TCP/IP)
Pico VRヘッドセット
```

### 使用ソフトウェア
- **PC側**: XRoboToolkit-RobotVision-PC (RobotVisionConsole)
- **Pico側**: XRoboToolkit Unity Client v1.1.1
- **映像形式**: SIDE_BY_SIDE ステレオ (2560x720, 30fps)

## 前提条件

### PC側
- [x] Ubuntu 22.04以上
- [x] ZED SDK インストール済み (`/usr/local/zed/`)
- [x] XRoboToolkit-RobotVision-PC ビルド済み
- [x] ZED Mini がUSBで接続されている

### Pico側
- [x] XRoboToolkit Unity Client v1.1.1 インストール済み
- [x] PCと同じWiFiネットワークに接続

## 事前準備

### 1. ネットワーク確認

#### PC側のIPアドレスを確認
```bash
ip addr show | grep "inet " | grep -v "127.0.0.1"
```

例: `192.168.50.37`

#### Pico側のIPアドレスを確認
1. Pico設定 → WiFi → 接続中のネットワークをタップ
2. IPアドレスをメモ（例: `192.168.50.232`）

### 2. 設定ファイルの確認（オプション）

Pico側の設定ファイルを確認・更新する場合：

```bash
# Pico接続確認
adb devices

# 設定ファイルを確認
adb shell cat /sdcard/Android/data/com.xrobotoolkit.client/files/video_source.yml

# 設定ファイルを更新する場合
adb push pico_video_source_actual.yml /sdcard/Android/data/com.xrobotoolkit.client/files/video_source.yml
```

## ストリーミング手順

### Step 1: Pico側の準備

1. **XRoboToolkit Unity Appを起動**
   - Picoのライブラリから「XRoboToolkit」を選択

2. **カメラソースを選択**
   - **ZEDMINI** を選択（重要: PICO4Uではない）

3. **待ち受け開始**
   - **Listen** ボタンをクリック
   - ポート12345で待ち受け状態になる

### Step 2: PC側の実行

ターミナルで以下のコマンドを実行：

```bash
cd ~/TWIST2

XRoboToolkit-RobotVision-PC/VideoTransferPC/RobotVisionTest/RobotVisionConsole \
  --tcp-camera c \
  --ip 192.168.50.232 \
  --port 12345 \
  --camera 0 \
  --width 1280 \
  --height 720 \
  --fps 30 \
  --bitrate 8000000
```

**パラメータの説明：**
- `--ip`: PicoのIPアドレス
- `--port`: 通信ポート（デフォルト: 12345）
- `--width 1280`: カメラの幅（SIDE_BY_SIDEで2560になる）
- `--height 720`: カメラの高さ
- `--fps 30`: フレームレート（安定性のため30推奨）
- `--bitrate 8000000`: ビットレート（8Mbps）

### Step 3: 接続確認

#### 正常な出力例
```
Starting connect to 192.168.50.232:12345
Connection succeeded
Encoder parameters:
Resolution: 2560x720
Time base: 1/30
Framerate: 30/1
[ZED][INFO] [Init]  Camera successfully opened.
[ZED][INFO] [Init]  Video mode: HD720@30
Press Q to stop capturing...
```

#### Pico側
- VR画面にZED Miniの映像が表示される
- ステレオ映像（左右の目に分かれた映像）

### Step 4: 停止

**PC側:**
- キーボードで `Q` を押す
- または `Ctrl+C`

**Pico側:**
- アプリを終了

## トラブルシューティング

### 問題: "CORRUPTED FRAME" エラーが頻発

**症状:**
```
[ZED][WARNING] Frames may be corrupted or degraded
CORRUPTED FRAME
```

**解決策:**
1. FPSを下げる（60→30）
2. ZED MiniのUSBケーブルを再接続
3. ビットレートを下げる（12000000→8000000）

### 問題: "Broken pipe" エラー

**症状:**
```
Fatal Error: Send error: Broken pipe
```

**解決策:**
1. Pico側で「Listen」が開始されているか確認
2. IPアドレスが正しいか確認
3. 同じWiFiネットワークに接続されているか確認
4. ファイアウォール設定を確認

### 問題: デバイスが認識されない

**症状:**
```
adb devices
List of devices attached
(何も表示されない)
```

**解決策:**
1. Picoで開発者モードを有効化
   - 設定 → 一般 → デバイス情報 → ソフトウェアバージョンを7回タップ
2. USBデバッグを有効化
   - 設定 → システム → 開発者向けオプション → USBデバッグをON
3. USBケーブルを再接続
4. Pico側で「USBデバッグを許可」を選択

### 問題: 画面に緑色の領域が多い

**解決策:**
`pico_video_source_actual.yml`の`visibleRatio`を調整：

```yaml
- name: "ZEDMINI"
  properties:
    - name: "visibleRatio"
      value: 0.55  # この値を調整（0.4～0.7の範囲で試す）
```

設定を更新後、Picoアプリを再起動してください。

### 問題: 映像が2つ重なって表示される

**原因:**
シェーダーの設定が適切でない可能性があります。

**対処:**
現在の設定（visibleRatio: 0.55, contentRatio: 1.704850）で片方のカメラ情報が見える状態であれば、データ収集と学習には問題ありません。

## 学習データ収集について

### データ形式
- **解像度**: 2560x720 (SIDE_BY_SIDE ステレオ)
- **形式**: RGB画像（左右並び）
- **保存**: `server_data_record.py`で自動保存

### 重要な注意点
1. **ステレオ映像（SIDE_BY_SIDE）を維持すること**
   - 学習システムは2カメラ分のデータを期待している
   - 単眼（LEFT のみ）に変更すると学習パイプラインとの互換性がなくなる

2. **VR表示の問題はデータ品質に影響しない**
   - 表示が完璧でなくても、データは正しく記録される
   - ただし、テレオペレーション時の操作性は低下する可能性がある

3. **フレーム破損を避ける**
   - CORRUPTED FRAMEエラーが出る場合はFPSを下げる
   - 安定したストリーミングを優先する

## パラメータのカスタマイズ

### 解像度の変更

より低い解像度で試す場合：

```bash
# 640x360 (SIDE_BY_SIDEで1280x360になる)
--width 640 --height 360 --fps 30 --bitrate 4000000
```

### FPSの変更

```bash
# 高フレームレート（60fps）
--fps 60 --bitrate 12000000

# 標準（30fps）- 推奨
--fps 30 --bitrate 8000000

# 低フレームレート（15fps）
--fps 15 --bitrate 4000000
```

## 参考情報

### 関連ドキュメント
- [XRoboToolkit-RobotVision-PC README](./XRoboToolkit-RobotVision-PC/README.md)
- [TWIST2 TELEOP](./doc/TELEOP.md)

### 設定ファイル
- PC側設定: `pico_video_source_actual.yml`
- Pico側設定: `/sdcard/Android/data/com.xrobotoolkit.client/files/video_source.yml`

### システム要件
- ZED SDK: 4.0以上
- Unity Client: v1.1.1
- WiFi: 同一ネットワーク、5GHz推奨

## 更新履歴

- 2026-01-04: 初版作成
  - FPS 30fps、解像度 1280x720（SIDE_BY_SIDE: 2560x720）での動作を確認
  - visibleRatio 0.55 での設定を推奨
