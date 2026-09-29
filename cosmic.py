"""
THE COSMIC SANCTUARY  (v2)
==========================
A single-file Streamlit mindfulness experience.

Phase 1  — an immersive, self-contained scroll portal: a premium duotone
           Three.js Earth (deep indigo oceans, muted mineral land), sized to
           always fit fully in view -- with clean margins -- on any screen
           or orientation, with two data layers -- a rippling aurora band
           and breathing night-side city lights -- that rotates and
           seamlessly dissolves into a Swiss-style line-art brain as you
           reach the end. On open, a brief consent card asks permission to
           play a calming tone; if granted, a Web Audio entrainment engine
           starts immediately: a 55Hz sub-bass heartbeat ramping from 82 BPM
           down to a resting 56 BPM over 60 seconds, under a softly filtered
           pink-noise breathing sweep. A small toggle in the final section
           offers the same control for anyone who said "not now."
Phase 2  — "The Canvas": a quiet card to name your emotional load and write
           what you're carrying, revealed only once the scroll story is
           actually finished. On submit, the typed text shatters into thin
           horizontal splinters -- each on its own drifting path -- and
           dissolves over 2.5 seconds; only once that ritual completes does
           the Gemini request fire, and its reflection always grounds itself
           in one real, verifiable scientific or environmental fact.

Setup
-----
    pip install streamlit google-genai pydantic

Add your Gemini key one of these ways:
    1) Environment variable:  export GOOGLE_API_KEY="your-key-here"
    2) .streamlit/secrets.toml:  GOOGLE_API_KEY = "your-key-here"
    3) Paste it into the "Connect your Gemini API key" box inside the app.

Run:
    streamlit run cosmic.py

Note on the two components.html blocks below: Streamlit's `components.html`
iframes are same-origin with the page (they carry the `allow-same-origin`
sandbox flag). That's what lets Phase 1 reveal "The Canvas" (found via its
`st.container(key="phase2_canvas")` CSS class) only once your scroll
progress actually finishes, and lets the ritual component find, replace,
and click the native "Surrender to the Cosmos" button on your behalf. Every
one of those lookups is wrapped in a defensive fallback: if anything about
your Streamlit version changes and an element can't be found, the code
leaves the native elements fully visible and functional rather than
breaking the app.
"""

import os
import html
import json
import time
from datetime import datetime
from typing import List, Optional, Tuple

import streamlit as st
import streamlit.components.v1 as components
from pydantic import BaseModel, Field

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


# ============================================================================
# 1. PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="The Cosmic Sanctuary",
    page_icon="\U0001F30C",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ============================================================================
# 2. GLOBAL THEME (dark, minimalist, Swiss-feeling)
# ============================================================================

GLOBAL_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">

<style>
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .stApp {
        background: #08080a;
        color: #e5e5ea;
    }
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {
        padding-top: 0.5rem;
        padding-bottom: 4rem;
        max-width: 760px;
    }
    iframe {border: none !important;}

    h1, h2, h3, .sanctuary-heading {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 500;
        letter-spacing: -0.01em;
    }
    .sanctuary-heading {
        text-align: center;
        font-size: clamp(1.3rem, 4vw, 1.9rem);
        color: #e5e5ea;
        margin: 2.2rem 0 0.4rem 0;
    }
    .sanctuary-sub {
        text-align: center;
        color: #8b8b93;
        font-size: 0.92rem;
        margin-bottom: 2.2rem;
        font-weight: 300;
    }
    .prompt-text {
        text-align: center;
        font-size: 1.05rem;
        color: #e5e5ea;
        font-weight: 300;
        margin: 1.8rem 0 0.8rem 0;
        letter-spacing: 0.01em;
    }
    .phase2-eyebrow {
        text-align: center;
        font-size: 0.7rem;
        letter-spacing: 0.24em;
        text-transform: uppercase;
        color: #4F83F5;
        margin: 0 0 0.7rem 0;
        font-weight: 500;
    }
    .phase2-divider {
        width: 34px;
        height: 1px;
        background: #2a2a33;
        margin: 0 auto 1.5rem auto;
    }
    /* "The Canvas" card -- targeted via Streamlit's container key class */
    .st-key-phase2_canvas {
        background: linear-gradient(180deg, #101014 0%, #0c0c0f 100%);
        border: 1px solid #1e1e24;
        border-radius: 28px;
        padding: 2.4rem 1.8rem 2.1rem 1.8rem;
        margin-top: 0.4rem;
        box-shadow: 0 30px 80px -42px rgba(79,131,245,0.22);
    }
    .st-key-phase2_canvas .sanctuary-heading { margin-top: 0; }

    /* Streamlit widgets restyled to match the sanctuary */
    .stTextArea textarea {
        background: #101014 !important;
        border: 1px solid #1e1e24 !important;
        border-radius: 16px !important;
        color: #e5e5ea !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 1rem !important;
        padding: 1.1rem !important;
        transition: opacity 0.4s ease !important;
    }
    .stTextArea textarea:focus {
        border-color: #4F83F5aa !important;
        box-shadow: 0 0 0 1px #4F83F555 !important;
    }
    .stTextInput input {
        background: #101014 !important;
        border: 1px solid #1e1e24 !important;
        border-radius: 10px !important;
        color: #e5e5ea !important;
    }
    .stTextInput input:focus {
        border-color: #4F83F5aa !important;
        box-shadow: 0 0 0 1px #4F83F555 !important;
    }
    label, .stSlider label p, .stSelectSlider label p {
        color: #b9b9c3 !important;
        font-weight: 400 !important;
        font-size: 0.92rem !important;
    }
    div[data-baseweb="slider"] > div > div {
        background: #1e1e24 !important;
    }
    div[data-baseweb="slider"] [role="slider"] {
        background-color: #4F83F5 !important;
        box-shadow: 0 0 0 6px #4F83F51f !important;
    }
    div[data-testid="stTickBar"] { display: none; }
    .stButton button {
        background: linear-gradient(135deg, #4F83F5, #7aa2ff);
        color: #08080a;
        border: none;
        border-radius: 999px;
        padding: 0.85rem 0;
        width: 100%;
        font-weight: 600;
        font-size: 1rem;
        letter-spacing: 0.02em;
        margin-top: 1.5rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 10px 26px #4F83F544;
        color: #08080a;
    }
    .stButton button:active { transform: translateY(0px); }

    .moment-chip {
        display: inline-block;
        font-size: 0.76rem;
        color: #9a9aa4;
        border: 1px solid #232329;
        padding: 0.3rem 0.8rem;
        border-radius: 999px;
    }
    .music-chip {
        background: #101014;
        border: 1px solid #1e1e24;
        border-radius: 14px;
        padding: 0.9rem 1.2rem;
        font-size: 0.88rem;
        color: #a9b8e8;
        margin-top: 2.2rem;
        animation: fadeUp 0.9s ease;
    }
    .phrase-box {
        background: radial-gradient(circle at 30% 15%, #11131c, #08080a 72%);
        border: 1px solid #1e2230;
        border-radius: 22px;
        padding: 2.4rem 2rem;
        margin-top: 1.4rem;
        text-align: center;
        font-family: 'Space Grotesk', sans-serif;
        font-size: clamp(1.1rem, 3vw, 1.45rem);
        line-height: 1.6;
        color: #eef1fb;
        animation: fadeUp 1s ease;
    }
    .action-box {
        background: #4F83F514;
        border: 1px solid #4F83F540;
        border-radius: 18px;
        padding: 1.5rem 1.6rem;
        margin-top: 1.2rem;
        animation: fadeUp 1.1s ease;
    }
    .action-box h4 {
        margin: 0 0 0.7rem 0;
        font-size: 0.76rem;
        text-transform: uppercase;
        letter-spacing: 0.09em;
        color: #8fb0ff;
        font-weight: 600;
    }
    .action-item {
        font-size: 0.97rem;
        color: #e5e5ea;
        margin: 0.4rem 0;
        padding-left: 1.15rem;
        position: relative;
        line-height: 1.5;
    }
    .action-item:before {
        content: '';
        position: absolute; left: 0; top: 0.55em;
        width: 6px; height: 6px; border-radius: 50%;
        background: #4F83F5;
    }
    @keyframes fadeUp {
        from {opacity: 0; transform: translateY(10px);}
        to {opacity: 1; transform: translateY(0);}
    }
</style>
"""

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# ============================================================================
# 3. PHASE 1 — THE SCROLL PORTAL
#    Shader-graded Earth + aurora/city-light data layers + Swiss brain
#    line-art morph + Web Audio entrainment engine, all self-contained.
#    The component syncs its own height to your real viewport (via the
#    same-origin parent window) so Phase 2 stays below the fold until the
#    story is actually finished -- normal nested-scroll behavior then keeps
#    it out of view until you've scrolled the portal all the way through.
# ============================================================================

SCROLL_PORTAL_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
  html, body {
    margin: 0; padding: 0;
    background: #08080a;
    color: #e5e5ea;
    height: 100%;
    font-family: 'Inter', -apple-system, sans-serif;
    overflow-x: hidden;
  }
  #story { position: relative; }

  .brandmark {
    position: absolute;
    top: 22px; left: 26px;
    font-size: 0.68rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #55555f;
    z-index: 4;
  }

  .stage {
    position: sticky;
    top: 0;
    height: 100vh;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    z-index: 1;
    background: radial-gradient(ellipse at 50% 40%, #0d0d12 0%, #08080a 70%);
  }
  #globeWrap {
    position: absolute;
    inset: 7% 9%;
    background: radial-gradient(circle at 50% 45%, rgba(79,131,245,0.10), transparent 62%);
  }
  #globeCanvas {
    width: 100%;
    height: 100%;
    display: block;
  }
  #brainSvg {
    position: absolute;
    top: 50%; left: 50%;
    width: 62%;
    max-width: 420px;
    transform: translate(-50%, -50%);
    opacity: 0;
    filter: drop-shadow(0 0 18px rgba(79,131,245,0.28));
  }
  #brainSvg path {
    fill: none;
    stroke: #4F83F5;
    stroke-width: 1.6;
    stroke-linecap: round;
    stroke-linejoin: round;
  }

  .hint {
    position: absolute;
    bottom: 26px; left: 0; right: 0;
    text-align: center;
    font-size: 0.7rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #5c5c66;
    z-index: 3;
    animation: pulse 2.4s ease-in-out infinite;
    transition: opacity 0.5s ease;
  }
  .hint.hidden { opacity: 0 !important; animation: none !important; }
  @keyframes pulse { 0%, 100% {opacity: 0.35;} 50% {opacity: 0.9;} }

  .sections { position: relative; z-index: 2; }
  .line {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 0 9%;
    box-sizing: border-box;
  }
  .line p {
    opacity: 0;
    transform: translateY(26px);
    filter: blur(8px);
    transition: opacity 1.15s cubic-bezier(.16,1,.3,1),
                transform 1.15s cubic-bezier(.16,1,.3,1),
                filter 1.15s cubic-bezier(.16,1,.3,1);
    font-size: clamp(1.25rem, 4vw, 2.05rem);
    font-weight: 300;
    letter-spacing: 0.01em;
    line-height: 1.55;
    max-width: 540px;
    text-shadow: 0 2px 26px rgba(0,0,0,0.65);
  }
  .line.show p { opacity: 1; transform: translateY(0); filter: blur(0px); }
  .line.final .final-inner {
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  .line.final p {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 400;
    font-size: clamp(1.35rem, 4.5vw, 2.2rem);
  }

  .sound-toggle {
    margin-top: 1.6rem;
    display: inline-flex;
    align-items: center;
    gap: 0.55rem;
    background: transparent;
    border: 1px solid #2a2a33;
    color: #b7b7c2;
    font-family: 'Inter', sans-serif;
    font-size: 0.78rem;
    letter-spacing: 0.04em;
    padding: 0.5rem 1.1rem;
    border-radius: 999px;
    cursor: pointer;
    opacity: 0;
    transform: translateY(10px);
    transition: opacity 1s ease 0.3s, transform 1s ease 0.3s,
                border-color 0.3s ease, color 0.3s ease;
  }
  .line.final.show .sound-toggle { opacity: 1; transform: translateY(0); }
  .sound-toggle .dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: #4a4a55;
    transition: background 0.3s ease, box-shadow 0.3s ease;
  }
  .sound-toggle.on {
    border-color: #4F83F566;
    color: #e5e5ea;
  }
  .sound-toggle.on .dot {
    background: #4F83F5;
    box-shadow: 0 0 8px #4F83F5aa;
  }

  .sound-gate {
    position: fixed;
    inset: 0;
    z-index: 50;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 8%;
    box-sizing: border-box;
    background: rgba(8,8,10,0.74);
    -webkit-backdrop-filter: blur(6px);
    backdrop-filter: blur(6px);
    opacity: 1;
    transition: opacity 0.6s ease;
  }
  .sound-gate.hidden { opacity: 0; pointer-events: none; }
  .sound-gate-card {
    max-width: 360px;
    text-align: center;
    background: radial-gradient(circle at 30% 15%, #14141a, #0a0a0c 75%);
    border: 1px solid #22222a;
    border-radius: 22px;
    padding: 2.2rem 1.8rem;
  }
  .sound-gate-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.08rem;
    font-weight: 400;
    color: #e5e5ea;
    margin: 0 0 0.7rem 0;
    line-height: 1.45;
  }
  .sound-gate-sub {
    font-size: 0.82rem;
    color: #8b8b93;
    font-weight: 300;
    line-height: 1.5;
    margin: 0 0 1.6rem 0;
  }
  .sound-gate-actions {
    display: flex;
    flex-direction: column;
    gap: 0.7rem;
  }
  .sg-btn {
    border-radius: 999px;
    padding: 0.75rem 1rem;
    font-family: 'Inter', sans-serif;
    font-size: 0.88rem;
    font-weight: 600;
    cursor: pointer;
    border: none;
  }
  .sg-btn-primary {
    background: linear-gradient(135deg, #4F83F5, #7aa2ff);
    color: #08080a;
  }
  .sg-btn-ghost {
    background: transparent;
    border: 1px solid #2a2a33;
    color: #b7b7c2;
    font-weight: 500;
  }
</style>
</head>
<body>
<div id="soundGate" class="sound-gate">
  <div class="sound-gate-card">
    <p class="sound-gate-title">Play a calming ambient tone while you're here?</p>
    <p class="sound-gate-sub">A soft, low breathing tone under everything else. Fully optional -- you can turn it on or off anytime.</p>
    <div class="sound-gate-actions">
      <button id="soundGateYes" type="button" class="sg-btn sg-btn-primary">Yes, play sound</button>
      <button id="soundGateNo" type="button" class="sg-btn sg-btn-ghost">Not now</button>
    </div>
  </div>
</div>
<div id="story">

  <div class="stage">
    <div class="brandmark">The Cosmic Sanctuary</div>
    <div id="globeWrap">
      <canvas id="globeCanvas"></canvas>
      <svg id="brainSvg" viewBox="0 0 300 260" xmlns="http://www.w3.org/2000/svg">
        <path d="M60,140 C40,110 45,70 80,50 C100,35 130,30 155,38 C170,25 195,22 215,35 C235,48 245,72 238,95 C255,100 268,118 265,138 C263,155 250,168 235,170 C238,185 230,200 215,205 C218,218 208,230 192,230 C185,242 168,248 152,240 C138,248 120,245 112,232 C95,235 80,225 78,208 C62,205 52,190 55,172 C42,168 35,155 42,142 C48,132 55,135 60,140 Z"/>
        <path d="M90,90 C105,80 120,85 130,100 C140,85 158,82 172,92"/>
        <path d="M96,130 C114,120 132,128 142,145 C155,128 175,125 192,138"/>
        <path d="M92,172 C110,163 127,169 137,183"/>
        <path d="M150,235 C147,248 152,259 163,261 C174,259 178,247 173,236"/>
      </svg>
    </div>
    <div class="hint">scroll</div>
  </div>

  <div class="sections">
    <div class="line" data-i="0"><p>Look closely at our home.</p></div>
    <div class="line" data-i="1"><p>No lines divide us from up here.</p></div>
    <div class="line" data-i="2"><p>Every breath we take is shared.</p></div>
    <div class="line final" data-i="3">
      <div class="final-inner">
        <p>Leave whatever you are carrying right here.</p>
        <button id="soundToggle" class="sound-toggle" type="button">
          <span class="dot"></span><span class="label">Calming tone</span>
        </button>
      </div>
    </div>
  </div>

</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
(function () {

  // ---- keep this portal exactly as tall as your real viewport, so ----
  // ---- Phase 2 stays out of view until the story actually finishes ----
  function syncFrameHeight() {
    try {
      var fe = window.frameElement;
      var vh = window.parent && window.parent.innerHeight ? window.parent.innerHeight : null;
      if (fe && vh) { fe.style.height = vh + 'px'; }
    } catch (e) { /* restricted context: keep the default static height */ }
  }
  syncFrameHeight();
  try { window.parent.addEventListener('resize', syncFrameHeight); } catch (e) {}
  window.addEventListener('orientationchange', function () { setTimeout(syncFrameHeight, 300); });

  var canvas = document.getElementById('globeCanvas');
  var wrap = document.getElementById('globeWrap');
  var brain = document.getElementById('brainSvg');
  var hint = document.querySelector('.hint');
  var storyEl = document.getElementById('story');

  var scene, camera, renderer, earthGroup, earthMat, cityMat, auroraMat, stars, clock;
  var ready = false;

  var SUN_DIR = new (window.THREE ? THREE.Vector3 : Object)(0.6, 0.35, 0.7);
  if (window.THREE) { SUN_DIR.normalize(); }

  function initThree() {
    if (typeof THREE === 'undefined') { return; }

    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);

    renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

    var loader = new THREE.TextureLoader();
    var dayMap = loader.load('https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg');
    var bumpMap = loader.load('https://unpkg.com/three-globe/example/img/earth-topology.png');
    var specMap = loader.load('https://unpkg.com/three-globe/example/img/earth-water.png');

    earthGroup = new THREE.Group();
    scene.add(earthGroup);

    // ---- premium duotone earth: indigo oceans, muted mineral land ----
    var earthVert = [
      'varying vec2 vUv;',
      'varying vec3 vNormalWorld;',
      'varying vec3 vWorldPos;',
      'void main() {',
      '  vUv = uv;',
      '  vNormalWorld = normalize(mat3(modelMatrix) * normal);',
      '  vWorldPos = (modelMatrix * vec4(position, 1.0)).xyz;',
      '  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);',
      '}'
    ].join(String.fromCharCode(10));

    var earthFrag = [
      'uniform sampler2D dayMap;',
      'uniform sampler2D bumpMap;',
      'uniform sampler2D specMap;',
      'uniform vec3 uSunDir;',
      'uniform vec3 uIndigo;',
      'uniform vec3 uMineral;',
      'varying vec2 vUv;',
      'varying vec3 vNormalWorld;',
      'varying vec3 vWorldPos;',
      'void main() {',
      '  vec3 tex = texture2D(dayMap, vUv).rgb;',
      '  float lum = dot(tex, vec3(0.299, 0.587, 0.114));',
      '  float landMask = smoothstep(0.32, 0.55, lum);',
      '  vec3 baseColor = mix(uIndigo, uMineral, landMask);',
      '  float relief = texture2D(bumpMap, vUv).r;',
      '  baseColor *= (0.88 + relief * 0.24);',
      '  float ndl = max(dot(vNormalWorld, uSunDir), 0.0);',
      '  float ambient = 0.22;',
      '  vec3 lit = baseColor * (ambient + ndl * 0.95);',
      '  float waterMask = texture2D(specMap, vUv).r;',
      '  vec3 viewDir = normalize(cameraPosition - vWorldPos);',
      '  vec3 halfDir = normalize(uSunDir + viewDir);',
      '  float spec = pow(max(dot(vNormalWorld, halfDir), 0.0), 28.0) * waterMask * 0.6;',
      '  vec3 finalColor = lit + spec * vec3(0.75, 0.85, 1.0);',
      '  gl_FragColor = vec4(finalColor, 1.0);',
      '}'
    ].join(String.fromCharCode(10));

    var geo = new THREE.SphereGeometry(1, 64, 64);
    earthMat = new THREE.ShaderMaterial({
      uniforms: {
        dayMap: { value: dayMap },
        bumpMap: { value: bumpMap },
        specMap: { value: specMap },
        uSunDir: { value: SUN_DIR },
        uIndigo: { value: new THREE.Color(0x141b3d) },
        uMineral: { value: new THREE.Color(0x8a7f6b) }
      },
      vertexShader: earthVert,
      fragmentShader: earthFrag
    });
    var earth = new THREE.Mesh(geo, earthMat);
    earthGroup.add(earth);

    // ---- atmosphere rim glow ----
    var glowGeo = new THREE.SphereGeometry(1.06, 64, 64);
    var glowMat = new THREE.ShaderMaterial({
      vertexShader: [
        'varying vec3 vNormal;',
        'void main() {',
        '  vNormal = normalize(normalMatrix * normal);',
        '  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);',
        '}'
      ].join(String.fromCharCode(10)),
      fragmentShader: [
        'varying vec3 vNormal;',
        'void main() {',
        '  float intensity = pow(0.68 - dot(vNormal, vec3(0.0, 0.0, 1.0)), 3.2);',
        '  gl_FragColor = vec4(0.33, 0.53, 0.96, 1.0) * intensity;',
        '}'
      ].join(String.fromCharCode(10)),
      blending: THREE.AdditiveBlending,
      side: THREE.BackSide,
      transparent: true
    });
    earthGroup.add(new THREE.Mesh(glowGeo, glowMat));

    // ---- data layer 1: rippling aurora band near the poles ----
    var auroraGeo = new THREE.SphereGeometry(1.018, 64, 64);
    auroraMat = new THREE.ShaderMaterial({
      uniforms: {
        uTime: { value: 0 },
        uAuroraColor: { value: new THREE.Color(16 / 255, 185 / 255, 129 / 255) }
      },
      vertexShader: [
        'varying vec3 vWorldPos;',
        'void main() {',
        '  vWorldPos = (modelMatrix * vec4(position, 1.0)).xyz;',
        '  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);',
        '}'
      ].join(String.fromCharCode(10)),
      fragmentShader: [
        'uniform float uTime;',
        'uniform vec3 uAuroraColor;',
        'varying vec3 vWorldPos;',
        'void main() {',
        '  float lat = abs(normalize(vWorldPos).y);',
        '  float band = smoothstep(0.60, 0.80, lat) * (1.0 - smoothstep(0.92, 1.0, lat));',
        '  float ripple = sin(uTime * 0.35 + vWorldPos.x * 3.0 + vWorldPos.z * 2.0) * 0.5 + 0.5;',
        '  float intensity = band * (0.5 + ripple * 0.5);',
        '  gl_FragColor = vec4(uAuroraColor, intensity * 0.12);',
        '}'
      ].join(String.fromCharCode(10)),
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      side: THREE.DoubleSide
    });
    earthGroup.add(new THREE.Mesh(auroraGeo, auroraMat));

    // ---- data layer 2: breathing amber city lights, night side only ----
    var cityCount = 260;
    var cityPositions = new Float32Array(cityCount * 3);
    var cityPhases = new Float32Array(cityCount);
    for (var i = 0; i < cityCount; i++) {
      var theta = Math.random() * Math.PI * 2;
      var v = Math.max(Math.min(Math.random() * 1.6 - 0.8, 0.92), -0.92);
      var phi = Math.acos(v);
      var r = 1.012;
      cityPositions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      cityPositions[i * 3 + 1] = r * Math.cos(phi);
      cityPositions[i * 3 + 2] = r * Math.sin(phi) * Math.sin(theta);
      cityPhases[i] = Math.random() * Math.PI * 2;
    }
    var cityGeo = new THREE.BufferGeometry();
    cityGeo.setAttribute('position', new THREE.BufferAttribute(cityPositions, 3));
    cityGeo.setAttribute('aPhase', new THREE.BufferAttribute(cityPhases, 1));
    cityMat = new THREE.ShaderMaterial({
      uniforms: {
        uTime: { value: 0 },
        uSunDir: { value: SUN_DIR }
      },
      vertexShader: [
        'attribute float aPhase;',
        'uniform float uTime;',
        'varying float vPhase;',
        'varying vec3 vNormalWorld;',
        'void main() {',
        '  vPhase = aPhase;',
        '  vNormalWorld = normalize(mat3(modelMatrix) * normalize(position));',
        '  vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);',
        '  gl_PointSize = 2.4 * (300.0 / -mvPosition.z);',
        '  gl_Position = projectionMatrix * mvPosition;',
        '}'
      ].join(String.fromCharCode(10)),
      fragmentShader: [
        'precision mediump float;',
        'uniform vec3 uSunDir;',
        'uniform float uTime;',
        'varying float vPhase;',
        'varying vec3 vNormalWorld;',
        'void main() {',
        '  float ndl = dot(vNormalWorld, uSunDir);',
        '  float dayFactor = smoothstep(-0.25, 0.05, ndl);',
        '  float nightMask = 1.0 - dayFactor;',
        '  float breathe = 0.5 + 0.5 * sin(uTime * 0.6 + vPhase);',
        '  float alpha = nightMask * (0.35 + breathe * 0.65) * 0.15;',
        '  vec2 c = gl_PointCoord - vec2(0.5);',
        '  float d = length(c);',
        '  if (d > 0.5) discard;',
        '  float edge = smoothstep(0.5, 0.0, d);',
        '  gl_FragColor = vec4(245.0/255.0, 158.0/255.0, 11.0/255.0, alpha * edge);',
        '}'
      ].join(String.fromCharCode(10)),
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending
    });
    earthGroup.add(new THREE.Points(cityGeo, cityMat));

    // ---- starfield ----
    var starGeo = new THREE.BufferGeometry();
    var starCount = 900;
    var positions = new Float32Array(starCount * 3);
    for (var s = 0; s < starCount; s++) {
      var rr = 40 + Math.random() * 60;
      var th = Math.random() * Math.PI * 2;
      var ph = Math.acos((Math.random() * 2) - 1);
      positions[s * 3] = rr * Math.sin(ph) * Math.cos(th);
      positions[s * 3 + 1] = rr * Math.sin(ph) * Math.sin(th);
      positions[s * 3 + 2] = rr * Math.cos(ph);
    }
    starGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    var starMat = new THREE.PointsMaterial({ color: 0xffffff, size: 0.14, transparent: true, opacity: 0.55 });
    stars = new THREE.Points(starGeo, starMat);
    scene.add(stars);

    clock = new THREE.Clock();
    ready = true;
    resize();
    animate();
  }

  function resize() {
    if (!ready) return;
    var w = wrap.clientWidth, h = wrap.clientHeight;
    if (w === 0 || h === 0) return;
    renderer.setSize(w, h, false);
    var aspect = w / h;
    camera.aspect = aspect;
    // "contain" fit: push the camera back enough that the globe (incl. its
    // glow shell, radius ~1.06) fits inside BOTH width and height, so it
    // never crops on narrow/tall screens -- true on every orientation.
    var fovYrad = camera.fov * Math.PI / 180;
    var sphereR = 1.06;
    var distForHeight = sphereR / Math.tan(fovYrad / 2);
    var distForWidth = sphereR / (Math.tan(fovYrad / 2) * aspect);
    camera.position.z = Math.max(distForHeight, distForWidth) * 1.12;
    camera.updateProjectionMatrix();
  }

  function animate() {
    requestAnimationFrame(animate);
    var dt = Math.min(clock.getDelta(), 0.05);
    var t = clock.getElapsedTime();
    earthGroup.rotation.y += dt * 0.06;
    if (auroraMat) auroraMat.uniforms.uTime.value = t;
    if (cityMat) cityMat.uniforms.uTime.value = t;
    stars.rotation.y += dt * 0.003;
    renderer.render(scene, camera);
  }

  window.addEventListener('resize', resize);
  window.addEventListener('orientationchange', function () { setTimeout(resize, 300); });

  try { initThree(); } catch (e) { console.warn('Cosmic Sanctuary: globe failed to load', e); }

  // ---- Swiss brain line-art: measured once, then drawn on via scroll ----
  var brainPaths = brain.querySelectorAll('path');
  var pathLens = [];
  brainPaths.forEach(function (p) { pathLens.push(p.getTotalLength()); });
  function setBrainDraw(t) {
    brainPaths.forEach(function (p, idx) {
      var len = pathLens[idx];
      p.style.strokeDasharray = len;
      p.style.strokeDashoffset = len * (1 - t);
    });
  }
  setBrainDraw(0);

  // ---- Phase 2 stays hidden (faded, non-interactive) until the story ----
  // ---- actually finishes -- driven directly by scroll progress below, ----
  // ---- not by nested-scroll physics, so it's reliable on touch devices. ----
  var phase2El = null;
  var phase2Revealed = false;
  try {
    phase2El = window.parent.document.querySelector('.st-key-phase2_canvas');
    if (phase2El) {
      phase2El.style.transition = 'opacity 0.9s ease';
      phase2El.style.opacity = '0';
      phase2El.style.pointerEvents = 'none';
    }
  } catch (e) { phase2El = null; }

  function revealPhase2() {
    if (phase2Revealed || !phase2El) return;
    phase2Revealed = true;
    phase2El.style.opacity = '1';
    phase2El.style.pointerEvents = '';
  }

  // ---- scroll-driven progress (fully internal to this component) ----
  function onScroll() {
    var scrollTop = document.documentElement.scrollTop || document.body.scrollTop;
    var max = storyEl.scrollHeight - window.innerHeight;
    var progress = max > 0 ? Math.min(Math.max(scrollTop / max, 0), 1) : 0;

    var scale = 1.0 - progress * 0.72; // never exceeds its inset box: clean margins always
    scale = Math.max(scale, 0.28);
    wrap.style.transform = 'scale(' + scale + ')';

    var crossStart = 0.72, crossEnd = 0.98;
    var cp = (progress - crossStart) / (crossEnd - crossStart);
    cp = Math.min(Math.max(cp, 0), 1);
    canvas.style.opacity = String(1 - cp);
    brain.style.opacity = String(cp);
    setBrainDraw(cp);

    hint.classList.toggle('hidden', progress > 0.05);
    if (progress > 0.9) { revealPhase2(); }
  }
  document.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // ---- text fade-in per section ----
  var lines = document.querySelectorAll('.line');
  if ('IntersectionObserver' in window) {
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting && en.intersectionRatio > 0.5) {
          en.target.classList.add('show');
        } else {
          en.target.classList.remove('show');
        }
      });
    }, { threshold: [0, 0.5, 1] });
    lines.forEach(function (l) { obs.observe(l); });
  } else {
    lines.forEach(function (l) { l.classList.add('show'); });
  }

  // ==========================================================================
  // WEB AUDIO ENTRAINMENT ENGINE
  // 55Hz sub-bass heartbeat anchor + low-pass filtered pink noise breathing
  // sweep. Tempo ramps 82 -> 56 BPM over a 60s linear window once engaged.
  // Started only on an explicit tap (the "Calming tone" toggle), which both
  // respects browser autoplay policy and keeps sound fully opt-in.
  // ==========================================================================
  var audioCtx = null;
  var audioNodes = null;
  var bpmRampStart = null;
  var beatTimer = null;
  var audioEnabled = false;

  function getCurrentBPM() {
    if (!bpmRampStart) return 82;
    var elapsedSec = (performance.now() - bpmRampStart) / 1000;
    var t = Math.min(elapsedSec / 60, 1);
    return 82 + (56 - 82) * t;
  }

  function buildPinkNoiseBuffer(ctx, seconds) {
    var bufferSize = Math.floor(ctx.sampleRate * seconds);
    var buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
    var data = buffer.getChannelData(0);
    var b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0;
    for (var i = 0; i < bufferSize; i++) {
      var white = Math.random() * 2 - 1;
      b0 = 0.99886 * b0 + white * 0.0555179;
      b1 = 0.99332 * b1 + white * 0.0750759;
      b2 = 0.96900 * b2 + white * 0.1538520;
      b3 = 0.86650 * b3 + white * 0.3104856;
      b4 = 0.55000 * b4 + white * 0.5329522;
      b5 = -0.7616 * b5 - white * 0.0168980;
      var pink = b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362;
      b6 = white * 0.115926;
      data[i] = pink * 0.11;
    }
    return buffer;
  }

  function scheduleNextBeat() {
    if (!audioEnabled || !audioCtx || !audioNodes) return;
    var now = audioCtx.currentTime;
    var g = audioNodes.subGain.gain;
    g.cancelScheduledValues(now);
    g.setValueAtTime(0.0001, now);
    g.linearRampToValueAtTime(0.34, now + 0.09);
    g.linearRampToValueAtTime(0.0001, now + 0.42);

    var bpm = getCurrentBPM();
    beatTimer = setTimeout(scheduleNextBeat, (60 / bpm) * 1000);
  }

  function startAudioEngine() {
    if (audioCtx) {
      if (audioCtx.state === 'suspended') { audioCtx.resume(); }
    } else {
      var Ctx = window.AudioContext || window.webkitAudioContext;
      if (!Ctx) return;
      audioCtx = new Ctx();

      var master = audioCtx.createGain();
      master.gain.value = 0.0001;
      master.connect(audioCtx.destination);
      master.gain.linearRampToValueAtTime(0.5, audioCtx.currentTime + 1.5);

      // sub-bass heartbeat anchor
      var sub = audioCtx.createOscillator();
      sub.type = 'sine';
      sub.frequency.value = 55;
      var subFilter = audioCtx.createBiquadFilter();
      subFilter.type = 'lowpass';
      subFilter.frequency.value = 120;
      var subGain = audioCtx.createGain();
      subGain.gain.value = 0.0001;
      sub.connect(subFilter);
      subFilter.connect(subGain);
      subGain.connect(master);
      sub.start();

      // filtered pink-noise breathing sweep
      var noise = audioCtx.createBufferSource();
      noise.buffer = buildPinkNoiseBuffer(audioCtx, 4);
      noise.loop = true;
      var noiseFilter = audioCtx.createBiquadFilter();
      noiseFilter.type = 'lowpass';
      noiseFilter.frequency.value = 420;
      noiseFilter.Q.value = 0.7;
      var noiseGain = audioCtx.createGain();
      noiseGain.gain.value = 0.16;

      var lfo = audioCtx.createOscillator();
      lfo.type = 'sine';
      lfo.frequency.value = 0.17; // ~6s breathing cycle
      var lfoGain = audioCtx.createGain();
      lfoGain.gain.value = 220;
      lfo.connect(lfoGain);
      lfoGain.connect(noiseFilter.frequency);

      noise.connect(noiseFilter);
      noiseFilter.connect(noiseGain);
      noiseGain.connect(master);
      noise.start();
      lfo.start();

      audioNodes = { master: master, subGain: subGain };
    }

    audioEnabled = true;
    bpmRampStart = bpmRampStart || performance.now();
    scheduleNextBeat();
  }

  function stopAudioEngine() {
    audioEnabled = false;
    if (beatTimer) { clearTimeout(beatTimer); beatTimer = null; }
    if (audioNodes && audioCtx) {
      var now = audioCtx.currentTime;
      audioNodes.master.gain.cancelScheduledValues(now);
      audioNodes.master.gain.setValueAtTime(audioNodes.master.gain.value, now);
      audioNodes.master.gain.linearRampToValueAtTime(0.0001, now + 0.8);
    }
  }

  var soundToggle = document.getElementById('soundToggle');

  function setAudioUIState(enabled) {
    if (!soundToggle) return;
    soundToggle.classList.toggle('on', enabled);
    var lbl = soundToggle.querySelector('.label');
    if (lbl) { lbl.textContent = enabled ? 'Calming tone: on' : 'Calming tone'; }
  }

  if (soundToggle) {
    soundToggle.addEventListener('click', function () {
      if (!audioEnabled) {
        try { startAudioEngine(); } catch (e) { console.warn('Cosmic Sanctuary: audio unavailable', e); return; }
        setAudioUIState(true);
      } else {
        stopAudioEngine();
        setAudioUIState(false);
      }
    });
  }

  // ---- opening permission gate: ask once, up front, before anything else ----
  var soundGate = document.getElementById('soundGate');
  var soundGateYes = document.getElementById('soundGateYes');
  var soundGateNo = document.getElementById('soundGateNo');
  function dismissGate() {
    if (soundGate) { soundGate.classList.add('hidden'); }
  }
  if (soundGateYes) {
    soundGateYes.addEventListener('click', function () {
      try { startAudioEngine(); setAudioUIState(true); } catch (e) { console.warn('Cosmic Sanctuary: audio unavailable', e); }
      dismissGate();
    });
  }
  if (soundGateNo) {
    soundGateNo.addEventListener('click', dismissGate);
  }
})();
</script>
</body>
</html>
"""

components.html(SCROLL_PORTAL_HTML, height=860, scrolling=True)


# ============================================================================
# 4. PYDANTIC CONTRACT + GEMINI CALL
# ============================================================================

class SanctuaryPeaceResponse(BaseModel):
    uplifting_environmental_phrase: str = Field(
        description="A short, genuinely mind-expanding sentence built around one real, well-established "
                    "scientific or environmental fact (astronomy, ecology, physics, or biology) -- true "
                    "and verifiable, never invented or exaggerated -- that connects the user's specific "
                    "worry to the vast, shared scale of the earth and cosmos, gently lifting their "
                    "perspective."
    )
    music_mix_profile: str = Field(
        description="Specific ambient music modifiers for Nolasko's tracks based on their state "
                    "(e.g., Tempo: 55BPM, Instrument: Ambient Acoustic Guitar, Low-pass filter active)."
    )
    micro_peace_action: str = Field(
        description="One tiny, concrete, completely zero-pressure physical action to take right "
                    "now to find grounding."
    )
    takeaway_actions: List[str] = Field(
        default_factory=list,
        description="Two to three additional tiny, zero-pressure things the person could do "
                    "afterward to keep the sense of peace. Each a short phrase, not a paragraph."
    )


SYSTEM_INSTRUCTION = (
    "You are the quiet intelligence behind The Cosmic Sanctuary, a mindfulness space. "
    "A person has just written down something they are carrying, along with how loaded their "
    "day feels. Respond only as data matching the required schema. Your tone is therapeutic, "
    "spacious, and gently scientifically grounded -- never clinical, never overly mystical, "
    "never dismissive. Explicitly but softly frame planet Earth as one shared, borderless "
    "vehicle carrying everyone through space together: their worry is real, and it is also "
    "happening on the same small, unified world as everyone else's. The uplifting phrase must be "
    "built around one real, well-established scientific or environmental fact -- something true "
    "and verifiable (astronomy, ecology, physics, biology), never invented or exaggerated -- stated "
    "so it is genuinely mind-expanding and perspective-shifting for someone in a hard moment. Do not "
    "diagnose, do not give clinical or medical advice, do not mention therapy or medication. Keep "
    "every field short -- a phrase or a sentence, never an essay."
)


def _resolve_api_key() -> Optional[str]:
    key = None
    try:
        key = st.secrets.get("GOOGLE_API_KEY")
    except Exception:
        key = None
    if not key:
        key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not key:
        key = st.session_state.get("manual_api_key")
    return key or None


def generate_sanctuary_response(
    user_text: str, emotional_state: str
) -> Tuple[Optional[SanctuaryPeaceResponse], Optional[str]]:
    """Calls Gemini 3.6 Flash and returns (result, error). error == 'missing_key' means
    no API key has been configured yet."""
    if not GENAI_AVAILABLE:
        return None, "The google-genai package isn't installed. Run: pip install google-genai"

    api_key = _resolve_api_key()
    if not api_key:
        return None, "missing_key"

    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        return None, "Couldn't connect to Gemini (" + str(e) + ")."

    prompt = (
        "Emotional load right now: " + emotional_state + ".\n\n"
        "What they're carrying, in their own words:\n"
        "\"\"\"\n" + user_text.strip() + "\n\"\"\"\n\n"
        "Respond strictly in the required schema."
    )

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=SanctuaryPeaceResponse,
                temperature=0.9,
            ),
        )
    except Exception as e:
        return None, "The cosmos didn't answer just now (" + str(e) + "). Please try again in a moment."

    parsed = getattr(response, "parsed", None)
    if isinstance(parsed, SanctuaryPeaceResponse):
        return parsed, None

    try:
        data = json.loads(response.text)
        return SanctuaryPeaceResponse(**data), None
    except Exception as e:
        return None, "Received an unreadable response from the model (" + str(e) + ")."


# ============================================================================
# 5. SESSION STATE
# ============================================================================

for _key, _default in [
    ("sanctuary_result", None),
    ("just_generated", False),
    ("moment_recorded_at", ""),
    ("moment_label_saved", ""),
    ("manual_api_key", None),
]:
    if _key not in st.session_state:
        st.session_state[_key] = _default


# ============================================================================
# 6. PHASE 2 — THE CANVAS
# ============================================================================

with st.container(key="phase2_canvas"):
    st.markdown('<div class="phase2-eyebrow">Phase II</div>', unsafe_allow_html=True)
    st.markdown('<div class="phase2-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sanctuary-heading">The Canvas</div>', unsafe_allow_html=True)
    st.markdown('<div class="sanctuary-sub">A quiet place to set something down.</div>', unsafe_allow_html=True)

    emotional_state = st.select_slider(
        "How heavy does today feel?",
        options=["Calm", "Busy", "Overwhelmed", "Exhausted"],
        value="Busy",
    )

    st.markdown(
        '<p class="prompt-text">Leave whatever you are carrying right here.</p>',
        unsafe_allow_html=True,
    )
    user_text = st.text_area(
        "burden",
        height=190,
        placeholder="Write freely. No one is grading this.",
        label_visibility="collapsed",
        key="burden_text",
    )

    col_a, col_b = st.columns([3, 2])
    with col_a:
        moment_label = st.text_input(
            "Name this moment (optional)",
            placeholder="e.g. Tuesday evening, after work",
            key="moment_label_input",
        )
    with col_b:
        st.markdown(
            '<div style="padding-top:1.9rem;text-align:right;">'
            '<span class="moment-chip">' + html.escape(datetime.now().strftime("%A \u00b7 %H:%M")) + '</span>'
            '</div>',
            unsafe_allow_html=True,
        )

    if not _resolve_api_key():
        with st.expander("Connect your Gemini API key"):
            key_in = st.text_input("Gemini API key", type="password", key="manual_api_key_input")
            if key_in:
                st.session_state["manual_api_key"] = key_in
                st.rerun()

    submitted = st.button("Surrender to the Cosmos", use_container_width=True)


# ============================================================================
# 6b. THE SWISS TYPOGRAPHIC SHATTER RITUAL
#    A tiny headless component that (same-origin, defensively) finds the
#    native button above and the textarea's live text, replaces the button
#    with a matching custom one, and on click: hides the textarea, renders
#    its text as thin word-wrapped horizontal splinters, floats them upward
#    while fading them out over 2.5s -- then, and only then, programmatically
#    clicks the real (hidden) Streamlit button to fire the actual rerun and
#    the Gemini request. If any lookup fails, the native button is left
#    fully visible and working, untouched.
# ============================================================================

SHATTER_RITUAL_HTML = """
<!DOCTYPE html>
<html><head><meta charset="utf-8" /></head>
<body>
<script>
(function () {
  var BTN_LABEL = 'Surrender to the Cosmos';
  var TA_PLACEHOLDER = 'Write freely. No one is grading this.';
  var attempts = 0;

  function trySetup() {
    attempts++;
    var pdoc;
    try { pdoc = window.parent.document; } catch (e) { return; }
    if (!pdoc || pdoc.getElementById('cosmicSurrenderBtn')) { return; }

    var realBtn = null;
    var btns = pdoc.querySelectorAll('button');
    for (var i = 0; i < btns.length; i++) {
      if (btns[i].textContent && btns[i].textContent.trim() === BTN_LABEL) { realBtn = btns[i]; break; }
    }
    var textarea = pdoc.querySelector('textarea[placeholder="' + TA_PLACEHOLDER + '"]');

    if (!realBtn || !textarea) {
      if (attempts < 20) { setTimeout(trySetup, 150); }
      return;
    }

    try {
      setupCustomButton(pdoc, realBtn, textarea);
    } catch (e) {
      console.warn('Cosmic Sanctuary: custom ritual button unavailable, using default.', e);
      realBtn.style.display = '';
    }
  }

  function setupCustomButton(pdoc, realBtn, textarea) {
    var customBtn = pdoc.createElement('button');
    customBtn.type = 'button';
    customBtn.id = 'cosmicSurrenderBtn';
    customBtn.textContent = 'Surrender to the Cosmos';
    customBtn.setAttribute('style', [
      'background: linear-gradient(135deg, #4F83F5, #7aa2ff)',
      'color: #08080a',
      'border: none',
      'border-radius: 999px',
      'padding: 0.85rem 0',
      'width: 100%',
      'font-weight: 600',
      'font-size: 1rem',
      'font-family: Inter, -apple-system, sans-serif',
      'letter-spacing: 0.02em',
      'margin-top: 1.5rem',
      'cursor: pointer',
      'transition: transform 0.2s ease, box-shadow 0.2s ease, opacity 0.3s ease'
    ].join(';'));

    realBtn.insertAdjacentElement('afterend', customBtn);
    realBtn.style.display = 'none';

    customBtn.addEventListener('mouseenter', function () {
      customBtn.style.transform = 'translateY(-1px)';
      customBtn.style.boxShadow = '0 10px 26px #4F83F544';
    });
    customBtn.addEventListener('mouseleave', function () {
      customBtn.style.transform = '';
      customBtn.style.boxShadow = '';
    });

    var ritualRunning = false;
    customBtn.addEventListener('click', function () {
      if (ritualRunning) { return; }
      var liveText = textarea.value || '';
      if (!liveText.trim()) { realBtn.click(); return; }

      ritualRunning = true;
      customBtn.disabled = true;
      customBtn.style.opacity = '0.55';
      customBtn.style.cursor = 'default';

      runShatterRitual(pdoc, textarea, liveText, function () {
        ritualRunning = false;
        realBtn.click();
      });
    });
  }

  function runShatterRitual(pdoc, textarea, text, onComplete) {
    var parentWin = pdoc.defaultView || window.parent;
    var rect = textarea.getBoundingClientRect();
    var cs = parentWin.getComputedStyle(textarea);

    var overlay = pdoc.createElement('div');
    overlay.id = 'cosmicShatterOverlay';
    overlay.setAttribute('style', [
      'position: fixed',
      'left:' + rect.left + 'px',
      'top:' + rect.top + 'px',
      'width:' + rect.width + 'px',
      'height:' + rect.height + 'px',
      'overflow: hidden',
      'z-index: 999999',
      'pointer-events: none',
      'background:' + cs.backgroundColor,
      'border-radius:' + cs.borderRadius
    ].join(';'));
    pdoc.body.appendChild(overlay);
    textarea.style.opacity = '0';

    var fontSize = parseFloat(cs.fontSize) || 16;
    var lineHeight = parseFloat(cs.lineHeight);
    if (!lineHeight || isNaN(lineHeight)) { lineHeight = fontSize * 1.4; }
    var fontSpec = cs.fontStyle + ' ' + cs.fontWeight + ' ' + fontSize + 'px ' + cs.fontFamily;
    var padLeft = parseFloat(cs.paddingLeft) || 0;
    var padRight = parseFloat(cs.paddingRight) || 0;
    var padTop = parseFloat(cs.paddingTop) || 0;
    var innerWidth = rect.width - padLeft - padRight;

    var measCanvas = pdoc.createElement('canvas');
    var ctx2d = measCanvas.getContext('2d');
    ctx2d.font = fontSpec;

    var rawLines = text.split(String.fromCharCode(10));
    var lines = [];
    rawLines.forEach(function (raw) {
      if (raw === '') { lines.push(''); return; }
      var words = raw.split(' ');
      var current = '';
      words.forEach(function (word) {
        var trial = current ? (current + ' ' + word) : word;
        if (ctx2d.measureText(trial).width > innerWidth && current) {
          lines.push(current);
          current = word;
        } else {
          current = trial;
        }
      });
      if (current) { lines.push(current); }
    });
    if (lines.length === 0) { lines.push(text); }

    // Each line is cut into thin horizontal splinters (clip-path bands of
    // the same text, stacked), so it genuinely shatters and dissolves --
    // not just fades -- each splinter drifting on its own gentle wind vector.
    var SLICES = 3;
    var pieces = [];
    lines.forEach(function (lineText, idx) {
      var lineTop = padTop + idx * lineHeight;
      var bandH = lineHeight / SLICES;
      for (var s = 0; s < SLICES; s++) {
        var clipTop = s * bandH;
        var clipBottom = (SLICES - s - 1) * bandH;
        var piece = pdoc.createElement('div');
        piece.textContent = lineText;
        piece.setAttribute('style', [
          'position:absolute',
          'left:' + padLeft + 'px',
          'top:' + lineTop + 'px',
          'white-space: nowrap',
          'font:' + fontSpec,
          'color:' + cs.color,
          'opacity: 1',
          'transform: translate(0px, 0px)',
          'filter: blur(0px)',
          'clip-path: inset(' + clipTop + 'px 0 ' + clipBottom + 'px 0)',
          '-webkit-clip-path: inset(' + clipTop + 'px 0 ' + clipBottom + 'px 0)',
          'transition: transform 2.5s cubic-bezier(.16,1,.3,1), opacity 2.3s ease, filter 2.3s ease',
          'transition-delay:' + (idx * 55 + s * 30) + 'ms',
          'will-change: transform, opacity, filter'
        ].join(';'));
        overlay.appendChild(piece);
        pieces.push({
          el: piece,
          driftX: (Math.random() * 34 - 17),
          riseY: 24 + Math.random() * 34
        });
      }
    });

    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        pieces.forEach(function (p) {
          p.el.style.transform = 'translate(' + p.driftX.toFixed(1) + 'px, -' + p.riseY.toFixed(1) + 'px)';
          p.el.style.opacity = '0';
          p.el.style.filter = 'blur(6px)';
        });
      });
    });

    var maxDelay = (lines.length - 1) * 55 + (SLICES - 1) * 30;
    var totalWait = 2500 + maxDelay + 150;
    setTimeout(function () {
      overlay.remove();
      textarea.style.opacity = '';
      onComplete();
    }, totalWait);
  }

  trySetup();
})();
</script>
</body></html>
"""

components.html(SHATTER_RITUAL_HTML, height=1, scrolling=False)


if submitted:
    if not user_text or not user_text.strip():
        st.warning("Write even a few words before you let go.")
    else:
        with st.spinner("Carrying your words out past the atmosphere..."):
            result, err = generate_sanctuary_response(user_text, emotional_state)
        if err == "missing_key":
            st.error("Add a Gemini API key above to open the sanctuary.")
        elif err:
            st.error(err)
        else:
            st.session_state["sanctuary_result"] = result
            st.session_state["just_generated"] = True
            st.session_state["moment_recorded_at"] = datetime.now().strftime("%A, %B %d \u2014 %H:%M")
            st.session_state["moment_label_saved"] = moment_label.strip() if moment_label else ""


# ============================================================================
# 7. SEQUENTIAL AUDIO-VISUAL REVEAL ("a slow, deep breath")
# ============================================================================

if st.session_state.get("sanctuary_result"):
    r: SanctuaryPeaceResponse = st.session_state["sanctuary_result"]
    reveal_slowly = st.session_state.get("just_generated", False)

    if st.session_state.get("moment_label_saved"):
        st.markdown(
            '<div style="text-align:center;margin-top:1.8rem;">'
            '<span class="moment-chip">'
            + html.escape(st.session_state["moment_label_saved"])
            + " \u2014 "
            + html.escape(st.session_state.get("moment_recorded_at", ""))
            + "</span></div>",
            unsafe_allow_html=True,
        )

    ph_music = st.empty()
    ph_phrase = st.empty()
    ph_action = st.empty()

    ph_music.markdown(
        '<div class="music-chip">\U0001F3A7 Now shaping your ambient mix &mdash; '
        + html.escape(r.music_mix_profile) + "</div>",
        unsafe_allow_html=True,
    )
    if reveal_slowly:
        time.sleep(1.2)

    ph_phrase.markdown(
        '<div class="phrase-box">' + html.escape(r.uplifting_environmental_phrase) + "</div>",
        unsafe_allow_html=True,
    )
    if reveal_slowly:
        time.sleep(1.2)

    actions_html = '<div class="action-box"><h4>To take with you</h4>'
    actions_html += '<div class="action-item">' + html.escape(r.micro_peace_action) + "</div>"
    for action in (r.takeaway_actions or []):
        actions_html += '<div class="action-item">' + html.escape(action) + "</div>"
    actions_html += "</div>"
    ph_action.markdown(actions_html, unsafe_allow_html=True)

    if reveal_slowly:
        st.session_state["just_generated"] = False
