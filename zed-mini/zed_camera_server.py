#!/usr/bin/env python3
"""
ZED Camera Streaming Server for PICO VR (XRoboToolkit APP)
ZED miniカメラの映像をPICO VRのXRoboToolkit APPに送信
"""

import pyzed.sl as sl
import cv2
import zmq
import struct
import time
import numpy as np
import argparse


class ZEDCameraServer:
    def __init__(
        self,
        port=5556,
        resolution=sl.RESOLUTION.VGA,  # 640x480 (default)
        fps=30,
        jpeg_quality=80,
    ):
        """
        ZED Camera Streaming Server for XRoboToolkit APP

        Args:
            port: ZeroMQ PUB socket port
            resolution: Camera resolution (VGA=640x480, HD720=1280x720, HD1080=1920x1080)
            fps: Camera frame rate
            jpeg_quality: JPEG compression quality (0-100, higher = better quality)
        """
        self.port = port
        self.jpeg_quality = jpeg_quality

        # Initialize ZED camera
        print("=" * 60)
        print("  ZED Camera Streaming Server")
        print("  for PICO VR XRoboToolkit APP")
        print("=" * 60)
        print("\n🎥 Initializing ZED camera...")

        self.zed = sl.Camera()

        # Set camera parameters
        init_params = sl.InitParameters()
        init_params.camera_resolution = resolution
        init_params.camera_fps = fps
        init_params.depth_mode = sl.DEPTH_MODE.NONE  # RGB only for faster streaming
        init_params.coordinate_units = sl.UNIT.METER

        # Open camera
        err = self.zed.open(init_params)
        if err != sl.ERROR_CODE.SUCCESS:
            print(f"❌ Failed to open ZED camera: {err}")
            print("\nTroubleshooting:")
            print("  1. Is ZED mini connected to USB?")
            print("  2. Run: lsusb | grep ZED")
            print("  3. Check USB permissions")
            exit(1)

        # Get camera information
        camera_info = self.zed.get_camera_information()
        print(f"✅ ZED camera opened successfully")
        print(f"   Model: {camera_info.camera_model}")
        print(f"   Serial: {camera_info.serial_number}")
        print(f"   Resolution: {camera_info.camera_configuration.resolution.width}x{camera_info.camera_configuration.resolution.height}")
        print(f"   FPS: {camera_info.camera_configuration.fps}")

        # Create ZMQ publisher
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(f"tcp://*:{self.port}")

        # Get local IP address for display
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)

        print(f"\n📡 ZeroMQ publisher bound to port {self.port}")
        print(f"   Local IP: {local_ip}")
        print(f"   PICO VR should connect to: tcp://{local_ip}:{self.port}\n")

        # Image container
        self.image = sl.Mat()

        # Statistics
        self.frame_count = 0
        self.start_time = time.time()

    def get_frame(self):
        """
        Capture a frame from ZED camera.

        Returns:
            numpy array (H, W, 3) BGR format, or None if failed
        """
        # Grab frame
        if self.zed.grab() == sl.ERROR_CODE.SUCCESS:
            # Retrieve left image (RGB)
            self.zed.retrieve_image(self.image, sl.VIEW.LEFT)

            # Convert to numpy array (RGBA -> RGB)
            frame = self.image.get_data()
            frame_rgb = frame[:, :, :3]  # Remove alpha channel

            # Convert RGB to BGR for OpenCV/JPEG encoding
            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

            return frame_bgr
        else:
            return None

    def send_frame(self, frame):
        """
        Send frame via ZeroMQ (JPEG compressed).
        Format: [width][height][jpeg_length][jpeg_data]

        Args:
            frame: numpy array (H, W, 3) BGR format
        """
        if frame is None:
            return

        # Get frame dimensions
        height, width = frame.shape[:2]

        # JPEG compression
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
        result, jpeg_data = cv2.imencode('.jpg', frame, encode_param)

        if not result:
            print("⚠️ Failed to encode JPEG")
            return

        jpeg_bytes = jpeg_data.tobytes()
        jpeg_length = len(jpeg_bytes)

        # Build message: [width][height][jpeg_length][jpeg_data]
        # This format matches TWIST2's vision_client.py
        message = struct.pack('iii', width, height, jpeg_length) + jpeg_bytes

        # Send via ZeroMQ
        self.socket.send(message)

    def run(self, show_preview=False):
        """
        Main streaming loop.

        Args:
            show_preview: Show local preview window
        """
        print("🚀 Starting ZED camera streaming...")
        print("📹 XRoboToolkit APP on PICO VR should now receive video")
        print("Press Ctrl+C to stop.\n")

        try:
            while True:
                loop_start = time.time()

                # Get frame
                frame = self.get_frame()

                if frame is not None:
                    # Send frame
                    self.send_frame(frame)

                    # Update statistics
                    self.frame_count += 1

                    # Print FPS every 30 frames
                    if self.frame_count % 30 == 0:
                        elapsed = time.time() - self.start_time
                        fps = self.frame_count / elapsed
                        print(f"📊 Frames: {self.frame_count}, FPS: {fps:.1f}, Resolution: {frame.shape[1]}x{frame.shape[0]}", end="\r")

                    # Local preview
                    if show_preview:
                        cv2.imshow("ZED Camera Server - Preview", frame)
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break

        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping ZED camera streaming...")
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup resources."""
        print("🔄 Closing ZED camera...")
        self.zed.close()

        print("🔌 Closing ZeroMQ socket...")
        self.socket.close()
        self.context.term()

        cv2.destroyAllWindows()

        print("✅ ZED Camera Server stopped.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ZED Camera Streaming Server for PICO VR (XRoboToolkit APP)"
    )
    parser.add_argument("--port", type=int, default=5556,
                       help="ZeroMQ publisher port (default: 5556)")
    parser.add_argument("--resolution", type=str, default="VGA",
                       choices=["VGA", "HD720", "HD1080"],
                       help="Camera resolution (default: VGA=640x480)")
    parser.add_argument("--fps", type=int, default=30,
                       help="Camera frame rate (default: 30)")
    parser.add_argument("--quality", type=int, default=80,
                       help="JPEG quality 0-100 (default: 80)")
    parser.add_argument("--preview", action="store_true",
                       help="Show local preview window")

    args = parser.parse_args()

    # Convert resolution string to ZED enum
    resolution_map = {
        "VGA": sl.RESOLUTION.VGA,        # 640x480
        "HD720": sl.RESOLUTION.HD720,    # 1280x720
        "HD1080": sl.RESOLUTION.HD1080,  # 1920x1080
    }
    resolution = resolution_map[args.resolution]

    # Create and run server
    server = ZEDCameraServer(
        port=args.port,
        resolution=resolution,
        fps=args.fps,
        jpeg_quality=args.quality,
    )

    server.run(show_preview=args.preview)
