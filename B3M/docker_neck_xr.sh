#!/bin/bash
# XRoboToolkit版 B3M Neck Controller

sudo chmod 777 /dev/ttyUSB0

source ~/miniconda3/bin/activate twist2

python ~/g1-onboard/b3m_head_controller.py \
    --port /dev/ttyUSB0 \
    --baudrate 1500000 \
    --xr_host <PC_IP_ADDRESS> \
    --xr_port 8000