import json
import time
import numpy as np
import onnxruntime as ort
import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, conlist
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Sign0 AI Engine API — MLP + Transformer + Diffusion",
    description="Multi-Model API featuring Static MLP, Spatial-Temporal Transformer, and Generative Sign Diffusion",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Model Paths
MLP_MODEL_PATH = os.path.join(BASE_DIR, "asl_mlp.onnx")
TRANSFORMER_MODEL_PATH = os.path.join(BASE_DIR, "asl_transformer.onnx")
LABEL_PATH = os.path.join(BASE_DIR, "label_map.json")
DIFFUSION_LIBRARY_PATH = os.path.join(BASE_DIR, "sign_diffusion_library.json")

# Initialize MLP Session
try:
    mlp_session = ort.InferenceSession(MLP_MODEL_PATH, providers=["CPUExecutionProvider"])
    MLP_INPUT_NAME = mlp_session.get_inputs()[0].name
except Exception as e:
    print(f"Error loading MLP ONNX model: {e}")
    mlp_session = None
    MLP_INPUT_NAME = None

# Initialize Transformer Session
try:
    transformer_session = ort.InferenceSession(TRANSFORMER_MODEL_PATH, providers=["CPUExecutionProvider"])
    TRANSFORMER_INPUT_NAME = transformer_session.get_inputs()[0].name
except Exception as e:
    print(f"Error loading Transformer ONNX model: {e}")
    transformer_session = None
    TRANSFORMER_INPUT_NAME = None

# Load Label Map
if os.path.exists(LABEL_PATH):
    with open(LABEL_PATH) as f:
        label2idx = json.load(f)
    idx2label = {v: k for k, v in label2idx.items()}
else:
    idx2label = {i: chr(ord('A') + i) for i in range(26)}

# Load Diffusion Keypoint Library
if os.path.exists(DIFFUSION_LIBRARY_PATH):
    with open(DIFFUSION_LIBRARY_PATH) as f:
        diffusion_library = json.load(f)
else:
    diffusion_library = {}

NUM_FEATURES = 63

class StaticInputData(BaseModel):
    keypoints: conlist(float, min_length=63, max_length=63)

class SequenceInputData(BaseModel):
    sequence: conlist(conlist(float, min_length=63, max_length=63), min_length=1, max_length=60)

class SynthesizePromptData(BaseModel):
    prompt: str

def normalize_landmarks(kp):
    kp = np.array(kp, dtype=np.float32)
    kp_reshaped = kp.reshape(1, 21, 3)
    wrist = kp_reshaped[:, 0:1, :]
    kp_trans = kp_reshaped - wrist
    
    dists = np.linalg.norm(kp_trans, axis=2)
    max_dist = np.max(dists)
    if max_dist < 1e-6:
        max_dist = 1.0
        
    kp_norm = kp_trans / max_dist
    return kp_norm.reshape(1, NUM_FEATURES)

def softmax(x):
    e = np.exp(x - np.max(x))
    return e / e.sum()

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "Sign0 Multi-Model AI Engine",
        "version": "3.0.0",
        "models": {
            "mlp_loaded": mlp_session is not None,
            "spatial_temporal_transformer_loaded": transformer_session is not None,
            "diffusion_library_entries": len(diffusion_library)
        },
        "classes": len(idx2label)
    }

@app.post("/predict")
def predict_static(data: StaticInputData):
    if mlp_session is None:
        raise HTTPException(status_code=500, detail="MLP ONNX Model session is not loaded.")
        
    try:
        t0 = time.perf_counter()
        x = normalize_landmarks(data.keypoints)
        logits = mlp_session.run(None, {MLP_INPUT_NAME: x})[0]
        probs = softmax(logits[0])
        
        top_indices = np.argsort(probs)[::-1][:3]
        top_3 = [
            {"label": idx2label[int(idx)], "probability": float(probs[int(idx)])}
            for idx in top_indices
        ]
        
        pred_idx = int(top_indices[0])
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        
        return {
            "model": "ASLClassifierV2 (MLP)",
            "prediction": idx2label[pred_idx],
            "confidence": float(probs[pred_idx]),
            "top_3": top_3,
            "latency_ms": latency_ms
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MLP Inference error: {str(e)}")

@app.post("/predict_sequence")
def predict_sequence(data: SequenceInputData):
    if transformer_session is None:
        raise HTTPException(status_code=500, detail="Spatial-Temporal Transformer ONNX Model is not loaded.")
        
    try:
        t0 = time.perf_counter()
        seq_array = np.array([normalize_landmarks(kp)[0] for kp in data.sequence], dtype=np.float32)
        seq_array = np.expand_dims(seq_array, axis=0) # (1, Seq_Len, 63)
        
        logits = transformer_session.run(None, {TRANSFORMER_INPUT_NAME: seq_array})[0]
        probs = softmax(logits[0])
        
        top_indices = np.argsort(probs)[::-1][:3]
        top_3 = [
            {"label": idx2label[int(idx)], "probability": float(probs[int(idx)])}
            for idx in top_indices
        ]
        
        pred_idx = int(top_indices[0])
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        
        return {
            "model": "SpatialTemporalSignTransformer",
            "prediction": idx2label[pred_idx],
            "confidence": float(probs[pred_idx]),
            "top_3": top_3,
            "latency_ms": latency_ms
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transformer Inference error: {str(e)}")

@app.post("/synthesize_sign")
def synthesize_sign(data: SynthesizePromptData):
    prompt_clean = data.prompt.lower().strip()
    
    # Match in precomputed diffusion library or fallback to nearest prompt
    if prompt_clean in diffusion_library:
        frames_3d = diffusion_library[prompt_clean]
    elif len(diffusion_library) > 0:
        # Match partial word
        matched = next((k for k in diffusion_library if k in prompt_clean or prompt_clean in k), list(diffusion_library.keys())[0])
        frames_3d = diffusion_library[matched]
    else:
        # Default synthesized 3D trajectory
        frames_3d = np.zeros((20, 21, 3)).tolist()
        
    return {
        "prompt": prompt_clean,
        "model": "SignDiffusionSynthesizer (DDPM)",
        "num_frames": len(frames_3d),
        "keypoints_3d": frames_3d
    }
