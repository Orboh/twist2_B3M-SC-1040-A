# G1全身テレオペレーション完全ガイド
**PICO VR × G1本体 × AmazingHand × Neck**

最終更新: 2026-01-11

---

## 目次
1. [システム構成](#システム構成)
2. [ハードウェア接続](#ハードウェア接続)
3. [必要なソフトウェア](#必要なソフトウェア)
4. [事前準備](#事前準備)
5. [起動手順](#起動手順)
6. [操作方法](#操作方法)
7. [終了手順](#終了手順)
8. [トラブルシューティング](#トラブルシューティング)

---

## システム構成

### 全体アーキテクチャ

```
┌─────────────────────────────────────────────────┐
│ PC (Ubuntu 22.04)                               │
│                                                 │
│ [XRoboToolkit PC Service]                       │
│   ↑ WiFi                                        │
│   PICO VR ヘッドセット/コントローラー             │
│                                                 │
│ [ターミナル: xrobot_teleop]                      │
│   conda環境: gmr (Python 3.10)                  │
│   ├─ モーションリターゲティング                   │
│   └─ Redisにコマンド送信                         │
│       ↓ Ethernet (192.168.123.0/24)            │
└─────────────────────────────────────────────────┘
                    │
                    │ PC: 192.168.123.222
                    │ G1: 192.168.123.164
                    ↓
┌─────────────────────────────────────────────────┐
│ G1 (Jetson Orin NX)                             │
│                                                 │
│ [SSH ターミナル1: Neck制御]                      │
│   conda環境: twist2 (Python 3.8)                │
│   └─ b3m_neck_controller_redis.py              │
│       └─ B3MController → Neck (USB2)           │
│                                                 │
│ [SSH ターミナル2: 本体+Hand制御]                 │
│   conda環境: twist2 (Python 3.8)                │
│   └─ server_low_level_g1_real.py               │
│       ├─ Unitree SDK2 → G1本体 (29関節)        │
│       └─ rustypot → AmazingHand (USB1)         │
└─────────────────────────────────────────────────┘
        │                           │
        │ USB1                      │ USB2
        │ /dev/ttyACM0              │ /dev/ttyUSB1
        ↓                           ↓
  ┌─────────────┐            ┌─────────────┐
  │ AmazingHand │            │    Neck     │
  │  (8DOF×2)   │            │   (B3M)     │
  │  16 servo   │            │   2 servo   │
  └─────────────┘            └─────────────┘
```

### データフロー

```
PICO VR
  ├─ ヘッドセット姿勢 → Neck角度
  ├─ コントローラー姿勢 → 全身+腕+Hand
  └─ ボタン入力 (index_trig/grip) → Hand開閉
      ↓ WiFi
XRoboToolkit PC Service (PC)
      ↓
xrobot_teleop_to_robot_w_hand.py (PC, gmr環境)
  ├─ モーションリターゲティング
  └─ Redis送信
      ↓ Ethernet
Redis (PC側で動作)
  ├─ action_body (35D: 全身)
  ├─ action_hand_left (8D: 左手)
  ├─ action_hand_right (8D: 右手)
  └─ action_neck (2D: Yaw/Pitch)
      ↓ Ethernet
G1 (Jetson Orin)
  ├─ server_low_level_g1_real.py
  │   ├─ Unitree SDK2 → G1本体 (29関節)
  │   └─ rustypot → AmazingHand (16サーボ)
  └─ b3m_neck_controller_redis.py
      └─ B3MController → Neck (2サーボ)
```

---

## ハードウェア接続

### 1. PICO VR
```
✅ PICO VRヘッドセットの電源ON
✅ 左右コントローラーの電源ON
✅ PCと同じWiFiネットワークに接続
✅ PICO VR上でXRobotToolkitアプリを起動
```

### 2. PC (Ubuntu)
```
✅ Ethernet接続: G1との接続用
   - IPアドレス: 192.168.123.222
   - ネットマスク: 255.255.255.0
   - ゲートウェイ: なし

✅ WiFi接続: PICO VRとの通信用
   - PICO VRと同じネットワーク
```

### 3. G1本体
```
✅ Jetson Orin NXの電源ON
✅ Ethernet接続: PCとの接続用
   - IPアドレス: 192.168.123.164 (デフォルト)

✅ USB1 (/dev/ttyACM0): Waveshare Bus Servo Adapter
   - AmazingHand (左右16サーボ)
   - 5V電源供給確認

✅ USB2 (/dev/ttyUSB1): B3M Neckコントローラー
   - Yaw/Pitchサーボ (2軸)
```

---

## 必要なソフトウェア

### PC側

#### 1. XRoboToolkit PC Service
- **インストール:**
  ```bash
  sudo dpkg -i XRoboToolkit_PC_Service_1.0.0_ubuntu_22.04_amd64.deb
  ```
- **起動方法:** デスクトップメニューから "RoboticsService" を起動

#### 2. Conda環境 (gmr)
```bash
conda create -n gmr python=3.10
conda activate gmr

# 必要なライブラリ
pip install mujoco scipy redis numpy
pip install loop-rate-limiters

# GMR (General Motion Retargeting)のインストール
cd /home/kota-ueda/TWIST2/GMR
pip install -e .
```

#### 3. Redis Server
```bash
sudo apt install redis-server

# 設定ファイル編集: /etc/redis/redis.conf
# 以下の行を変更:
bind 0.0.0.0
protected-mode no

# Redisサーバー再起動
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

---

### G1側 (Jetson Orin)

#### 1. Conda環境 (twist2)
```bash
conda create -n twist2 python=3.8
conda activate twist2

# 必要なライブラリ
pip install redis numpy onnxruntime
pip install rustypot  # AmazingHand用
pip install pyserial  # B3M用
```

#### 2. Unitree SDK2
```bash
cd /home/unitree
git clone https://github.com/YanjieZe/unitree_sdk2.git
cd unitree_sdk2

sudo apt-get install build-essential cmake python3-dev
pip install pybind11 numpy

cd python_binding
export UNITREE_SDK2_PATH=$(pwd)/..
bash build.sh --sdk-path $UNITREE_SDK2_PATH

# インストール確認
python -c "import unitree_interface; print('OK')"
```

#### 3. TWIST2プロジェクトファイル
PCからG1にコピーが必要なファイル:
```bash
# G1の /home/unitree/TWIST2/ に以下をコピー:
- deploy_real/server_low_level_g1_real.py
- deploy_real/robot_control/
- deploy_real/data_utils/
- deploy_real/configs/
- B3M/b3m_controller.py
- B3M/b3m_neck_controller_redis.py
```

#### 4. ONNXポリシーファイル
```bash
# 学習済みポリシーをG1に配置
# 例: /home/unitree/policies/twist2_policy.onnx
```

---

## 事前準備

### PC側準備

#### 1. ネットワーク設定確認
```bash
# Ethernet IPアドレス確認
ip addr show

# G1への接続確認
ping 192.168.123.164
# 応答があればOK
```

#### 2. Redis起動確認
```bash
redis-cli ping
# PONG が返ればOK

# 返らない場合
sudo systemctl start redis-server
```

#### 3. XRoboToolkit PC Service起動
```bash
# デスクトップメニューから "RoboticsService" を起動
# または
/opt/apps/roboticsservice/runService.sh

# プロセス確認
ps aux | grep RoboticsServiceProcess
```

---

### G1側準備 (SSH接続)

#### 1. SSH接続
```bash
ssh unitree@192.168.123.164
# パスワード: (G1のパスワード)
```

#### 2. シリアルポート確認
```bash
# AmazingHand
ls -l /dev/ttyACM0
# 存在しない場合: USB接続確認

# Neck
ls -l /dev/ttyUSB1
# 存在しない場合: USB接続確認
```

#### 3. パーミッション設定 (初回のみ)
```bash
# ユーザーをdialoutグループに追加
sudo usermod -a -G dialout $USER

# ログアウト→ログインで反映
exit
ssh unitree@192.168.123.164
```

---

## 起動手順

### ステップ1: PC側起動

#### ターミナル1: XRoboToolkit PC Service
```bash
# デスクトップGUIから起動
# アプリメニュー → "RoboticsService"

# 起動確認
ps aux | grep RoboticsServiceProcess
```

**確認事項:**
- ✅ GUIウィンドウが表示される
- ✅ "Waiting for connection..." などが表示される

---

#### ターミナル2: xrobot_teleop (Pico入力処理)
```bash
conda activate gmr
cd /home/kota-ueda/TWIST2/deploy_real

python xrobot_teleop_to_robot_w_hand.py \
    --robot unitree_g1_with_hands \
    --redis_ip localhost
```

**確認事項:**
- ✅ "Teleop data streamer initialized"
- ✅ "Redis connected successfully"
- ✅ "Ready to receive teleop data."
- ✅ "Teleop Loop Execution FPS: ~100 Hz" が表示される

**表示例:**
```
Pinch mode: False
Initializing teleop systems...
Teleop data streamer initialized
Redis connected successfully
Use robot model: .../g1_mocap_29dof.xml
[GMR] Robot Degrees of Freedom (DoF) names...
Ready to receive teleop data.
Teleop Loop Execution FPS (last 100 steps): 98.35 Hz
```

---

### ステップ2: G1側起動 (SSH経由)

**新しいターミナルを2つ開いて、それぞれG1にSSH接続します。**

#### SSH ターミナル1: Neck制御
```bash
ssh unitree@192.168.123.164

conda activate twist2
cd /home/unitree/TWIST2/B3M

python b3m_neck_controller_redis.py \
    --redis_ip 192.168.123.222 \
    --port /dev/ttyUSB1 \
    --baudrate 1500000
```

**確認事項:**
- ✅ "✅ Redis connected"
- ✅ "✅ B3M motors initialized and centered"
- ✅ "✅ B3M Neck Controller initialized!"
- ✅ "🎮 Starting neck control @ 50Hz..."

**表示例:**
```
============================================================
  B3M Neck Controller (Redis版)
  PC (Redis) → G1 → B3M Neck
============================================================
Redis server: 192.168.123.222:6379
Serial port: /dev/ttyUSB1

Step 1: Connecting to Redis...
✅ Redis connected

Step 2: Initializing B3M controller...
✅ B3M motors initialized and centered

============================================================
✅ B3M Neck Controller initialized!
============================================================

🎮 Starting neck control @ 50Hz...
📡 Waiting for neck data from PC (Redis)...
```

---

#### SSH ターミナル2: G1本体 + AmazingHand制御
```bash
ssh unitree@192.168.123.164

conda activate twist2
cd /home/unitree/TWIST2/deploy_real

python server_low_level_g1_real.py \
    --policy /home/unitree/policies/twist2_policy.onnx \
    --config configs/g1.yaml \
    --use_hand \
    --hand_type amazing_hand \
    --serial_port /dev/ttyACM0 \
    --baudrate 1000000 \
    --redis_ip 192.168.123.222 \
    --net eth0
```

**確認事項:**
- ✅ "✅ Using AmazingHand (8 DOF, port: /dev/ttyACM0)"
- ✅ "Robot: G1"
- ✅ "Motors: 29"
- ✅ "[green]Successfully connected to the robot[/green]"
- ✅ G1がデフォルトポーズに移行

**表示例:**
```
Starting TWIST2 real robot controller...
  Policy file: /home/unitree/policies/twist2_policy.onnx
  Config file: configs/g1.yaml
  Use hand: True

============================================================
Initialize AmazingHandController...
============================================================
Serial port: /dev/ttyACM0
Baudrate: 1000000

✅ Serial connection established
🔧 Enabling torque for all servos...
✅ Torque enabled for all motors
✅ Using AmazingHand (8 DOF, port: /dev/ttyACM0)

Robot: G1
Motors: 29
Control mode set to: PR
[green]Successfully connected to the robot[/green]
```

---

### ステップ3: PICO VR準備

1. **PICO VRヘッドセットを装着**
2. **XRobotToolkitアプリが起動していることを確認**
3. **左右コントローラーを握る**

---

### ステップ4: テレオペ開始

#### 状態遷移
TWIST2は以下の状態を持ちます:
- **idle**: 待機状態（何もしない）
- **teleop**: テレオペ実行中
- **pause**: データ受信するが実行しない
- **exit**: 終了

#### 操作方法

**右コントローラー key_one ボタン:**
- idle → teleop → pause → teleop → ... (サイクル)

**左コントローラー key_one ボタン:**
- どの状態からでも → exit (終了)

**左コントローラー axis_click:**
- 緊急停止

---

## 操作方法

### 全身動作
| 入力 | 動作 |
|------|------|
| **頭を動かす** | Neckが追従（Yaw/Pitch） |
| **体を動かす** | G1全身が追従（29関節） |
| **腕を動かす** | 腕が追従（左右7DOF×2） |

### Hand操作
| ボタン | 動作 |
|--------|------|
| **右コントローラー index_trig** | 右手が段階的に閉じる（5%/フレーム） |
| **右コントローラー grip** | 右手が段階的に開く（5%/フレーム） |
| **左コントローラー index_trig** | 左手が段階的に閉じる（5%/フレーム） |
| **左コントローラー grip** | 左手が段階的に開く（5%/フレーム） |

### 状態制御
| ボタン | 動作 |
|--------|------|
| **右 key_one** | idle → teleop → pause (サイクル) |
| **左 key_one** | 終了 |
| **左 axis_click** | 緊急停止 |

---

## 終了手順

### 1. テレオペ停止
```
左コントローラーの key_one ボタンを押す
→ exitモードに遷移
→ 自動的にデフォルトポーズに戻る
```

### 2. G1側プロセス停止

**SSH ターミナル2 (server_low_level):**
```
Ctrl+C を押す
→ AmazingHandがデフォルトポーズに戻る
→ トルク無効化
→ プロセス終了
```

**SSH ターミナル1 (b3m_neck_controller):**
```
Ctrl+C を押す
→ Neckがセンター位置に戻る
→ トルク無効化
→ プロセス終了
```

### 3. PC側プロセス停止

**PC ターミナル2 (xrobot_teleop):**
```
Ctrl+C を押す
→ プロセス終了
```

**XRoboToolkit PC Service:**
```
GUIウィンドウを閉じる
```

---

## トラブルシューティング

### 問題1: PC → G1のEthernet接続ができない

**症状:**
```bash
ping 192.168.123.164
# 応答なし
```

**解決策:**
```bash
# 1. PCのEthernet IPアドレス確認
ip addr show

# 2. IPアドレスが正しく設定されているか確認
# 192.168.123.222 になっているべき

# 3. G1のEthernet接続確認
# G1側でifconfigを実行し、eth0が192.168.123.164になっているか確認
```

---

### 問題2: "Redis connection failed"

**症状:**
```
❌ Redis connection failed: Connection refused
```

**解決策:**
```bash
# PC側でRedis起動確認
redis-cli ping
# PONG が返ればOK

# 返らない場合
sudo systemctl start redis-server
sudo systemctl status redis-server

# Redis設定確認
sudo nano /etc/redis/redis.conf
# bind 0.0.0.0
# protected-mode no
sudo systemctl restart redis-server
```

---

### 問題3: "Serial port not found" (/dev/ttyACM0 または /dev/ttyUSB1)

**症状:**
```
FileNotFoundError: [Errno 2] No such file or directory: '/dev/ttyACM0'
```

**解決策:**
```bash
# シリアルポート一覧確認
ls -l /dev/tty* | grep -E 'USB|ACM'

# USB接続確認
# - AmazingHandのWaveshare Adapterが接続されているか
# - NeckのUSBケーブルが接続されているか

# パーミッション確認
ls -l /dev/ttyACM0
# crw-rw---- となっていればOK

# パーミッションエラーの場合
sudo usermod -a -G dialout $USER
# ログアウト→ログインで反映
```

---

### 問題4: AmazingHandが動かない

**症状:**
- server_low_levelは起動するがHandが動かない
- "Waiting for commands from xrobot_teleop..."が続く

**解決策:**
```bash
# 1. PC側でxrobot_teleopが起動しているか確認
# Teleop Loop Execution FPS が表示されているか

# 2. Redisにデータが書き込まれているか確認
redis-cli get action_hand_left_unitree_g1_with_hands
# JSON配列が返ればOK

# 3. index_trig/gripボタンを押してみる
# → Hand位置が変化するはず

# 4. 電源確認
# Waveshare Adapterの5V LEDが点灯しているか
```

---

### 問題5: Neckが動かない

**症状:**
- b3m_neck_controllerは起動するがNeckが動かない

**解決策:**
```bash
# 1. B3Mサーボの電源確認
# B3Mコントローラーの電源LEDが点灯しているか

# 2. シリアルポート確認
ls -l /dev/ttyUSB1

# 3. ボーレート確認
# B3Mは1.5Mbps (1500000) が推奨

# 4. 手動でヘッドセットを動かしてみる
# → Neckが追従するはず
```

---

### 問題6: G1本体は動くがHandやNeckが動かない

**症状:**
- G1本体は正常に動作
- HandやNeckが反応しない

**原因:**
PC側のxrobot_teleopで`--robot`オプションが間違っている

**解決策:**
```bash
# 正しいコマンド:
python xrobot_teleop_to_robot_w_hand.py \
    --robot unitree_g1_with_hands \  # ← これが重要
    --redis_ip localhost

# 間違い例:
# --robot unitree_g1  ← これだとHandデータが送信されない
```

---

### 問題7: "ModuleNotFoundError: No module named 'unitree_interface'"

**症状:**
```
ModuleNotFoundError: No module named 'unitree_interface'
```

**解決策:**
```bash
# G1側でUnitree SDK2をインストール
cd /home/unitree/unitree_sdk2/python_binding
export UNITREE_SDK2_PATH=$(pwd)/..
bash build.sh --sdk-path $UNITREE_SDK2_PATH

# インストール確認
python -c "import unitree_interface; print('OK')"
```

---

### 問題8: ONNXポリシーファイルが見つからない

**症状:**
```
Error: Policy file /path/to/policy.onnx does not exist
```

**解決策:**
```bash
# ポリシーファイルの場所確認
ls -l /home/unitree/policies/

# ファイルが存在しない場合、PCからG1にコピー
scp /path/to/policy.onnx unitree@192.168.123.164:/home/unitree/policies/
```

---

## パフォーマンス指標

### 正常動作時の目安

| 項目 | 目標値 | 確認方法 |
|------|--------|----------|
| **xrobot_teleop FPS** | 95-100 Hz | ターミナル出力 |
| **G1制御ループ** | 50 Hz | server_low_levelログ |
| **Neck制御** | 50 Hz | b3m_neck_controllerログ |
| **Hand制御** | 50 Hz | server_low_levelログ |
| **Ethernet遅延** | <10 ms | `ping 192.168.123.164` |

---

## 付録

### A. ディレクトリ構成

#### PC側
```
/home/kota-ueda/
├── TWIST2/
│   ├── deploy_real/
│   │   ├── xrobot_teleop_to_robot_w_hand.py
│   │   ├── robot_control/
│   │   ├── data_utils/
│   │   └── configs/
│   ├── GMR/
│   └── test_amazinghand/
└── XRoboToolkit-PC-Service-Pybind/
```

#### G1側
```
/home/unitree/
├── TWIST2/
│   ├── deploy_real/
│   │   ├── server_low_level_g1_real.py
│   │   ├── robot_control/
│   │   ├── data_utils/
│   │   └── configs/
│   └── B3M/
│       ├── b3m_controller.py
│       └── b3m_neck_controller_redis.py
├── unitree_sdk2/
└── policies/
    └── twist2_policy.onnx
```

---

### B. 使用するRedisキー

| キー名 | 次元 | 内容 |
|--------|------|------|
| `action_body_unitree_g1_with_hands` | 35D | G1全身コマンド |
| `action_hand_left_unitree_g1_with_hands` | 8D | 左手コマンド |
| `action_hand_right_unitree_g1_with_hands` | 8D | 右手コマンド |
| `action_neck_unitree_g1_with_hands` | 2D | Neck Yaw/Pitch |

---

### C. conda環境一覧

| 環境名 | Python | 用途 | マシン |
|--------|--------|------|--------|
| `gmr` | 3.10 | モーションリターゲティング | PC |
| `twist2` | 3.8 | G1制御 | G1 |
| `amazinghand` | 3.10 | テスト用 | PC |

---

## サポート

### 関連ドキュメント
- [RUN_PICO_CONTROL.md](./RUN_PICO_CONTROL.md) - AmazingHand単体テスト
- [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - 実装サマリー
- [GitHub Issue #2](https://github.com/Orboh/twist2_B3M-SC-1040-A/issues/2) - Neck統合版

### 問題報告
問題が発生した場合は、以下の情報を含めて報告してください:
1. 実行したコマンド
2. エラーメッセージ（ターミナル出力全体）
3. どのステップで発生したか
4. 環境情報（OS、conda環境、etc）

---

**最終更新: 2026-01-11**
**作成者: TWIST2 AmazingHand Integration Project**
