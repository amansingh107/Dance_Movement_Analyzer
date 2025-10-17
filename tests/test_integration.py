# tests/test_integration.py - UPDATE
import pytest
from pathlib import Path
import time
import cv2
import numpy as np

class TestEndToEndIntegration:
    """Integration tests with real video files"""
    
    @pytest.fixture(scope="class")
    def real_dance_video(self, tmp_path_factory):
        """Create a test video fixture"""
        # Check if real fixture exists, otherwise create synthetic one
        fixture_path = Path("tests/fixtures/sample_dance.mp4")
        
        if fixture_path.exists():
            return fixture_path
        
        # Create synthetic test video
        tmp_dir = tmp_path_factory.mktemp("fixtures")
        video_path = tmp_dir / "sample_dance.mp4"
        
        # Create a simple test video with moving circle (simulating movement)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(video_path), fourcc, 30, (640, 480))
        
        # Create 3 seconds of video (90 frames at 30 FPS)
        for i in range(90):
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            # Moving circle to simulate dance movement
            x = int(320 + 100 * np.sin(i * 0.1))
            y = int(240 + 50 * np.cos(i * 0.1))
            cv2.circle(frame, (x, y), 60, (255, 255, 255), -1)
            out.write(frame)
        
        out.release()
        return video_path
    
    @pytest.mark.integration
    def test_complete_workflow(self, real_dance_video):
        """Test entire upload -> process -> download workflow"""
        try:
            import requests
        except ImportError:
            pytest.skip("requests not installed")
        
        base_url = "http://localhost:8000"
        
        # Check if server is running
        try:
            health_response = requests.get(f"{base_url}/health", timeout=2)
            if health_response.status_code != 200:
                pytest.skip("Server not running or unhealthy")
        except requests.exceptions.ConnectionError:
            pytest.skip("Server not running on localhost:8000")
        
        # 1. Upload
        with open(real_dance_video, 'rb') as f:
            files = {'video': ('dance.mp4', f, 'video/mp4')}
            response = requests.post(f"{base_url}/api/analyze", files=files, timeout=60)
        
        assert response.status_code == 200
        result = response.json()
        job_id = result['job_id']
        
        # 2. Wait for processing (if async)
        time.sleep(2)
        
        # 3. Download
        response = requests.get(f"{base_url}/api/download/{job_id}", timeout=30)
        assert response.status_code == 200
        assert 'video/mp4' in response.headers.get('content-type', '')
        
        # 4. Verify output video
        output_path = Path(f"test_output_{job_id}.mp4")
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        assert output_path.stat().st_size > 0
        
        # Verify it's a valid video
        cap = cv2.VideoCapture(str(output_path))
        assert cap.isOpened()
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1
        cap.release()
        assert frame_count > 0
        
        # Cleanup local test file
        output_path.unlink()
        
        # 5. Cleanup server files
        response = requests.delete(f"{base_url}/api/cleanup/{job_id}")
        assert response.status_code == 200
