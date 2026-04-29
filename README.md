# 🤟 Sign0 — AI-Powered Sign Language Recognition

> Bridging communication gaps using real-time AI-driven sign language recognition.

🌐 **Live Demo:** https://sign0.vercel.app
🔗 **Model Demo:** https://asl-prediction.vercel.app

---

## 📌 Overview

**Sign0** is an end-to-end AI system that translates sign language into text (and optionally speech) in real time using computer vision and deep learning.

It consists of:

* 🧠 A trained neural network model for ASL classification
* 🎥 Real-time webcam-based inference
* 🌐 A modern web interface (Next.js + Tailwind)
* ⚙️ Backend API for prediction

---

## ✨ Features

* 🎥 Real-time sign language recognition
* ⚡ Low-latency prediction pipeline
* 🧠 Deep learning model trained on ASL dataset
* 🌐 Clean and responsive UI (Next.js)
* 🔗 Separate frontend + backend architecture
* ☁️ Deployed on Vercel

---

## 🏗️ Project Structure

```
ASL_prediction/
│
├── backend/              # Model + API (FastAPI / Flask)
├── frontend/             # Web interface
├── sign0-frontend/       # Deployed UI (submodule)
├── ASL_Training.ipynb    # Model training notebook
├── README.md
└── .gitmodules
```

---

## 🧠 Model Details

* Model Type: CNN / Deep Learning (custom trained)
* Task: Multi-class classification (ASL alphabets)
* Input: Hand gesture images / webcam frames
* Output: Predicted sign label

Training pipeline includes:

* Data preprocessing
* Image normalization
* Model training & evaluation
* Accuracy optimization

---

## ⚙️ Tech Stack

### 🧠 AI / ML

* Python
* TensorFlow / PyTorch (based on your implementation)
* OpenCV

### 🌐 Frontend

* Next.js
* Tailwind CSS
* React

### 🔧 Backend

* FastAPI / Flask
* REST API

### ☁️ Deployment

* Vercel (Frontend)
* (Optional) Render / Railway / Local (Backend)

---

## 🚀 Getting Started (Local Setup)

### 1️⃣ Clone the repo

```bash
git clone https://github.com/Agniva2006/ASL_prediction.git
cd ASL_prediction
```

---

### 2️⃣ Backend Setup

```bash
cd backend
pip install -r requirements.txt
python app.py
```

---

### 3️⃣ Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

---

### 4️⃣ Open in browser

```
http://localhost:3000
```

---

## 🎥 How It Works

1. Webcam captures hand gestures
2. Frames are processed using OpenCV
3. Model predicts the sign
4. Output is displayed in real-time

---

## 📊 Future Improvements

* 🔊 Text-to-Speech integration
* 🌍 Multi-language support
* 🤟 Sentence-level prediction (not just alphabets)
* 📱 Mobile app version
* 🧠 Transformer-based gesture recognition

---

## 🧑‍💻 Author

**Agniva Ghosh**

* GitHub: https://github.com/Agniva2006

---

## ⭐ Show Your Support

If you like this project:

* ⭐ Star the repo
* 🍴 Fork it
* 🧠 Contribute

---

## 📜 License

This project is open-source and available under the MIT License.

---
\
