# tests/load_test.py
from locust import HttpUser, task, between
import random

class DanceAnalyzerUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def health_check(self):
        self.client.get("/health")
    
    @task(1)
    def upload_video(self):
        files = {
            'video': ('test.mp4', b'fake video data', 'video/mp4')
        }
        with self.client.post("/api/analyze", files=files, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 500:
                response.failure("Processing failed")
