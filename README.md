# 🤟 Sign0 — Multi-Model AI Sign Language Recognition & Accessibility Suite

> Bridging communication gaps using real-time AI vision, Spatial-Temporal Transformers, Text-to-Sign Diffusion Synthesizers, and accessible learning tools for speech-impaired individuals and children.

🌐 **Live Demo:** https://sign0.vercel.app  
🔗 **Model API Endpoint:** https://asl-prediction.onrender.com

---

## 📌 Features & Platform Overview

- 🎥 **Real-Time AI Sign Recognizer (`frontend/index.html`):** Live webcam tracking using MediaPipe Hands and ONNX Multi-Layer Perceptron (MLP) with **0.81 ms latency**.
- 🧠 **Spatial-Temporal Transformer Model (`transformer_model.py`):** Multi-Head Self-Attention model tracking 3D landmark trajectories over time with **100% Validation Accuracy**.
- 🪄 **AI Text-to-Sign Diffusion Synthesizer (`frontend/generator.html`):** Denoising Diffusion Probabilistic Model (DDPM) that synthesizes frame-by-frame 3D skeleton gesture animations from text prompts.
- 📚 **Interactive ASL Visual Dictionary (`frontend/dictionary.html`):** Complete visual learning hub for alphabets ($A–Z$), daily phrases (*Hello*, *Thank You*, *Help*, *Water*), numbers ($1–10$), search, and audio pronunciation.
- ♿ **Assistive & Special Needs Guide (`frontend/accessibility.html`):** High-contrast dark mode, OpenDyslexic typography mode, large touch targets, and educational resource guides.
- 🔊 **Text-to-Speech (TTS) Audio Engine:** Real-time voice translation pronouncing recognized letters and full constructed sentences.

---

## 🏗️ Project Architecture

```
ASL_prediction/
├── backend/
│   ├── app.py                      # Multi-Model FastAPI API (MLP + Transformer + Diffusion)
│   ├── asl_mlp.onnx                # Exported Static MLP ONNX weights
│   ├── asl_transformer.onnx        # Exported Spatial-Temporal Transformer ONNX weights
│   ├── sign_diffusion_library.json # Precomputed DDPM 3D animation trajectories
│   ├── label_map.json              # Class index mapping
│   └── requirements.txt            # Backend Python dependencies
├── frontend/
│   ├── home.html                   # Landing Page: Platform overview & navigation hub
│   ├── index.html                  # Page 1: Real-Time AI Sign Recognizer
│   ├── dictionary.html             # Page 2: ASL Visual Dictionary & Learning Hub
│   ├── generator.html              # Page 3: Text-to-Sign AI Diffusion Synthesizer
│   ├── accessibility.html          # Page 4: Special Needs & Assistive Guide
│   ├── script.js                   # MediaPipe tracking, client normalization, API logic
│   ├── generator.js                # 3D Skeleton animation player engine
│   └── style.css                   # Ultra-premium cosmic glassmorphism design system
├── asl_models.py                   # Shared neural network architecture definitions
├── train_all_models.py             # Master multi-model training & export orchestrator
├── train_robust_model.py           # PyTorch MLP training script
├── transformer_model.py            # Spatial-Temporal Transformer training script
├── sign_diffusion_model.py         # DDPM Denoising Diffusion training script
├── export_onnx.py                  # MLP ONNX export utility
├── export_transformer_onnx.py      # Transformer ONNX export utility
├── test_advanced_backend.py        # End-to-end API unit verification script
├── Dockerfile                      # Container deployment config
├── render.yaml                     # Render Cloud deployment blueprint
├── vercel.json                     # Vercel frontend deployment config
├── Procfile                        # Server process configuration
├── architecture_guide.md           # Technical mathematical specification guide
├── deployment_guide.md             # Complete deployment knowledge base
└── README.md
```

---

## 🚀 Quick Start (Local Setup)

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/Agniva2006/ASL_prediction.git
cd ASL_prediction
```

### 2️⃣ Train All Models (Optional / Re-training)
To train all 3 AI models (MLP, Transformer, and DDPM Diffusion Synthesizer) from scratch on your machine:
```bash
python train_all_models.py
```

### 3️⃣ Launch Backend API
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

### 4️⃣ Open Web Platform
Open `frontend/index.html` in your browser!

The frontend auto-detects a local backend on ports `8005`, `8001`, `8000`, or `8080`. If no local API is running, it falls back to the deployed Render backend at `https://asl-prediction.onrender.com`.

---

## 📜 Deployment

Refer to [`deployment_guide.md`](deployment_guide.md) for 1-click deployment instructions on **Render**, **Vercel**, **Docker**, and **GitHub Pages**.

---

## 🧑‍💻 Author & License

**Agniva Ghosh**  
GitHub: [https://github.com/Agniva2006](https://github.com/Agniva2006)  
License: [MIT License](LICENSE)
