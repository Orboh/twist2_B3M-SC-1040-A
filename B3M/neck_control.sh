#!/bin/bash
#
# B3M Neck Controller 起動スクリプト
# Usage: bash neck_control.sh [redis_ip]
#

# デフォルト設定
REDIS_IP="${1:-192.168.123.99}"
SERIAL_PORT="/dev/ttyUSB0"
BAUDRATE=1500000

echo "============================================================"
echo "  B3M Neck Controller 起動スクリプト"
echo "============================================================"
echo "Redis IP: ${REDIS_IP}"
echo "Serial port: ${SERIAL_PORT}"
echo ""

# Step 1: FTDIドライバーをロード
echo "Step 1: FTDIドライバーをロード..."
sudo modprobe ftdi_sio
if [ $? -eq 0 ]; then
    echo "  ✅ ftdi_sioドライバーをロードしました"
else
    echo "  ⚠️ ftdi_sioドライバーのロードに失敗（既にロード済みの可能性）"
fi

# Step 2: Kondo Kagaku RS485アダプターを登録
echo "Step 2: Kondo Kagaku RS485アダプターを登録..."
echo "165c 0009" | sudo tee /sys/bus/usb-serial/drivers/ftdi_sio/new_id > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ デバイスIDを登録しました"
else
    echo "  ⚠️ デバイスID登録に失敗（既に登録済みの可能性）"
fi

# Step 3: デバイスが作成されるまで待機
echo "Step 3: デバイスの作成を待機..."
sleep 1

if [ -e "${SERIAL_PORT}" ]; then
    echo "  ✅ ${SERIAL_PORT} が見つかりました"
else
    echo "  ❌ ${SERIAL_PORT} が見つかりません"
    echo "  USBケーブルが接続されているか確認してください"
    exit 1
fi

# Step 4: パーミッション設定
echo "Step 4: パーミッション設定..."
sudo chmod 666 ${SERIAL_PORT}
if [ $? -eq 0 ]; then
    echo "  ✅ パーミッションを設定しました"
else
    echo "  ❌ パーミッション設定に失敗しました"
    exit 1
fi

# Step 5: Python環境をアクティベート
echo "Step 5: Python環境をアクティベート..."
if [ -f ~/miniconda3/bin/activate ]; then
    source ~/miniconda3/bin/activate twist2
    echo "  ✅ twist2環境をアクティベートしました"
elif [ -f ~/.local/bin/activate ]; then
    source ~/.local/bin/activate
    echo "  ✅ 仮想環境をアクティベートしました"
else
    echo "  ⚠️ 仮想環境が見つかりません（システムPythonを使用）"
fi

echo ""
echo "============================================================"
echo "  B3M Neck Controller を起動します"
echo "============================================================"
echo ""

# Step 6: B3M Neck Controllerを起動
SCRIPT_DIR=$(dirname $(realpath $0))
cd ${SCRIPT_DIR}
python b3m_neck_controller_redis.py \
    --redis_ip ${REDIS_IP} \
    --port ${SERIAL_PORT} \
    --baudrate ${BAUDRATE}
