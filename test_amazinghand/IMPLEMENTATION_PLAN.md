# TWIST2 × AmazingHand 統合実装計画

## 概要

**目的**: TWIST2のG1 Dex3-1ハンド（7DOF、3本指）をAmazingHand（8DOF、4本指）に置き換え

**制御方式**: 段階的開閉（現在のG1方式を維持）
- `index_trig`ボタン押下 → 段階的に閉じる（5%/フレーム）
- `grip`ボタン押下 → 段階的に開く（5%/フレーム）

**接続構成**:
- Waveshare Bus Servo Adapter: 1台
- G1のType-CポートにUSB接続
- 左右両手を同じシリアルバスに接続
- サーボID: 右手1-8、左手11-18

---

## システム対比

| 項目 | G1 Dex3-1 | AmazingHand |
|------|-----------|-------------|
| DOF | 7 (親指3+人差し指2+中指2) | 8 (親指2+人差し指2+中指2+薬指2) |
| 通信 | Unitree SDK2 | シリアル通信（rustypot） |
| データ | 7次元配列（ラジアン） | 8次元配列（ラジアン） |
| API | unitree_interface.HandInterface | rustypot.Scs0009PyController |

---

## 実装ファイル一覧

### 新規作成ファイル

1. **amazing_hand_wrapper.py** (~350行)
   - パス: `/home/kota-ueda/TWIST2/deploy_real/robot_control/amazing_hand_wrapper.py`
   - 役割: AmazingHand制御の中核クラス
   - 特徴: Dex3_1_Controllerと同じインターフェース

2. **テストスクリプト群**
   - `test_amazinghand/test_basic_connection.py` - シリアル接続テスト
   - `test_amazinghand/test_dual_hand.py` - 両手制御テスト
   - `test_amazinghand/test_redis_integration.py` - Redis統合テスト
   - `test_amazinghand/README.md` - テスト手順書

### 変更が必要なファイル

3. **params.py** (約20行追加)
   - パス: `/home/kota-ueda/TWIST2/deploy_real/data_utils/params.py`
   - 変更: DEFAULT_HAND_POSEに"amazing_hand"エントリを追加

4. **server_low_level_g1_real.py** (約50行変更)
   - パス: `/home/kota-ueda/TWIST2/deploy_real/server_low_level_g1_real.py`
   - 変更:
     - 引数に--hand_type, --serial_port, --baudrateを追加
     - 条件分岐でAmazingHandControllerを初期化

5. **xrobot_teleop_to_robot_w_hand.py** (1行変更)
   - パス: `/home/kota-ueda/TWIST2/deploy_real/xrobot_teleop_to_robot_w_hand.py`
   - 変更: --robotの選択肢に"amazing_hand"を追加

---

## データフロー

```
[Picoコントローラー]
  ↓ index_trig/grip (デジタルボタン)
[StateMachine] (xrobot_teleop_to_robot_w_hand.py)
  ↓ hand_position: 0.0-1.0 (段階的に±5%)
[get_hand_pose()]
  ↓ 8次元配列補間 (open + (close - open) * position)
[Redis] action_hand_left/right_unitree_g1_with_hands
  ↓
[server_low_level_g1_real.py]
  ↓
[AmazingHandController] (amazing_hand_wrapper.py)
  ↓ ctrl_dual_hand(left_8d, right_8d)
[rustypot.Scs0009PyController]
  ↓ write_goal_position(servo_id, angle)
[AmazingHand ハードウェア]
```

---

## 段階的実装手順

### フェーズ1: 準備（1日目）

#### ステップ1.1: 環境準備
```bash
# テストディレクトリ作成
mkdir -p /home/kota-ueda/TWIST2/test_amazinghand/{configs,logs}

# rustypotインストール確認
conda activate amazinghand
python -c "from rustypot import Scs0009PyController; print('OK')"

# シリアルポート確認
ls -l /dev/ttyUSB0
# 権限エラーが出る場合:
sudo chmod 666 /dev/ttyUSB0
```

#### ステップ1.2: ハードウェア接続テスト
```bash
# AmazingHandの既存デモで接続確認
cd ~/AmazingHand/PythonExample
python3 AmazingHand_Demo_Both.py
# → 左右の手が動けばOK
```

---

### フェーズ2: コア実装（2日目）

#### ステップ2.1: amazing_hand_wrapper.py作成
- 完全な実装コードは別途提供
- 主要機能:
  - `__init__()`: シリアル接続、トルク有効化
  - `ctrl_dual_hand()`: 8次元配列で両手制御
  - `get_hand_state()`: 現在位置読み取り
  - `close()`: トルク無効化、クリーンアップ

#### ステップ2.2: 単体テスト
```bash
cd /home/kota-ueda/TWIST2/deploy_real/robot_control
python amazing_hand_wrapper.py --serial_port /dev/ttyUSB0
```
期待する動作: 人差し指が段階的に動く

---

### フェーズ3: 設定追加（2日目）

#### ステップ3.1: params.py修正
DEFAULT_HAND_POSEに追加:
```python
"amazing_hand": {
    "left": {
        "open": np.array([-0.61, 0.61, -0.61, 0.61, -0.61, 0.61, -0.61, 0.61]),
        "close": np.array([1.57, -1.57, 1.57, -1.57, 1.57, -1.57, 1.57, -1.57])
    },
    "right": {
        "open": np.array([-0.61, 0.61, -0.61, 0.61, -0.61, 0.61, -0.61, 0.61]),
        "close": np.array([1.57, -1.57, 1.57, -1.57, 1.57, -1.57, 1.57, -1.57])
    }
}
```

配列の順序: [Index_0, Index_1, Middle_0, Middle_1, Ring_0, Ring_1, Thumb_0, Thumb_1]

---

### フェーズ4: テスト作成（3日目）

#### ステップ4.1: テストスクリプト作成
3つのテストファイルを作成:
1. `test_basic_connection.py` - 全16モーター（1-8, 11-18）の接続確認
2. `test_dual_hand.py` - 開閉動作テスト
3. `test_redis_integration.py` - Redis経由のデータ送受信

#### ステップ4.2: テスト実行
```bash
cd /home/kota-ueda/TWIST2/test_amazinghand

# テスト1: 接続確認
python test_basic_connection.py --serial_port /dev/ttyUSB0

# テスト2: 両手制御
python test_dual_hand.py --serial_port /dev/ttyUSB0

# テスト3: Redis（redis-server起動が必要）
redis-server &
python test_redis_integration.py
```

---

### フェーズ5: サーバー統合（4日目）

#### ステップ5.1: server_low_level_g1_real.py修正
4箇所の変更:
1. 引数パーサーに`--hand_type`, `--serial_port`, `--baudrate`追加
2. `__init__`で条件分岐してAmazingHandControllerを初期化
3. hand_dof変数で7/8を切り替え
4. main関数呼び出しで新引数を渡す

#### ステップ5.2: 構文チェック
```bash
cd /home/kota-ueda/TWIST2/deploy_real
python server_low_level_g1_real.py --help | grep hand_type
# → hand_typeオプションが表示されればOK
```

---

### フェーズ6: テレオペ統合（4日目）

#### ステップ6.1: xrobot_teleop_to_robot_w_hand.py修正
1行だけ変更:
```python
choices=["unitree_g1", "unitree_g1_with_hands", "amazing_hand"],
```

#### ステップ6.2: 構文チェック
```bash
python xrobot_teleop_to_robot_w_hand.py --help | grep amazing_hand
# → amazing_handが選択肢に表示されればOK
```

---

### フェーズ7: エンドツーエンドテスト（5日目）

#### ステップ7.1: フルシステム起動

**ターミナル1: サーバー起動**
```bash
cd /home/kota-ueda/TWIST2/deploy_real
python server_low_level_g1_real.py \
    --policy /path/to/policy.onnx \
    --config robot_control/configs/g1.yaml \
    --use_hand \
    --hand_type amazing_hand \
    --serial_port /dev/ttyUSB0 \
    --net wlp0s20f3
```

**ターミナル2: テレオペ起動**
```bash
cd /home/kota-ueda/TWIST2/deploy_real
python xrobot_teleop_to_robot_w_hand.py \
    --robot amazing_hand \
    --redis_ip localhost
```

#### ステップ7.2: 動作確認
1. Picoコントローラーで`index_trig`を押す → 手が段階的に閉じる
2. `grip`を押す → 手が段階的に開く
3. 左右独立制御を確認
4. フル開閉（0.0 → 1.0）を確認

---

### フェーズ8: キャリブレーション（6日目）

#### ステップ8.1: ポーズ調整
実機で確認して必要に応じて調整:
- openポーズ: 手が完全に開いているか？
- closeポーズ: 手が完全に閉じているか？機械的干渉はないか？

調整が必要な場合はparams.pyの値を微調整

#### ステップ8.2: 関節制限確認
amazing_hand_wrapper.pyの`QPOS_*_MIN/MAX`を必要に応じて調整

---

## サーボIDマッピング

### 右手 (シリアルバスID 1-8)
- 人差し指: モーター1, 2
- 中指: モーター3, 4
- 薬指: モーター5, 6
- 親指: モーター7, 8

### 左手 (シリアルバスID 11-18)
- 人差し指: モーター11, 12
- 中指: モーター13, 14
- 薬指: モーター15, 16
- 親指: モーター17, 18

### 配列内の順序
`[Index_0, Index_1, Middle_0, Middle_1, Ring_0, Ring_1, Thumb_0, Thumb_1]`

**重要**: 配列のインデックスと実際のサーボIDは異なります！
- 配列[0] (Index_0) → 右手ならID=1、左手ならID=11
- 配列[6] (Thumb_0) → 右手ならID=7、左手ならID=17

---

## トラブルシューティング

### 問題1: "Permission denied" on /dev/ttyUSB0
```bash
sudo chmod 666 /dev/ttyUSB0
# または恒久的に:
sudo usermod -a -G dialout $USER
# ログアウト→ログイン
```

### 問題2: モーターが応答しない
確認事項:
1. 電源供給（5V、2A以上）
2. サーボIDが正しく設定されているか
3. Waveshareアダプタの配線

デバッグ:
```python
from rustypot import Scs0009PyController
c = Scs0009PyController('/dev/ttyUSB0', 1000000)
print(c.read_present_position(1))  # モーター1の位置
```

### 問題3: Redis receives 7D instead of 8D
原因: teleop側でロボットタイプが間違っている
```bash
# NG:
--robot unitree_g1_with_hands

# OK:
--robot amazing_hand
```

### 問題4: 手の動きが速すぎる/遅すぎる
xrobot_teleop_to_robot_w_hand.pyの136行目を調整:
```python
self.hand_movement_step = 0.05  # デフォルト5%
# 遅くしたい → 0.03
# 速くしたい → 0.10
```

---

## 実装チェックリスト

### 準備
- [ ] rustypotインストール済み
- [ ] シリアルポートアクセス可能
- [ ] 電源供給確認（5V 2A）
- [ ] 全16モーター応答確認

### コア実装
- [ ] amazing_hand_wrapper.py作成
- [ ] 単体テスト成功
- [ ] params.py修正
- [ ] 8次元配列確認

### テスト
- [ ] test_basic_connection.py作成・成功
- [ ] test_dual_hand.py作成・成功
- [ ] test_redis_integration.py作成・成功

### 統合
- [ ] server_low_level_g1_real.py修正
- [ ] xrobot_teleop_to_robot_w_hand.py修正
- [ ] サーバー起動確認
- [ ] テレオペ起動確認

### 動作確認
- [ ] index_trigで閉じる動作
- [ ] gripで開く動作
- [ ] 段階的制御（5%ずつ）
- [ ] 左右独立制御
- [ ] フル開閉動作

### 最終調整
- [ ] openポーズ調整
- [ ] closeポーズ調整
- [ ] 機械的干渉なし
- [ ] 通信レート安定（50Hz）

---

## 次のステップ

実装完了後、以下の拡張が可能:

1. **トルクフィードバック**: SCS0009のトルクセンサーで物体検出
2. **温度監視**: モーター温度アラート
3. **ジェスチャーライブラリ**: 指差し、サムズアップなど
4. **自動キャリブレーション**: ゼロ位置の保存・読み込み
5. **設定ファイル化**: TOML形式でパラメータ管理

---

## 参考ファイルパス

### 既存のTWIST2ファイル
- `/home/kota-ueda/TWIST2/deploy_real/robot_control/dex_hand_wrapper.py`
- `/home/kota-ueda/TWIST2/deploy_real/data_utils/params.py`
- `/home/kota-ueda/TWIST2/deploy_real/server_low_level_g1_real.py`
- `/home/kota-ueda/TWIST2/deploy_real/xrobot_teleop_to_robot_w_hand.py`

### 参考になるAmazingHandファイル
- `/home/kota-ueda/AmazingHand/PythonExample/AmazingHand_Demo_Both.py`
- `/home/kota-ueda/AmazingHand/README.md`

### 作成するファイル
- `/home/kota-ueda/TWIST2/deploy_real/robot_control/amazing_hand_wrapper.py`
- `/home/kota-ueda/TWIST2/test_amazinghand/test_*.py`

---

**実装準備完了！次は具体的なコード実装に進みますか？**
