# tests/test_video_processor_comprehensive.py
import pytest
import cv2
import numpy as np
from pathlib import Path
from app.video_processor import DanceMovementAnalyzer, VideoProcessingError
import os
import tempfile

class TestVideoProcessorEdgeCases:
    """Comprehensive edge case testing for video processor"""
    
    @pytest.fixture
    def analyzer(self):
        return DanceMovementAnalyzer()
    
    # FILE FORMAT & CODEC TESTS
    def test_different_video_codecs(self, analyzer, tmp_path):
        """Test various video codecs (H.264, H.265, VP9, MJPEG)"""
        codecs = [
            ('mp4v', '.mp4'),
            ('XVID', '.avi'),
            ('MJPG', '.avi')
        ]
        
        for codec, ext in codecs:
            video_path = tmp_path / f"test_{codec}{ext}"
            self._create_test_video(video_path, codec, 30, (640, 480))
            
            output_path = tmp_path / f"output_{codec}.mp4"
            result = analyzer.process_video(str(video_path), str(output_path))
            
            assert result['success'] is True, f"Failed for codec: {codec}"
            assert output_path.exists()
    
    def test_different_resolutions(self, analyzer, tmp_path):
        """Test various resolutions from mobile to 4K"""
        resolutions = [
            (320, 240),   # QVGA
            (640, 480),   # VGA
            (1280, 720),  # HD
            (1920, 1080), # Full HD
            (3840, 2160)  # 4K (may need memory limits)
        ]
        
        for width, height in resolutions:
            video_path = tmp_path / f"test_{width}x{height}.mp4"
            self._create_test_video(video_path, 'mp4v', 30, (width, height))
            
            output_path = tmp_path / f"output_{width}x{height}.mp4"
            result = analyzer.process_video(str(video_path), str(output_path))
            
            assert result['resolution'] == f"{width}x{height}"
    
    def test_different_frame_rates(self, analyzer, tmp_path):
        """Test various FPS (15, 24, 30, 60, 120)"""
        fps_values = [15, 24, 30, 60]
        
        for fps in fps_values:
            video_path = tmp_path / f"test_{fps}fps.mp4"
            self._create_test_video(video_path, 'mp4v', fps, (640, 480))
            
            output_path = tmp_path / f"output_{fps}fps.mp4"
            result = analyzer.process_video(str(video_path), str(output_path))
            
            assert result['fps'] == fps
    
    # CORRUPTED VIDEO TESTS
    def test_corrupted_video_file(self, analyzer, tmp_path):
        """Test with corrupted/incomplete video file"""
        corrupted_path = tmp_path / "corrupted.mp4"
        with open(corrupted_path, 'wb') as f:
            f.write(b'corrupted data')
        
        with pytest.raises(VideoProcessingError):  # Changed here
            output_path = tmp_path / "output.mp4"
            analyzer.process_video(str(corrupted_path), str(output_path))
    
    def test_empty_video_file(self, analyzer, tmp_path):
        """Test with 0-byte video file"""
        empty_path = tmp_path / "empty.mp4"
        empty_path.touch()
        
        with pytest.raises(VideoProcessingError):  # Changed here
            output_path = tmp_path / "output.mp4"
            analyzer.process_video(str(empty_path), str(output_path))
    
    def test_video_with_zero_frames(self, analyzer, tmp_path):
        """Test video file with metadata but no frames"""
        video_path = tmp_path / "zero_frames.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(video_path), fourcc, 30, (640, 480))
        out.release()
        
        with pytest.raises(VideoProcessingError):  # Changed here
            output_path = tmp_path / "output.mp4"
            analyzer.process_video(str(video_path), str(output_path))
    

    # CONTENT TESTS
    def test_video_with_no_humans(self, analyzer, tmp_path):
        """Test video with no human subjects (landscape, objects only)"""
        video_path = tmp_path / "no_humans.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(video_path), fourcc, 30, (640, 480))
        
        # Write frames with geometric shapes only
        for i in range(60):
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.rectangle(frame, (100, 100), (200, 200), (255, 0, 0), -1)
            out.write(frame)
        
        out.release()
        
        output_path = tmp_path / "output.mp4"
        result = analyzer.process_video(str(video_path), str(output_path))
        
        # Should have low or zero detection rate
        detection_rate = float(result['detection_rate'].strip('%'))
        assert detection_rate < 10  # Expect minimal false positives
    
    def test_video_with_multiple_dancers(self, analyzer, tmp_path):
        """Test video with multiple people (should track main dancer)"""
        # This would require more complex test video generation
        # In real implementation, use actual test video file
        pass
    
    def test_video_with_occlusions(self, analyzer, tmp_path):
        """Test with partially occluded human subjects"""
        # Test landmark visibility scores
        pass
    
    def test_extreme_lighting_conditions(self, analyzer, tmp_path):
        """Test very dark and very bright videos"""
        video_path = tmp_path / "dark.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(video_path), fourcc, 30, (640, 480))
        
        # Very dark frames
        for i in range(60):
            frame = np.full((480, 640, 3), 10, dtype=np.uint8)  # Very dark
            out.write(frame)
        
        out.release()
        
        output_path = tmp_path / "output.mp4"
        result = analyzer.process_video(str(video_path), str(output_path))
        
        assert result['success'] is True
    
    # SIZE & DURATION TESTS
    def test_very_short_video(self, analyzer, tmp_path):
        """Test 1-frame video"""
        video_path = tmp_path / "one_frame.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(video_path), fourcc, 30, (640, 480))
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        out.write(frame)
        out.release()
        
        output_path = tmp_path / "output.mp4"
        result = analyzer.process_video(str(video_path), str(output_path))
        
        assert result['total_frames'] == 1
    
    def test_long_video(self, analyzer, tmp_path):
        """Test 5-minute video (memory handling)"""
        video_path = tmp_path / "long_video.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(video_path), fourcc, 30, (640, 480))
        
        # 5 minutes at 30 FPS = 9000 frames
        for i in range(9000):
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            out.write(frame)
        
        out.release()
        
        output_path = tmp_path / "output.mp4"
        result = analyzer.process_video(str(video_path), str(output_path))
        
        assert result['total_frames'] == 9000
        assert output_path.exists()
    
    @pytest.mark.parametrize("file_size_mb", [10, 50, 100])
    def test_large_file_sizes(self, analyzer, tmp_path, file_size_mb):
        """Test handling of large video files"""
        # Test memory efficiency with large files
        pass
    
    # RESOURCE & ERROR HANDLING TESTS
    def test_insufficient_disk_space(self, analyzer, tmp_path):
        """Test behavior when disk space is insufficient"""
        # Mock disk space check
        pass
    
    def test_concurrent_processing(self, analyzer, tmp_path):
        """Test thread safety with concurrent video processing"""
        import concurrent.futures
        
        videos = []
        for i in range(5):
            video_path = tmp_path / f"test_{i}.mp4"
            self._create_test_video(video_path, 'mp4v', 30, (640, 480))
            videos.append(video_path)
        
        def process_video(video_path):
            analyzer_instance = DanceMovementAnalyzer()
            output_path = tmp_path / f"output_{video_path.stem}.mp4"
            return analyzer_instance.process_video(str(video_path), str(output_path))
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(process_video, videos))
        
        assert all(r['success'] for r in results)
    
    def test_memory_leak_prevention(self, analyzer, tmp_path):
        """Test for memory leaks with repeated processing"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process same video 10 times
        video_path = tmp_path / "test.mp4"
        self._create_test_video(video_path, 'mp4v', 30, (640, 480))
        
        for i in range(10):
            output_path = tmp_path / f"output_{i}.mp4"
            analyzer.process_video(str(video_path), str(output_path))
        
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (< 500MB for 10 videos)
        assert memory_increase < 500, f"Possible memory leak: {memory_increase}MB increase"
    
    def test_invalid_output_path(self, analyzer, tmp_path):
        """Test with invalid/readonly output path"""
        import platform
        
        video_path = tmp_path / "test.mp4"
        self._create_test_video(video_path, 'mp4v', 30, (640, 480))
        
        if platform.system() == 'Windows':
            readonly_path = "C:\\Windows\\System32\\output.mp4"
        else:
            readonly_path = "/root/output.mp4"
        
        with pytest.raises((PermissionError, OSError, VideoProcessingError)):
            analyzer.process_video(str(video_path), readonly_path)
    
    # ACCURACY TESTS
    def test_landmark_detection_confidence_scores(self, analyzer, tmp_path):
        """Verify confidence scores are within valid range [0, 1]"""
        video_path = tmp_path / "test.mp4"
        self._create_test_video(video_path, 'mp4v', 30, (640, 480))
        
        # Access internal keypoints data
        output_path = tmp_path / "output.mp4"
        result = analyzer.process_video(str(video_path), str(output_path))
        
        # All visibility scores should be between 0 and 1
        # This would require exposing keypoints_data in return value
        pass
    
    def test_keypoint_coordinate_bounds(self, analyzer, tmp_path):
        """Test that all keypoints are within frame bounds"""
        video_path = tmp_path / "test.mp4"
        self._create_test_video(video_path, 'mp4v', 30, (640, 480))
        
        output_path = tmp_path / "output.mp4"
        result = analyzer.process_video(str(video_path), str(output_path))
        
        # All normalized coordinates should be 0-1
        pass
    
    def test_skeleton_drawing_accuracy(self, analyzer, tmp_path):
        """Verify skeleton overlay is drawn correctly"""
        video_path = tmp_path / "test.mp4"
        self._create_test_video(video_path, 'mp4v', 30, (640, 480))
        
        output_path = tmp_path / "output.mp4"
        analyzer.process_video(str(video_path), str(output_path))
        
        # Verify output video has visual differences from input
        # (skeleton lines should be present)
        input_cap = cv2.VideoCapture(str(video_path))
        output_cap = cv2.VideoCapture(str(output_path))
        
        ret1, frame1 = input_cap.read()
        ret2, frame2 = output_cap.read()
        
        # Frames should be different (skeleton overlay added)
        diff = cv2.absdiff(frame1, frame2)
        # In actual test with human, there should be differences
        
        input_cap.release()
        output_cap.release()
    
    # HELPER METHOD
    def _create_test_video(self, path, codec, fps, resolution, num_frames=60):
        """Helper to create test videos with specific properties"""
        fourcc = cv2.VideoWriter_fourcc(*codec)
        out = cv2.VideoWriter(str(path), fourcc, fps, resolution)
        
        for i in range(num_frames):
            frame = np.zeros((resolution[1], resolution[0], 3), dtype=np.uint8)
            # Add some content
            cv2.circle(frame, (resolution[0]//2, resolution[1]//2), 
                      50 + i, (255, 255, 255), -1)
            out.write(frame)
        
        out.release()
