# G1 全身テレオペレーション手順書（AmazingHand付き）

最終確認日: 2026-02-25

---

## システム構成

```
┌─ PC (Ubuntu 22.04) ─────────────────────────────────┐
│                                                      │
│  [T1] XRoboToolkit PC Service (GUI)                  │
│        ← PICO VRからWiFiでモーション受信              │
│                                                      │
│  [T2] bash teleop.sh (conda: gmr)                    │
│        xrobot_teleop_to_robot_w_hand.py              │
│        → Redis(localhost)にコマンド書き込み            │
│          action_body / action_hand / action_neck      │
│                                                      │
│  [T3] bash sim2real.sh (conda: twist2)               │
│        server_low_level_g1_real.py                    │
│        ← Redisからaction_bodyを読み取り               │
│        → Unitree SDK2でG1本体29関節を制御             │
│          (Ethernet経由)                               │
└────────────────────┬─────────────────────────────────┘
                     │ Ethernet (192.168.123.0/24)
                     │ PC: 192.168.123.222
                     │ G1: 192.168.123.164
                     │
┌─ G1 (Jetson Orin NX) ──────────────────────────────┐
│                                                      │
│  [T4] pico_amazinghand_control.py                    │
│        ← PC側Redisからaction_hand_left/rightを読取り  │
│        → AmazingHand 16サーボ制御                     │
│          (USB: /dev/ttyACM0)                          │
│                                                      │
│  [T5] b3m_neck_controller_redis.py                   │
│        ← PC側Redisからaction_neckを読み取り           │
│        → B3M Neck 2サーボ制御                         │
│          (USB: /dev/ttyUSB0 or ttyUSB1)               │
└──────────────────────────────────────────────────────┘
```

### データフロー

```
PICO VR (WiFi)
  ├─ ヘッドセット姿勢     → Neck角度 (2D)
  ├─ コントローラー姿勢   → 全身+腕 (35D)
  └─ ボタン入力           → Hand開閉 (8D x 2)
      ↓
XRoboToolkit PC Service → teleop.sh → Redis (PC localhost)
      ↓                                    ↓
sim2real.sh (PC)                    G1側プロセス (SSH経由)
  → G1本体 29関節                     ├─ AmazingHand 16サーボ
                                      └─ Neck 2サーボ
```

---

## 事前準備

### 1. ハードウェア接続確認

| 機器 | 接続 | 確認事項 |
|------|------|----------|
| PC ↔ G1 | Ethernet (有線) | LANケーブル接続 |
| PC ↔ PICO VR | WiFi (同一ネットワーク) | 同じSSIDに接続 |
| G1 ↔ AmazingHand | USB (/dev/ttyACM0) | Waveshare Adapter + 5V電源 |
| G1 ↔ Neck | USB (/dev/ttyUSB0 or ttyUSB1) | B3Mコントローラー + 電源 |

### 2. PCのEthernet IP設定

```bash
# 現在のインターフェース名を確認
ip link show

# IPアドレスを設定（インターフェース名は環境に合わせて変更）
sudo ip addr add 192.168.123.222/24 dev enx6c1ff771dc67
```

### 3. G1への接続確認

```bash
ping 192.168.123.164
# 応答があればOK

ssh unitree@192.168.123.164
# パスワードを入力してログインできることを確認
```

### 4. Redisサーバー確認（PC側）

```bash
redis-cli ping
# PONG が返ればOK

# 返らない場合
sudo systemctl start redis-server
```

> Redis設定（/etc/redis/redis.conf）で `bind 0.0.0.0` かつ `protected-mode no` になっていること。
> G1からPC側のRedisにアクセスするために必要。

---

## 起動手順

**必ず以下の順番で起動すること。**

### Step 1: XRoboToolkit PC Service（PC側）

デスクトップGUIメニューから "RoboticsService" を起動する。

確認:
- GUIウィンドウが表示される
- PICO VRのXRobotToolkitアプリを起動し接続する

### Step 2: teleop.sh（PC側 ターミナル1）

```bash
cd ~/TWIST2
bash teleop.sh
```

確認:
```
Teleop data streamer initialized
Redis connected successfully
Ready to receive teleop data.
Teleop Loop Execution FPS (last 100 steps): ~98 Hz
```

### Step 3: sim2real.sh（PC側 ターミナル2）

```bash
cd ~/TWIST2
bash sim2real.sh
```

> **注意**: `sim2real.sh` 内の `net=` が実際のEthernetインターフェース名と一致していること。
> 異なる場合は `sim2real.sh` を編集して修正する。

起動後、Unitreeリモコンで操作:
1. **START** ボタン → デフォルトポーズに移行
2. **A** ボタン → ポリシーループ開始

確認:
```
Successfully connected to the robot
ONNX policy loaded from ...
Press START on remote to move to default position ...
```

### Step 4: AmazingHand + Neck（G1側 SSH）

```bash
ssh unitree@192.168.123.164
bash ~/TWIST2/G1_deploy/start_teleop.sh 192.168.123.222
```

確認:
```
✅ /dev/ttyACM0 (Amazing Hand)
✅ /dev/ttyUSB0 (B3M Neck)
Starting Amazing Hand controller (background)...
Starting Neck controller (foreground)...
```

> **個別に起動する場合（問題切り分け時）:**
>
> SSHターミナル1 - AmazingHand:
> ```bash
> conda activate twist2
> cd ~/TWIST2/G1_deploy
> python pico_amazinghand_control.py \
>     --serial_port /dev/ttyACM0 \
>     --baudrate 1000000 \
>     --redis_ip 192.168.123.222
> ```
>
> SSHターミナル2 - Neck:
> ```bash
> conda activate twist2
> cd ~/TWIST2/B3M
> python b3m_neck_controller_redis.py \
>     --redis_ip 192.168.123.222 \
>     --port /dev/ttyUSB1 \
>     --baudrate 1500000
> ```

### Step 5: テレオペ開始（PICO VR）

1. PICO VRヘッドセットを装着
2. 左右コントローラーを握る
3. **右コントローラーのAボタン**を押す → `idle` → `teleop` に切り替わり動作開始

---

## 操作方法

### PICOコントローラー

| ボタン | 動作 |
|--------|------|
| **右 Aボタン** | idle → teleop → pause サイクル |
| **左 Xボタン** | 終了（exitモードへ） |
| **左 スティック押し込み** | 緊急停止 |

### Hand操作

| ボタン | 動作 |
|--------|------|
| 右 人差し指トリガー (index_trig) | 右手が閉じる |
| 右 グリップ (grip) | 右手が開く |
| 左 人差し指トリガー (index_trig) | 左手が閉じる |
| 左 グリップ (grip) | 左手が開く |

### 全身動作

| 入力 | 動作 |
|------|------|
| 頭を動かす | Neck追従（Yaw/Pitch） |
| 体を動かす | G1全身が追従（29関節） |
| 左スティック | 前後左右移動 |
| 右スティック | Yaw回転 |

---

## 終了手順

**以下の順番で終了すること。**

### 1. テレオペ停止

PICO VRの**左Xボタン**を押す → exitモードに遷移 → デフォルトポーズに戻る

### 2. G1側プロセス停止

SSH接続先で `Ctrl+C` → AmazingHandとNeckがデフォルトポーズに戻り終了

### 3. PC側プロセス停止

- sim2real.sh: `Ctrl+C`
- teleop.sh: `Ctrl+C`
- XRoboToolkit PC Service: GUIウィンドウを閉じる

---

## トラブルシューティング

### G1に接続できない（pingが通らない）

```bash
# PCのEthernet IPアドレスを確認
ip addr show
# 192.168.123.222/24 が設定されているか

# インターフェース名が正しいか確認
ip link show
# enx... という名前のデバイスを探す
```

### sim2real.shで "does not match an available interface" エラー

`sim2real.sh` 内の `net=` を現在のEthernetインターフェース名に修正する。

```bash
# 現在のインターフェース名を確認
ip link show | grep enx
```

### Redis connection failed

```bash
# PC側でRedis起動確認
redis-cli ping

# 起動していない場合
sudo systemctl start redis-server

# 外部接続を許可しているか確認
# /etc/redis/redis.conf で以下を設定:
#   bind 0.0.0.0
#   protected-mode no
sudo systemctl restart redis-server
```

### AmazingHandが動かない

```bash
# G1側でシリアルポート確認
ls -l /dev/ttyACM0

# パーミッションエラーの場合
sudo chmod 666 /dev/ttyACM0

# Redisにhandデータが届いているか確認（PC側で実行）
redis-cli get action_hand_left_unitree_g1_with_hands
# JSON配列が返ればOK
```

### Neckが動かない

```bash
# G1側でシリアルポート確認
ls -l /dev/ttyUSB*

# FTDIドライバーのロード
sudo modprobe ftdi_sio
echo "165c 0009" | sudo tee /sys/bus/usb-serial/drivers/ftdi_sio/new_id

# パーミッション設定
sudo chmod 666 /dev/ttyUSB0
```

### ONNX CUDAエラー（CPUフォールバック）

```
Failed to create CUDAExecutionProvider
```

ポリシー推論がCPUで実行されます。動作に問題がなければそのまま使用可能。
GPU推論が必要な場合はCUDA 12 + cuDNN 9のインストールが必要。

---

## 使用するRedisキー

| キー名 | 次元 | 内容 |
|--------|------|------|
| `action_body_unitree_g1_with_hands` | 35D | G1全身コマンド |
| `action_hand_left_unitree_g1_with_hands` | 8D | 左手コマンド |
| `action_hand_right_unitree_g1_with_hands` | 8D | 右手コマンド |
| `action_neck_unitree_g1_with_hands` | 2D | Neck Yaw/Pitch |

## conda環境

| 環境名 | Python | 用途 | マシン |
|--------|--------|------|--------|
| `gmr` | 3.10 | teleop.sh（モーションリターゲティング） | PC |
| `twist2` | 3.8 | sim2real.sh / Hand / Neck制御 | PC / G1 |
