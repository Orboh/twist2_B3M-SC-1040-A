import redis
import json
import time
import numpy as np

# Redisに接続
r = redis.Redis(host='localhost', port=6379, db=0)

print("Redis経由で首の角度(Yaw)をスイングさせます。Ctrl+Cで終了。")

try:
    angle = 0
    while True:
        # -0.5rad から 0.5rad (約±30度) の間でサイン波を作る
        target_yaw = np.sin(angle) * 0.5
        
        # TWIST2の形式 [Pitch, Yaw] に合わせてリストを作成
        neck_data = [0.0, target_yaw]
        
        # Redisに書き込み
        r.set("action_neck_unitree_g1_with_hands", json.dumps(neck_data))
        
        angle += 0.1
        time.sleep(0.05)
except KeyboardInterrupt:  # ← アンダースコアを削除
    print("\nテスト終了")