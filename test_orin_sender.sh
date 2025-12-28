#!/bin/bash
# OrinVideoSender test script
# デバッグ用の低負荷設定でテストします

cd /home/kota-ueda/XRoboToolkit-Orin-Video-Sender

echo "========================================"
echo "OrinVideoSender Debug Test"
echo "========================================"
echo ""
echo "Configuration:"
echo "  Resolution: Will be set by Pico (default 2560x720)"
echo "  Framerate: Will be set by Pico (default 60fps)"
echo "  Bitrate: Will be set by Pico (default 4Mbps)"
echo ""
echo "Recommendations for stable streaming:"
echo "  - 1280x720 @ 30fps @ 8Mbps (good quality, stable)"
echo "  - 2560x720 @ 30fps @ 12Mbps (stereo, stable)"
echo "  - 2560x720 @ 60fps @ 16Mbps (stereo, high quality)"
echo ""
echo "Current setup: listening on 192.168.50.37:13579"
echo "Video stream target: Pico at 192.168.50.232:12345"
echo ""
echo "========================================"
echo ""

# プレビューなしで起動（リソース削減）
echo "Starting OrinVideoSender (no preview)..."
./OrinVideoSender --listen 192.168.50.37:13579

# プレビューありで起動する場合は以下を使用:
# ./OrinVideoSender --preview --listen 192.168.50.37:13579
