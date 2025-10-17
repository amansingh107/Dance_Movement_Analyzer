# app/video_processor.py
import cv2
import mediapipe as mp
import numpy as np
from typing import Tuple, Optional, Dict, Any
import logging
from pathlib import Path
from contextlib import contextmanager
import time

class VideoProcessingError(Exception):
    """Custom exception for video processing errors"""
    pass

class DanceMovementAnalyzer:
    """Robust dance movement analyzer with comprehensive error handling"""
    
    # Supported video codecs
    SUPPORTED_CODECS = ['mp4v', 'avc1', 'H264', 'XVID', 'MJPG', 'DIVX']
    
    # Maximum video duration (seconds) to prevent resource exhaustion
    MAX_VIDEO_DURATION = 600  # 10 minutes
    MAX_FILE_SIZE_MB = 500
    
    def __init__(self, 
                 min_detection_confidence: float = 0.5,
                 min_tracking_confidence: float = 0.5,
                 model_complexity: int = 1):
        """
        Initialize MediaPipe Pose with robust configuration
        
        Args:
            min_detection_confidence: Minimum confidence for pose detection [0.0, 1.0]
            min_tracking_confidence: Minimum confidence for pose tracking [0.0, 1.0]
            model_complexity: Model complexity (0=Lite, 1=Full, 2=Heavy)
        """
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.model_complexity = model_complexity
        
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Don't initialize pose here - use context manager instead
        self.pose = None
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    @contextmanager
    def _get_pose_detector(self):
        """
        Context manager for MediaPipe Pose to ensure proper initialization and cleanup
        
        Yields:
            MediaPipe Pose detector instance
        """
        pose = None
        try:
            self.logger.info("Initializing MediaPipe Pose detector")
            pose = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=self.model_complexity,
                smooth_landmarks=True,
                enable_segmentation=False,
                smooth_segmentation=False,
                min_detection_confidence=self.min_detection_confidence,
                min_tracking_confidence=self.min_tracking_confidence
            )
            
            # Verify pose detector is properly initialized
            if pose is None:
                raise VideoProcessingError("Failed to initialize MediaPipe Pose detector")
            
            yield pose
            
        except Exception as e:
            self.logger.error(f"Error initializing pose detector: {str(e)}")
            raise VideoProcessingError(f"Pose detector initialization failed: {str(e)}")
        
        finally:
            if pose is not None:
                try:
                    pose.close()
                    self.logger.info("Pose detector closed successfully")
                except Exception as e:
                    self.logger.warning(f"Error closing pose detector: {str(e)}")
    
    def _validate_video_file(self, video_path: str) -> Dict[str, Any]:
        """
        Validate video file before processing
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with video metadata
            
        Raises:
            VideoProcessingError: If video is invalid
        """
        path = Path(video_path)
        
        # Check file exists
        if not path.exists():
            raise VideoProcessingError(f"Video file not found: {video_path}")
        
        # Check file size
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.MAX_FILE_SIZE_MB:
            raise VideoProcessingError(
                f"Video file too large: {file_size_mb:.2f}MB (max: {self.MAX_FILE_SIZE_MB}MB)"
            )
        
        # Check if file is empty
        if path.stat().st_size == 0:
            raise VideoProcessingError("Video file is empty (0 bytes)")
        
        # Try to open with OpenCV
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            cap.release()
            raise VideoProcessingError(
                f"Cannot open video file. File may be corrupted or in unsupported format: {video_path}"
            )
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        cap.release()
        
        # Validate properties
        if fps <= 0 or fps > 240:
            raise VideoProcessingError(f"Invalid FPS: {fps}")
        
        if frame_count <= 0:
            raise VideoProcessingError("Video has no frames")
        
        if width <= 0 or height <= 0:
            raise VideoProcessingError(f"Invalid resolution: {width}x{height}")
        
        duration = frame_count / fps if fps > 0 else 0
        
        if duration > self.MAX_VIDEO_DURATION:
            raise VideoProcessingError(
                f"Video too long: {duration:.2f}s (max: {self.MAX_VIDEO_DURATION}s)"
            )
        
        metadata = {
            'fps': fps,
            'frame_count': frame_count,
            'width': width,
            'height': height,
            'duration': duration,
            'file_size_mb': file_size_mb
        }
        
        self.logger.info(f"Video validated: {metadata}")
        return metadata
    
    def _get_output_codec(self, output_path: str) -> Tuple[int, str]:
        """
        Determine best codec for output video
        
        Args:
            output_path: Output file path
            
        Returns:
            Tuple of (fourcc, extension)
        """
        extension = Path(output_path).suffix.lower()
        
        # Try different codecs in order of preference
        codec_preferences = [
            ('mp4v', '.mp4'),  # Most compatible
            ('avc1', '.mp4'),  # H.264
            ('XVID', '.avi'),
            ('MJPG', '.avi'),
        ]
        
        for codec, ext in codec_preferences:
            try:
                fourcc = cv2.VideoWriter_fourcc(*codec)
                if fourcc is not None:
                    # Use original extension if it matches, otherwise use codec's default
                    final_ext = extension if extension == ext else ext
                    return fourcc, final_ext
            except Exception as e:
                self.logger.warning(f"Codec {codec} not available: {str(e)}")
                continue
        
        # Fallback to mp4v
        self.logger.warning("Using fallback codec: mp4v")
        return cv2.VideoWriter_fourcc(*'mp4v'), '.mp4'
    
    def process_video(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """
        Process dance video with robust error handling
        
        Args:
            input_path: Path to input video file
            output_path: Path to save output video
            
        Returns:
            Dictionary with processing results and metadata
            
        Raises:
            VideoProcessingError: If processing fails
        """
        start_time = time.time()
        
        try:
            # Validate input video
            metadata = self._validate_video_file(input_path)
            
            # Open video capture
            cap = cv2.VideoCapture(input_path)
            
            if not cap.isOpened():
                raise VideoProcessingError("Failed to open video after validation")
            
            # Get video properties
            fps = metadata['fps']
            width = metadata['width']
            height = metadata['height']
            total_frames = metadata['frame_count']
            
            # Determine output codec and path
            fourcc, codec_ext = self._get_output_codec(output_path)
            
            # Ensure output path has correct extension
            output_path_obj = Path(output_path)
            if output_path_obj.suffix != codec_ext:
                output_path = str(output_path_obj.with_suffix(codec_ext))
                self.logger.info(f"Adjusted output path to: {output_path}")
            
            # Create output directory if needed
            output_path_obj = Path(output_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            # Initialize video writer
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            if not out.isOpened():
                cap.release()
                raise VideoProcessingError(
                    f"Failed to initialize video writer. Codec may not be supported."
                )
            
            # Process video with MediaPipe Pose
            frame_count = 0
            detected_frames = 0
            failed_frames = 0
            keypoints_data = []
            
            self.logger.info(f"Processing {total_frames} frames at {fps} FPS...")
            
            # Use context manager for pose detector
            with self._get_pose_detector() as pose:
                
                while cap.isOpened():
                    success, frame = cap.read()
                    
                    if not success:
                        self.logger.debug(f"End of video at frame {frame_count}")
                        break
                    
                    try:
                        # Validate frame
                        if frame is None or frame.size == 0:
                            self.logger.warning(f"Invalid frame at {frame_count}")
                            failed_frames += 1
                            continue
                        
                        # Ensure frame has correct dimensions
                        if frame.shape[1] != width or frame.shape[0] != height:
                            frame = cv2.resize(frame, (width, height))
                        
                        # Convert BGR to RGB
                        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        image_rgb.flags.writeable = False
                        
                        # Process with MediaPipe - wrap in try-catch for frame-level errors
                        try:
                            results = pose.process(image_rgb)
                        except Exception as e:
                            self.logger.warning(f"MediaPipe processing failed at frame {frame_count}: {str(e)}")
                            failed_frames += 1
                            # Write original frame without skeleton
                            out.write(frame)
                            frame_count += 1
                            continue
                        
                        # Prepare frame for drawing
                        image_rgb.flags.writeable = True
                        frame = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
                        
                        # Check if pose landmarks were detected
                        if results.pose_landmarks is not None:
                            detected_frames += 1
                            
                            try:
                                # Draw pose landmarks
                                self.mp_drawing.draw_landmarks(
                                    frame,
                                    results.pose_landmarks,
                                    self.mp_pose.POSE_CONNECTIONS,
                                    landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
                                )
                                
                                # Extract keypoint data
                                landmarks = []
                                for landmark in results.pose_landmarks.landmark:
                                    landmarks.append({
                                        'x': float(landmark.x),
                                        'y': float(landmark.y),
                                        'z': float(landmark.z),
                                        'visibility': float(landmark.visibility)
                                    })
                                
                                keypoints_data.append({
                                    'frame': frame_count,
                                    'landmarks': landmarks,
                                    'timestamp': frame_count / fps
                                })
                                
                            except Exception as e:
                                self.logger.warning(f"Error drawing landmarks at frame {frame_count}: {str(e)}")
                        
                        # Add frame info overlay
                        detection_status = "DETECTED" if results.pose_landmarks else "NO POSE"
                        color = (0, 255, 0) if results.pose_landmarks else (0, 0, 255)
                        
                        cv2.putText(
                            frame, 
                            f'Frame: {frame_count}/{total_frames} | {detection_status}', 
                            (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 
                            0.6, 
                            color, 
                            2
                        )
                        
                        # Write processed frame
                        out.write(frame)
                        frame_count += 1
                        
                        # Log progress every 100 frames
                        if frame_count % 100 == 0:
                            self.logger.info(f"Processed {frame_count}/{total_frames} frames")
                    
                    except Exception as e:
                        self.logger.error(f"Error processing frame {frame_count}: {str(e)}")
                        failed_frames += 1
                        # Try to write original frame
                        try:
                            out.write(frame)
                        except:
                            pass
                        frame_count += 1
                        continue
            
            # Cleanup
            cap.release()
            out.release()
            
            processing_time = time.time() - start_time
            
            # Calculate statistics
            detection_rate = (detected_frames / total_frames * 100) if total_frames > 0 else 0
            failed_rate = (failed_frames / total_frames * 100) if total_frames > 0 else 0
            
            # Verify output file was created and has content
            if not Path(output_path).exists():
                raise VideoProcessingError("Output file was not created")
            
            output_size = Path(output_path).stat().st_size
            if output_size == 0:
                raise VideoProcessingError("Output file is empty")
            
            result = {
                'success': True,
                'input_file': input_path,
                'output_file': output_path,
                'output_size_mb': output_size / (1024 * 1024),
                'total_frames': total_frames,
                'processed_frames': frame_count,
                'detected_frames': detected_frames,
                'failed_frames': failed_frames,
                'detection_rate': f"{detection_rate:.2f}%",
                'failed_rate': f"{failed_rate:.2f}%",
                'fps': fps,
                'resolution': f"{width}x{height}",
                'duration': f"{metadata['duration']:.2f}s",
                'processing_time': f"{processing_time:.2f}s",
                'keypoints_count': len(keypoints_data),
                'average_visibility': self._calculate_average_visibility(keypoints_data)
            }
            
            self.logger.info(f"Processing complete: {detected_frames}/{total_frames} frames detected")
            return result
        
        except VideoProcessingError as e:
            self.logger.error(f"Video processing error: {str(e)}")
            raise
        
        except Exception as e:
            self.logger.error(f"Unexpected error during video processing: {str(e)}", exc_info=True)
            raise VideoProcessingError(f"Processing failed: {str(e)}")
        
        finally:
            # Ensure resources are released
            try:
                if 'cap' in locals() and cap is not None:
                    cap.release()
                if 'out' in locals() and out is not None:
                    out.release()
            except:
                pass
    
    def _calculate_average_visibility(self, keypoints_data: list) -> Optional[float]:
        """Calculate average visibility score across all detected frames"""
        if not keypoints_data:
            return None
        
        try:
            total_visibility = 0
            count = 0
            
            for frame_data in keypoints_data:
                for landmark in frame_data['landmarks']:
                    total_visibility += landmark['visibility']
                    count += 1
            
            return round(total_visibility / count, 3) if count > 0 else None
        
        except Exception as e:
            self.logger.warning(f"Error calculating visibility: {str(e)}")
            return None
    
    def process_video_with_retry(self, input_path: str, output_path: str, 
                                 max_retries: int = 3) -> Dict[str, Any]:
        """
        Process video with automatic retry on failure
        
        Args:
            input_path: Path to input video
            output_path: Path to output video
            max_retries: Maximum number of retry attempts
            
        Returns:
            Processing result dictionary
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Processing attempt {attempt + 1}/{max_retries}")
                return self.process_video(input_path, output_path)
            
            except Exception as e:
                last_error = e
                self.logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < max_retries - 1:
                    # Wait before retry with exponential backoff
                    wait_time = 2 ** attempt
                    self.logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
        
        raise VideoProcessingError(f"All {max_retries} attempts failed. Last error: {str(last_error)}")
