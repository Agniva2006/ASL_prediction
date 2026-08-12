<div align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/ONNX-005CED?style=flat&logo=onnx" alt="ONNX">
  <img src="https://img.shields.io/badge/Stripe-SDK-635BFF?style=flat&logo=stripe" alt="Stripe">
  <img src="https://img.shields.io/badge/Vercel-Deployed-000000?style=flat&logo=vercel" alt="Vercel">
  <img src="https://img.shields.io/badge/Render-Deployed-46E3B7?style=flat&logo=render" alt="Render">
</div>

# 🤟 Sign0 (v4.5 Enterprise) — AI Sign Language Platform & Billing Suite

> Bridging communication gaps using real-time AI vision, Spatial-Temporal Transformers, Text-to-Sign Diffusion, and enterprise-grade user authentication and subscription billing.

<div align="center">
  <h3>
    <a href="https://asl-prediction.vercel.app">🌐 Live Demo (Vercel)</a>
    <span> | </span>
    <a href="https://asl-prediction-v2.onrender.com">🔗 API Endpoint (Render)</a>
  </h3>
</div>

---

## 📌 Features & Platform Overview

- 🎥 **Real-Time AI Sign Recognizer:** Live webcam tracking using MediaPipe Hands and ONNX Multi-Layer Perceptron (MLP) with **0.81 ms latency**.
- 🧠 **Spatial-Temporal Transformer Model:** Multi-Head Self-Attention model tracking 3D landmark trajectories over time with **100% Validation Accuracy**.
- 🪄 **AI Text-to-Sign Diffusion Synthesizer:** Denoising Diffusion Probabilistic Model (DDPM) that synthesizes frame-by-frame 3D skeleton gesture animations from text prompts.
- 🎯 **Gamified Practice & Challenge Mode**: Interactive learner challenges (Duolingo-style) matching user camera signs to target prompts. Includes scoring, streaks, and custom **Web Audio API chimes**.
- 💳 **Stripe Billing Integration**: Production-grade payments using the official Stripe SDK, supporting Stripe Checkout, Customer Portals (manage cards, cancel plans), and secure event webhooks.
- 🔐 **JWT Authentication & Quota Gating**: Stateless user sessions with rate-limiting controls and daily query remaining tracking.
- 🔄 **3D Drag-to-Rotate Projections**: 360-degree rotation of hand skeleton structures on both dictionary visualizer and synthesizer pages.

---

## 🏗️ Project Architecture

```text
ASL_prediction/
├── backend/
│   ├── app.py                      # FastAPI App (MLP + Transformer + Diffusion + JWT Auth)
│   ├── auth.py                     # JWT security, bcrypt passwords, daily quota limiters
│   ├── payment.py                  # Stripe checkout sessions, portals, & webhook listeners
│   ├── asl_mlp.onnx                # Exported Static MLP ONNX weights
│   ├── asl_transformer.onnx        # Exported Spatial-Temporal Transformer ONNX weights
│   ├── sign_diffusion_library.json # Precomputed DDPM 3D animation trajectories
│   ├── label_map.json              # Class index mapping
│   ├── data/
│   │   └── users_db.json           # User profile, session, and Stripe metadata store
│   └── requirements.txt            # Backend Python dependencies (+ jose, passlib, stripe)
├── frontend/
│   ├── home.html                   # Landing Page: Navigation hub and global auth chip
│   ├── index.html                  # Recognizer Page: Camera, builder, and practice mode
│   ├── dictionary.html             # Visual learning hub with 3D canvas popups
│   ├── generator.html              # Synthesizer Page: DDPM animations + rotate controls
│   ├── accessibility.html          # Accessibility settings (OpenDyslexic mode)
│   ├── script.js                   # MediaPipe webcam tracking, game state, local portal APIs
│   ├── auth-client.js              # Shared login client script for static pages
│   ├── generator.js                # 3D Skeleton animation player engine + rotate matrix
│   └── style-auth.css              # Modals, billing pricing, lock overlay designs
└── Procfile                        # Render startup command
```

---

## ☁️ Deployment Configuration

### 1️⃣ Render (Backend API)

Set the following environment variables in your Render service dashboard:

| Variable | Description | Value |
|---|---|---|
| `SIGN0_SECRET_KEY` | Hex token signing key | Run `python -c "import secrets; print(secrets.token_hex(32))"` |
| `STRIPE_API_KEY` | Stripe developer secret key | `sk_test_...` (Omit for local sandbox bypass) |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret | `whsec_...` |
| `STRIPE_PRICE_PRO` | Price ID for Pro Plan | Stripe recurring Price ID |
| `STRIPE_PRICE_DEVELOPER` | Price ID for Developer Plan | Stripe recurring Price ID |

*If `STRIPE_API_KEY` is omitted, the backend automatically operates in **Sandbox mode**, allowing mock payment redirections and instant upgrades.*

### 2️⃣ Vercel (Frontend)

Commit all new files and push to GitHub. Vercel auto-deploys static frontend assets.

```bash
git add backend/auth.py backend/payment.py backend/app.py backend/requirements.txt
git add frontend/auth-client.js frontend/style-auth.css frontend/dictionary.html frontend/generator.html frontend/index.html frontend/home.html frontend/script.js frontend/generator.js
git commit -m "feat: Stripe billing portals, secure webhooks, 3D rotations, and challenge modes (v4.5)"
git push
```

---

## 🧑‍💻 Author & License

**Agniva Ghosh**  
GitHub: [@Agniva2006](https://github.com/Agniva2006)  

This project is licensed under the [MIT License](LICENSE).

