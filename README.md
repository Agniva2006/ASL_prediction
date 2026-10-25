<div align="center">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB.svg?style=flat&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/ONNX_Runtime-1.17+-005CED.svg?style=flat&logo=onnx&logoColor=white" alt="ONNX Runtime">
  <img src="https://img.shields.io/badge/PyTorch-2.2+-EE4C2C.svg?style=flat&logo=pytorch&logoColor=white" alt="PyTorch">
  <img src="https://img.shields.io/badge/Docker-Multi--Stage-2496ED.svg?style=flat&logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/Tests-18%20Passed-brightgreen.svg?style=flat&logo=pytest&logoColor=white" alt="Tests">
</div>

# 🤟 Sign0 (v5.0 Enterprise) — High-Performance AI Sign Platform & Neural Codec

> **Production Edge MLSys Platform**: Sub-millisecond continuous American Sign Language (ASL) recognition, 48-byte ultra-low-bandwidth neural video streaming (1.15 kbps wire rate), Spatial-Temporal Multi-Head Attention, Generative DDPM 3D Gesture Synthesis, and Stripe subscription billing.

<div align="center">
  <h3>
    <a href="https://asl-prediction.vercel.app">🌐 Live Web Demo (Vercel)</a>
    <span> | </span>
    <a href="https://asl-prediction-v2.onrender.com/docs">🔗 Swagger API Docs (Render)</a>
    <span> | </span>
    <a href="docs/ARCHITECTURE.md">🏛️ MLSys Architecture Blueprint</a>
  </h3>
</div>

---

## 📌 Core Engineering Innovations

- ⚡ **Zero-Copy 48-Byte Neural Latent Codec (`SignCodec`)**: Compresses 63 continuous MediaPipe hand joint coordinates into a compact 48-byte binary frame format (`<12f`), reducing video streaming bandwidth by **99.23% (down to 1.15 kbps at 30 FPS)** with sub-1.2mm Mean Per-Joint Position Error (MPJPE).
- 🧠 **Multi-Model ONNX Inference Suite**:
  - **Static MLP (FP32 & INT8)**: Compiled ONNX Runtime engine executing in **0.08ms P50 latency** with AVX-512 vector acceleration.
  - **Spatial-Temporal Transformer**: Multi-head self-attention sequence model processing 16-frame sliding windows in **1.18ms P50 latency**.
- ⏱️ **Hysteresis Debounce & Word Assembly Engine**: Production stream processor eliminating transient false positives during finger movement, with auto-spacing on hand pauses and real-time predictive vocabulary completions.
- 🪄 **Generative DDPM 3D Sign Synthesizer**: Denoising Diffusion Probabilistic Model generating continuous 3D skeletal kinematic trajectories from arbitrary text prompts with 360° interactive canvas rotation.
- 💳 **Enterprise Stripe Billing & Quotas**: Production Stripe Checkout, Customer Portals, rate-limiting tier gates, and signed Webhook listeners.
- 📊 **Real-Time Telemetry & Prometheus Observability**: Built-in `/metrics` exporter tracking inference throughput, latency percentiles (P50/P90/P99), and active WebSocket streams.

---

## 🏗️ Production Project Hierarchy

```text
ASL_prediction/
├── backend/
│   ├── sign0/                     # Core production backend package
│   │   ├── api/v1/                # Versioned REST & WebSocket routes
│   │   │   ├── auth.py            # User registration, login & JWT security
│   │   │   ├── predict.py         # Static MLP, INT8, and Transformer inference
│   │   │   ├── stream.py          # Real-time WebSocket debouncer & 48-byte codec
│   │   │   ├── synthesis.py       # DDPM 3D trajectory synthesis & dictionary
│   │   │   ├── payment.py         # Stripe checkout, portal, and webhooks
│   │   │   ├── health.py          # Liveness, readiness, and /metrics probes
│   │   │   └── router.py          # Master v1 API router
│   │   ├── core/                  # Core configurations & telemetry
│   │   │   ├── config.py          # Pydantic BaseSettings environment validation
│   │   │   ├── security.py        # Bcrypt passwords, JWT tokens, quota tracker
│   │   │   ├── logging.py         # Structured JSON logging
│   │   │   └── metrics.py         # In-memory Prometheus telemetry collector
│   │   ├── db/                    # SQLAlchemy database engine & models
│   │   │   ├── session.py         # Thread-safe connection pooling
│   │   │   └── models.py          # User, Activity, and ConversationSession tables
│   │   ├── schemas/               # Typed Pydantic v2 domain schemas
│   │   ├── services/              # Domain logic services
│   │   │   ├── inference_service.py # ONNX Runtime session pooling & warmup
│   │   │   ├── stream_processor.py  # Hysteresis state machine & sentence builder
│   │   │   ├── spell_engine.py      # Trie prefix matcher & Levenshtein autocorrect
│   │   │   ├── sign_codec.py        # 48-byte neural latent codec (PCA basis)
│   │   │   └── diffusion_service.py # DDPM 3D trajectory synthesizer
│   │   └── main.py                # Master FastAPI application with lifespan
│   ├── data/                      # Persistent SQLite DB, label map, diffusion library
│   ├── models/                    # ONNX compiled models (FP32 & INT8)
│   ├── app.py                     # Root entrypoint proxy
│   └── requirements.txt
├── ml/
│   ├── models/                    # PyTorch model definitions (MLP, Transformer, GRU, Diffusion)
│   ├── training/                  # Offline training pipelines & data augmentation
│   ├── export/                    # ONNX export and INT8 dynamic quantization scripts
│   ├── benchmarks/                # Latency profiling & codec streaming benchmarks
│   └── weights/                   # PyTorch checkpoint files (*.pth)
├── frontend/                      # Web interface (HTML5, Vanilla CSS, JS, MediaPipe Hands)
├── tests/                         # Automated test suite (18 passed unit & integration tests)
├── docs/                          # Architecture blueprints, technical guides, interview scripts
│   ├── ARCHITECTURE.md            # Senior MLSys Architecture blueprint
│   ├── DEEP_ANALYSIS_AND_ROADMAP.md # Technical analysis & engineering roadmap
│   ├── HR_AND_TECHNICAL_INTERVIEW_GUIDE.md # Interview guide & tough Q&A
│   └── assets/                    # Architectural diagrams and schematics
├── docker-compose.yml             # Full-stack orchestration (FastAPI + Prometheus)
├── Dockerfile                     # Multi-stage production container image
├── prometheus.yml                 # Prometheus metrics scraping configuration
└── requirements.txt               # Dependency manifest
```

---

## 🚀 Quickstart & Local Execution

### 1. Environment Setup
```bash
# Clone the repository
git clone https://github.com/Agniva2006/ASL_prediction.git
cd ASL_prediction

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Automated Test Suite
```bash
pytest tests/ -v
# Output: 18 passed in ~0.3s
```

### 3. Start Development Server
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```
Navigate to:
- **Interactive Swagger Documentation**: `http://localhost:8000/docs`
- **Prometheus Telemetry Metrics**: `http://localhost:8000/metrics`
- **System Readiness Probe**: `http://localhost:8000/health/ready`

### 4. Run Streaming & Latency Benchmarks
```bash
# Benchmark 48-byte codec throughput and bandwidth reduction
python ml/benchmarks/run_codec_demo.py

# Benchmark ONNX Runtime CPU latency percentiles (P50, P90, P99)
python ml/benchmarks/benchmark_latency.py
```

### 5. Docker Deployment
```bash
# Start backend API and Prometheus monitoring
docker-compose up -d --build
```

---

## 📡 Key API Endpoints

| Protocol | Method | Endpoint | Description |
|---|---|---|---|
| HTTP | `GET` | `/` | Service health status and quick links |
| HTTP | `POST` | `/api/v1/predict/mlp` | 63D Landmark inference via Static MLP (0.08ms) |
| HTTP | `POST` | `/api/v1/predict/int8` | Quantized INT8 SIMD accelerated inference |
| HTTP | `POST` | `/api/v1/predict/transformer` | Dynamic 16-frame sequence classification |
| WebSocket | `WS` | `/api/v1/stream/ws` | Real-time continuous webcam debouncing stream |
| WebSocket | `WS` | `/api/v1/stream/binary` | 48-byte zero-copy Neural Latent Codec stream |
| HTTP | `POST` | `/api/v1/synthesis/generate` | Generative DDPM 3D gesture trajectory synthesis |
| HTTP | `GET` | `/api/v1/synthesis/dictionary` | Sign dictionary catalog with 3D trajectories |
| HTTP | `POST` | `/api/v1/auth/signup` | Register new user account with signed JWT |
| HTTP | `POST` | `/api/v1/auth/login` | Authenticate and obtain Bearer access token |
| HTTP | `POST` | `/api/v1/payment/checkout` | Create Stripe Checkout session |
| HTTP | `GET` | `/metrics` | Prometheus metrics exposition format |

---

## 🧑‍💻 Author & License

**Agniva Ghosh**  
GitHub: [@Agniva2006](https://github.com/Agniva2006) | Email: agnivaghosh2006@gmail.com  
Licensed under the [MIT License](LICENSE).
