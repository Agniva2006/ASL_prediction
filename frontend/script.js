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
    kp.push(landmarks[i].x, landmarks[i].y, landmarks[i].z);
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
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ keypoints }),
    });

    const data = await res.json();
    letterEl.innerText = data.prediction;
    confidenceEl.innerText =
      "Confidence: " + (data.confidence * 100).toFixed(1) + "%";
  } catch (err) {
    letterEl.innerText = "-";
    confidenceEl.innerText = "Waiting for stable hand";
  }
}

// =====================
// THROTTLING
// =====================
let lastSent = 0;
const SEND_INTERVAL = 500;

// =====================
// MAIN HANDLER
// =====================
function onResults(results) {
  canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
  canvasCtx.drawImage(results.image, 0, 0, canvasElement.width, canvasElement.height);

  if (
    results.multiHandLandmarks &&
    results.multiHandLandmarks.length === 1
  ) {
    const landmarks = results.multiHandLandmarks[0];

    drawConnectors(canvasCtx, landmarks, HAND_CONNECTIONS, { color: "#22c55e" });
    drawLandmarks(canvasCtx, landmarks, { color: "#ef4444" });

    const keypoints = extractKeypoints(landmarks);
    const now = Date.now();

    if (keypoints.length === 63 && now - lastSent > SEND_INTERVAL) {
      sendToBackend(keypoints);
      lastSent = now;
    }
  } else {
    letterEl.innerText = "-";
    confidenceEl.innerText = "No hand detected";
  }
}

// =====================
// GEMINI CHATBOT (INLINE)
// =====================
const GEMINI_API_KEY = "AIzaSyBj1dXb_jlXzkJC85b3PbLm1u6ltBtGmLI";

const chatbot = document.createElement("div");
chatbot.innerHTML = `
  <div style="margin-top:20px;width:320px;background:#0f172a;padding:12px;border-radius:12px">
    <div id="chatOut" style="height:140px;overflow:auto;color:#e5e7eb;font-size:14px"></div>
    <input id="chatIn" placeholder="Ask about ASL…" 
      style="width:100%;margin-top:6px;padding:6px;border-radius:6px;border:none"/>
  </div>`;
document.body.appendChild(chatbot);

const chatIn = document.getElementById("chatIn");
const chatOut = document.getElementById("chatOut");

chatIn.addEventListener("keydown", async (e) => {
  if (e.key === "Enter" && chatIn.value.trim()) {
    const msg = chatIn.value;
    chatIn.value = "";
    chatOut.innerHTML += `<div><b>You:</b> ${msg}</div>`;

    const res = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${GEMINI_API_KEY}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contents: [{ parts: [{ text: "ASL assistant:\n" + msg }] }],
        }),
      }
    );

    const data = await res.json();
    const reply = data.candidates?.[0]?.content?.parts?.[0]?.text || "No response";
    chatOut.innerHTML += `<div style="color:#22c55e"><b>Bot:</b> ${reply}</div>`;
    chatOut.scrollTop = chatOut.scrollHeight;
  }
});

