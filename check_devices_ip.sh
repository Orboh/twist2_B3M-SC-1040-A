#!/bin/bash
# デバイスIPアドレス確認スクリプト

echo "========================================="
echo "  デバイスIPアドレス確認"
echo "========================================="

echo -e "\n=== PC IP Addresses ==="
echo "WiFi (wlp0s20f3) - Pico接続用:"
ip -4 addr show wlp0s20f3 2>/dev/null | grep inet | awk '{print "  " $2}' || echo "  未接続"

echo "Ethernet (enx4c858aeb8f5a) - G1接続用:"
ip -4 addr show enx4c858aeb8f5a 2>/dev/null | grep inet | awk '{print "  " $2}' || echo "  未接続"

echo -e "\n=== Pico Ultra ==="
PICO_INFO=$(arp -a | grep -i "04:34:c3:8b:08:56")
if [ -n "$PICO_INFO" ]; then
    echo "  $PICO_INFO"
else
    echo "  ARPテーブルに未登録 (WiFiサブネットをスキャンしてください)"
fi

echo -e "\n=== G1 Unitree ==="
# イーサネットのサブネットを取得
ETH_SUBNET=$(ip -4 addr show enx4c858aeb8f5a 2>/dev/null | grep inet | awk '{print $2}')
if [ -n "$ETH_SUBNET" ]; then
    # サブネットを取得（例: 192.168.123.99/24 -> 192.168.123.0/24）
    SUBNET=$(echo $ETH_SUBNET | awk -F'.' '{print $1"."$2"."$3".0/24"}')
    echo "  イーサネットサブネット $SUBNET をスキャン中..."
    G1_IP=$(arp -a | grep -i "fc:23:cd:92:62:b6")
    if [ -n "$G1_IP" ]; then
        echo "  $G1_IP"
    else
        echo "  ARPテーブルに未登録 (通信を試してください)"
    fi
else
    echo "  イーサネット未接続"
fi

echo -e "\n========================================="
echo "  確認完了"
echo "========================================="
