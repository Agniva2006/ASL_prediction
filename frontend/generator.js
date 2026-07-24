// ==========================================================================
// SIGN0 TEXT-TO-SIGN DIFFUSION ANIMATION RENDERER
// ==========================================================================

const promptInput = document.getElementById("promptInput");
const generateBtn = document.getElementById("generateBtn");
const animCanvas = document.getElementById("animCanvas");
const ctx = animCanvas.getContext("2d");

const playPauseBtn = document.getElementById("playPauseBtn");
const loopBtn = document.getElementById("loopBtn");
const speedSelect = document.getElementById("speedSelect");
const playerStatus = document.getElementById("playerStatus");

const API_SYNTHESIZE_URL = "http://localhost:8000/synthesize_sign";

// MediaPipe Hand Connection Pairs
const HAND_CONNECTIONS = [
  [0, 1], [1, 2], [2, 3], [3, 4],       // Thumb
  [0, 5], [5, 6], [6, 7], [7, 8],       // Index
  [5, 9], [9, 10], [10, 11], [11, 12],  // Middle
  [9, 13], [13, 14], [14, 15], [15, 16],// Ring
  [13, 17], [17, 18], [18, 19], [19, 20],// Pinky
  [0, 17]                               // Palm base
];

let currentAnimation = null; // Array of 3D frames (Time, 21, 3)
let currentFrameIndex = 0;
let isPlaying = false;
let isLooping = true;
let animTimer = null;
let playbackSpeed = 1.0;

function setPrompt(val) {
  promptInput.value = val;
  generateAnimation();
}

async function generateAnimation() {
  const promptText = promptInput.value.trim();
  if (!promptText) return;

  playerStatus.innerText = "Synthesizing Diffusion Keypoints...";
  playerStatus.style.color = "#38bdf8";

  try {
    const res = await fetch(API_SYNTHESIZE_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: promptText }),
    });

    if (!res.ok) throw new Error(`API HTTP ${res.status}`);

    const data = await res.json();
    currentAnimation = data.keypoints_3d;
    currentFrameIndex = 0;
    
    playerStatus.innerText = `Generated ${data.num_frames} frames for "${data.prompt}"`;
    playerStatus.style.color = "#22c55e";

    startPlayback();
  } catch (err) {
    console.warn("Backend API not reachable, rendering synthesized local trajectory:", err);
    currentAnimation = generateLocalTrajectory(promptText);
    currentFrameIndex = 0;
    playerStatus.innerText = `Local 3D Trajectory (${promptText})`;
    playerStatus.style.color = "#a855f7";
    startPlayback();
  }
}

function startPlayback() {
  if (animTimer) clearInterval(animTimer);
  isPlaying = true;
  playPauseBtn.innerText = "⏸ Pause Animation";

  const frameIntervalMs = 80 / playbackSpeed;
  animTimer = setInterval(() => {
    if (!currentAnimation || currentAnimation.length === 0) return;

    renderFrame(currentAnimation[currentFrameIndex]);
    currentFrameIndex++;

    if (currentFrameIndex >= currentAnimation.length) {
      if (isLooping) {
        currentFrameIndex = 0;
      } else {
        stopPlayback();
      }
    }
  }, frameIntervalMs);
}

function stopPlayback() {
  isPlaying = false;
  if (animTimer) clearInterval(animTimer);
  playPauseBtn.innerText = "▶ Play Animation";
}

function renderFrame(frame3D) {
  const W = animCanvas.width;
  const H = animCanvas.height;
  const cx = W / 2;
  const cy = H / 2 + 30;
  const scale = 220;

  ctx.clearRect(0, 0, W, H);

  // Background Grid Glow
  ctx.strokeStyle = "rgba(56, 189, 248, 0.05)";
  ctx.lineWidth = 1;
  for (let x = 0; x < W; x += 40) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
  }
  for (let y = 0; y < H; y += 40) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
  }

  if (!frame3D || frame3D.length < 21) return;

  // Project 3D to 2D
  const coords2D = frame3D.map(([x, y, z]) => [cx + x * scale, cy + y * scale]);

  // Draw 3D Connectors
  ctx.lineWidth = 3.5;
  ctx.strokeStyle = "#38bdf8"; // Neon Cyan
  ctx.shadowColor = "#38bdf8";
  ctx.shadowBlur = 10;

  for (const [i, j] of HAND_CONNECTIONS) {
    const [x1, y1] = coords2D[i];
    const [x2, y2] = coords2D[j];
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
  }

  // Draw Joint Spheres
  ctx.shadowBlur = 0;
  for (let i = 0; i < coords2D.length; i++) {
    const [x, y] = coords2D[i];
    ctx.beginPath();
    ctx.arc(x, y, i === 0 ? 8 : 4.5, 0, 2 * Math.PI);
    ctx.fillStyle = i === 0 ? "#ef4444" : "#22c55e"; // Red wrist, green joints
    ctx.fill();
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 1.5;
    ctx.stroke();
  }
}

// Fallback dynamic generator
function generateLocalTrajectory(prompt) {
  const frames = [];
  const base = [
    [0, 0, 0], [0.1, -0.1, 0], [0.2, -0.2, 0], [0.25, -0.3, 0], [0.28, -0.35, 0],
    [0.05, -0.4, 0], [0.08, -0.5, 0], [0.1, -0.6, 0], [0.12, -0.65, 0],
    [0, -0.42, 0], [0, -0.52, 0], [0, -0.62, 0], [0, -0.68, 0],
    [-0.05, -0.4, 0], [-0.08, -0.5, 0], [-0.1, -0.58, 0], [-0.12, -0.64, 0],
    [-0.1, -0.35, 0], [-0.14, -0.42, 0], [-0.18, -0.48, 0], [-0.2, -0.52, 0]
  ];

  for (let t = 0; t < 20; t++) {
    const factor = Math.sin((t / 20) * Math.PI * 2) * 0.08;
    const frame = base.map(([x, y, z]) => [x + factor, y + factor * 0.5, z]);
    frames.push(frame);
  }
  return frames;
}

// Event Listeners
generateBtn.addEventListener("click", generateAnimation);

playPauseBtn.addEventListener("click", () => {
  if (isPlaying) {
    stopPlayback();
  } else {
    startPlayback();
  }
});

loopBtn.addEventListener("click", () => {
  isLooping = !isLooping;
  loopBtn.classList.toggle("active", isLooping);
  loopBtn.innerText = isLooping ? "🔁 Loop: ON" : "➡️ Loop: OFF";
});

speedSelect.addEventListener("change", (e) => {
  playbackSpeed = parseFloat(e.target.value);
  if (isPlaying) startPlayback();
});

// Auto generate on page load
generateAnimation();
