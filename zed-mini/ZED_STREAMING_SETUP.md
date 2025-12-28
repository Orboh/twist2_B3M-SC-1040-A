# ZED Camera Streaming to PICO VR Setup Guide
# ZED miniカメラ映像をPICO VRに表示する設定ガイド

## システム構成

```
ZED mini カメラ
    ↓ USB接続
このPC (kota-ueda)
    ↓ ネットワーク (ZeroMQ)
PICO VR ヘッドセット
    ↓
XRoboToolkit APP で映像表示
```

---

## 📋 セットアップ手順

### 1️⃣ PCのIPアドレスを確認

```bash
# 方法A: ifconfig
ifconfig | grep "inet "

# 方法B: ip コマンド
ip a | grep "inet "

# 例: 192.168.1.100 のような形式
```

**出力例：**
```
inet 192.168.1.100 netmask 255.255.255.0
```

→ この場合、PCのIPアドレスは `192.168.1.100`

---

### 2️⃣ video_source.yml を編集

```bash
cd /home/kota-ueda/TWIST2/B3M
nano video_source.yml
```

`<YOUR_PC_IP>` を実際のIPアドレスに変更：

```yaml
video_source: "tcp://192.168.1.100:5556"
```

保存して閉じる（Ctrl+O, Enter, Ctrl+X）

---

### 3️⃣ PICO VRに設定ファイルを転送

**前提条件：**
- PICO VRをUSBケーブルでPCに接続
- 開発者モードが有効
- adb コマンドが使える

**手順：**

```bash
# PICO VRが認識されているか確認
adb devices

# video_source.yml をPICO VRに転送
cd /home/kota-ueda/TWIST2/B3M
adb push video_source.yml /sdcard/Android/data/com.xrobotoolkit.client/files/video_source.yml

# 確認
adb shell ls /sdcard/Android/data/com.xrobotoolkit.client/files/
```

---

### 4️⃣ ZED miniカメラを接続

```bash
# ZED miniがUSB接続されているか確認
lsusb | grep -i zed

# 出力例:
# Bus 001 Device 005: ID 2b03:f780 Stereolabs ZED mini
```

もし見つからない場合：
- USBケーブルを再接続
- 別のUSBポートを試す
- ZED SDKが正しくインストールされているか確認

---

### 5️⃣ ZEDカメラサーバーを起動

```bash
cd /home/kota-ueda/TWIST2/B3M

# 基本起動（デフォルト設定）
python zed_camera_server.py

# プレビュー表示付き（デバッグ用）
python zed_camera_server.py --preview

# 高解像度（HD720 = 1280x720）
python zed_camera_server.py --resolution HD720

# カスタム設定
python zed_camera_server.py --port 5556 --resolution VGA --fps 30 --quality 85
```

**起動成功の表示例：**
```
============================================================
  ZED Camera Streaming Server
  for PICO VR XRoboToolkit APP
============================================================

🎥 Initializing ZED camera...
✅ ZED camera opened successfully
   Model: ZED Mini
   Serial: 12345678
   Resolution: 640x480
   FPS: 30

📡 ZeroMQ publisher bound to port 5556
   Local IP: 192.168.1.100
   PICO VR should connect to: tcp://192.168.1.100:5556

🚀 Starting ZED camera streaming...
📹 XRoboToolkit APP on PICO VR should now receive video
Press Ctrl+C to stop.
```

---

### 6️⃣ PICO VRで映像を確認

1. **PICO VRを装着**
2. **XRoboToolkit APPを起動**
3. **PCに接続**（IPアドレスを入力）
4. **映像が表示されるはずです**

もし映像が表示されない場合：
- PCとPICO VRが同じネットワークに接続されているか確認
- ファイアウォールでポート5556がブロックされていないか確認
- video_source.yml のIPアドレスが正しいか確認

---

## 🔧 トラブルシューティング

### エラー: "Failed to open ZED camera"

**原因：**
- ZED miniが接続されていない
- 他のプログラムがZEDカメラを使用中

**解決策：**
```bash
# ZEDカメラを使用中のプロセスを確認
lsof | grep -i zed

# プロセスを終了
kill <プロセスID>

# USBを再接続
```

---

### 映像が表示されない

**確認事項：**

1. **ネットワーク接続**
   ```bash
   # PICO VRからPCにpingできるか
   ping <PC_IP_ADDRESS>
   ```

2. **ファイアウォール**
   ```bash
   # ポート5556を開放（Ubuntu）
   sudo ufw allow 5556/tcp

   # または一時的にファイアウォールを無効化
   sudo ufw disable
   ```

3. **video_source.yml の確認**
   ```bash
   # PICO VRから設定を取得
   adb pull /sdcard/Android/data/com.xrobotoolkit.client/files/video_source.yml
   cat video_source.yml
   ```

---

### 映像が遅延する / カクつく

**解決策：**

1. **解像度を下げる**
   ```bash
   python zed_camera_server.py --resolution VGA
   ```

2. **JPEG品質を下げる（データ量削減）**
   ```bash
   python zed_camera_server.py --quality 60
   ```

3. **FPSを下げる**
   ```bash
   python zed_camera_server.py --fps 20
   ```

4. **有線LAN接続を使う**（WiFiより高速）

---

## 🎮 統合テスト：モーショントラッキング + カメラ

### B3M首制御とZEDカメラを同時に使用

**ターミナル1（B3M首制御）：**
```bash
cd /home/kota-ueda/TWIST2/B3M
python b3m_head_controller_twist2.py
```

**ターミナル2（ZEDカメラストリーミング）：**
```bash
cd /home/kota-ueda/TWIST2/B3M
python zed_camera_server.py
```

**PICO VR側：**
1. XRoboToolkit APP起動
2. PCに接続
3. モーショントラッカー装着
4. **頭を動かす → 首が追従 → カメラ映像も連動**

これで**egocentric active perception**（主観視点の能動視線）が完成！

---

## 📝 コマンドラインオプション

### zed_camera_server.py

```
--port PORT          ZeroMQポート番号 (default: 5556)
--resolution RES     解像度 VGA/HD720/HD1080 (default: VGA)
--fps FPS            フレームレート (default: 30)
--quality QUALITY    JPEG品質 0-100 (default: 80)
--preview            ローカルプレビュー表示
```

**例：**
```bash
# 高画質・高フレームレート
python zed_camera_server.py --resolution HD720 --fps 60 --quality 95 --preview

# 低遅延・軽量
python zed_camera_server.py --resolution VGA --fps 20 --quality 60
```

---

## 📚 参考ファイル

- `zed_camera_server.py` - ZEDカメラストリーミングサーバー
- `video_source.yml` - PICO VR用設定ファイル
- `b3m_head_controller_twist2.py` - B3M首制御プログラム

---

## 🎯 次のステップ

- [ ] PCのIPアドレス確認
- [ ] video_source.yml編集
- [ ] PICO VRに設定転送
- [ ] ZEDカメラサーバー起動
- [ ] PICO VRで映像確認
- [ ] B3M首制御と統合テスト

**完成したら、主観視点の能動視線システムが動作します！** 🎉
