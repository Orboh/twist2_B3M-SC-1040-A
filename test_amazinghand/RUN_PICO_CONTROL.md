# Picoコントローラー × AmazingHand 操作ガイド

G1本体なしでPicoコントローラーからAmazingHandを直接制御する方法

## システム構成

```
Picoコントローラー
  ↓ (USB接続)
PC (xrobot_teleop実行)
  ↓ (Redis)
pico_amazinghand_control.py
  ↓ (シリアル)
AmazingHand実機
```

---

## 事前準備

### 1. ハードウェア接続
```
✅ AmazingHandに電源供給（5V 2A+）
✅ Waveshare Bus Servo AdapterをPCに接続（/dev/ttyACM0）
✅ Picoヘッドセット/コントローラーの電源ON
✅ PicoがPCと同じWiFiネットワークに接続されていることを確認
```

### 2. ソフトウェア確認
```bash
# Redisサーバー起動確認
redis-cli ping
# PONG が返ればOK

# 返らない場合は起動
redis-server &
```

### 3. XROBOtoolkit PC Service起動
```
✅ デスクトップメニューから "RoboticsService" を起動
   または
✅ コマンドラインから: /opt/apps/roboticsservice/runService.sh

確認: GUIウィンドウが表示され、Picoからのデータ受信が開始される
```

---

## 起動手順

### ターミナル1: Picoコントローラー入力読み取り

```bash
cd /home/kota-ueda/TWIST2/deploy_real
conda activate gmr

# xrobot_teleopを起動（amazing_handモード）
python xrobot_teleop_to_robot_w_hand.py \
    --robot amazing_hand \
    --redis_ip localhost
```

**確認事項:**
- Picoコントローラーが認識されている
- "Ready!"と表示される
- index_trig/gripボタンを押すとログが流れる

### ターミナル2: AmazingHand制御プログラム

別のターミナルを開いて：

```bash
cd /home/kota-ueda/TWIST2/test_amazinghand
conda activate amazinghand

# 簡易制御プログラムを起動
python pico_amazinghand_control.py --serial_port /dev/ttyACM0
```

**確認事項:**
- "✅ Redis connected"と表示される
- "✅ AmazingHandController initialized successfully!"と表示される
- "🎮 Ready!"と表示される

---

## 操作方法

Picoコントローラーで操作：

| ボタン | 動作 |
|--------|------|
| **index_trig（人差し指トリガー）** | 押している間、手が段階的に閉じる（5%/フレーム） |
| **grip（握るボタン）** | 押している間、手が段階的に開く（5%/フレーム） |

- 左右のコントローラーで左右の手を独立制御
- ボタンを離すとその位置で停止
- 0%（完全に開く）〜 100%（完全に閉じる）の範囲で制御

---

## 動作確認

### 正常動作の場合

**ターミナル1（xrobot_teleop）:**
```
Hand position: 0.25  # index_trigを押すと増加
```

**ターミナル2（pico_control）:**
```
[   10] Left:  1.23 rad  Right:  1.45 rad
[   20] Left:  2.45 rad  Right:  2.67 rad
```

実機のハンドが動く ✅

### トラブルシューティング

#### 問題1: "Waiting for commands from xrobot_teleop..."が続く

**原因:** ターミナル1が起動していない、またはボタンを押していない

**解決策:**
```bash
# ターミナル1でxrobot_teleopが起動しているか確認
# Picoのindex_trig/gripボタンを押してみる
```

#### 問題2: "Redis connection failed"

**原因:** Redisサーバーが起動していない

**解決策:**
```bash
redis-server &
redis-cli ping  # PONG を確認
```

#### 問題3: ハンドが動かない

**原因:** シリアルポートまたは電源の問題

**解決策:**
```bash
# シリアルポート確認
ls -l /dev/ttyACM0

# 電源確認（5V LEDが点灯しているか）
# 接続テストを実行
cd /home/kota-ueda/TWIST2/test_amazinghand
python test_basic_connection.py --serial_port /dev/ttyACM0
```

---

## 停止方法

### 通常の停止

1. ターミナル2で **Ctrl+C** を押す
   - ハンドが自動的にデフォルトポーズに戻る
   - トルクが無効化される

2. ターミナル1で **Ctrl+C** を押す

### 緊急停止

どちらのターミナルでも **Ctrl+C** を押せばすぐに停止します

---

## ワンライナー起動スクリプト

### start_pico_control.sh を作成

```bash
#!/bin/bash
# start_pico_control.sh

echo "Starting Pico → AmazingHand Control System..."
echo ""

# Check Redis
if ! redis-cli ping > /dev/null 2>&1; then
    echo "Starting Redis server..."
    redis-server &
    sleep 1
fi

echo "Redis: OK"
echo ""
echo "Please run these commands in separate terminals:"
echo ""
echo "Terminal 1:"
echo "  cd /home/kota-ueda/TWIST2/deploy_real"
echo "  conda activate gmr"
echo "  python xrobot_teleop_to_robot_w_hand.py --robot amazing_hand"
echo ""
echo "Terminal 2:"
echo "  cd /home/kota-ueda/TWIST2/test_amazinghand"
echo "  conda activate amazinghand"
echo "  python pico_amazinghand_control.py --serial_port /dev/ttyACM0"
```

実行権限付与:
```bash
chmod +x /home/kota-ueda/TWIST2/test_amazinghand/start_pico_control.sh
```

---

## 動作フロー詳細

```
1. Picoのindex_trigボタンを押す
   ↓
2. xrobot_teleop: hand_position += 0.05 (5%増加)
   ↓
3. xrobot_teleop: open + (close - open) * position を計算
   ↓
4. xrobot_teleop: 8次元配列をRedisに書き込み
   ↓
5. pico_control: Redisから8次元配列を読み取り
   ↓
6. pico_control: AmazingHandControllerに送信
   ↓
7. AmazingHandController: rustypot経由でサーボに指令
   ↓
8. ハンドが動く！
```

---

## パフォーマンス

- **制御周波数**: 約50Hz
- **レイテンシ**: 20-50ms（Picoボタン押下からハンド動作まで）
- **更新頻度**: 変化があった時のみ送信（効率的）

---

## まとめ

このシステムでG1本体なしでも：
- ✅ Picoコントローラーでの直接操作が可能
- ✅ 段階的な開閉制御
- ✅ 左右独立制御
- ✅ リアルタイム応答

G1本体がある環境では、server_low_level_g1_real.pyを使用して全身とハンドを統合制御できます。
