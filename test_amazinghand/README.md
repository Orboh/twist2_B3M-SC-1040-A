# AmazingHand Integration Tests

このディレクトリには、TWIST2システムにAmazingHandを統合するためのテストスクリプトが含まれています。

## ハードウェアセットアップ

実行前に以下を確認してください：

1. **電源供給**: AmazingHandに5V 2A以上の電源を接続
2. **シリアル接続**: Waveshare Bus Servo AdapterをG1のUSBポートに接続
3. **配線**: 左右両手を同じシリアルバスに接続
   - 右手: サーボID 1-8
   - 左手: サーボID 11-18
4. **シリアルポート**: デバイス名を確認（通常は`/dev/ttyUSB0`または`/dev/ttyACM0`）

## テスト実行手順

### 事前準備

```bash
# シリアルポートの確認
ls -l /dev/ttyUSB0

# パーミッションエラーが出る場合
sudo chmod 666 /dev/ttyUSB0

# amazinghand環境をアクティベート
conda activate amazinghand

# テストディレクトリに移動
cd /home/kota-ueda/TWIST2/test_amazinghand
```

### テスト1: 基本接続テスト

全16モーター（ID 1-8, 11-18）との通信を確認します。

```bash
python test_basic_connection.py --serial_port /dev/ttyUSB0
```

**期待する結果:**
```
✅ TEST 1 PASSED - All motors responding!
Total: 16/16 motors responding
```

### テスト2: 両手制御テスト

両手の開閉、非対称制御、段階的補間をテストします。

```bash
python test_dual_hand.py --serial_port /dev/ttyUSB0
```

**期待する結果:**
```
✅ TEST 2 PASSED - All dual hand tests completed successfully!
```

**テスト内容:**
- 両手を開く
- 両手を閉じる
- 左手開、右手閉（非対称制御）
- 0%から100%まで段階的に閉じる
- デフォルトポーズに戻る

### テスト3: Redis統合テスト

Redis経由での8次元配列の送受信をテストします。

```bash
# Redisサーバーが起動していない場合は起動
redis-server &

# テスト実行
python test_redis_integration.py
```

**期待する結果:**
```
✅ TEST 3 PASSED - Redis integration working correctly!
```

## トラブルシューティング

### エラー: "Permission denied" on /dev/ttyUSB0

```bash
# 一時的な解決策
sudo chmod 666 /dev/ttyUSB0

# 恒久的な解決策（再ログイン必要）
sudo usermod -a -G dialout $USER
```

### エラー: "No such file or directory"

シリアルデバイス名が異なる可能性があります：

```bash
# 接続されているシリアルデバイスを確認
ls -l /dev/tty* | grep -E 'USB|ACM'

# 見つかったデバイス名で実行
python test_basic_connection.py --serial_port /dev/ttyACM0
```

### モーターが応答しない

1. **電源確認**: 5V電源が接続され、LEDが点灯しているか
2. **サーボID確認**: モーターIDが正しく設定されているか
   - AmazingHandのキャリブレーションツールで確認可能
3. **ボーレート**: 1000000で通信できない場合、500000を試す

```bash
python test_basic_connection.py --baudrate 500000
```

### Redis connection failed

```bash
# Redisサーバーを起動
redis-server &

# Redisが起動しているか確認
redis-cli ping
# PONG が返ってくればOK
```

## 全テスト一括実行

```bash
#!/bin/bash
# run_all_tests.sh

echo "Running AmazingHand Integration Tests..."
echo ""

# Test 1
echo "=== Test 1: Basic Connection ==="
python test_basic_connection.py --serial_port /dev/ttyUSB0
if [ $? -ne 0 ]; then
    echo "Test 1 failed. Stopping."
    exit 1
fi

echo ""
echo "=== Test 2: Dual Hand Control ==="
python test_dual_hand.py --serial_port /dev/ttyUSB0
if [ $? -ne 0 ]; then
    echo "Test 2 failed. Stopping."
    exit 1
fi

echo ""
echo "=== Test 3: Redis Integration ==="
redis-cli ping > /dev/null 2>&1 || redis-server &
sleep 1
python test_redis_integration.py
if [ $? -ne 0 ]; then
    echo "Test 3 failed. Stopping."
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ All tests passed!"
echo "=========================================="
```

実行方法:
```bash
chmod +x run_all_tests.sh
./run_all_tests.sh
```

## 次のステップ

全テストが成功したら、TWIST2システムとの統合に進めます：

1. **server_low_level_g1_real.py**: `--hand_type amazing_hand`オプションを追加
2. **xrobot_teleop_to_robot_w_hand.py**: `--robot amazing_hand`オプションを追加
3. **フルシステムテスト**: Picoコントローラーで実機制御

詳細は `IMPLEMENTATION_PLAN.md` を参照してください。

## 参考ファイル

- `/home/kota-ueda/TWIST2/deploy_real/robot_control/amazing_hand_wrapper.py`
- `/home/kota-ueda/TWIST2/deploy_real/data_utils/params.py`
- `/home/kota-ueda/AmazingHand/PythonExample/AmazingHand_Demo_Both.py`
