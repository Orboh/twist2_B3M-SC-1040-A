#!/usr/bin/env python3
  """
  B3M Head Controller for TWIST2
  近藤科学 B3M-SB-1040-A サーボモーター版

  Based on: XRoboToolkit-Teleop-Sample-Python/dynamixel_head_controller.py
  Modified for: Kondo Kagaku B3M servos
  """

  import threading
  import time
  import numpy as np
  import meshcat.transformations as tf

  # XRoboToolkit client for PICO VR headset pose
  try:
      from xrobotoolkit_teleop.common.xr_client import XrClient
  except ImportError:
      print("Warning: xrobotoolkit_teleop not found. Install from:")
      print("https://github.com/XR-Robotics/XRoboToolkit-Teleop-Sample-Python")
      XrClient = None

  # B3M Controller (実装方法は後述)
  from b3m_controller import B3MController  # 要作成


  class B3MHeadController:
      """PICO VR headset tracking with B3M servo motors for neck control."""

      def __init__(
          self,
          xr_client: XrClient,
          port: str = "/dev/ttyUSB0",
          baudrate: int = 1500000,
      ):
          """
          Initialize B3M Head Controller
          
          Args:
              xr_client: XRoboToolkit client for headset pose
              port: Serial port for B3M communication
              baudrate: Communication speed (1.5Mbps recommended)
          """
          # Head control specific constants for B3M
          self.YAW_MOTOR_ID = 0
          self.PITCH_MOTOR_ID = 1

          # B3M center positions (in degrees)
          self.YAW_CENTER = 90.0    # 中心位置 (10~150°の中央)
          self.PITCH_CENTER = 60.0  # 中心位置 (8~125°の中央)

          # B3M range limits (in degrees)
          self.YAW_MIN = 10.0
          self.YAW_MAX = 150.0
          self.PITCH_MIN = 8.0
          self.PITCH_MAX = 125.0

          # Store dependencies
          self.xr_client = xr_client
          self.tf = tf

          # Initialize the B3M controller
          self.controller = B3MController(port, baudrate)

          # Initialize motors for head control
          self._initialize_head_motors()

      def _initialize_head_motors(self):
          """Initialize yaw and pitch motors for head control."""
          print("Initializing B3M head control motors...")

          # B3M motors are always ready (no explicit torque enable needed)
          # Set initial position to center
          self.controller.set_position(self.YAW_MOTOR_ID, self.YAW_CENTER)
          self.controller.set_position(self.PITCH_MOTOR_ID, self.PITCH_CENTER)

          print(f"B3M motors initialized: YAW={self.YAW_MOTOR_ID}, PITCH={self.PITCH_MOTOR_ID}")

      def mapYawToB3MPosition(self, yaw: float) -> float:
          """
          Map yaw angle (degrees) to B3M position.
          
          Args:
              yaw: Yaw angle from headset (-180 to 180 degrees)
          
          Returns:
              B3M position in degrees (10~150)
          """
          # Map headset yaw to B3M range
          position = self.YAW_CENTER + yaw

          # Clamp to valid range
          position = np.clip(position, self.YAW_MIN, self.YAW_MAX)

          return position

      def mapPitchToB3MPosition(self, pitch: float) -> float:
          """
          Map pitch angle (degrees) to B3M position.
          
          Args:
              pitch: Pitch angle from headset (-90 to 90 degrees)
          
          Returns:
              B3M position in degrees (8~125)
          """
          # Clamp pitch to valid range
          pitch = np.clip(pitch, -50.0, 50.0)

          # Map headset pitch to B3M range
          # 負の符号は、頭を上げる→カメラも上げるため
          position = self.PITCH_CENTER - pitch

          # Clamp to valid range
          position = np.clip(position, self.PITCH_MIN, self.PITCH_MAX)

          return position

      def setHeadPosition(self, yaw: float, pitch: float) -> bool:
          """
          Set head position using yaw and pitch angles in degrees.
          
          Args:
              yaw: Yaw angle in degrees
              pitch: Pitch angle in degrees
          
          Returns:
              True if successful, False otherwise
          """
          yaw_position = self.mapYawToB3MPosition(yaw)
          pitch_position = self.mapPitchToB3MPosition(pitch)

          try:
              self.controller.set_position(self.YAW_MOTOR_ID, yaw_position)
              self.controller.set_position(self.PITCH_MOTOR_ID, pitch_position)
              return True
          except Exception as e:
              print(f"Error setting B3M position: {e}")
              return False

      def get_target_orientation(self) -> tuple:
          """
          Fetches the current head orientation from PICO VR headset.
          Returns a tuple (yaw, pitch) in degrees.
          """
          try:
              head_pose = self.xr_client.get_pose_by_name("headset")
              # head_pose format: [x, y, z, qx, qy, qz, qw]
              quat = np.array([head_pose[6], head_pose[3], head_pose[4], head_pose[5]])  # [w, x, y, z]

              # Convert quaternion to rotation matrix
              rot_matrix = self.tf.quaternion_matrix(quat)[:3, :3]

              # Extract Euler angles
              euler = self.tf.euler_from_matrix(rot_matrix, "rzxy")
              currentYaw = euler[2] * 180.0 / np.pi
              currentPitch = euler[1] * 180.0 / np.pi

              return currentYaw, currentPitch

          except Exception as e:
              print(f"Error fetching head orientation: {e}")
              return 0.0, 0.0  # Default values in case of error

      def run(self, stop_event: threading.Event = None):
          """
          Run the head controller main loop.
          
          Args:
              stop_event: Threading event to stop the controller
          """
          if stop_event is None:
              stop_event = threading.Event()

          control_thread = threading.Thread(
              target=self.run_thread,
              args=(stop_event,),
              daemon=True
          )
          control_thread.start()

          try:
              while not stop_event.is_set():
                  time.sleep(0.01)
          except KeyboardInterrupt:
              print("Stopping B3M head control...")
              stop_event.set()

          control_thread.join()

      def run_thread(self, stop_event: threading.Event):
          """
          Main control loop for head tracking.
          
          Args:
              stop_event: Threading event. The loop stops when set.
          """
          print("B3M head control loop starting...")
          last_yaw = 0.0
          last_pitch = 0.0

          try:
              while not stop_event.is_set():
                  # Get current headset orientation
                  current_yaw_raw, current_pitch_raw = self.get_target_orientation()

                  # Normalize yaw to -90~90 range
                  current_yaw = current_yaw_raw
                  if current_yaw > 90.0 and current_yaw < 180.0:
                      current_yaw -= 180.0
                  if current_yaw < -90.0:
                      current_yaw = 180.0 + current_yaw

                  # Normalize pitch
                  current_pitch = current_pitch_raw
                  if current_pitch < -90.0:
                      current_pitch = -current_pitch - 180.0
                  if current_pitch > 90.0:
                      current_pitch = 180.0 - current_pitch

                  # Deadband: Only update if change is significant (>0.01°)
                  if abs(current_yaw - last_yaw) > 0.01 or abs(current_pitch - last_pitch) > 0.01:
                      success = self.setHeadPosition(current_yaw, current_pitch)
                      if success:
                          last_yaw = current_yaw
                          last_pitch = current_pitch
                          # Debug output
                          # print(f"Head: Yaw={current_yaw:.1f}°, Pitch={current_pitch:.1f}°", end="\r")

                  # Control frequency: 100Hz
                  time.sleep(0.01)

          except Exception as e:
              print(f"Exception in B3M head control loop: {e}")
          finally:
              self._cleanup_head_motors()

      def _cleanup_head_motors(self):
          """Cleanup head control motors - return to center position."""
          print("B3M head control loop stopping. Returning to center position...")

          try:
              self.controller.set_position(self.YAW_MOTOR_ID, self.YAW_CENTER)
              self.controller.set_position(self.PITCH_MOTOR_ID, self.PITCH_CENTER)
              print("B3M motors returned to center.")
          except Exception as e:
              print(f"Error during cleanup: {e}")

      def close(self):
          """Close the head controller and cleanup resources."""
          self._cleanup_head_motors()
          self.controller.close()

      def __del__(self):
          """Ensures resources are released when the object is deleted."""
          try:
              self.close()
          except:
              pass


  # ===== Main entry point for standalone testing =====
  if __name__ == "__main__":
      import argparse

      parser = argparse.ArgumentParser(description="B3M Head Controller for PICO VR")
      parser.add_argument("--port", type=str, default="/dev/ttyUSB0",
                         help="Serial port for B3M")
      parser.add_argument("--baudrate", type=int, default=1500000,
                         help="Baud rate (1.5Mbps)")
      parser.add_argument("--xr_host", type=str, default="localhost",
                         help="XRoboToolkit server host")
      parser.add_argument("--xr_port", type=int, default=8000,
                         help="XRoboToolkit server port")

      args = parser.parse_args()

      # Initialize XRoboToolkit client
      if XrClient:
          xr_client = XrClient(host=args.xr_host, port=args.xr_port)
      else:
          print("XrClient not available. Exiting.")
          exit(1)

      # Initialize B3M head controller
      controller = B3MHeadController(
          xr_client=xr_client,
          port=args.port,
          baudrate=args.baudrate
      )

      # Run the controller
      print("Starting B3M head tracking...")
      print("Press Ctrl+C to stop.")
      controller.run()
