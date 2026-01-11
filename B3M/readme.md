b3m_head_controller_twist2.py を作成しました。このプログラムは：

  ✅ twist2環境だけで動く（追加インストール不要）
  ✅ TWIST2のXRobotStreamerを使用
  ✅ TWIST2のhuman_head_to_robot_neck()を使用
  ✅ B3M制御を完全実装

  実行方法

  1. パーミッション確認

  sudo chmod 666 /dev/ttyUSB0

  2. PICO VRを接続

  PICO VRヘッドセットをPCに接続し、XRoboToolkit APPを起動

  3. プログラム実行

  cd /home/kota-ueda/TWIST2/B3M

  # twist2環境で実行
  conda activate twist2
  python b3m_head_controller_twist2.py

  オプション

  # 制御周波数を変更（デフォルト30Hz）
  python b3m_head_controller_twist2.py --freq 50

  # 動きのスケールを変更（デフォルト1.5）
  python b3m_head_controller_twist2.py --scale 1.0

  # シリアルポートを指定
  python b3m_head_controller_twist2.py --port /dev/ttyUSB1

  動作の流れ

  1. PICO VRヘッドセットの向きを取得
  2. TWIST2の方法でneck角度に変換
  3. B3Mモーター（YawとPitch）に送信
  4. リアルタイムで頭の動きを追跡

  表示例

  🚀 Initializing B3M Head Controller (TWIST2 Edition)...
  ✅ XRobotStreamer initialized (PICO VR connected)
  ✅ B3M Controller initialized on /dev/ttyUSB0 @ 1500000bps

デバックモード

デバッグモードを追加しました！🔍

  デバッグモードで実行

  # パーミッション確認
  sudo chmod 666 /dev/ttyUSB0

  # デバッグモードで実行
  cd /home/kota-ueda/TWIST2/B3M
  python b3m_head_controller_twist2.py --debug

  デバッグ情報の見方

  以下のような詳細情報が表示されます：

  📊 Raw headset_pose: [x, y, z, qx, qy, qz, qw]
     Position (x,y,z): [0.123, 0.456, 1.234]
     Quaternion (qx,qy,qz,qw): [0.001, 0.002, 0.003, 0.999]
     Neck angles (rad): yaw=0.123, pitch=0.456
     After scale (×1.5): yaw=10.5°, pitch=39.2°
     Final (clamped): yaw=10.5°, pitch=39.2°

  確認してほしいこと

  PICO VRを装着して、以下を試してください：

  1️⃣ 頭を左に振る

  期待される変化:
    Quaternion → 変化
    yaw → 大きく変化（プラス方向）
    pitch → あまり変化しない

  2️⃣ 頭を右に振る

  期待される変化:
    yaw → 大きく変化（マイナス方向）
    pitch → あまり変化しない

  3️⃣ 頭を上に向ける

  期待される変化:
    yaw → あまり変化しない
    pitch → 大きく変化（プラス方向）

  4️⃣ 頭を下に向ける

  期待される変化:
    pitch → 大きく変化（マイナス方向）

  実行してください

  デバッグ情報をコピーして貼り付けてください。何が起きているか

モータの遅延問題を解決！！！
  # 1. レイテンシタイマを1msに変更（今すぐ適用）
  sudo chmod a+w /sys/bus/usb-serial/devices/ttyUSB0/latency_timer
  echo 1 | sudo tee /sys/bus/usb-serial/devices/ttyUSB0/latency_timer

  # 2. udevルールをシステムにコピー（再起動後も自動適用）
  sudo cp /home/kota-ueda/TWIST2/B3M/b3m_latency_timer.rules /etc/udev/rules.d/

  # 3. udevルールを再読み込み
  sudo udevadm control --reload-rules

  # 4. 確認（1になっていればOK）
  cat /sys/bus/usb-serial/devices/ttyUSB0/latency_timer


キャリブレーション
python b3m_head_controller_twist2.py --calibrate


● 問題が特定できました！Kondo Kagaku RS485 USB/Serial Converterは認識されていますが、適切なドライバーがロードされていないため/dev/ttyUSB0デバイスが作成されていません。

  解決方法

  1. USBシリアルドライバーをロードする

  ターミナルで以下のコマンドを実行してください：

  # FTDIドライバーをロード（Kondo Kagakuデバイス用）
  sudo modprobe ftdi_sio

  # ベンダーIDとプロダクトIDを手動で追加
  echo "165c 0009" | sudo tee /sys/bus/usb-serial/drivers/ftdi_sio/new_id

  2. デバイスが作成されたか確認

  ls -la /dev/ttyUSB*

  成功すると以下のように表示されます：
  crw-rw---- 1 root dialout 188, 0 Jan 6 17:00 /dev/ttyUSB0

  3. パーミッションを設定（必要な場合）

  sudo chmod 666 /dev/ttyUSB0

  または、永続的な解決策として：

  # dialoutグループに所属しているか確認
  groups
  # dialoutがあれば、ログアウト→ログインで反映されます

  4. B3Mスクリプトを実行

  cd /home/kota-ueda/TWIST2/B3M
  conda activate twist2
  python b3m_head_controller_twist2.py

