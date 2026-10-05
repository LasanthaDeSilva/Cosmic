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
           in one real, verifiable scientific or environmental fact. Gemini
           also returns a structured, non-clinical PsychologicalProfile of
           the writing (never shown to the person), which this file's own
           deterministic build_music_profile() turns into a MusicProfile --
           tempo, harmonic complexity, density, brightness, and so on -- that
           a single persistent, multi-layer CosmicAudioEngine (foundation
           pad, motif, texture, sub-bass, and spatial layers) renders and
           then smoothly crossfades toward on every new submission, with no
           page refresh and no duplicate audio engines. See the comment
           above build_music_profile() for how that mapping is reasoned
           through, and the comment above CosmicAudioEngine in
           AMBIENT_MIX_PLAYER_TEMPLATE for how the engine itself stays a
           singleton across Streamlit's reruns.

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
and click the native "Fade into the Vastness" button on your behalf. Every
one of those lookups is wrapped in a defensive fallback: if anything about
your Streamlit version changes and an element can't be found, the code
leaves the native elements fully visible and functional rather than
breaking the app.
"""

import os
import re
import html
import json
import math
import time
import hashlib
import concurrent.futures
from datetime import datetime
from typing import List, Optional, Tuple

import streamlit as st
import streamlit.components.v1 as components
from pydantic import BaseModel, Field, model_validator

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
    /* "The Canvas" -- flat, hairline-ruled, no card/gradient: Swiss, not SaaS.
       Hidden and non-interactive from the very first paint -- straight from
       this base stylesheet, before the scroll portal's script has even had
       a chance to run -- so there is never a flash of visible content on
       load. The scroll portal component is the only thing that ever turns
       this back on (via inline style, which wins over this rule), once
       you've actually scrolled all the way through Phase 1. */
    .st-key-phase2_canvas {
        border-top: 1px solid #232329;
        padding: 2.8rem 0.2rem 0.5rem 0.2rem;
        margin-top: 0.6rem;
        opacity: 0;
        pointer-events: none;
        transition: opacity 0.9s ease;
    }
    .st-key-phase2_canvas .sanctuary-heading { margin-top: 0; }

    /* Streamlit widgets restyled to match the sanctuary */
    .stTextArea textarea {
        background: #0c0c0f !important;
        border: 1px solid #232329 !important;
        border-radius: 2px !important;
        color: #e5e5ea !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 1rem !important;
        padding: 1.1rem !important;
        transition: opacity 0.4s ease !important;
    }
    .stTextArea textarea:focus {
        border-color: #4F83F5 !important;
        box-shadow: none !important;
    }
    .stTextInput input {
        background: #0c0c0f !important;
        border: 1px solid #232329 !important;
        border-radius: 2px !important;
        color: #e5e5ea !important;
    }
    .stTextInput input:focus {
        border-color: #4F83F5 !important;
        box-shadow: none !important;
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
        border-radius: 2px !important;
        box-shadow: none !important;
    }
    div[data-testid="stTickBar"] { display: none; }
    .stButton button {
        background: #4F83F5;
        color: #08080a;
        border: none;
        border-radius: 2px;
        padding: 0.85rem 0;
        width: 100%;
        font-weight: 600;
        font-size: 0.92rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-top: 1.6rem;
        transition: background 0.2s ease;
    }
    .stButton button:hover {
        background: #6a9aff;
        color: #08080a;
    }

    .moment-chip {
        display: inline-block;
        font-size: 0.76rem;
        color: #9a9aa4;
        border: 1px solid #232329;
        padding: 0.3rem 0.7rem;
        border-radius: 2px;
        letter-spacing: 0.02em;
    }
    .result-index {
        font-size: 0.68rem;
        letter-spacing: 0.22em;
        text-transform: uppercase;
        color: #6f7a94;
        font-weight: 500;
        margin: 0 0 0.9rem 0;
    }
    .music-panel {
        border-top: 1px solid #1e1e24;
        border-bottom: 1px solid #1e1e24;
        padding: 1.3rem 0;
        margin-top: 2.6rem;
        animation: fadeUp 0.9s ease;
    }
    .music-readout {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.92rem;
        color: #c7d2f0;
        letter-spacing: 0.01em;
        line-height: 1.6;
        font-weight: 400;
    }
    .phrase-panel {
        padding: 2.6rem 0 2.2rem 0;
        margin-top: 1.8rem;
        text-align: center;
        animation: fadeUp 1s ease;
    }
    .phrase-rule {
        width: 34px;
        height: 1px;
        background: #4F83F5;
        margin: 0 auto 1.8rem auto;
    }
    .phrase-text {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 400;
        font-size: clamp(1.2rem, 3.4vw, 1.6rem);
        line-height: 1.65;
        color: #f2f3fb;
        letter-spacing: -0.005em;
    }
    .actions-panel {
        margin-top: 1.6rem;
        padding-top: 2rem;
        border-top: 1px solid #1e1e24;
        animation: fadeUp 1.1s ease;
    }
    .action-row {
        display: flex;
        gap: 1.1rem;
        padding: 1.05rem 0;
        border-bottom: 1px solid #17171c;
        align-items: baseline;
    }
    .action-row:last-child { border-bottom: none; }
    .action-num {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.78rem;
        color: #4F83F5;
        min-width: 1.6rem;
        flex-shrink: 0;
    }
    .action-text {
        font-size: 0.96rem;
        color: #dcdce4;
        line-height: 1.55;
        font-weight: 300;
    }
    .cosmic-loader {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1.1rem;
        padding: 2.6rem 0 1.2rem 0;
    }
    .cosmic-loader-dot {
        width: 9px; height: 9px;
        border-radius: 50%;
        background: #4F83F5;
        animation: breathe 2.4s ease-in-out infinite;
    }
    .cosmic-loader p {
        font-size: 0.72rem;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: #6f6f79;
        font-weight: 400;
        margin: 0;
    }
    @keyframes breathe {
        0%, 100% { transform: scale(0.7); opacity: 0.35; box-shadow: 0 0 0 0 #4F83F540; }
        50% { transform: scale(1.25); opacity: 1; box-shadow: 0 0 0 9px #4F83F500; }
    }
    @keyframes fadeUp {
        from {opacity: 0; transform: translateY(10px);}
        to {opacity: 1; transform: translateY(0);}
    }

    .sanctuary-footer {
        margin-top: 3.4rem;
        padding: 1.8rem 0.5rem 0.4rem 0.5rem;
        border-top: 1px solid #1a1a20;
        text-align: center;
    }
    .sanctuary-footer-desc {
        font-size: 0.78rem;
        color: #6f6f79;
        font-weight: 300;
        line-height: 1.6;
        max-width: 420px;
        margin: 0 auto 0.7rem auto;
    }
    .sanctuary-footer-credit {
        font-size: 0.72rem;
        color: #4a4a52;
        letter-spacing: 0.02em;
        font-weight: 400;
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
    inset: 0;
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

  // ---- Phase 2 is already hidden and non-interactive from the base CSS ----
  // ---- itself (see .st-key-phase2_canvas), so there is nothing for this ----
  // ---- script to do on load except find the container and, eventually, ----
  // ---- REVEAL it -- either because you already earned that in an earlier ----
  // ---- run this session (persisted in the parent window's sessionStorage, ----
  // ---- so a Streamlit rerun can't re-hide something you already unlocked), ----
  // ---- or because you've just scrolled far enough down the portal. The ----
  // ---- lookup itself combines an immediate check, a MutationObserver ----
  // ---- watching the parent document for the container mounting, and an ----
  // ---- indefinite polling fallback -- so it is found reliably no matter ----
  // ---- when Streamlit actually renders it relative to this script. ----
  var phase2El = null;
  var phase2Revealed = false;
  try { phase2Revealed = window.parent.sessionStorage.getItem('cosmicPhase2Seen') === '1'; } catch (e) {}

  function showPhase2(el) {
    el.style.opacity = '1';
    // Explicit 'auto', not '' -- clearing the inline value would just fall
    // back to the base stylesheet's pointer-events:none (the default-hidden
    // rule), silently leaving every tap and click on Phase 2 dead even
    // though it's visibly on screen.
    el.style.pointerEvents = 'auto';
  }

  function tryFindPhase2El() {
    if (phase2El) { return phase2El; }
    var el = null;
    try { el = window.parent.document.querySelector('.st-key-phase2_canvas'); } catch (e) {}
    if (el) {
      phase2El = el;
      if (phase2Revealed) { showPhase2(phase2El); }
    }
    return phase2El;
  }
  tryFindPhase2El();

  try {
    if (!phase2El && window.parent && window.parent.document) {
      var ParentObserver = window.parent.MutationObserver || window.MutationObserver;
      if (ParentObserver) {
        var phase2Observer = new ParentObserver(function () {
          if (tryFindPhase2El() && phase2Observer) {
            phase2Observer.disconnect();
            phase2Observer = null;
          }
        });
        phase2Observer.observe(window.parent.document.body, { childList: true, subtree: true });
      }
    }
  } catch (e) {}

  // Belt-and-braces polling in case the observer can't attach (cross-origin
  // edge cases, older browsers): quick at first, then a slow heartbeat that
  // never gives up, rather than a hard timeout that stops looking.
  (function pollPhase2El(attempt) {
    if (tryFindPhase2El()) { return; }
    setTimeout(function () { pollPhase2El(attempt + 1); }, attempt < 40 ? 200 : 2000);
  })(0);

  function revealPhase2() {
    if (phase2Revealed) { return; }
    phase2Revealed = true;
    try { window.parent.sessionStorage.setItem('cosmicPhase2Seen', '1'); } catch (e) {}
    if (tryFindPhase2El()) { showPhase2(phase2El); }
  }

  // ---- scroll-driven progress (fully internal to this component) ----
  // Nothing about scroll range or viewport size is ever cached: scrollTop,
  // the story's scrollHeight, and the viewport height are all re-read from
  // the live DOM on every single animation frame, and progress is derived
  // fresh from them each time. That makes this self-correcting by
  // construction across any screen size or orientation, and immune to the
  // startup race where the portal's iframe is still being resized to match
  // the real viewport (see syncFrameHeight above) at the moment this script
  // first runs -- a one-time cached measurement taken at that instant could
  // freeze at a stale (even zero) value forever; reading fresh every frame
  // means it simply catches up the moment the real layout settles, no
  // matter when that happens. Driving this off requestAnimationFrame rather
  // than the 'scroll' event also means it doesn't depend on scroll events
  // firing reliably at all (some touch/inertial scrolling can be sparse).
  var REVEAL_THRESHOLD = 0.82; // within the requested 80-85% range
  var rawProgress = 0;
  var shownProgress = 0;

  function readRawProgress() {
    var scrollEl = document.scrollingElement || document.documentElement;
    var scrollTop = scrollEl.scrollTop || document.body.scrollTop || 0;
    var max = Math.max(storyEl.scrollHeight - window.innerHeight, 0);
    return max > 0 ? Math.min(Math.max(scrollTop / max, 0), 1) : 0;
  }

  function paintMorph(progress) {
    var scale = 1.0 - progress * 0.72; // never exceeds its inset box: clean margins always
    scale = Math.max(scale, 0.28);
    wrap.style.transform = 'scale(' + scale + ')';

    // A pure function of the (damped) scroll position -- no memory, no
    // one-way locks -- so it paints the same transform forward and in
    // reverse as you scroll up or down. A blur that peaks mid-transition
    // (instead of a flat cross-fade) hides the seam between the two
    // renderings, so the globe reads as dissolving into the brain -- and,
    // in reverse, the brain reads as dissolving back into the globe --
    // rather than one popping in after the other vanishes.
    // Starts once "Every breath we take is shared" (the third line) has had
    // its own moment and is on its way out, rather than dissolving under it.
    var crossStart = 0.72, crossEnd = 0.79; // still finishes with room before Phase 2 unlocks
    var cp = (progress - crossStart) / (crossEnd - crossStart);
    cp = Math.min(Math.max(cp, 0), 1);
    var morphBlur = (1 - Math.abs(cp - 0.5) * 2) * 9; // 0 at the ends, peaks at the midpoint
    canvas.style.opacity = String(1 - cp);
    canvas.style.filter = 'blur(' + morphBlur.toFixed(1) + 'px)';
    brain.style.opacity = String(cp);
    brain.style.filter = 'blur(' + morphBlur.toFixed(1) + 'px) drop-shadow(0 0 18px rgba(79,131,245,0.28))';
    setBrainDraw(cp);

    hint.classList.toggle('hidden', progress > 0.05);
  }

  function morphTick() {
    requestAnimationFrame(morphTick);
    rawProgress = readRawProgress();
    // Checked off the raw, un-damped value so it unlocks the instant you've
    // actually scrolled far enough, and stays untouched if you reverse back
    // up before reaching it.
    if (rawProgress > REVEAL_THRESHOLD) { revealPhase2(); }

    // Critically-damped follow rather than painting rawProgress directly:
    // smooths out the uneven bursts of scroll input a trackpad flick or a
    // fast mouse wheel produce -- in either direction -- without adding
    // perceptible lag.
    shownProgress += (rawProgress - shownProgress) * 0.22;
    if (Math.abs(rawProgress - shownProgress) < 0.0008) { shownProgress = rawProgress; }
    paintMorph(shownProgress);
  }
  // Paint the real starting state synchronously (no one-frame flash of
  // default styles, and no easing-up-from-zero if the page happens to
  // mount already scrolled), then hand off to the continuous rAF loop.
  rawProgress = readRawProgress();
  shownProgress = rawProgress;
  paintMorph(shownProgress);
  if (rawProgress > REVEAL_THRESHOLD) { revealPhase2(); }
  morphTick();

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
  // 55Hz sub-bass heartbeat anchor (soft exponential swell, not a thump) +
  // low-pass filtered pink noise, its cutoff breathing at ~5.5 cycles/min --
  // a real, evidence-based "coherent breathing" pace used in HRV
  // biofeedback -- plus a warm, quiet two-note pad drifting gently across
  // the stereo field for a softer, more human warmth under it all. Tempo
  // ramps 82 -> 56 BPM over a 60s linear window once engaged. Started only
  // on an explicit tap, which both respects browser autoplay policy and
  // keeps sound fully opt-in.
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
    g.exponentialRampToValueAtTime(0.3, now + 0.12);
    g.exponentialRampToValueAtTime(0.0001, now + 0.55);

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
      master.gain.linearRampToValueAtTime(0.46, audioCtx.currentTime + 1.5);

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
      noiseFilter.frequency.value = 380;
      noiseFilter.Q.value = 0.6;
      var noiseGain = audioCtx.createGain();
      noiseGain.gain.value = 0.13;

      var lfo = audioCtx.createOscillator();
      lfo.type = 'sine';
      lfo.frequency.value = 0.092; // ~10.9s cycle -- ~5.5 breaths/min, a real calming pace
      var lfoGain = audioCtx.createGain();
      lfoGain.gain.value = 200;
      lfo.connect(lfoGain);
      lfoGain.connect(noiseFilter.frequency);

      noise.connect(noiseFilter);
      noiseFilter.connect(noiseGain);
      noiseGain.connect(master);
      noise.start();
      lfo.start();

      // warm pad -- two quiet sines a fifth apart, drifting gently across
      // the stereo field, for a soft human warmth under the drone and noise
      var padGain = audioCtx.createGain();
      padGain.gain.value = 0.05;
      var pad1 = audioCtx.createOscillator();
      pad1.type = 'sine';
      pad1.frequency.value = 110; // A2
      var pad2 = audioCtx.createOscillator();
      pad2.type = 'sine';
      pad2.frequency.value = 164.81; // E3 -- a fifth above: open, restful interval
      var padFilter = audioCtx.createBiquadFilter();
      padFilter.type = 'lowpass';
      padFilter.frequency.value = 480;
      pad1.connect(padFilter);
      pad2.connect(padFilter);
      padFilter.connect(padGain);

      if (audioCtx.createStereoPanner) {
        var padPanner = audioCtx.createStereoPanner();
        padGain.connect(padPanner);
        padPanner.connect(master);
        var panLfo = audioCtx.createOscillator();
        panLfo.type = 'sine';
        panLfo.frequency.value = 0.05;
        var panLfoGain = audioCtx.createGain();
        panLfoGain.gain.value = 0.55;
        panLfo.connect(panLfoGain);
        panLfoGain.connect(padPanner.pan);
        panLfo.start();
      } else {
        padGain.connect(master);
      }
      pad1.start();
      pad2.start();

      audioNodes = { master: master, subGain: subGain };
    }

    audioEnabled = true;
    bpmRampStart = bpmRampStart || performance.now();
    scheduleNextBeat();
    try { window.parent.sessionStorage.setItem('cosmicAudioOn', '1'); } catch (e) {}
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
    try { window.parent.sessionStorage.setItem('cosmicAudioOn', '0'); } catch (e) {}
  }

  // ---- release chime: an audible change layered over the ambient bed the ----
  // ---- instant the written thought is let go, marking the moment rather ----
  // ---- than leaving the ambience to simply continue unchanged. Only plays ----
  // ---- if the ambient tone is already on (sound stays fully opt-in); if it ----
  // ---- isn't, this quietly does nothing. ----
  function playReleaseChime() {
    if (!audioEnabled || !audioCtx || !audioNodes) return;
    try {
      var now = audioCtx.currentTime;

      // a soft, clearly audible three-note rising chime (an open, resolving
      // triad) -- each note with a quick attack and a slow 3s decay
      var chimeFreqs = [392.00, 493.88, 587.33]; // G4, B4, D5
      chimeFreqs.forEach(function (freq, idx) {
        var osc = audioCtx.createOscillator();
        osc.type = 'sine';
        osc.frequency.value = freq;
        var g = audioCtx.createGain();
        g.gain.value = 0.0001;
        var startAt = now + idx * 0.14;
        g.gain.setValueAtTime(0.0001, startAt);
        g.gain.exponentialRampToValueAtTime(0.3, startAt + 0.05);
        g.gain.exponentialRampToValueAtTime(0.0001, startAt + 3.0);
        osc.connect(g);
        g.connect(audioNodes.master);
        osc.start(startAt);
        osc.stop(startAt + 3.2);
      });

      // a brief, unmistakable swell of the whole ambient bed under the
      // chime, then an easy settle back to its resting level
      var mg = audioNodes.master.gain;
      mg.cancelScheduledValues(now);
      mg.setValueAtTime(mg.value, now);
      mg.linearRampToValueAtTime(0.62, now + 0.6);
      mg.linearRampToValueAtTime(0.46, now + 3.2);
    } catch (e) { /* never let an audio hiccup break the release ritual */ }
  }
  // Exposed on the shared top-level window (same-origin, like every other
  // cross-frame lookup in this app) so the shatter-ritual component -- a
  // separate iframe -- can ring this the instant you submit, without the
  // two components needing any other channel between them.
  try { window.parent.__cosmicReleaseChime = playReleaseChime; } catch (e) {}

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
  // ---- (persisted so it won't reappear on every Streamlit rerun) ----
  var soundGate = document.getElementById('soundGate');
  var soundGateYes = document.getElementById('soundGateYes');
  var soundGateNo = document.getElementById('soundGateNo');
  try {
    if (soundGate && window.parent.sessionStorage.getItem('cosmicSoundGateSeen') === '1') {
      soundGate.style.transition = 'none';
      soundGate.classList.add('hidden');
    }
  } catch (e) {}
  function dismissGate() {
    if (soundGate) { soundGate.classList.add('hidden'); }
    try { window.parent.sessionStorage.setItem('cosmicSoundGateSeen', '1'); } catch (e) {}
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
#
#    Two layers, kept deliberately separate (see build_music_profile below):
#
#        user text  ->  PsychologicalProfile  ->  MusicProfile  ->  sound
#                       (Gemini, structured)      (this file,
#                                                   deterministic)
#
#    Gemini's only job is reading the writing itself -- genuinely something
#    only a language model can do well. Everything from there on (which
#    musical knobs that reading implies) is a plain, auditable Python
#    function, never left to the model to invent per-call. That split is
#    what keeps the generated music reproducible and debuggable rather than
#    an opaque black box, and it's what keeps PsychologicalProfile itself
#    honest: every field describes the WRITING, never the person, and is
#    never diagnostic, clinical, or shown to anyone.
# ============================================================================

def _clamp01(v) -> float:
    try:
        v = float(v)
    except (TypeError, ValueError):
        return 0.5
    if v != v:  # NaN
        return 0.5
    return max(0.0, min(1.0, v))


_PSYCH_FIELD_NAMES = (
    "arousal", "emotional_intensity", "cognitive_load", "tension", "urgency",
    "uncertainty", "perceived_overwhelm", "rumination_like_language",
    "need_for_predictability", "need_for_attentional_simplicity",
    "social_emotional_weight", "energy_level",
)


class PsychologicalProfile(BaseModel):
    """A structured, non-clinical, purely descriptive reading of how a piece of
    writing reads -- never a diagnosis, never shown to the user. Every field
    describes the WRITING's characteristics, not a claim about the person's
    mental state, character, or history. Used only to shape the generative
    music below. Field-level ge/le bounds are a strong hint to Gemini's
    structured output, and _clamp_all below is a hard backstop regardless of
    what comes back."""

    arousal: float = Field(
        default=0.45, ge=0.0, le=1.0,
        description="How activated/keyed-up the writing reads, from very settled (0) to very "
                    "keyed-up (1). About the writing's energy, not a clinical anxiety rating."
    )
    emotional_intensity: float = Field(
        default=0.45, ge=0.0, le=1.0,
        description="How strongly felt the writing reads, regardless of whether the feeling is "
                    "pleasant or not. A flat, matter-of-fact note scores low; a vivid, deeply "
                    "felt one scores high, whether the feeling is grief, joy, or anything else."
    )
    cognitive_load: float = Field(
        default=0.4, ge=0.0, le=1.0,
        description="How much the writing reads like several things being juggled or tracked "
                    "at once, versus one clear thread."
    )
    tension: float = Field(
        default=0.4, ge=0.0, le=1.0,
        description="How unresolved or keyed-up the writing feels, independent of intensity -- "
                    "something left hanging or unsettled, versus something at rest."
    )
    urgency: float = Field(
        default=0.35, ge=0.0, le=1.0,
        description="How much the writing reads like something pressing or time-bound, versus "
                    "something with no particular clock on it."
    )
    uncertainty: float = Field(
        default=0.4, ge=0.0, le=1.0,
        description="How much the writing reads like not knowing what comes next or being "
                    "unsure, versus a clear, settled picture of things."
    )
    perceived_overwhelm: float = Field(
        default=0.35, ge=0.0, le=1.0,
        description="How much the writing reads like more is happening than can comfortably be "
                    "held at once, versus a manageable amount."
    )
    rumination_like_language: float = Field(
        default=0.3, ge=0.0, le=1.0,
        description="How much the writing reads like circling back on the same thought rather "
                    "than moving through it -- repeating a worry, not just mentioning it once."
    )
    need_for_predictability: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="A design judgment rather than something read directly off the text: how "
                    "much a steady, foreseeable musical structure seems likely to suit this "
                    "moment."
    )
    need_for_attentional_simplicity: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="A design judgment: how much a sparse, uncluttered soundscape -- fewer "
                    "things happening at once -- seems likely to suit this moment."
    )
    social_emotional_weight: float = Field(
        default=0.3, ge=0.0, le=1.0,
        description="How much the writing centers on other people or relationships, versus an "
                    "internal or solitary experience."
    )
    energy_level: float = Field(
        default=0.4, ge=0.0, le=1.0,
        description="The writing's apparent physical/mental energy, from depleted (0) to "
                    "energized (1) -- independent of whether that energy reads as a good thing."
    )

    @model_validator(mode="before")
    @classmethod
    def _clamp_all(cls, data):
        if isinstance(data, dict):
            for name in _PSYCH_FIELD_NAMES:
                if name in data:
                    data[name] = _clamp01(data.get(name))
        return data


_MUSIC_FLOAT_FIELDS = (
    "arousal_target", "harmonic_complexity", "rhythmic_complexity", "layer_density",
    "spectral_brightness", "dynamic_range", "motif_repetition", "harmonic_tension",
    "harmonic_resolution", "rhythmic_predictability", "texture_density", "evolution_rate",
    "attack_softness", "low_frequency_weight", "high_frequency_weight", "spaciousness",
    "variation_amount", "calm_direction",
)


class MusicProfile(BaseModel):
    """The deterministic, machine-readable music-design profile the generative
    audio engine actually renders. Computed entirely by build_music_profile()
    below -- NEVER filled in by Gemini -- so sound generation stays
    reproducible, debuggable, and immune to an unexpected or malformed model
    response. tempo_bpm and root_freq have their own physically-meaningful
    ranges; every other knob is normalized to [0, 1]."""

    tempo_bpm: float = Field(ge=35.0, le=90.0)
    arousal_target: float = Field(ge=0.0, le=1.0)
    harmonic_complexity: float = Field(ge=0.0, le=1.0)
    rhythmic_complexity: float = Field(ge=0.0, le=1.0)
    layer_density: float = Field(ge=0.0, le=1.0)
    spectral_brightness: float = Field(ge=0.0, le=1.0)
    dynamic_range: float = Field(ge=0.0, le=1.0)
    motif_repetition: float = Field(ge=0.0, le=1.0)
    harmonic_tension: float = Field(ge=0.0, le=1.0)
    harmonic_resolution: float = Field(ge=0.0, le=1.0)
    rhythmic_predictability: float = Field(ge=0.0, le=1.0)
    texture_density: float = Field(ge=0.0, le=1.0)
    evolution_rate: float = Field(ge=0.0, le=1.0)
    attack_softness: float = Field(ge=0.0, le=1.0)
    low_frequency_weight: float = Field(ge=0.0, le=1.0)
    high_frequency_weight: float = Field(ge=0.0, le=1.0)
    spaciousness: float = Field(ge=0.0, le=1.0)
    variation_amount: float = Field(ge=0.0, le=1.0)
    calm_direction: float = Field(ge=0.0, le=1.0)
    root_freq: float = Field(ge=100.0, le=260.0)
    voice: Optional[str] = Field(default=None)
    seed: int = Field(ge=0)

    @model_validator(mode="before")
    @classmethod
    def _clamp_all(cls, data):
        if not isinstance(data, dict):
            return data
        for name in _MUSIC_FLOAT_FIELDS:
            if name in data:
                data[name] = _clamp01(data.get(name))
        if "tempo_bpm" in data:
            try:
                data["tempo_bpm"] = max(35.0, min(90.0, float(data["tempo_bpm"])))
            except (TypeError, ValueError):
                data["tempo_bpm"] = 55.0
        if "root_freq" in data:
            try:
                data["root_freq"] = max(100.0, min(260.0, float(data["root_freq"])))
            except (TypeError, ValueError):
                data["root_freq"] = 180.0
        if data.get("voice") not in (None, "piano", "pluck"):
            data["voice"] = None
        if "seed" in data:
            try:
                data["seed"] = max(0, int(data["seed"]))
            except (TypeError, ValueError):
                data["seed"] = 0
        return data


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
    psychological_profile: PsychologicalProfile = Field(
        default_factory=PsychologicalProfile,
        description="A structured, non-clinical, non-diagnostic reading of the writing's "
                    "music-relevant characteristics, used only to shape a generated ambient "
                    "soundscape and never shown to the person. Judge each dimension carefully "
                    "from the writing itself -- do not default every field to the middle of "
                    "the range."
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
    "so it is genuinely mind-expanding and perspective-shifting for someone in a hard moment. "
    "For psychological_profile: read the writing itself carefully and judge each dimension on "
    "its own terms, varying your reading with what's actually there rather than defaulting to "
    "the middle of the range -- this field is only ever used internally to shape a generated "
    "soundscape and is never shown to anyone, so it must never contain a diagnosis, a clinical "
    "label, or a claim about the person's mental health, character, or history: describe the "
    "WRITING, not the person. Do not diagnose, do not give clinical or medical advice, do not "
    "mention therapy or medication anywhere in any field. Keep every text field short -- a "
    "phrase or a sentence, never an essay."
)


PRIMARY_MODEL = "gemini-3.6-flash"
FALLBACK_MODEL = "gemini-3.5-flash-lite"
PRIMARY_TIMEOUT_SECONDS = 12
FALLBACK_TIMEOUT_SECONDS = 20


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


def _call_model_with_timeout(client, model_name: str, prompt: str, config, timeout_seconds: float):
    """Runs one generate_content call on a worker thread and enforces a hard wall-clock
    timeout on it, raising concurrent.futures.TimeoutError if it's exceeded. This is
    deliberately independent of whatever timeout support the installed google-genai
    version does or doesn't expose, so a hung/unreachable model reliably surfaces as a
    failure -- triggering the fallback below -- instead of blocking forever. The
    worker thread itself isn't force-killed on timeout (Python can't safely do that);
    it's simply abandoned to finish or die on its own while the caller moves on."""
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        future = executor.submit(client.models.generate_content, model=model_name, contents=prompt, config=config)
        return future.result(timeout=timeout_seconds)
    finally:
        executor.shutdown(wait=False)


def generate_sanctuary_response(
    user_text: str, emotional_state: str
) -> Tuple[Optional[SanctuaryPeaceResponse], Optional[str], Optional[str]]:
    """Calls Gemini and returns (result, error, model_used). error == 'missing_key' means
    no API key has been configured yet. PRIMARY_MODEL is always tried first, with its own
    timeout; if it's unreachable, errors, or times out, the request transparently retries
    against FALLBACK_MODEL for that same call. The single JSON response carries both the
    existing reflection fields and the new structured psychological_profile -- one call,
    one round trip, same timeout architecture as before."""
    if not GENAI_AVAILABLE:
        return None, "The google-genai package isn't installed. Run: pip install google-genai", None

    api_key = _resolve_api_key()
    if not api_key:
        return None, "missing_key", None

    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        return None, "Couldn't connect to Gemini (" + str(e) + ").", None

    prompt = (
        "Emotional load right now: " + emotional_state + ".\n\n"
        "What they're carrying, in their own words:\n"
        "\"\"\"\n" + user_text.strip() + "\n\"\"\"\n\n"
        "Respond strictly in the required schema."
    )
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        response_schema=SanctuaryPeaceResponse,
        temperature=0.9,
    )

    last_error: Optional[Exception] = None
    attempts = ((PRIMARY_MODEL, PRIMARY_TIMEOUT_SECONDS), (FALLBACK_MODEL, FALLBACK_TIMEOUT_SECONDS))
    for model_name, timeout_seconds in attempts:
        try:
            response = _call_model_with_timeout(client, model_name, prompt, config, timeout_seconds)
        except Exception as e:
            last_error = e
            continue

        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, SanctuaryPeaceResponse):
            return parsed, None, model_name
        try:
            data = json.loads(response.text)
            return SanctuaryPeaceResponse(**data), None, model_name
        except Exception as e:
            last_error = e
            continue

    return None, "The cosmos didn't answer just now (" + str(last_error) + "). Please try again in a moment.", None


# ============================================================================
# 5. PSYCHOLOGICAL PROFILE -> MUSIC PROFILE
#
#    The whole "meet the moment, then guide toward calm" design logic lives
#    here, once, in plain auditable Python -- not scattered across prompts
#    or left for a model to re-derive differently on every call. A few
#    deliberate choices worth naming:
#
#    - Tempo responds to load/overwhelm, not urgency-as-speed: the instinct
#      to make urgent writing produce a faster track is avoided on purpose
#      (see HIGH URGENCY in the project notes this mapping follows) --
#      regularity and settling matter more here than pace itself.
#    - Low energy does not simply mean "slow and dark": evolution_rate and
#      spectral_brightness both get a small deliberate lift for low
#      energy_level, so a depleted entry still gets gentle movement and a
#      touch of warmth rather than something flatter and heavier still.
#    - High emotional_intensity leans on dynamic_range (expressive swells)
#      rather than spectral_brightness or density, preserving emotional
#      depth without harshness or clutter.
#    - calm_direction is the one parameter that is NOT about where the
#      piece starts -- it is how far it travels. A moment with real tension
#      or overwhelm gets a bigger journey; an already-settled one doesn't
#      need engineering into something it already is.
#    - voice (which small instrument model plays the motif, if any) is
#      skipped entirely under real need_for_attentional_simplicity, and
#      otherwise chosen with a seeded coin-flip leaning toward the warmer
#      voice for more relationally-centered writing -- never a fixed rule,
#      always reproducible for the same input.
# ============================================================================

_ROOT_POOL_LOW = (123.47, 130.81, 138.59, 146.83)    # B2-D3 -- deeper, for heavier writing
_ROOT_POOL_MID = (164.81, 174.61, 185.00, 196.00)    # E3-G3 -- neutral
_ROOT_POOL_HIGH = (207.65, 220.00, 233.08, 246.94)   # G#3-B3 -- lighter, for lighter writing


def generate_music_seed(user_text: str, psych: dict, session_salt: str = "") -> int:
    """A stable seed from the submission + its psychological reading (+ an optional
    per-session salt, so two different people are not guaranteed identical music for
    similar writing). Deterministic: the same inputs always produce the same seed."""
    payload = (user_text or "") + "|" + json.dumps(psych, sort_keys=True, default=str) + "|" + (session_salt or "")
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return int(digest, 16) % (2 ** 31)


def build_music_profile(psych: dict, user_text: str, emotional_state: str, seed: int) -> MusicProfile:
    """Deterministically translates a PsychologicalProfile reading into a MusicProfile.
    The only inputs that matter are the twelve psychological dimensions and the seed --
    never raw keyword matching on the text, so this works the same whether the
    psychological reading came from Gemini or from the local fallback below."""
    p = {name: _clamp01(psych.get(name, 0.4)) for name in _PSYCH_FIELD_NAMES}

    heaviness = max(p["tension"], p["perceived_overwhelm"], p["cognitive_load"] * 0.8, p["urgency"] * 0.7)

    tempo_bpm = 60.0 - 10.0 * p["cognitive_load"] - 6.0 * p["perceived_overwhelm"] - 4.0 * p["urgency"]
    tempo_bpm = max(35.0, min(90.0, tempo_bpm))

    arousal_target = 0.12 + 0.5 * p["arousal"]
    calm_direction = 0.4 + 0.5 * max(p["tension"], p["perceived_overwhelm"], p["urgency"])

    harmonic_complexity = (0.5 - 0.4 * p["need_for_attentional_simplicity"] - 0.2 * p["cognitive_load"]
                            + 0.15 * p["emotional_intensity"] + 0.1 * p["social_emotional_weight"])
    rhythmic_complexity = 0.5 - 0.35 * p["need_for_predictability"] - 0.25 * p["urgency"] - 0.15 * p["cognitive_load"]
    layer_density = 0.6 - 0.45 * max(p["cognitive_load"], p["perceived_overwhelm"], p["need_for_attentional_simplicity"])
    spectral_brightness = 0.45 - 0.25 * p["emotional_intensity"] + 0.15 * (1 - p["energy_level"]) - 0.1 * p["perceived_overwhelm"]
    dynamic_range = 0.3 + 0.3 * p["emotional_intensity"] - 0.25 * max(p["perceived_overwhelm"], p["cognitive_load"])
    motif_repetition = 0.4 + 0.35 * p["need_for_predictability"] + 0.15 * p["need_for_attentional_simplicity"]
    harmonic_tension = 0.25 + 0.45 * p["tension"]
    harmonic_resolution = 0.75 + 0.2 * (1 - p["uncertainty"])
    rhythmic_predictability = (0.5 + 0.3 * p["need_for_predictability"]
                                + 0.2 * max(p["cognitive_load"], p["perceived_overwhelm"]) - 0.15 * p["uncertainty"])
    texture_density = 0.2 + 0.5 * max(p["perceived_overwhelm"], p["tension"], p["cognitive_load"] * 0.6)
    evolution_rate = 0.5 - 0.3 * p["cognitive_load"] + 0.25 * (1 - p["energy_level"]) - 0.15 * p["need_for_attentional_simplicity"]
    attack_softness = 0.55 + 0.25 * max(p["tension"], p["perceived_overwhelm"]) + 0.1 * p["emotional_intensity"]
    low_frequency_weight = 0.2 + 0.45 * max(p["perceived_overwhelm"], p["tension"])
    high_frequency_weight = 0.35 - 0.2 * max(p["perceived_overwhelm"], p["tension"]) + 0.15 * (1 - p["energy_level"])
    spaciousness = 0.4 + 0.3 * max(p["cognitive_load"], p["perceived_overwhelm"], p["need_for_attentional_simplicity"])
    variation_amount = max(0.12, 0.35 - 0.2 * p["need_for_predictability"] + 0.15 * (1 - p["rumination_like_language"]))

    if heaviness < 0.35:
        pool = _ROOT_POOL_HIGH
    elif heaviness > 0.6:
        pool = _ROOT_POOL_LOW
    else:
        pool = _ROOT_POOL_MID
    root_freq = pool[seed % len(pool)]

    if layer_density < 0.22:
        voice = None
    else:
        piano_chance = 0.3 + 0.5 * p["social_emotional_weight"]
        voice = "piano" if (seed % 100) / 100.0 < piano_chance else "pluck"

    return MusicProfile(
        tempo_bpm=tempo_bpm,
        arousal_target=arousal_target,
        harmonic_complexity=harmonic_complexity,
        rhythmic_complexity=rhythmic_complexity,
        layer_density=layer_density,
        spectral_brightness=spectral_brightness,
        dynamic_range=dynamic_range,
        motif_repetition=motif_repetition,
        harmonic_tension=harmonic_tension,
        harmonic_resolution=harmonic_resolution,
        rhythmic_predictability=rhythmic_predictability,
        texture_density=texture_density,
        evolution_rate=evolution_rate,
        attack_softness=attack_softness,
        low_frequency_weight=low_frequency_weight,
        high_frequency_weight=high_frequency_weight,
        spaciousness=spaciousness,
        variation_amount=variation_amount,
        calm_direction=calm_direction,
        root_freq=root_freq,
        voice=voice,
        seed=seed,
    )


# ----------------------------------------------------------------------------
# Local fallback (section 23 of the project brief this follows): used only if
# BOTH Gemini models are unreachable. A small, clearly-labeled heuristic --
# not a claim of real language understanding -- that produces a plausible,
# safe PsychologicalProfile locally, which is then run through the exact same
# build_music_profile() above, so there is only one music-design mapping in
# the whole app to reason about, not two different behaviors to keep in sync.
# ----------------------------------------------------------------------------

_FALLBACK_HEAVY_WORDS = {
    "stressed", "stress", "anxious", "anxiety", "worried", "worry", "scared", "afraid",
    "overwhelmed", "overwhelming", "exhausted", "panic", "panicking", "can't stop",
    "can't sleep", "racing", "deadline", "pressure", "frantic", "spiraling",
    "tired", "numb", "drained", "heavy", "stuck", "lost", "hurt", "pain", "cry", "crying",
}
_FALLBACK_LIGHT_WORDS = {
    "grateful", "hopeful", "happy", "joy", "peace", "peaceful", "calm", "relieved",
    "proud", "love", "safe", "good", "content", "relaxed", "bright", "free",
}
_FALLBACK_SLIDER_BASE = {
    "Calm": dict(arousal=0.25, cognitive_load=0.2, perceived_overwhelm=0.15, energy_level=0.5),
    "Busy": dict(arousal=0.45, cognitive_load=0.5, perceived_overwhelm=0.4, energy_level=0.5),
    "Overwhelmed": dict(arousal=0.75, cognitive_load=0.8, perceived_overwhelm=0.8, energy_level=0.45),
    "Exhausted": dict(arousal=0.3, cognitive_load=0.55, perceived_overwhelm=0.55, energy_level=0.12),
}


def _fallback_word_score(text_lower: str, words: set) -> int:
    score = 0
    for w in words:
        score += len(re.findall(r"(?<!\w)" + re.escape(w) + r"(?!\w)", text_lower))
    return score


def create_fallback_psychological_profile(user_text: str, emotional_state: str) -> dict:
    """A safe, locally-computed stand-in for Gemini's reading, used only when the AI is
    unreachable. Still contains controlled variation (via the heavy/light word tilt and
    the emotional-state slider), never a single hard-coded result."""
    text_lower = (user_text or "").lower()
    heavy = _fallback_word_score(text_lower, _FALLBACK_HEAVY_WORDS)
    light = _fallback_word_score(text_lower, _FALLBACK_LIGHT_WORDS)
    tilt = math.tanh((heavy - light) / 3.0)  # -1 (light) .. +1 (heavy)
    base = _FALLBACK_SLIDER_BASE.get(emotional_state, _FALLBACK_SLIDER_BASE["Busy"])

    def mix(key, default):
        b = base.get(key, default)
        return _clamp01(b + (0.2 * tilt if tilt > 0 else 0.1 * tilt))

    return {
        "arousal": mix("arousal", 0.45),
        "emotional_intensity": _clamp01(0.35 + 0.3 * abs(tilt)),
        "cognitive_load": mix("cognitive_load", 0.4),
        "tension": _clamp01(0.3 + 0.35 * max(0.0, tilt)),
        "urgency": _clamp01(0.25 + 0.3 * max(0.0, tilt)),
        "uncertainty": _clamp01(0.35 + 0.15 * abs(tilt)),
        "perceived_overwhelm": mix("perceived_overwhelm", 0.35),
        "rumination_like_language": _clamp01(0.25 + 0.3 * max(0.0, tilt)),
        "need_for_predictability": _clamp01(0.45 + 0.25 * max(0.0, tilt)),
        "need_for_attentional_simplicity": _clamp01(0.4 + 0.25 * max(0.0, tilt)),
        "social_emotional_weight": 0.3,
        "energy_level": base.get("energy_level", 0.4),
    }


_FALLBACK_FACTS = (
    "Earth's atmosphere has no hard edge -- it simply thins into space, with most of the "
    "air you're breathing packed into just the bottom few miles of it.",
    "The sunlight reaching your skin right now left the sun about eight minutes ago, "
    "travelling the whole way at the fastest speed anything in the universe can move.",
    "Much of the calcium in your bones and the iron in your blood was forged inside stars "
    "that lived and died long before the sun ever formed.",
    "Every person alive is, at this exact moment, moving together through space at over "
    "100,000 kilometers an hour as Earth carries everyone around the sun.",
    "The water currently in your body has, in one form or another, very likely cycled "
    "through ancient oceans and ice ages long before it ever reached you.",
)
_FALLBACK_MICRO_ACTIONS = (
    "Let your shoulders drop and take one slower breath than your last.",
    "Notice three things you can hear right now, without judging any of them.",
    "Unclench your jaw and let your hands rest open for a moment.",
)
_FALLBACK_TAKEAWAYS = (
    "Drink a glass of water slowly.",
    "Step outside for ten seconds of air.",
    "Write down just one thing, nothing more.",
)


def create_fallback_music_profile(user_text: str, emotional_state: str, session_salt: str = "") -> MusicProfile:
    psych = create_fallback_psychological_profile(user_text, emotional_state)
    seed = generate_music_seed(user_text or "", psych, session_salt)
    return build_music_profile(psych, user_text or "", emotional_state, seed)


def create_fallback_sanctuary_response(user_text: str, emotional_state: str, seed: int) -> SanctuaryPeaceResponse:
    """Used only when BOTH Gemini models are unreachable (see section 23 of the brief this
    follows: 'never leave the user without an experience'). Draws from a small set of
    pre-written, already-verified true facts rather than inventing one on the fly."""
    psych = create_fallback_psychological_profile(user_text, emotional_state)
    return SanctuaryPeaceResponse(
        uplifting_environmental_phrase=_FALLBACK_FACTS[seed % len(_FALLBACK_FACTS)],
        music_mix_profile="A quiet, settled ambient bed, composed locally while the sanctuary reconnects.",
        psychological_profile=PsychologicalProfile(**psych),
        micro_peace_action=_FALLBACK_MICRO_ACTIONS[seed % len(_FALLBACK_MICRO_ACTIONS)],
        takeaway_actions=[_FALLBACK_TAKEAWAYS[seed % len(_FALLBACK_TAKEAWAYS)],
                           _FALLBACK_TAKEAWAYS[(seed + 1) % len(_FALLBACK_TAKEAWAYS)]],
    )


# ============================================================================
# 5. SESSION STATE
# ============================================================================

for _key, _default in [
    ("sanctuary_result", None),
    ("just_generated", False),
    ("moment_recorded_at", ""),
    ("moment_label_saved", ""),
    ("manual_api_key", None),
    ("model_used", None),
    ("submitted_text", ""),
    ("submitted_emotional_state", "Busy"),
    ("music_profile", None),
    ("generation_id", 0),
    ("submission_count", 0),
    ("session_salt", None),
]:
    if _key not in st.session_state:
        st.session_state[_key] = _default

if not st.session_state["session_salt"]:
    # Folded into the music seed so two different people writing similar
    # things don't necessarily get identical music, while staying stable
    # for the rest of this one session.
    st.session_state["session_salt"] = hashlib.sha256(os.urandom(16)).hexdigest()[:16]


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

    submitted = st.button("Fade into the Vastness", use_container_width=True)


# ============================================================================
# 6b. THE GENERATIVE AMBIENT MUSIC ENGINE
#    A single persistent, multi-layer Web Audio engine (CosmicAudioEngine,
#    defined inside the template below) that lives once per browser session,
#    stored on window.parent so it survives every Streamlit rerun. Each new
#    submission calls transitionToProfile() on that SAME instance, smoothly
#    automating its existing nodes toward the new MusicProfile rather than
#    tearing anything down -- so repeated submissions crossfade cleanly with
#    no restart, no click, and never a duplicate AudioContext. See the
#    comment at the top of CosmicAudioEngine below for the full layer
#    breakdown and the singleton bootstrap at the bottom of the script.
# ============================================================================

AMBIENT_MIX_PLAYER_TEMPLATE = """
<!DOCTYPE html>
<html><head><meta charset="utf-8" /></head>
<body>
<script>
// ============================================================================
// CosmicAudioEngine -- a single persistent, multi-layer generative audio
// engine. Exactly one instance lives for the whole browser session (stored
// on window.parent, which survives Streamlit's iframe recreation on every
// rerun). New submissions call transitionToProfile(), which smoothly
// automates existing nodes toward new target values -- nothing is ever
// torn down and recreated, so there is never a click, restart, or duplicate
// voice stacking up.
// ============================================================================

function mulberry32(seed) {
  var s = seed >>> 0;
  return function () {
    s |= 0; s = (s + 0x6D2B79F5) | 0;
    var t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

var MOTIF_DEGREES = [1, 9 / 8, 5 / 4, 3 / 2, 5 / 3, 2]; // major-pentatonic-ish, all consonant with the root

function CosmicAudioEngine() {
  var Ctx = window.AudioContext || window.webkitAudioContext;
  this.ctx = Ctx ? new Ctx() : null;
  this.lastGenerationId = -1;
  this.profile = null;
  this.soundOn = false;
  this.targetMasterPeak = 0.34;
  this.tempoRampStart = 0;
  this.tempoRampFromBpm = 55;
  this.tempoRampMs = 8000;
  this.motifSteps = [1, 5 / 4, 3 / 2];
  this.motifStepIndex = 0;
  this.motifRng = mulberry32(1);
  this.genChangedAt = performance.now();
  if (!this.ctx) { return; }

  var ctx = this.ctx;
  var now = ctx.currentTime;

  this.master = ctx.createGain();
  this.master.gain.value = 0.0001;

  this.filter = ctx.createBiquadFilter();
  this.filter.type = 'lowpass';
  this.filter.frequency.value = 1200;
  this.filter.Q.value = 0.5;

  this.master.connect(this.filter);
  this.filter.connect(ctx.destination);

  // ---- shared paced-breathing LFO: modulates both the pad's slow swell
  // ---- and the sub-bass pulse, so the whole mix breathes on one pace ----
  this.breathe = ctx.createOscillator();
  this.breathe.type = 'sine';
  this.breathe.frequency.value = 0.12;
  this.breathe.start();

  // ---- foundation/harmonic pad: 3 scale-degree slots, each with a
  // ---- primary + a detuned "ensemble" voice (gain-automated, not
  // ---- created/destroyed) so richness can be dialed smoothly by
  // ---- harmonic_complexity ----
  this.padVoices = [];
  for (var i = 0; i < 3; i++) {
    var slot = { osc: [], gain: [] };
    for (var layer = 0; layer < 2; layer++) {
      var osc = ctx.createOscillator();
      osc.type = (i === 1) ? 'triangle' : 'sine';
      osc.frequency.value = 220 * (i + 1);
      var g = ctx.createGain();
      g.gain.value = 0.0001;
      osc.connect(g);
      osc.start();
      slot.osc.push(osc);
      slot.gain.push(g);
    }
    this.padVoices.push(slot);
  }

  // ---- spatial layer: a slow, fixed-rate panner LFO on the pad bus, whose
  // ---- DEPTH (not rate) is what spaciousness controls ----
  this.padBus = ctx.createGain();
  this.padBus.gain.value = 1.0;
  for (i = 0; i < this.padVoices.length; i++) {
    for (layer = 0; layer < 2; layer++) {
      this.padVoices[i].gain[layer].connect(this.padBus);
    }
  }
  this.panner = (ctx.createStereoPanner) ? ctx.createStereoPanner() : null;
  if (this.panner) {
    this.padBus.connect(this.panner);
    this.panner.connect(this.master);
    this.panLfo = ctx.createOscillator();
    this.panLfo.type = 'sine';
    this.panLfo.frequency.value = 0.025; // one slow left-right cycle every ~40s
    this.panDepth = ctx.createGain();
    this.panDepth.gain.value = 0.0001;
    this.panLfo.connect(this.panDepth);
    this.panDepth.connect(this.panner.pan);
    this.panLfo.start();
  } else {
    this.padBus.connect(this.master);
  }

  var swellGain = ctx.createGain();
  swellGain.gain.value = 0.045;
  this.breathe.connect(swellGain);
  swellGain.connect(this.master.gain);

  // ---- felt sub-bass / low-frequency weight ----
  this.sub = ctx.createOscillator();
  this.sub.type = 'sine';
  this.sub.frequency.value = 55;
  this.subGain = ctx.createGain();
  this.subGain.gain.value = 0.0001;
  this.sub.connect(this.subGain);
  this.subGain.connect(this.master);
  this.sub.start();
  var subBreatheGain = ctx.createGain();
  subBreatheGain.gain.value = 0.0001;
  this.subBreatheGainNode = subBreatheGain;
  this.breathe.connect(subBreatheGain);
  subBreatheGain.connect(this.subGain.gain);

  // ---- soft pink-noise texture bed (persistent looped source, gain-only
  // ---- automation on every transition) ----
  var bufSeconds = 4;
  var bufSize = Math.floor(ctx.sampleRate * bufSeconds);
  var buffer = ctx.createBuffer(1, bufSize, ctx.sampleRate);
  var data = buffer.getChannelData(0);
  var b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0;
  for (var n = 0; n < bufSize; n++) {
    var white = Math.random() * 2 - 1;
    b0 = 0.99886 * b0 + white * 0.0555179;
    b1 = 0.99332 * b1 + white * 0.0750759;
    b2 = 0.96900 * b2 + white * 0.1538520;
    b3 = 0.86650 * b3 + white * 0.3104856;
    b4 = 0.55000 * b4 + white * 0.5329522;
    b5 = -0.7616 * b5 - white * 0.0168980;
    var pinkSample = b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362;
    b6 = white * 0.115926;
    data[n] = pinkSample * 0.11;
  }
  this.noise = ctx.createBufferSource();
  this.noise.buffer = buffer;
  this.noise.loop = true;
  this.textureGain = ctx.createGain();
  this.textureGain.gain.value = 0.0001;
  this.noise.connect(this.textureGain);
  this.textureGain.connect(this.master);
  this.noise.start();

  // ---- the motif's own always-running scheduler (reads this.profile live
  // ---- on every tick, never torn down) ----
  this._scheduleMotif();

  // ---- sound permission: polls the same sessionStorage flag Phase 1's
  // ---- consent gate / toggle already maintains, so this engine respects
  // ---- whatever the person has decided, and reacts live if they change
  // ---- their mind later without needing a fresh submission ----
  var self = this;
  this._pollSoundTimer = setInterval(function () { self._pollSound(); }, 900);
  this._pollSound();
}

CosmicAudioEngine.prototype._pollSound = function () {
  if (!this.ctx) { return; }
  var on = false;
  try { on = window.parent.sessionStorage.getItem('cosmicAudioOn') === '1'; } catch (e) {}
  if (on === this.soundOn) { return; }
  this.soundOn = on;
  var now = this.ctx.currentTime;
  if (on) {
    try { this.ctx.resume(); } catch (e) {}
    this.master.gain.cancelScheduledValues(now);
    this.master.gain.setValueAtTime(this.master.gain.value, now);
    this.master.gain.linearRampToValueAtTime(this.targetMasterPeak, now + 2.4);
  } else {
    this.master.gain.cancelScheduledValues(now);
    this.master.gain.setValueAtTime(this.master.gain.value, now);
    this.master.gain.linearRampToValueAtTime(0.0001, now + 1.2);
  }
};

CosmicAudioEngine.prototype._currentBpm = function () {
  var target = this.profile ? this.profile.tempo_bpm : 55;
  if (!this.tempoRampStart) { return target; }
  var t = Math.min(1, (performance.now() - this.tempoRampStart) / this.tempoRampMs);
  return this.tempoRampFromBpm + (target - this.tempoRampFromBpm) * t;
};

CosmicAudioEngine.prototype._settleT = function () {
  // 0 right after a new generation lands, easing to 1 over about a minute --
  // used to let the rhythmic layer recede as the piece settles, same idea
  // as the rest of the engine's "meet, then ease toward calm" arcs
  var elapsed = performance.now() - this.genChangedAt;
  return Math.min(1, elapsed / 60000);
};

CosmicAudioEngine.prototype._chordRatios = function (profile) {
  var tense = [1.0, 1.2, 4 / 3];
  var resolved = [1.0, 1.25, 1.5];
  var resolveAmt = Math.max(0, Math.min(1, profile.harmonic_resolution - profile.harmonic_tension * 0.35));
  var out = [];
  for (var i = 0; i < 3; i++) {
    out.push(tense[i] + (resolved[i] - tense[i]) * resolveAmt);
  }
  return out;
};

CosmicAudioEngine.prototype.transitionToProfile = function (profile, generationId) {
  if (!this.ctx || generationId === this.lastGenerationId) { return; }
  var isFirst = this.lastGenerationId === -1;
  this.lastGenerationId = generationId;
  this.profile = profile;
  this.genChangedAt = performance.now();

  var ctx = this.ctx;
  var now = ctx.currentTime;
  var T = 5.5; // crossfade window in seconds

  function rampTo(param, target, dur) {
    param.cancelScheduledValues(now);
    param.setValueAtTime(param.value, now);
    param.linearRampToValueAtTime(target, now + dur);
  }

  var ratios = this._chordRatios(profile);
  var richness = profile.harmonic_complexity;
  for (var i = 0; i < this.padVoices.length; i++) {
    var slot = this.padVoices[i];
    var baseTarget = profile.root_freq * ratios[i];
    rampTo(slot.osc[0].frequency, baseTarget, T);
    rampTo(slot.osc[1].frequency, baseTarget * 1.0023, T);
    var baseGain = (0.1 - i * 0.015) * (0.5 + 0.5 * profile.dynamic_range);
    rampTo(slot.gain[0].gain, baseGain, T);
    rampTo(slot.gain[1].gain, baseGain * 0.5 * richness, T);
  }

  rampTo(this.filter.frequency, 350 + profile.spectral_brightness * 3200, T);
  rampTo(this.textureGain.gain, profile.texture_density * 0.16, T);
  rampTo(this.subGain.gain, profile.low_frequency_weight * 0.3, T);
  rampTo(this.subBreatheGainNode.gain, profile.low_frequency_weight * 0.3, T);
  if (this.panDepth) { rampTo(this.panDepth.gain, profile.spaciousness * 0.6, T); }

  var breathTarget = 0.1 + profile.arousal_target * 0.08;
  rampTo(this.breathe.frequency, breathTarget, Math.max(T, 20));

  this.targetMasterPeak = 0.28 + profile.dynamic_range * 0.16;
  if (this.soundOn) {
    rampTo(this.master.gain, this.targetMasterPeak, isFirst ? 2.4 : T);
  }

  // -- re-seed the motif's own shape fresh for this generation --
  var rng = mulberry32((profile.seed >>> 0) || 1);
  var len = 4 + Math.floor(rng() * 3);
  var steps = [];
  for (var s = 0; s < len; s++) { steps.push(MOTIF_DEGREES[Math.floor(rng() * MOTIF_DEGREES.length)]); }
  this.motifSteps = steps;
  this.motifStepIndex = 0;
  this.motifRng = rng;

  // -- reset the tempo arc so it eases toward the new resting tempo --
  this.tempoRampFromBpm = this._currentBpm();
  this.tempoRampStart = performance.now();
  this.tempoRampMs = T * 1000 + 14000;
};

// ---- FM synthesis electric-piano voice (two-operator, DX7-style) ----
CosmicAudioEngine.prototype._playFMPiano = function (freq, now, peakGain, softness) {
  var ctx = this.ctx;
  var carrier = ctx.createOscillator();
  carrier.type = 'sine';
  carrier.frequency.value = freq;

  var modulator = ctx.createOscillator();
  modulator.type = 'sine';
  modulator.frequency.value = freq * 1.4;

  var modGain = ctx.createGain();
  modGain.gain.setValueAtTime(freq * 1.1, now);
  modGain.gain.linearRampToValueAtTime(0, now + 0.4);
  modulator.connect(modGain);
  modGain.connect(carrier.frequency);

  var attack = 0.01 + softness * 0.05;
  var g = ctx.createGain();
  g.gain.setValueAtTime(0.0001, now);
  g.gain.exponentialRampToValueAtTime(Math.max(0.0001, peakGain), now + attack);
  g.gain.exponentialRampToValueAtTime(0.0001, now + 2.6);
  carrier.connect(g);
  g.connect(this.master);

  modulator.start(now); modulator.stop(now + 2.8);
  carrier.start(now); carrier.stop(now + 2.8);
};

// ---- Karplus-Strong plucked-string voice ----
CosmicAudioEngine.prototype._playPluck = function (freq, now, peakGain) {
  var ctx = this.ctx;
  var period = 1 / freq;
  var burstLen = Math.max(2, Math.floor(ctx.sampleRate * period));
  var buffer = ctx.createBuffer(1, burstLen, ctx.sampleRate);
  var data = buffer.getChannelData(0);
  for (var i = 0; i < burstLen; i++) { data[i] = Math.random() * 2 - 1; }

  var burst = ctx.createBufferSource();
  burst.buffer = buffer;

  var delay = ctx.createDelay(1);
  delay.delayTime.value = period;

  var damping = ctx.createBiquadFilter();
  damping.type = 'lowpass';
  damping.frequency.value = Math.min(ctx.sampleRate / 2 - 100, freq * 7);

  var feedback = ctx.createGain();
  feedback.gain.value = 0.983;

  var g = ctx.createGain();
  g.gain.value = Math.max(0.0001, peakGain) * 1.6;

  burst.connect(delay);
  delay.connect(damping);
  damping.connect(feedback);
  feedback.connect(delay);
  damping.connect(g);
  g.connect(this.master);

  burst.start(now);
  setTimeout(function () {
    try { feedback.disconnect(); delay.disconnect(); damping.disconnect(); g.disconnect(); } catch (e) {}
  }, 3200);
};

CosmicAudioEngine.prototype._scheduleMotif = function () {
  var self = this;
  function tick() {
    var profile = self.profile;
    var nextMs = 1200;
    if (profile && profile.voice && self.soundOn) {
      var bpm = self._currentBpm();
      var beatSec = 60 / Math.max(20, bpm);
      var recede = 1 - 0.55 * self._settleT();
      var playDensity = (0.3 + profile.rhythmic_complexity * 0.35 + profile.layer_density * 0.2) * recede;
      if (self.motifRng() < playDensity) {
        var useCanonical = self.motifRng() < profile.motif_repetition;
        var degree;
        if (useCanonical) {
          degree = self.motifSteps[self.motifStepIndex % self.motifSteps.length];
        } else {
          degree = MOTIF_DEGREES[Math.floor(self.motifRng() * MOTIF_DEGREES.length)];
        }
        self.motifStepIndex++;
        var freq = profile.root_freq * degree * 2;
        var now = self.ctx.currentTime;
        var peakGain = (0.09 + profile.layer_density * 0.07) * recede;
        if (profile.voice === 'piano') {
          self._playFMPiano(freq, now, peakGain, profile.attack_softness);
        } else {
          self._playPluck(freq, now, peakGain);
        }
      } else {
        self.motifStepIndex++;
      }
      var subdivision = profile.rhythmic_complexity > 0.5 ? 1 : 2;
      nextMs = beatSec * subdivision * 1000;
    }
    self.motifTimer = setTimeout(tick, nextMs);
  }
  this.motifTimer = setTimeout(tick, 500);
};

// ---- singleton bootstrap: reuse the engine already living on the stable
// ---- top-level window if one exists -- it survives this iframe being
// ---- torn down and recreated on every Streamlit rerun, which is why a
// ---- naive "create one on mount" approach would otherwise spin up a
// ---- brand-new AudioContext (and duplicate every oscillator) on every
// ---- single submission. Only the very first mount of the whole browser
// ---- session actually constructs one; every later submission just calls
// ---- transitionToProfile on that same, still-running instance. ----
(function () {
  var PROFILE = __PROFILE_JSON__;
  var GENERATION_ID = __GENERATION_ID__;

  var engine = null;
  try {
    if (window.parent.__cosmicAudioEngine && window.parent.__cosmicAudioEngine.ctx) {
      engine = window.parent.__cosmicAudioEngine;
    }
  } catch (e) {}
  if (!engine) {
    engine = new CosmicAudioEngine();
    try { window.parent.__cosmicAudioEngine = engine; } catch (e) {}
  }
  engine.transitionToProfile(PROFILE, GENERATION_ID);
})();
</script>
</body></html>
"""


# ============================================================================
# 6c. THE SWISS TYPOGRAPHIC SHATTER RITUAL
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
  var BTN_LABEL = 'Fade into the Vastness';
  var TA_PLACEHOLDER = 'Write freely. No one is grading this.';

  // A short, clearly audible "release" chime (an open, resolving rising
  // triad), played from a fresh audio context belonging to THIS component --
  // not borrowed from the ambient-tone component -- so it fires reliably
  // right on the real click that triggers it, regardless of whatever state
  // that other component happens to be in. Only plays if the calming tone
  // has actually been turned on (checked via the shared sessionStorage flag
  // the ambient-tone component keeps up to date), so sound stays opt-in.
  function playSubmitChime() {
    var audioOn = false;
    try { audioOn = window.parent.sessionStorage.getItem('cosmicAudioOn') === '1'; } catch (e) {}
    if (!audioOn) { return; }
    try {
      var Ctx = window.AudioContext || window.webkitAudioContext;
      if (!Ctx) { return; }
      var ctx = new Ctx();
      var master = ctx.createGain();
      master.gain.value = 0.0001;
      master.connect(ctx.destination);

      var now = ctx.currentTime;
      var freqs = [392.00, 493.88, 587.33]; // G4, B4, D5 -- open, resolving
      freqs.forEach(function (freq, idx) {
        var osc = ctx.createOscillator();
        osc.type = 'sine';
        osc.frequency.value = freq;
        var g = ctx.createGain();
        g.gain.value = 0.0001;
        var startAt = now + idx * 0.14;
        g.gain.setValueAtTime(0.0001, startAt);
        g.gain.exponentialRampToValueAtTime(0.32, startAt + 0.05);
        g.gain.exponentialRampToValueAtTime(0.0001, startAt + 3.0);
        osc.connect(g);
        g.connect(master);
        osc.start(startAt);
        osc.stop(startAt + 3.2);
      });

      master.gain.setValueAtTime(0.9, now);
      setTimeout(function () { try { ctx.close(); } catch (e) {} }, 3600);
    } catch (e) { /* never let an audio hiccup break the release ritual */ }
  }

  // Streamlit redraws this button (and the textarea) as a brand-new DOM
  // node on every rerun -- including right after a submission completes --
  // so a one-time lookup only ever wraps the very first one, leaving later
  // edits with no working button until the page is refreshed. Instead, this
  // keeps watching for as long as the component lives: a MutationObserver
  // plus a never-giving-up polling heartbeat, both calling the same scan,
  // which wraps any live "Fade into the Vastness" button it finds that
  // doesn't already carry our marker -- so every resubmission gets its own
  // fresh, enabled custom button, not just the first.
  function scanAndWrap() {
    var pdoc;
    try { pdoc = window.parent.document; } catch (e) { return; }
    if (!pdoc) { return; }

    var realBtn = null;
    var btns = pdoc.querySelectorAll('button');
    for (var i = 0; i < btns.length; i++) {
      var candidate = btns[i];
      // Our own injected button carries the same visible label by design
      // (that's the whole point), so a plain text match alone would
      // eventually catch it too and try to "wrap" itself -- excluding its
      // class here is what keeps the scan pointed only at the real one.
      if (candidate.textContent && candidate.textContent.trim() === BTN_LABEL
          && !candidate.dataset.cosmicWrapped
          && !candidate.classList.contains('cosmicSurrenderBtn')) {
        realBtn = candidate;
        break;
      }
    }
    if (!realBtn) { return; }
    var textarea = pdoc.querySelector('textarea[placeholder="' + TA_PLACEHOLDER + '"]');
    if (!textarea) { return; }

    realBtn.dataset.cosmicWrapped = '1';
    try {
      setupCustomButton(pdoc, realBtn, textarea);
    } catch (e) {
      console.warn('Cosmic Sanctuary: custom ritual button unavailable, using default.', e);
      realBtn.style.display = '';
    }
  }

  function setupCustomButton(pdoc, realBtn, textarea) {
    // Clear out any custom button left over from a previous submission
    // cycle before attaching today's -- Streamlit's own rerender usually
    // already clears these, but this keeps it tidy if one is ever orphaned.
    var stale = pdoc.querySelectorAll('.cosmicSurrenderBtn');
    for (var s = 0; s < stale.length; s++) { stale[s].remove(); }

    var customBtn = pdoc.createElement('button');
    customBtn.type = 'button';
    customBtn.className = 'cosmicSurrenderBtn';
    customBtn.dataset.cosmicWrapped = '1'; // belt-and-braces alongside the class check above
    customBtn.textContent = 'Fade into the Vastness';
    customBtn.setAttribute('style', [
      'background: #4F83F5',
      'color: #08080a',
      'border: none',
      'border-radius: 2px',
      'padding: 0.85rem 0',
      'width: 100%',
      'font-weight: 600',
      'font-size: 0.92rem',
      'font-family: Inter, -apple-system, sans-serif',
      'letter-spacing: 0.06em',
      'text-transform: uppercase',
      'margin-top: 1.6rem',
      'cursor: pointer',
      'transition: background 0.2s ease, opacity 0.3s ease'
    ].join(';'));

    realBtn.insertAdjacentElement('afterend', customBtn);
    realBtn.style.display = 'none';

    customBtn.addEventListener('mouseenter', function () {
      customBtn.style.background = '#6a9aff';
    });
    customBtn.addEventListener('mouseleave', function () {
      customBtn.style.background = '#4F83F5';
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

      // let the sound change right here, the moment you submit -- a no-op
      // if the calming tone was never turned on
      playSubmitChime();
      try {
        if (window.parent && typeof window.parent.__cosmicReleaseChime === 'function') {
          window.parent.__cosmicReleaseChime();
        }
      } catch (e) {}

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

    // Build one faithful snapshot of the WHOLE box -- background, border,
    // radius, and the text laid out exactly where it was. This entire
    // thing (box included, not just the words) is what gets sliced into
    // splinters and dissolved -- so the box disappears along with the text.
    var snapshot = pdoc.createElement('div');
    snapshot.setAttribute('style', [
      'position:absolute',
      'inset:0',
      'box-sizing:border-box',
      'background:' + cs.backgroundColor,
      'border:' + cs.borderTopWidth + ' ' + cs.borderTopStyle + ' ' + cs.borderTopColor,
      'border-radius:' + cs.borderRadius
    ].join(';'));

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

    lines.forEach(function (lineText, idx) {
      var lineEl = pdoc.createElement('div');
      lineEl.textContent = lineText;
      lineEl.setAttribute('style', [
        'position:absolute',
        'left:' + padLeft + 'px',
        'top:' + (padTop + idx * lineHeight) + 'px',
        'white-space: nowrap',
        'font:' + fontSpec,
        'color:' + cs.color
      ].join(';'));
      snapshot.appendChild(lineEl);
    });

    // Slice the whole snapshot (box + text together) into thin horizontal
    // splinters, each drifting away on its own gentle wind vector.
    var SLICES = 10;
    var bandH = rect.height / SLICES;
    var pieces = [];
    for (var s = 0; s < SLICES; s++) {
      var clipTop = s * bandH;
      var clipBottom = (SLICES - s - 1) * bandH;
      var band = pdoc.createElement('div');
      band.setAttribute('style', [
        'position: fixed',
        'left:' + rect.left + 'px',
        'top:' + rect.top + 'px',
        'width:' + rect.width + 'px',
        'height:' + rect.height + 'px',
        'z-index: 999999',
        'pointer-events: none',
        'clip-path: inset(' + clipTop + 'px 0 ' + clipBottom + 'px 0)',
        '-webkit-clip-path: inset(' + clipTop + 'px 0 ' + clipBottom + 'px 0)',
        'transition: transform 2.5s cubic-bezier(.16,1,.3,1), opacity 2.3s ease, filter 2.3s ease',
        'transition-delay:' + (s * 55) + 'ms',
        'will-change: transform, opacity, filter'
      ].join(';'));
      band.appendChild(snapshot.cloneNode(true));
      pdoc.body.appendChild(band);
      pieces.push({
        el: band,
        driftX: (Math.random() * 30 - 15),
        riseY: 20 + Math.random() * 30
      });
    }
    textarea.style.opacity = '0';

    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        pieces.forEach(function (p) {
          p.el.style.transform = 'translate(' + p.driftX.toFixed(1) + 'px, -' + p.riseY.toFixed(1) + 'px)';
          p.el.style.opacity = '0';
          p.el.style.filter = 'blur(6px)';
        });
      });
    });

    var totalWait = 2500 + (SLICES - 1) * 55 + 150;
    setTimeout(function () {
      pieces.forEach(function (p) { p.el.remove(); });
      textarea.style.opacity = '';
      onComplete();
    }, totalWait);
  }

  scanAndWrap();
  try {
    if (window.parent && window.parent.document) {
      var ParentObserver = window.parent.MutationObserver || window.MutationObserver;
      if (ParentObserver) {
        var btnObserver = new ParentObserver(function () { scanAndWrap(); });
        btnObserver.observe(window.parent.document.body, { childList: true, subtree: true });
      }
    }
  } catch (e) {}

  // Belt-and-braces polling in case the observer can't attach (cross-origin
  // edge cases, older browsers): quick at first, then a slow heartbeat that
  // never gives up -- so a second, third, or later edit-and-resubmit is
  // always caught, not just the first one.
  (function pollButton(attempt) {
    scanAndWrap();
    setTimeout(function () { pollButton(attempt + 1); }, attempt < 40 ? 200 : 1500);
  })(0);
})();
</script>
</body></html>
"""

components.html(SHATTER_RITUAL_HTML, height=1, scrolling=False)


if submitted:
    if not user_text or not user_text.strip():
        st.warning("Write even a few words before you let go.")
    else:
        loading_ph = st.empty()
        loading_ph.markdown(
            '<div class="cosmic-loader">'
            '<div class="cosmic-loader-dot"></div>'
            '<p>Carrying your words out past the atmosphere&hellip;</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        result, err, model_used = generate_sanctuary_response(user_text, emotional_state)
        loading_ph.empty()
        if err == "missing_key":
            st.error("Add a Gemini API key above to open the sanctuary.")
        else:
            if err:
                # Both models are unreachable: never leave the person without
                # an experience -- a safe, locally-generated reflection and
                # music profile stand in, rather than just an error message.
                _fallback_seed = generate_music_seed(user_text, {}, st.session_state["session_salt"])
                result = create_fallback_sanctuary_response(user_text, emotional_state, _fallback_seed)
                model_used = "local-fallback"

            _psych_dict = result.psychological_profile.model_dump()
            _seed = generate_music_seed(user_text, _psych_dict, st.session_state["session_salt"])
            _music_profile = build_music_profile(_psych_dict, user_text, emotional_state, _seed)

            st.session_state["sanctuary_result"] = result
            st.session_state["model_used"] = model_used
            st.session_state["just_generated"] = True
            st.session_state["moment_recorded_at"] = datetime.now().strftime("%A, %B %d \u2014 %H:%M")
            st.session_state["moment_label_saved"] = moment_label.strip() if moment_label else ""
            st.session_state["submitted_text"] = user_text
            st.session_state["submitted_emotional_state"] = emotional_state
            st.session_state["music_profile"] = _music_profile.model_dump()
            st.session_state["generation_id"] = st.session_state["generation_id"] + 1
            st.session_state["submission_count"] = st.session_state["submission_count"] + 1


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
        '<div class="music-panel">'
        '<div class="result-index">01 &mdash; Ambient mix</div>'
        '<div class="music-readout">' + html.escape(r.music_mix_profile) + "</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    # Real, individualized audio, not just the readout above: a structured,
    # non-clinical reading of THIS writing (psychological_profile) was
    # turned into a MusicProfile once at submission time (see
    # build_music_profile); the persistent engine below smoothly
    # crossfades toward it, keyed by generation_id so it knows this is a
    # new composition rather than just another rerun of the same one.
    _music_profile_dict = st.session_state.get("music_profile") or create_fallback_music_profile(
        st.session_state.get("submitted_text", ""),
        st.session_state.get("submitted_emotional_state", "Busy"),
        st.session_state.get("session_salt", ""),
    ).model_dump()
    _profile_json = json.dumps(_music_profile_dict).replace("</", "<\\/")
    _generation_id = st.session_state.get("generation_id", 0)
    components.html(
        AMBIENT_MIX_PLAYER_TEMPLATE
        .replace("__PROFILE_JSON__", _profile_json)
        .replace("__GENERATION_ID__", str(_generation_id)),
        height=1,
        scrolling=False,
    )
    if reveal_slowly:
        time.sleep(1.2)

    ph_phrase.markdown(
        '<div class="phrase-panel">'
        '<div class="phrase-rule"></div>'
        '<div class="phrase-text">' + html.escape(r.uplifting_environmental_phrase) + "</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    if reveal_slowly:
        time.sleep(1.2)

    all_actions = [r.micro_peace_action] + list(r.takeaway_actions or [])
    actions_html = '<div class="actions-panel"><div class="result-index">02 &mdash; To take with you</div>'
    for idx, action in enumerate(all_actions, start=1):
        actions_html += (
            '<div class="action-row">'
            '<div class="action-num">' + str(idx).zfill(2) + "</div>"
            '<div class="action-text">' + html.escape(action) + "</div>"
            "</div>"
        )
    actions_html += "</div>"
    ph_action.markdown(actions_html, unsafe_allow_html=True)

    if reveal_slowly:
        st.session_state["just_generated"] = False

    _model_used_note = st.session_state.get("model_used")
    if _model_used_note in (FALLBACK_MODEL, "local-fallback"):
        _note_text = "using 3.5-lite backup" if _model_used_note == FALLBACK_MODEL else "composed locally while reconnecting"
        st.markdown(
            '<div style="text-align:center;font-family:\'Inter\',-apple-system,sans-serif;'
            'font-size:10px;font-weight:400;color:#4a4a52;'
            'letter-spacing:0.03em;margin-top:0.9rem;">'
            + _note_text +
            "</div>",
            unsafe_allow_html=True,
        )


# ============================================================================
# 8. FOOTER
# ============================================================================

st.markdown(
    '<div class="sanctuary-footer">'
    '<div class="sanctuary-footer-desc">'
    "The Cosmic Sanctuary is a quiet place to set down what you\u2019re carrying "
    "and be reminded, for a moment, of the shared vastness of Earth and sky."
    "</div>"
    '<div class="sanctuary-footer-credit">'
    "Designed &amp; Engineered by Nikolai de Silva &nbsp;&bull;&nbsp; \u00a9 2026 ninolades.com"
    "</div>"
    "</div>",
    unsafe_allow_html=True,
)
