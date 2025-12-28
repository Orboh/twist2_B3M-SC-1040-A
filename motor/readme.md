pip install pynput
pip install pyserial

（ドライバ）がいるか確認
  lsmod | grep ftdi

ドライバを呼ぶ
sudo modprobe ftdi_sio

# 近藤科学のデバイス用に設定
echo "165c 0009" | sudo tee /sys/bus/usb-serial/drivers/ftdi_sio/new_id

/dev/ttyUSB0）ができたか確認
  ls -l /dev/ttyUSB0

  # test3.py を実行
  cd /home/kota-ueda/TWIST2/motor
  python test3.py

   sudo chmod 666 /dev/ttyUSB0
  python test3.py