
source ~/miniconda3/bin/activate twist2

SCRIPT_DIR=$(dirname $(realpath $0))
ckpt_path=${SCRIPT_DIR}/assets/ckpts/twist2_1017_20k.onnx

# PC側のネットワークインターフェース（G1と接続）
net=enx4c858aeb8f5a

cd deploy_real

# PC側で実行（GPU使用可能、ハンドはG1側で別途制御）
python server_low_level_g1_real.py \
    --policy ${ckpt_path} \
    --net ${net} \
    --device cuda \
    --redis_ip localhost
    # --use_hand \
    # --hand_type amazing_hand \
    # --serial_port /dev/ttyACM0 \
    # --smooth_body 0.5
    # --record_proprio \
