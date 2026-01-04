# ZED Mini → Pico VR ビデオストリーミング デバッグレポート

## 現在の構成（互換性確認済み）

| コンポーネント | バージョン | 状態 |
|---|---|---|
| Unity Client (Pico) | v1.1.0 | ✅ インストール済み |
| OrinVideoSender (PC) | v1.0.0 | ✅ 動作中 |
| XRoboToolkit PC Service | インストール済み | ✅ 正常 |
| 互換性 | 公式確認済み | ✅ v1.1.0 ⟷ v1.0.0 |

## 設定

```yaml
ZEDMINI:
  CamWidth: 2560
  CamHeight: 720
  CamFPS: 60
  CamBitrate: 12000000  # 12Mbps
```

## PC側の動作（完璧）

```
✅ OrinVideoSender起動成功
✅ Picoからの接続を受信 (192.168.50.232)
✅ OPEN_CAMERAコマンド受信
✅ カメラ設定確認: 2560x720@60fps, 12Mbps
✅ ZED Miniカメラ正常にオープン
✅ GStreamer H.264エンコードパイプライン作成成功
✅ Picoのポート12345に接続成功
✅ ストリーミング開始
```

## Pico側の動作（問題あり）

```
✅ OrinVideoSenderのポート13579に接続成功
✅ OPEN_CAMERAコマンド送信成功
❌ ストリーミング開始直後に切断 ("Client disconnected gracefully")
❌ ビデオデコーダーのログなし（MediaCodec起動なし）
❌ 白い画面のまま
```

## 問題の核心

**OrinVideoSenderは正常に動作し、H.264ビデオストリームを送信している。**
**しかし、Pico Unity Clientが接続後すぐに切断し、ビデオデコーダーを起動していない。**

## 試したこと（すべて失敗）

1. ✗ ビットレートを4Mbps→12Mbpsに変更
2. ✗ Unity Clientをv1.1.1→v1.1.0にダウングレード
3. ✗ OrinVideoSenderをv1.0.0に固定
4. ✗ 設定ファイルの再転送
5. ✗ アプリの再インストール
6. ✗ 異なるビデオソース（PICO4U、ZEDMINI）の試行

## 推定される原因

1. **Unity Client v1.1.0自体のバグ**
   - ビデオデコーダー初期化に失敗している可能性
   - H.264デコーダーがPico 4で正しく動作していない可能性

2. **プロトコル/フォーマットの不一致**
   - OrinVideoSenderが送信するH.264ストリームの形式がUnity Clientの期待と異なる
   - NAL unit構造の問題

3. **Picoハードウェアデコーダーの問題**
   - MediaCodecが初期化できない
   - ハードウェアリソース不足

4. **アプリの権限や設定の問題**
   - 何か重要な設定が欠けている
   - 初回セットアップが必要

## 次に試すべきこと

### 1. 別のUnity Clientバージョンを試す
- v1.0.0やv1.0.1をインストールしてみる
- Quest版ではなく通常版を試す

### 2. Picoアプリの詳細ログを有効化
- Unity Clientのログレベルを上げる
- 何が失敗しているか特定する

### 3. 最小構成でのテスト
- test_video_receiver_fixed.pyでPC側の受信テスト
- OrinVideoSenderからPC内部での動作確認

### 4. XR-Robotics開発者への問い合わせ
- GitHub Issuesで報告
- この構成での成功例があるか確認

### 5. 別のVRヘッドセットでテスト
- Meta Quest 2/3などで同じ構成を試す
- Pico 4特有の問題か確認

## ログ証拠

### OrinVideoSender最終ログ
```
Camera config - Width: 2560, Height: 720, FPS: 60, Bitrate: 12000000
ZED camera opened successfully
Pipeline created: H.264 encoding @ 12Mbps
Connected to 192.168.50.232:12345
Starting streaming loop...
Client disconnected gracefully
```

### Picoログ
```
(ビデオデコーダー関連のログなし)
(MediaCodec関連のログなし)
```

## 結論

技術的には全て正しく設定されているが、**Pico Unity Client v1.1.0が何らかの理由でビデオストリームを受信/デコードできていない**。

これはアプリケーション層の問題であり、ネットワークやハードウェアの問題ではない。
