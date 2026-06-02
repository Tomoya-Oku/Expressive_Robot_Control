import cv2
import numpy as np
from ultralytics import YOLO
from deepface import DeepFace
from collections import deque
import os
import mediapipe as mp
import face_alignment

class VideoAnalyzer:
    """
    Analyzes video to track body movements using YOLO pose detection.
    """
    
    def __init__(self, model_name='yolov8n-pose.pt', output_dir='output'):
        """
        Initialize the video analyzer with YOLO pose model.
        
        Args:
            model_name: YOLOv8 model to use (yolov8n-pose for lightweight)
            output_dir: Directory to save output videos
        """
        self.pose_model = YOLO(model_name)
        
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Keypoint history for motion tracking
        self.keypoint_history = deque(maxlen=30)
        
    def analyze_video(self, video_path, output_path=None, show_live=True):
        """
        Analyze video for body movements using pose detection.
        
        Args:
            video_path: Path to input video file
            output_path: Path to save output video (optional)
            show_live: Whether to display live analysis
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"Error: Cannot open video {video_path}")
            return
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"Video: {width}x{height} @ {fps} FPS, Total frames: {total_frames}")
        
        # Setup video writer if output path provided
        if output_path is None:
            output_path = os.path.join(self.output_dir, 'bodyMovements.mp4')
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detect and visualize body pose
            frame = self._detect_body_pose(frame, frame_rgb)
            
            # Add frame counter and info
            cv2.putText(frame, f"Frame: {frame_count}/{total_frames}",  (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Write to output video
            out.write(frame)
            
            # Display live
            if show_live:
                cv2.imshow('Body Movement Analysis - YOLO Pose Detection', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            if frame_count % 30 == 0:
                print(f"Processed {frame_count}/{total_frames} frames")
        
        cap.release()
        out.release()
        cv2.destroyAllWindows()
        
        print(f"\nAnalysis complete! Output saved to: {output_path}")
        return output_path
    
    def _detect_body_pose(self, frame, frame_rgb):
        """
        Detect and visualize body pose (skeleton) using YOLO.
        Returns frame with pose keypoints and skeleton drawn.
        """
        # Run YOLO pose detection
        results = self.pose_model(frame_rgb, verbose=False)
        
        if results[0].keypoints is not None:
            keypoints = results[0].keypoints
            
            for person_keypoints in keypoints:
                # Extract keypoint data (x, y, confidence) - handle different tensor formats
                try:
                    kpts = person_keypoints.xy[0]
                    conf = person_keypoints.conf[0]
                except:
                    kpts = person_keypoints.xy
                    conf = person_keypoints.conf
                
                # Convert to numpy if it's a tensor
                if hasattr(kpts, 'numpy'):
                    kpts = kpts.cpu().numpy()
                elif hasattr(kpts, 'cpu'):
                    kpts = kpts.cpu().numpy()
                
                if hasattr(conf, 'numpy'):
                    conf = conf.cpu().numpy()
                elif hasattr(conf, 'cpu'):
                    conf = conf.cpu().numpy()
                
                # Ensure numpy array
                kpts = np.asarray(kpts)
                conf = np.asarray(conf)
                
                # Store keypoint history for motion analysis
                if kpts.shape[0] > 0:
                    self.keypoint_history.append(kpts.copy())
                    
                    # Draw skeleton
                    frame = self._draw_skeleton(frame, kpts, conf, threshold=0.3)
        
        return frame
    
    def _draw_skeleton(self, frame, keypoints, confidence, threshold=0.5):
        """
        Draw skeleton connections between keypoints.
        YOLO pose model keypoints (17 points for COCO format):
        0: nose, 1-2: eyes, 3-4: ears, 5-6: shoulders, 7-8: elbows, 
        9-10: wrists, 11-12: hips, 13-14: knees, 15-16: ankles
        """
        # COCO pose skeleton connections
        skeleton = [
            (0, 1), (0, 2), (1, 3), (2, 4),  # head
            (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),  # arms
            (5, 11), (6, 12), (11, 12),  # torso
            (11, 13), (13, 15), (12, 14), (14, 16)  # legs
        ]
        
        # Draw keypoints
        for i, (x, y) in enumerate(keypoints):
            if confidence[i] > threshold:
                cv2.circle(frame, (int(x), int(y)), 5, (0, 255, 0), -1)
                cv2.putText(frame, str(i), (int(x)+5, int(y)-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
        
        # Draw skeleton connections
        for start, end in skeleton:
            if confidence[start] > threshold and confidence[end] > threshold:
                x1, y1 = int(keypoints[start][0]), int(keypoints[start][1])
                x2, y2 = int(keypoints[end][0]), int(keypoints[end][1])
                cv2.line(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
        
        # Display motion intensity if history available
        if len(self.keypoint_history) > 1:
            motion = self._calculate_motion_intensity()
            cv2.putText(frame, f"Motion: {motion:.2f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        return frame
    
    def _calculate_motion_intensity(self):
        """Calculate motion intensity based on keypoint movement."""
        if len(self.keypoint_history) < 2:
            return 0.0
        
        prev_kpts = self.keypoint_history[-2]
        curr_kpts = self.keypoint_history[-1]
        
        # Calculate average displacement
        displacement = np.linalg.norm(curr_kpts - prev_kpts, axis=1)
        return float(np.mean(displacement))


class FacialExpressionAnalyzer:
    """
    Simple facial expression analyzer using DeepFace.
    """

    def __init__(self, output_dir='output'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def analyze_video(self, video_path, output_path=None, show_live=True):

        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            print(f"Error: Cannot open video {video_path}")
            return

        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if output_path is None:
            output_path = os.path.join(
                self.output_dir,
                'FacialExpressions_analyzed.mp4'
            )

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        frame_count = 0
        last_emotion = "neutral"
        SKIP_FRAMES = 5

        while True:

            ret, frame = cap.read()

            if not ret:
                break

            frame_count += 1

            # Only run emotion analysis every N frames
            if frame_count % SKIP_FRAMES == 0:

                try:
                    result = DeepFace.analyze(
                        frame,
                        actions=['emotion'],
                        enforce_detection=False,
                        detector_backend='opencv',
                        silent=True
                    )

                    last_emotion = result[0]['dominant_emotion']

                except Exception as e:
                    print("Emotion detection error:", e)

            # Display latest emotion
            cv2.putText(
                frame,
                f"Emotion: {last_emotion}",
                (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

            # Frame counter
            cv2.putText(
                frame,
                f"Frame: {frame_count}/{total_frames}",
                (20, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            out.write(frame)

            if show_live:
                cv2.imshow("Facial Expression Analysis", frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        cap.release()
        out.release()
        cv2.destroyAllWindows()

        print(f"Saved to: {output_path}")

        return output_path


def main():
    """Main function to run video analysis."""
    
    print("=== Video Analysis: Body Movements & Facial Expressions ===\n")
    
    # Define video files
    body_video = 'bodyMovements.mp4'
    facial_video = 'facialExpressions2.mp4'
    
    # Process body movements video using YOLO pose detection
    doBodyAnalysis = False
    if doBodyAnalysis:
        if os.path.exists(body_video):
            print(f"[1/2] Processing body movements video: {body_video}")
            analyzer = VideoAnalyzer()
            output_body = 'output/bodyMovements_analyzed.mp4'
            analyzer.analyze_video(body_video, output_path=output_body, show_live=True)
        else:
            print(f"Error: {body_video} not found in current directory")
            return
    
    # Process facial expressions video using facial expression analyzer
    doFacialAnalysis = True
    if doFacialAnalysis:
        if os.path.exists(facial_video):
            print(f"\n[2/2] Processing facial expressions video: {facial_video}")
            facial_analyzer = FacialExpressionAnalyzer()
            output_facial = 'output/facialExpressions_analyzed.mp4'
            facial_analyzer.analyze_video(facial_video, output_path=output_facial, show_live=True)
        else:
            print(f"Note: {facial_video} not available yet")


if __name__ == "__main__":
    main()
