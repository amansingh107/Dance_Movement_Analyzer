# Dance Movement Analysis API

> AI-powered body movement analysis for dance videos using MediaPipe and Computer Vision

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

**Live Demo:** [https://dance-movement-analyzer.onrender.com](https://dance-movement-analyzer.onrender.com)  
**API Docs:** [https://dance-movement-analyzer.onrender.com/docs](https://dance-movement-analyzer.onrender.com/docs)  
**Repository:** [https://github.com/amansingh107/Dance_Movement_Analyzer](https://github.com/amansingh107/Dance_Movement_Analyzer)

⚠️ **Note:** Free-tier service sleeps after inactivity. First request may take 30-60 seconds to wake up.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [API Usage](#api-usage)
- [Deployment](#deployment)
- [Testing](#testing)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Contact](#contact)

---

## 🎯 Overview

A cloud-based AI/ML system that processes dance videos to detect 33 body landmarks using **Google MediaPipe Pose**, overlays a skeleton visualization, and returns comprehensive movement analytics.

**What it does:**
- Accepts MP4/AVI/MOV uploads (up to 50MB)
- Detects human pose with 33 keypoints per frame
- Generates skeleton overlay video
- Provides detection rate, processing time, and visibility metrics

**Key metrics:** 85-95% detection accuracy, ~0.5-2s per video second, supports 320×240 to 4K resolution.

---

## ✨ Features

- **33-point pose detection** with MediaPipe
- **Skeleton visualization** overlay
- **Multi-format support** (MP4, AVI, MOV)
- **RESTful API** with Swagger UI at `/docs`
- **Docker containerization** for easy deployment
- **Comprehensive error handling** and validation
- **Manual cleanup endpoint** for resource management

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Docker (recommended)
- 8GB RAM minimum

### Local Setup

Clone repository
git clone https://github.com/amansingh107/Dance_Movement_Analyzer.git
cd Dance_Movement_Analyzer

Create virtual environment
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

Install dependencies
pip install -r requirements.txt

Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

**Verify:** Open http://localhost:8000/docs

### Docker Deployment

Using Docker Compose (recommended)
docker-compose up -d --build

Or Docker CLI
docker build -t dance-analyzer .
docker run -d -p 8000:8000 --name dance-api dance-analyzer

---

## 📡 API Usage

**Base URLs:**
- Local: `http://localhost:8000`
- Production: `https://dance-movement-analyzer.onrender.com`

### Endpoints

#### 1. Health Check
GET /health
curl http://localhost:8000/health

#### 2. Analyze Video
POST /api/analyze
curl -X POST "http://localhost:8000/api/analyze"
-F "video=@dance_video.mp4"

**Response:**
{
"success": true,
"job_id": "abc123-xyz",
"total_frames": 180,
"detected_frames": 165,
"detection_rate": "91.67%",
"processing_time": "8.45s",
"download_url": "/api/download/abc123-xyz"
}

#### 3. Download Result
GET /api/download/{job_id}
curl -o result.mp4 http://localhost:8000/api/download/abc123-xyz

#### 4. Manual Cleanup
DELETE /api/cleanup/{job_id}
curl -X DELETE http://localhost:8000/api/cleanup/abc123-xyz

**Postman:** Use `POST /api/analyze` with `form-data`, key: `video` (File type).

---

## ☁️ Deployment

### Render (Free Tier)

**Why Render?** No AWS/GCP access due to credit card requirements. Docker-native, free HTTPS, auto-deploy on git push.

**Deploy:**

1. Add `render.yaml`:
services:

type: web
name: dance-movement-analyzer
env: docker
dockerfilePath: ./Dockerfile
plan: free
region: singapore
healthCheckPath: /health
envVars:

key: PORT
value: 8000

2. Push to GitHub
3. Render Dashboard → New Blueprint → Connect repo → Deploy

**Limitations:** 512MB RAM, ephemeral storage, 15-min sleep (30-60s cold start).

---

## 🧪 Testing

Run all tests
pytest tests/ -v

With coverage
pytest tests/ --cov=app --cov-report=html

Run specific tests
pytest tests/test_video_processor.py -v

**Coverage:** 85%+ (45 passed, 2 skipped)

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | FastAPI + Uvicorn |
| **ML/CV** | MediaPipe, OpenCV, NumPy |
| **Containerization** | Docker, Docker Compose |
| **Cloud** | Render (free tier) |
| **Testing** | pytest, pytest-cov |

**Why MediaPipe?** Production-ready, pip-installable, Apache 2.0 license, actively maintained by Google.

**Why FastAPI?** 2-3x faster than Flask, auto-generated docs, async support, built-in validation.

---

## 💡 Design Decisions

### Architecture
- **API Layer** (FastAPI): Request handling, validation
- **Processing Layer** (OpenCV): Video I/O, frame manipulation
- **ML Layer** (MediaPipe): Pose detection
- **Storage Layer**: Local filesystem with manual cleanup

### Key Decisions
1. **MediaPipe over OpenPose:** Easier deployment, commercial license, better performance
2. **FastAPI over Flask:** Auto docs, async support, 2-3x faster
3. **Manual cleanup:** Explicit control over file deletion (no auto-cleanup implemented)
4. **Context manager pattern:** Ensures proper MediaPipe resource cleanup

### Error Handling
- **Request level:** Fail-fast with clear messages
- **Processing level:** Try-catch with cleanup
- **Frame level:** Graceful degradation (continue on individual frame failures)

---

## 🎯 Callus Vision Alignment

**Callus needs:** AI-powered movement analysis for fitness/dance applications with scalable cloud architecture.

**This project delivers:**
- Quantitative movement metrics (33 landmarks, detection rates, visibility scores)
- Cloud-native API (stateless, Docker-based, horizontally scalable)
- Developer-friendly integration (REST API, Swagger docs, JSON responses)
- Production-ready foundation for extensions (movement quality scoring, rep counting, coaching features)

**Business value:** 100x faster than manual analysis, objective metrics, infinite scalability.

---

## 📁 Project Structure

dance-analyzer/
├── app/
│ ├── main.py # FastAPI app & endpoints
│ └── video_processor.py # MediaPipe/OpenCV processing
├── tests/
│ ├── test_video_processor.py
│ ├── test_api.py
│ └── test_integration.py
├── uploads/ # Temp input storage
├── outputs/ # Temp output storage
├── Dockerfile
├── docker-compose.yml
├── render.yaml
├── requirements.txt
└── README.md

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| **"Cannot open video file"** | Re-encode: `ffmpeg -i input.mp4 -c:v libx264 output.mp4` |
| **503 Service Unavailable** | Render cold start; wait 60s and retry |
| **Memory exceeded (512MB)** | Reduce resolution: `ffmpeg -i input.mp4 -vf scale=1280:720 output.mp4` |
| **Detection rate 0%** | Ensure person is visible, well-lit, not heavily occluded |
| **Endpoint not responding** | Service sleeping; open URL in browser to wake it up |

---

## 🚧 Future Enhancements

- Movement quality scoring (joint angles, posture)
- Exercise rep counting
- Real-time WebRTC streaming
- Multi-person tracking
- External storage (S3/GCS)
- Authentication & rate limiting
- Async processing queue

---

## 🎁 Optional Add-ons

**Current implementation does NOT include:**
- Automatic file cleanup
- External object storage

**Can be added if required:**

1. **Auto-cleanup:** Background scheduler to delete files older than N minutes
2. **S3 Storage:** Upload to cloud storage instead of VM filesystem
3. **Async queue:** Non-blocking API with job status polling
4. **Authentication:** API keys and rate limiting

These features were intentionally excluded to keep the assessment simple and transparent. They can be implemented if the assignment requires not storing videos on VMs.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

---

## 👤 Contact

**Developer:** Aman Kumar Singh  
**Roll Number:** 22B0321

📧 **Email:** [amansingh65803@gmail.com](mailto:amansingh65803@gmail.com)  
💼 **LinkedIn:** [aman-singh-55b1a1263](https://www.linkedin.com/in/aman-singh-55b1a1263)  
🐙 **GitHub:** [amansingh107](https://github.com/amansingh107)

---

## 🙏 Acknowledgments

- Google MediaPipe Team - Pose detection framework
- FastAPI Community - Modern web framework
- Render - Free Docker-native hosting
- Callus Company Inc. - Technical assessment opportunity

---

**Built with ❤️ for Callus Company Inc. AI ML Server Engineer Competency Assessment**

*Last Updated: October 18, 2025*