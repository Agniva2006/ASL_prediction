// =====================
// DOM ELEMENTS
// =====================
const videoElement = document.getElementById("video");
const canvasElement = document.getElementById("canvas");
const canvasCtx = canvasElement.getContext("2d");

const letterEl = document.getElementById("letter");
const confidenceEl = document.getElementById("confidence");

// =====================
// BACKEND URL
// =====================
// ⚠️ CHANGE THIS TO YOUR RENDER URL
const API_URL = "https://asl-prediction.onrender.com/predict";

// =====================
// MEDIAPIPE HANDS
// =====================
const hands = new Hands({
  locateFile: (file) =>
    `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`,
});

hands.setOptions({
  maxNumHands: 1,
  modelComplexity: 1,
  minDetectionConfidence: 0.6,
  minTrackingConfidence: 0.6,
});

hands.onResults(onResults);

// =====================
// CAMERA
// =====================
const camera = new Camera(videoElement, {
  onFrame: async () => {
    await hands.send({ image: videoElement });
  },
  width: 640,
  height: 480,
});

camera.start();

// =====================
// KEYPOINT EXTRACTION (21 × 3 = 63)
// =====================
function extractKeypoints(landmarks) {
  const kp = [];
  for (let i = 0; i < 21; i++) {
    kp.push(landmarks[i].x);
    kp.push(landmarks[i].y);
    kp.push(landmarks[i].z);
  }
  return kp;
}

// =====================
// BACKEND CALL
// =====================
async function sendToBackend(keypoints) {
  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ keypoints }),
    });

    if (!res.ok) {
      throw new Error(`Backend error: ${res.status}`);
    }

    const data = await res.json();

    if (!data.prediction) {
      throw new Error("Invalid response");
    }

    letterEl.innerText = data.prediction;
    confidenceEl.innerText =
      "Confidence: " + (data.confidence * 100).toFixed(1) + "%";

  } catch (err) {
    console.error("Prediction error:", err);
    letterEl.innerText = "-";
    confidenceEl.innerText = "Waiting for stable hand";
  }
}

// =====================
// THROTTLING
// =====================
let lastSent = 0;
const SEND_INTERVAL = 500; // ms

// =====================
// MAIN HANDLER
// =====================
function onResults(results) {
  canvasCtx.save();
  canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
  canvasCtx.drawImage(
    results.image,
    0,
    0,
    canvasElement.width,
    canvasElement.height
  );

  // STRICT VALIDATION
  if (
    results.multiHandLandmarks &&
    results.multiHandLandmarks.length === 1 &&
    results.multiHandLandmarks[0].length === 21
  ) {
    const landmarks = results.multiHandLandmarks[0];

    // Draw skeleton
    drawConnectors(canvasCtx, landmarks, HAND_CONNECTIONS, {
      color: "#22c55e",
      lineWidth: 2,
    });
    drawLandmarks(canvasCtx, landmarks, {
      color: "#ef4444",
      lineWidth: 1,
    });

    const keypoints = extractKeypoints(landmarks);

    // FINAL SAFETY CHECK
    if (keypoints.length !== 63) {
      letterEl.innerText = "-";
      confidenceEl.innerText = "Invalid hand data";
      canvasCtx.restore();
      return;
    }

    const now = Date.now();
    if (now - lastSent > SEND_INTERVAL) {
      sendToBackend(keypoints);
      lastSent = now;
    }

  } else {
    letterEl.innerText = "-";
    confidenceEl.innerText = "No hand detected";
  }

  canvasCtx.restore();
}
