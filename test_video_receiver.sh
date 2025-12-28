#!/bin/bash
# Test video receiver script
# このスクリプトはOrinVideoSenderからのH.264ストリームを受信してテストします

echo "Starting test video receiver on port 12345..."
echo "Press Ctrl+C to stop"
echo ""
echo "This will:"
echo "1. Listen for TCP connection on port 12345"
echo "2. Receive H.264 video stream"
echo "3. Display video in ffplay window"
echo ""

# NCATまたはnetcatでTCP接続を受け付け、ffplayでデコード
# ポート12345でリッスン → H.264データをffplayにパイプ
nc -l 12345 | ffplay -f h264 -i -

# Alternative using socat if nc doesn't work:
# socat TCP-LISTEN:12345,reuseaddr,fork STDOUT | ffplay -f h264 -i -
