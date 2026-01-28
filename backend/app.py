import json
import numpy as np
import onnxruntime as ort
import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, conlist

app = FastAPI(title="ASL Alphabet Recognition API")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "asl_mlp.onnx")
LABEL_PATH = os.path.join(BASE_DIR, "label_map.json")

session = ort.InferenceSession(
    MODEL_PATH,
    providers=["CPUExecutionProvider"]
)

INPUT_NAME = session.get_inputs()[0].name  # SAFE

with open(LABEL_PATH) as f:
    label2idx = json.load(f)

idx2label = {v: k for k, v in label2idx.items()}

NUM_FEATURES = 63


class InputData(BaseModel):
    keypoints: conlist(float, min_length=63, max_length=63)


def softmax(x):
    e = np.exp(x - np.max(x))
    return e / e.sum()

@app.get("/")
def root():
    return {"status": "ASL backend running"}

@app.post("/predict")
def predict(data: InputData):
    try:
        x = np.array(data.keypoints, dtype=np.float32).reshape(1, NUM_FEATURES)

        logits = session.run(None, {INPUT_NAME: x})[0]
        probs = softmax(logits[0])

        pred_idx = int(np.argmax(probs))

        return {
            "prediction": idx2label[pred_idx],
            "confidence": float(probs[pred_idx])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
