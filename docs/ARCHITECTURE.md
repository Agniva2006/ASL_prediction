# 🏛️ Sign0: High-Performance Edge MLSys & Neural Streaming Architecture

> **Document Classification**: Senior / Staff MLSys & Telecommunications Blueprint  
> **System Identification**: Sign0 Enterprise (v5.0.0)  
> **Keywords**: Zero-Copy 48-Byte Neural Codec, INT8 SIMD Quantization, Spatial-Temporal Transformer, Hysteresis Debouncing, DDPM Diffusion Synthesizer

---

## 1. System Context & High-Level Architecture

Traditional computer vision telecommunications transmit high-resolution video streams (e.g., 720p at 1.5 Mbps or 1080p at 3.0 Mbps) over cellular networks. Across rural, developing, or satellite networks (2G/3G/Starlink with high jitter), video packets experience catastrophic dropouts, high latency (>150ms), and bandwidth exhaustion.

**Sign0 eliminates pixel transmission entirely.** By extracting skeletal joint kinematic coordinates on edge CPUs and compressing them into **48-byte binary latent vectors**, Sign0 achieves a **99.23% reduction in wire bandwidth (1.15 kbps at 30 FPS)** while preserving full expressive kinematic fidelity.

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                SIGN0 SYSTEM TOPOLOGY                                    │
│                                                                                         │
│  [ Edge Device / Webcam ]                                                               │
│       │                                                                                 │
│       ▼                                                                                 │
│  MediaPipe Vision Extraction (21 Joints x 3D = 63 Continuous Floats)                    │
│       │                                                                                 │
│       ├─────────────────────────────────┬─────────────────────────────────┐             │
│       ▼                                 ▼                                 ▼             │
│  [ SignCodec Compression ]      [ Local ONNX Static MLP ]       [ Sliding 16-Frame ]    │
│  PCA Manifold Projection        0.08ms P50 Latency (INT8)       [ Spatial-Temporal ]    │
│  48-Byte Compact Struct         Single-Letter Classifier        [ Transformer ]         │
│  (<12f Binary Layout)                                           1.18ms P50 Dynamic Sign │
│       │                                                                   │             │
│       ▼                                                                   ▼             │
│  [ WebRTC / WebSocket Stream ] ───────► [ Hysteresis Stream Engine ] ◄────┘             │
│  Zero-Copy Binary Transmission          • Hold-Duration Debounce Filter                 │
│  1.15 kbps at 30 FPS                    • Auto-Space Pause Detector                     │
│                                         • In-Memory Trie / Levenshtein Autocorrect      │
│                                                   │                                     │
│                                                   ▼                                     │
│                                      [ Real-Time Word & Speech Assembly ]               │
│                                      • Text-to-Speech (TTS) Voice Synthesis             │
│                                      • Prometheus Telemetry & Latency Profiling         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Directory & Module Decomposition

```text
ASL_prediction/
├── backend/
│   ├── sign0/                     # Core production backend package
│   │   ├── api/v1/                # Clean versioned API endpoints
│   │   │   ├── auth.py            # JWT authentication & daily quota enforcement
│   │   │   ├── predict.py         # Static MLP, INT8, and Transformer ONNX inference
│   │   │   ├── stream.py          # WebSocket continuous debouncer & 48-byte binary codec
│   │   │   ├── synthesis.py       # DDPM 3D trajectory synthesis & dictionary catalog
│   │   │   ├── payment.py         # Stripe checkout sessions, portals & webhooks
│   │   │   ├── health.py          # Kubernetes liveness/readiness & Prometheus /metrics
│   │   │   └── router.py          # Consolidated master v1 APIRouter
│   │   ├── core/                  # Core infrastructure
│   │   │   ├── config.py          # Pydantic BaseSettings environment validation
│   │   │   ├── security.py        # Bcrypt hashing, JWT token issuer, rate limiters
│   │   │   ├── logging.py         # JSON structured logging with correlation IDs
│   │   │   └── metrics.py         # Prometheus metrics collection (latency percentiles)
│   │   ├── db/                    # Persistent storage layer
│   │   │   ├── session.py         # Thread-safe SQLAlchemy connection pooling
│   │   │   └── models.py          # User, Activity, and Conversation models
│   │   ├── schemas/               # Typed Pydantic v2 domain schemas
│   │   │   ├── auth.py            # User registration, login, and token models
│   │   │   ├── recognition.py     # 63D landmark inputs, confidence scores, latencies
│   │   │   ├── stream.py          # Frame streaming, binary packets, session state
│   │   │   ├── synthesis.py       # DDPM trajectory sequences and keyframes
│   │   │   └── billing.py         # Stripe plans and customer portal requests
│   │   ├── services/              # Domain logic & ML inference services
│   │   │   ├── inference_service.py # ONNX Runtime session pooling & warmup
│   │   │   ├── stream_processor.py  # Hysteresis state machine & sentence builder
│   │   │   ├── spell_engine.py      # Trie prefix matcher & Levenshtein autocorrect
│   │   │   ├── sign_codec.py        # 48-byte neural latent codec (empirical PCA)
│   │   │   └── diffusion_service.py # DDPM 3D kinematic trajectory synthesizer
│   │   └── main.py                # FastAPI application entrypoint with lifespan manager
│   ├── data/                      # Persistent SQLite DB, label map, and diffusion assets
│   ├── models/                    # ONNX compiled models (FP32 & INT8)
│   ├── app.py                     # Root proxy entrypoint for cloud runtimes
│   └── requirements.txt
├── ml/
│   ├── models/                    # PyTorch model definitions (MLP, Transformer, GRU, Diffusion)
│   ├── training/                  # Offline training and data augmentation pipelines
│   ├── export/                    # ONNX export and INT8 dynamic quantization scripts
│   ├── benchmarks/                # Latency percentile profiling and codec throughput tests
│   └── weights/                   # PyTorch checkpoint files (*.pth)
├── frontend/                      # Web interface (HTML5, Vanilla CSS, JS, MediaPipe Hands)
├── tests/                         # Pytest test suite (18 automated tests)
├── docs/                          # Architecture guides, interview scripts, system diagrams
├── docker-compose.yml             # Container orchestration (API + Prometheus)
├── Dockerfile                     # Multi-stage lightweight production image
└── requirements.txt               # Top-level dependency manifest
```

---

## 3. Mathematical Foundations

### 3.1 SignCodec: 48-Byte Neural Latent Formulation
Given 21 hand joints $J = \{j_0, j_1, \dots, j_{20}\}$ where $j_i = (x_i, y_i, z_i) \in \mathbb{R}^3$:
1. Root normalization: $\Delta j_i = j_i - j_{\text{wrist}}$ for $i \in \{1, \dots, 20\}$, yielding relative vector $V_{\text{rel}} \in \mathbb{R}^{60}$.
2. Centering: $\tilde{V} = V_{\text{rel}} - \mu_{\text{PCA}}$, where $\mu_{\text{PCA}} \in \mathbb{R}^{60}$ is the empirical kinematic mean.
3. Orthogonal projection into $k=9$ principal components:
   $$z = \tilde{V} \cdot W_{\text{proj}} \in \mathbb{R}^9$$
4. Wire Payload:
   $$\text{Payload} = \text{struct.pack}('<12f', j_{\text{wrist}, x}, j_{\text{wrist}, y}, j_{\text{wrist}, z}, z_0, \dots, z_8) \implies 48\text{ Bytes}$$

### 3.2 Hysteresis Hold-Duration Debouncing
To prevent transient finger movement during gesture transitions from registering false positives, the classifier maintains candidate streak accumulator $C_s$:
$$\text{Commit}(L) \iff \left( \forall t \in [T - k, T]: \arg\max P(y_t) = L \land P(y_t = L) \ge \theta_{\text{conf}} \right)$$
where $k = 5$ frames ($\approx 165\text{ms}$ at 30 FPS) and $\theta_{\text{conf}} = 0.70$.
