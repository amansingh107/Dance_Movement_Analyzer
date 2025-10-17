# Dance Movement Analysis API

> AI-powered body movement analysis system for dance videos using MediaPipe and Computer Vision

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Server Endpoint: https://dance-movement-analyzer.onrender.com 
API Docs: https://dance-movement-analyzer.onrender.com/docs  
Repository: https://github.com/amansingh107/Dance_Movement_Analyzer.git

---

## Table of Contents

- Overview
- Features
- Architecture
- Technology Stack
- Getting Started
- API Usage
- Cloud Deployment
- Thought Process & Design Decisions
- Alignment with Callus's Vision
- Testing
- Performance
- Future Enhancements
- Troubleshooting
- Project Structure
- License
- Contact
- Add-ons (Optional)

---

## Overview

The Dance Movement Analysis API is a cloud-based AI/ML system that processes short dance videos to detect and analyze body movements. Using Google's MediaPipe Pose, it identifies 33 body landmarks and overlays a skeleton visualization on the original video. The service returns the processed video along with useful analytics like detection rate and frame statistics.

Key capabilities:
- Accepts MP4/AVI/MOV uploads (configurable size limits)
- Performs pose detection and overlays a skeleton in real time per frame
- Produces an annotated output video and analysis metadata
- Exposes a clean REST API for uploads, downloads, and manual cleanup

---

## Features

- Pose detection with 33 landmarks per frame
- Skeleton overlay rendering on the original video
- Multi-format video support: MP4, AVI, MOV
- Robust validations and error handling (file type, size, corruption, zero frames)
- Dockerized service suitable for cloud deployment
- FastAPI with interactive OpenAPI docs at /docs
- Manual cleanup endpoint to remove per-job files on demand

---

## Architecture

High-level flow:
1. Client uploads a dance video via the API.
2. The server validates format, duration, and size.
3. Frames are processed with MediaPipe Pose to detect landmarks.
4. OpenCV draws the skeleton overlay and writes output frames.
5. The API returns analysis metadata and a job_id to download results.
6. Clients can manually call the cleanup endpoint to delete files.

Layers:
- API Layer (FastAPI): routing, validation, responses
- Processing Layer (OpenCV + NumPy): video IO, drawing overlays
- ML Layer (MediaPipe Pose): pose detection and tracking
- Storage Layer: local filesystem (uploads/ and outputs/) managed by the service owner

Note on storage:
- This implementation stores input and output files in local directories on the server until manual cleanup is performed or the service is redeployed/restarted.
- Manual cleanup is provided via a DELETE endpoint.

---

## Technology Stack

- FastAPI, Uvicorn
- MediaPipe, OpenCV, NumPy
- Python 3.10+
- Docker, Docker Compose
- pytest, pytest-cov (testing)

---

## Getting Started

Prerequisites:
- Python 3.10+
- Docker and Docker Compose (optional but recommended)
- Git

Clone:
git clone https://github.com/amansingh107/Dance_Movement_Analyzer.git
cd dance-analyzer

Create a virtual environment and install dependencies:
Windows
python -m venv venv
venv\Scripts\activate

macOS/Linux
python3 -m venv venv
source venv/bin/activate

Install
pip install --upgrade pip
pip install -r requirements.txt

Run locally:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Open:
- http://localhost:8000
- http://localhost:8000/docs
- http://localhost:8000/health

Docker (recommended):
docker build -t dance-analyzer:latest .
docker run -d --name dance-api -p 8000:8000 dance-analyzer:latest

Docker Compose:
docker-compose up -d --build

---

## API Usage

Base URLs:
- Local: http://localhost:8000
- Production: https://dance-movement-analyzer.onrender.com

Endpoints:

1) Health
- GET /health
- Returns service status and basic environment checks.

Example:
curl http://localhost:8000/health

2) Analyze video
- POST /api/analyze
- multipart/form-data with key: video (file)
- Accepts .mp4, .avi, .mov (size and duration can be configured)

Example:
curl -X POST "http://localhost:8000/api/analyze"
-F "video=@path/to/dance.mp4"

Sample success response:
{
"success": true,
"input_file": "uploads/<job_id>_input.mp4",
"output_file": "outputs/<job_id>_output.mp4",
"output_size_mb": 3.24,
"total_frames": 180,
"processed_frames": 180,
"detected_frames": 165,
"failed_frames": 0,
"detection_rate": "91.67%",
"failed_rate": "0.00%",
"fps": 30,
"resolution": "1920x1080",
"duration": "6.00s",
"processing_time": "8.45s",
"keypoints_count": 165,
"average_visibility": 0.847,
"job_id": "<job_id>",
"original_filename": "dance.mp4",
"download_url": "/api/download/<job_id>",
"cleanup_url": "/api/cleanup/<job_id>"
}

3) Download processed video
- GET /api/download/{job_id}

Example:
curl -o result.mp4 http://localhost:8000/api/download/<job_id>

4) Cleanup files (manual)
- DELETE /api/cleanup/{job_id}
- Deletes both input and output files for the job.

Example:
curl -X DELETE http://localhost:8000/api/cleanup/<job_id>

---

## Cloud Deployment

Deployment platform used for the assessment: Render (free web service instance).  
Reason: No access to AWS or GCP billing in this environment, and the assignment requires a publicly accessible endpoint. The Dockerized server was deployed directly from the repository using Render's Docker support.

Render deployment steps (blueprint):
1. Ensure Dockerfile is present and runs FastAPI on 0.0.0.0 using the PORT environment variable.
2. Add a render.yaml with a single web service using env: docker and a healthCheckPath: /health.
3. Push repository to GitHub.
4. In Render dashboard, create a new Blueprint (or Web Service), connect the GitHub repo, and deploy.
5. Obtain the public URL and test /health and /docs.

Notes for free tier:
- No persistent disks on free tier; files live on the instance filesystem while the service is running.
- Free services may spin down after inactivity; first request after idle may be slower (cold start).

This project is portable and can be deployed on AWS EC2 or GCP Compute Engine with the same Docker image when such access becomes available.

---

## Thought Process & Design Decisions

- Chosen stack: FastAPI for performance and automatic docs; Docker for reproducibility; MediaPipe Pose for reliable, production-grade pose detection.
- Robustness: Input validation, explicit error messages, per-frame fallbacks, and codec compatibility checks.
- Separation of concerns: API handling in FastAPI; video processing in a dedicated class; MediaPipe within a controlled context to ensure proper initialization and teardown.
- Manual cleanup: Provided as an explicit endpoint to keep behavior predictable and transparent for the evaluator.

---

## Alignment with Callus's Vision

- AI for movement analysis: Provides accurate pose landmarks, visibility scores, and detection metrics that can power coaching, comparison, or feedback features.
- Cloud-native: Containerized, stateless API that fits scalable infrastructure patterns.
- Developer-friendly: Clear REST endpoints, interactive docs, and reproducible Dockerized setup.

---

## Testing

Run tests:
pytest -v
pytest --cov=app --cov-report=html

Categories covered:
- Unit tests for processing (validations, codecs, resolutions, corrupted inputs)
- API tests (status codes, validation, download/cleanup correctness)
- Integration test for upload → process → download flow

---

## Performance

Reference on a 1080p, 30 FPS, 6-second clip (hardware dependent):
- Processing time: ~8-10 seconds
- Throughput: ~20-25 FPS equivalent
- Memory usage: a few hundred MB during processing
- Detection rate: high on well-lit videos with clear subjects

Tuning options:
- Model complexity (0/1/2): trade speed vs accuracy
- Resolution/FPS of inputs: lower for faster processing
- Sampling strategies: process every Nth frame for speed-sensitive scenarios

---

## Future Enhancements

- Movement quality scoring (angles, posture, symmetry)
- Exercise rep counting or move classification
- Async job queue and webhooks for long-running tasks
- Authentication, rate limiting, and API keys
- GPU acceleration when available
- External object storage integration for persistence (S3, GCS, R2)
- Multi-person tracking and group analysis

---

## Troubleshooting

Common issues and suggestions:
- "Invalid file type": Ensure .mp4/.avi/.mov and correct MIME type.
- "Cannot open video file": Try re-encoding with ffmpeg: `ffmpeg -i in.mp4 -c:v libx264 out.mp4`.
- Low detection: Improve lighting, reduce occlusion, ensure the subject is visible.
- Cold starts on free-tier: First request after idle may be slow; retry after a short delay.
- Endpoint not working - Open enpoint in a browser and let it load because i am using a free version of render, so it sleep if it is not being used for a while
---

## Project Structure

dance-analyzer/
├── app/
│ ├── init.py
│ ├── main.py # FastAPI app & endpoints (manual cleanup)
│ └── video_processor.py # MediaPipe/OpenCV processing
├── tests/
│ ├── test_video_processor.py
│ ├── test_api.py
│ └── test_integration.py
├── uploads/ 
├── outputs/ 
├── Dockerfile
├── docker-compose.yml
├── render.yaml
├── requirements.txt
└── README.md

---

## License

MIT License. 

---

## Contact

Developer: Aman Kumar Singh
Email: amansingh65803@gmail.com  
LinkedIn: https://www.linkedin.com/in/aman-singh-55b1a1263

---

## Add-ons (Optional)

The current deployment does not use any auto-cleanup background tasks. If the assignment requires not storing videos on the VM or enforcing strict retention, the following add-ons can be implemented:
- Auto-cleanup scheduler: Periodically remove files older than a configurable threshold (e.g., 30 minutes).
- Cleanup-after-download: Delete files automatically once a download completes.
- External object storage: Upload outputs to S3/GCS/R2 and return signed URLs instead of serving from local disk, avoiding VM storage entirely.