"""
THE COSMIC SANCTUARY
A single-file Streamlit experience.

Run:
    streamlit run cosmic.py

requirements:
    streamlit>=1.48.0
    google-genai>=1.30.0
    pydantic>=2.8.0
"""

from __future__ import annotations

import html
import os
from typing import Optional

import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai import types
from pydantic import BaseModel, Field, ValidationError


APP_TITLE = "The Cosmic Sanctuary"
MODEL_NAME = "gemini-3.6-flash"


# ---------------------------------------------------------------------------
# Structured Gemini response
# ---------------------------------------------------------------------------

class SanctuaryPeaceResponse(BaseModel):
    uplifting_environmental_phrase: str = Field(
        description=(
            "A short, deeply comforting and poetic message connecting the "
            "user's specific concern to Earth as one shared, borderless home. "
            "It must feel personal and spacious, not generic."
        )
    )
    music_mix_profile: str = Field(
        description=(
            "Concise ambient production notes for the user's state, such as "
            "tempo, texture, instrument, dynamics and filtering. Do not make "
            "medical claims."
        )
    )
    micro_peace_action: str = Field(
        description=(
            "A short list of 2 to 4 tiny, concrete, zero-pressure things the "
            "user can take away and try for grounding and wellbeing. These "
            "must be ordinary low-risk actions, not treatment."
        )
    )


# ---------------------------------------------------------------------------
# Streamlit configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="◦",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ---------------------------------------------------------------------------
# Premium Swiss-inspired interface
# ---------------------------------------------------------------------------

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500&family=Manrope:wght@300;400;500&display=swap');

:root {
    --bg: #08080a;
    --text: #e5e5ea;
    --muted: #85858e;
    --soft: #a8a8b0;
    --accent: #4F83F5;
    --line: rgba(229,229,234,.11);
    --panel: rgba(255,255,255,.026);
}

html {
    scroll-behavior: smooth;
    background: var(--bg);
}

body {
    background: var(--bg);
}

.stApp {
    background: var(--bg);
    color: var(--text);
    font-family: "DM Sans", Inter, sans-serif;
}

header[data-testid="stHeader"] {
    background: transparent;
}

div[data-testid="stToolbar"] {
    display: none;
}

section[data-testid="stSidebar"] {
    display: none;
}

.block-container {
    max-width: 1120px;
    padding: 0 30px 120px 30px;
}

.sanctuary-wordmark {
    position: fixed;
    z-index: 1000;
    top: 25px;
    left: 32px;
    color: rgba(229,229,234,.72);
    font-family: "DM Sans", sans-serif;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: .19em;
    text-transform: uppercase;
    pointer-events: none;
}

.hero-scroll {
    position: relative;
    height: 335vh;
    margin-left: calc(50% - 50vw);
    margin-right: calc(50% - 50vw);
    overflow: visible;
}

.hero-stage {
    position: sticky;
    top: 0;
    height: 100vh;
    min-height: 620px;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
}

.globe-frame {
    position: absolute;
    z-index: 1;
    width: min(82vw, 1040px);
    height: min(82vw, 1040px);
    max-width: 1040px;
    max-height: 1040px;
    min-width: 300px;
    min-height: 300px;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    pointer-events: none;
}

.globe-frame iframe {
    width: 100% !important;
    height: 100% !important;
    border: 0 !important;
    background: transparent !important;
}

.hero-copy-layer {
    position: absolute;
    z-index: 5;
    inset: 0;
    pointer-events: none;
}

.hero-line {
    position: absolute;
    left: 50%;
    top: 50%;
    width: min(900px, 86vw);
    transform: translate(-50%, -50%);
    text-align: center;
    color: #f3f3f5;
    font-family: "Manrope", sans-serif;
    font-weight: 300;
    font-size: clamp(32px, 5.3vw, 72px);
    line-height: 1.06;
    letter-spacing: -.055em;
    opacity: 0;
    text-shadow: 0 2px 28px rgba(0,0,0,.32);
    will-change: transform, opacity;
}

.scroll-breath {
    position: absolute;
    z-index: 6;
    left: 50%;
    bottom: 34px;
    transform: translateX(-50%);
    color: rgba(229,229,234,.32);
    font-size: 9px;
    letter-spacing: .22em;
    text-transform: uppercase;
    white-space: nowrap;
    pointer-events: none;
}

.sanctuary-canvas {
    position: relative;
    z-index: 10;
    max-width: 780px;
    margin: 0 auto;
    padding: 150px 0 40px;
}

.canvas-title {
    font-family: "Manrope", sans-serif;
    font-size: clamp(38px, 5vw, 64px);
    line-height: 1.02;
    letter-spacing: -.055em;
    font-weight: 300;
    margin: 0 0 20px;
}

.canvas-intro {
    max-width: 650px;
    color: var(--muted);
    font-size: 15px;
    line-height: 1.8;
    margin-bottom: 70px;
}

.brain-wrap {
    width: min(100%, 620px);
    margin: 0 auto 74px;
    height: 300px;
    position: relative;
}

.brain-art {
    width: 100%;
    height: 100%;
    overflow: visible;
}

.brain-art path,
.brain-art ellipse {
    fill: none;
    stroke: rgba(229,229,234,.72);
    stroke-width: 1.15;
    stroke-linecap: round;
    stroke-linejoin: round;
}

.brain-art .accent-stroke {
    stroke: rgba(79,131,245,.72);
}

.field {
    margin-top: 38px;
}

.field-label {
    color: rgba(229,229,234,.55);
    font-size: 9px;
    font-weight: 500;
    letter-spacing: .19em;
    text-transform: uppercase;
    margin-bottom: 14px;
}

.state-value {
    color: #f0f0f2;
    font-family: "Manrope", sans-serif;
    font-size: 22px;
    font-weight: 300;
    margin-bottom: 4px;
}

.state-note {
    color: #686871;
    font-size: 12px;
    line-height: 1.6;
    margin-bottom: 10px;
}

.stSlider > div > div > div > div {
    background: var(--accent) !important;
}

.stTextArea textarea {
    background: transparent !important;
    border: 0 !important;
    border-bottom: 1px solid rgba(229,229,234,.16) !important;
    border-radius: 0 !important;
    color: #e8e8ec !important;
    font-family: "Manrope", sans-serif !important;
    font-size: 20px !important;
    font-weight: 300 !important;
    line-height: 1.7 !important;
    padding: 16px 0 20px !important;
    box-shadow: none !important;
    resize: vertical;
}

.stTextArea textarea:focus {
    border-bottom-color: rgba(79,131,245,.72) !important;
    box-shadow: none !important;
}

.stTextArea label {
    display: none !important;
}

.record-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
    margin-top: 18px;
}

.record-chip {
    border: 1px solid var(--line);
    background: var(--panel);
    padding: 17px 18px;
    min-height: 72px;
}

.record-chip-title {
    color: rgba(229,229,234,.40);
    font-size: 8px;
    letter-spacing: .17em;
    text-transform: uppercase;
    margin-bottom: 8px;
}

.record-chip-value {
    color: #c7c7ce;
    font-size: 13px;
    line-height: 1.45;
}

.stButton {
    margin-top: 34px;
}

.stButton > button {
    background: #4F83F5 !important;
    color: #fff !important;
    border: 0 !important;
    border-radius: 999px !important;
    min-height: 48px !important;
    padding: 0 30px !important;
    font-family: "DM Sans", sans-serif !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    letter-spacing: .02em !important;
    box-shadow: 0 8px 30px rgba(79,131,245,.13) !important;
    transition: transform .2s ease, opacity .2s ease !important;
}

.stButton > button:hover {
    transform: translateY(-1px);
    opacity: .92;
}

.analysis {
    margin-top: 110px;
    padding-top: 55px;
    border-top: 1px solid var(--line);
}

.analysis-kicker {
    color: rgba(229,229,234,.35);
    font-size: 8px;
    letter-spacing: .20em;
    text-transform: uppercase;
    margin-bottom: 24px;
}

.analysis-message {
    font-family: "Manrope", sans-serif;
    font-size: clamp(28px, 4vw, 48px);
    line-height: 1.17;
    letter-spacing: -.045em;
    font-weight: 300;
    color: #f1f1f4;
    margin-bottom: 52px;
}

.takeaway {
    border: 1px solid rgba(79,131,245,.18);
    background: linear-gradient(
        135deg,
        rgba(79,131,245,.075),
        rgba(255,255,255,.018)
    );
    padding: 26px 28px;
    margin-top: 18px;
}

.takeaway-title {
    color: rgba(79,131,245,.88);
    font-size: 9px;
    letter-spacing: .18em;
    text-transform: uppercase;
    margin-bottom: 12px;
}

.takeaway-text {
    color: #d0d0d6;
    font-family: "Manrope", sans-serif;
    font-size: 16px;
    line-height: 1.75;
    white-space: pre-line;
}

.mix {
    border: 1px solid var(--line);
    background: rgba(255,255,255,.018);
    padding: 21px 24px;
    margin-bottom: 45px;
}

.mix-title {
    color: rgba(229,229,234,.38);
    font-size: 8px;
    letter-spacing: .18em;
    text-transform: uppercase;
    margin-bottom: 9px;
}

.mix-text {
    color: #9e9ea7;
    font-size: 12px;
    line-height: 1.7;
}

.stAlert {
    border-radius: 0 !important;
}

@media (max-width: 700px) {
    .block-container {
        padding-left: 20px;
        padding-right: 20px;
    }

    .sanctuary-wordmark {
        left: 20px;
        top: 20px;
        font-size: 8px;
    }

    .hero-scroll {
        height: 350vh;
    }

    .hero-stage {
        min-height: 580px;
    }

    .globe-frame {
        width: min(88vw, 720px);
        height: min(88vw, 720px);
        min-width: 280px;
        min-height: 280px;
    }

    .hero-line {
        width: 84vw;
        font-size: clamp(30px, 9vw, 48px);
    }

    .canvas-intro {
        font-size: 14px;
        margin-bottom: 52px;
    }

    .record-grid {
        grid-template-columns: 1fr;
    }

    .brain-wrap {
        height: 230px;
        margin-bottom: 54px;
    }
}

@media (orientation: landscape) and (max-height: 700px) {
    .globe-frame {
        width: min(72vh, 760px);
        height: min(72vh, 760px);
    }

    .hero-line {
        font-size: clamp(27px, 4vw, 48px);
    }
}
</style>

<div class="sanctuary-wordmark">The Cosmic Sanctuary</div>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Three.js visual: photorealistic Earth with controlled parent-scroll input
# ---------------------------------------------------------------------------

earth_html = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
html, body {
    margin: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
    background: transparent;
}
#scene {
    position: absolute;
    inset: 0;
    overflow: hidden;
}
canvas {
    display: block;
    width: 100%;
    height: 100%;
}
</style>
</head>
<body>
<div id="scene"></div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>

<script>
(() => {
    const scene = new THREE.Scene();

    const camera = new THREE.PerspectiveCamera(
        34,
        Math.max(window.innerWidth, 1) / Math.max(window.innerHeight, 1),
        0.1,
        100
    );
    camera.position.set(0, 0, 3.25);

    const renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true,
        powerPreference: "high-performance"
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.outputEncoding = THREE.sRGBEncoding;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.05;
    document.getElementById("scene").appendChild(renderer.domElement);

    const earth = new THREE.Group();
    scene.add(earth);

    const loader = new THREE.TextureLoader();
    loader.crossOrigin = "anonymous";

    // High-resolution public Earth textures. The cloud layer is separate,
    // allowing the atmosphere and surface to move at subtly different rates.
    const BASE =
        "https://threejs.org/examples/textures/planets/";
    const earthMap = BASE + "earth_atmos_2048.jpg";
    const earthNormal = BASE + "earth_normal_2048.jpg";
    const earthSpecular = BASE + "earth_specular_2048.jpg";
    const cloudsMap = BASE + "earth_clouds_1024.png";

    const surfaceMaterial = new THREE.MeshPhongMaterial({
        color: 0xffffff,
        shininess: 24,
        specular: new THREE.Color(0x30343a)
    });

    const globe = new THREE.Mesh(
        new THREE.SphereGeometry(1, 128, 128),
        surfaceMaterial
    );
    earth.add(globe);

    loader.load(earthMap, (tex) => {
        tex.anisotropy = renderer.capabilities.getMaxAnisotropy();
        surfaceMaterial.map = tex;
        surfaceMaterial.needsUpdate = true;
    });

    loader.load(earthNormal, (tex) => {
        tex.anisotropy = renderer.capabilities.getMaxAnisotropy();
        surfaceMaterial.normalMap = tex;
        surfaceMaterial.normalScale = new THREE.Vector2(.34, .34);
        surfaceMaterial.needsUpdate = true;
    });

    loader.load(earthSpecular, (tex) => {
        tex.anisotropy = renderer.capabilities.getMaxAnisotropy();
        surfaceMaterial.specularMap = tex;
        surfaceMaterial.needsUpdate = true;
    });

    const cloudMaterial = new THREE.MeshPhongMaterial({
        color: 0xffffff,
        transparent: true,
        opacity: .48,
        depthWrite: false,
        side: THREE.DoubleSide
    });

    const clouds = new THREE.Mesh(
        new THREE.SphereGeometry(1.012, 96, 96),
        cloudMaterial
    );
    earth.add(clouds);

    loader.load(cloudsMap, (tex) => {
        tex.anisotropy = renderer.capabilities.getMaxAnisotropy();
        cloudMaterial.map = tex;
        cloudMaterial.alphaMap = tex;
        cloudMaterial.needsUpdate = true;
    });

    // Very subtle atmosphere rim.
    const atmosphere = new THREE.Mesh(
        new THREE.SphereGeometry(1.045, 96, 96),
        new THREE.MeshBasicMaterial({
            color: 0x6ea0ff,
            transparent: true,
            opacity: .045,
            side: THREE.BackSide,
            depthWrite: false
        })
    );
    earth.add(atmosphere);

    const ambient = new THREE.AmbientLight(0x8e99aa, .50);
    scene.add(ambient);

    const sun = new THREE.DirectionalLight(0xffffff, 2.05);
    sun.position.set(4.5, 2.4, 5.5);
    scene.add(sun);

    const coolRim = new THREE.DirectionalLight(0x507fda, .32);
    coolRim.position.set(-4, 1.5, -3.5);
    scene.add(coolRim);

    // Initial scale deliberately large while maintaining a clean breathing margin.
    earth.scale.setScalar(1.30);

    let target = 0;
    let smooth = 0;

    window.addEventListener("message", (event) => {
        if (!event.data || event.data.type !== "COSMIC_SANCTUARY_SCROLL") return;
        if (typeof event.data.progress !== "number") return;
        target = Math.min(Math.max(event.data.progress, 0), 1);
    });

    function animate() {
        requestAnimationFrame(animate);

        smooth += (target - smooth) * .055;

        // The Earth starts large and slowly recedes as the visitor descends.
        // It never reaches the viewport edge because the scale is bounded.
        const scale = 1.30 - smooth * .72;
        earth.scale.setScalar(scale);

        // Slow, continuous planetary rotation.
        earth.rotation.y += .00125;
        earth.rotation.x = -0.08 + smooth * .10;
        clouds.rotation.y += .00152;

        // Gentle camera retreat reinforces depth without a sudden zoom.
        camera.position.z = 3.25 + smooth * .55;

        // Surface gradually gives way to the hand-drawn brain.
        const surfaceOpacity = Math.max(0, 1 - smooth * 1.42);
        surfaceMaterial.opacity = surfaceOpacity;
        surfaceMaterial.transparent = surfaceOpacity < .999;

        const cloudOpacity = Math.max(0, 1 - smooth * 1.55);
        cloudMaterial.opacity = .48 * cloudOpacity;
        atmosphere.material.opacity = .045 * cloudOpacity;

        renderer.render(scene, camera);
    }

    function resize() {
        const w = Math.max(window.innerWidth, 1);
        const h = Math.max(window.innerHeight, 1);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        renderer.setSize(w, h);
    }

    window.addEventListener("resize", resize);
    animate();
})();
</script>
</body>
</html>
"""

# A large component gives the globe a real visual surface. The CSS keeps the
# actual globe inside a clean frame rather than touching the viewport edge.
components.html(earth_html, height=760, scrolling=False)


# ---------------------------------------------------------------------------
# Parent page controls the iframe's visual state from the actual page scroll.
# ---------------------------------------------------------------------------

st.markdown(
    """
<script>
(() => {
    let lastProgress = -1;

    function sendScroll() {
        const maxScroll = Math.max(
            document.documentElement.scrollHeight - window.innerHeight,
            1
        );
        const progress = Math.min(
            Math.max(window.scrollY / maxScroll, 0),
            1
        );

        if (Math.abs(progress - lastProgress) < 0.001) return;
        lastProgress = progress;

        document.querySelectorAll("iframe").forEach((frame) => {
            try {
                frame.contentWindow.postMessage(
                    {
                        type: "COSMIC_SANCTUARY_SCROLL",
                        progress: progress
                    },
                    "*"
                );
            } catch (_) {}
        });
    }

    window.addEventListener("scroll", sendScroll, {passive: true});
    window.addEventListener("resize", sendScroll);

    let attempts = 0;
    const timer = setInterval(() => {
        sendScroll();
        attempts += 1;
        if (attempts > 30) clearInterval(timer);
    }, 250);

    sendScroll();
})();
</script>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Scrollytelling narrative
# ---------------------------------------------------------------------------

st.markdown(
    """
<div class="hero-scroll">
    <div class="hero-stage">
        <div class="globe-frame"></div>

        <div class="hero-copy-layer">
            <div class="hero-line" data-start=".03" data-end=".19">
                Look closely at our home.
            </div>

            <div class="hero-line" data-start=".25" data-end=".42">
                No lines divide us from up here.
            </div>

            <div class="hero-line" data-start=".49" data-end=".66">
                Every breath we take is shared.
            </div>
        </div>

        <div class="scroll-breath">Scroll slowly</div>
    </div>
</div>

<script>
(() => {
    const root = document.querySelector(".hero-scroll");
    const lines = Array.from(document.querySelectorAll(".hero-line"));

    function updateNarrative() {
        if (!root) return;

        const rect = root.getBoundingClientRect();
        const travel = Math.max(root.offsetHeight - window.innerHeight, 1);
        const progress = Math.min(Math.max(-rect.top / travel, 0), 1);

        lines.forEach((line) => {
            const start = Number(line.dataset.start);
            const end = Number(line.dataset.end);
            const midpoint = (start + end) / 2;
            const half = (end - start) / 2;

            let opacity = 1 - Math.abs(progress - midpoint) / half;
            opacity = Math.min(Math.max(opacity, 0), 1);

            // A gentle float rather than a hard slide.
            const y = (1 - opacity) * 18;
            line.style.opacity = String(Math.pow(opacity, 1.15));
            line.style.transform =
                "translate(-50%, calc(-50% + " + y + "px))";
        });
    }

    window.addEventListener("scroll", updateNarrative, {passive: true});
    window.addEventListener("resize", updateNarrative);
    updateNarrative();
})();
</script>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# The brain / reflection canvas
# ---------------------------------------------------------------------------

# Hand-drawn Swiss-style line art. It is intentionally restrained rather than
# resembling a medical illustration.
brain_svg = """
<svg class="brain-art" viewBox="0 0 620 300" aria-hidden="true">
  <path d="M308 238 C282 230 265 209 263 184
           C240 188 218 178 211 159
           C189 158 172 144 174 124
           C156 113 153 91 166 76
           C157 57 168 38 188 33
           C198 14 224 11 241 23
           C256 4 285 9 294 29
           C314 15 342 19 352 39
           C373 30 396 41 398 63
           C418 68 429 89 417 107
           C435 120 432 146 414 157
           C416 180 399 194 379 194
           C369 219 342 231 319 220" />
  <path d="M263 184 C250 164 253 143 270 130
           C250 113 254 89 273 79
           C267 58 281 43 300 43
           C310 61 308 78 298 93
           C319 106 322 128 308 145
           C326 158 329 181 316 198" />
  <path d="M352 39 C340 56 342 75 356 87
           C337 100 335 121 349 135
           C330 148 331 169 344 181
           C334 194 331 208 339 221" />
  <path d="M188 33 C205 48 207 68 197 84
           C216 92 220 112 208 127
           C228 136 232 155 219 169" />
  <path d="M398 63 C378 72 375 92 388 106
           C369 116 367 136 380 149
           C363 159 361 178 373 194" />
  <path class="accent-stroke"
        d="M286 251 C304 260 327 259 345 250
           M276 258 C286 270 305 275 321 271" />
</svg>
"""


st.markdown(
    f"""
<div class="sanctuary-canvas" id="canvas">
    <div class="canvas-title">
        Leave whatever you are carrying right here.
    </div>

    <div class="canvas-intro">
        This is a quiet record of a moment. There is no correct way to describe
        it. Notice what is present, put it into words if you can, and let the
        Sanctuary help you make one small amount of room around it.
    </div>

    <div class="brain-wrap">
        {brain_svg}
    </div>
</div>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Moment capture
# ---------------------------------------------------------------------------

state_options = ["Exhausted", "Overwhelmed", "Busy", "Calm"]
state_notes = {
    "Exhausted": "Very little demand. More softness, less effort.",
    "Overwhelmed": "Too much may be arriving at once. Keep the next step small.",
    "Busy": "Attention may be moving quickly. Create one quiet point.",
    "Calm": "There is already some space. Notice it without needing to change it.",
}

st.markdown('<div class="sanctuary-canvas">', unsafe_allow_html=True)

st.markdown('<div class="field-label">How does this moment feel?</div>', unsafe_allow_html=True)

state = st.select_slider(
    "How does this moment feel?",
    options=state_options,
    value="Busy",
    label_visibility="collapsed",
)

st.markdown(
    f"""
<div class="state-value">{html.escape(state)}</div>
<div class="state-note">{html.escape(state_notes[state])}</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="field-label">What is here?</div>',
    unsafe_allow_html=True,
)

feeling = st.text_area(
    "What is here?",
    placeholder="Leave whatever you are carrying right here.",
    height=190,
    label_visibility="collapsed",
)

# Cleanly record the moment alongside the written reflection.
st.markdown(
    '<div class="field-label">Record this moment</div>',
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)

with col1:
    moment_context = st.selectbox(
        "Context",
        [
            "Just now",
            "Today",
            "A difficult moment",
            "A quiet moment",
            "Something I want to remember",
        ],
        label_visibility="collapsed",
    )

with col2:
    intensity = st.select_slider(
        "Intensity",
        options=["Gentle", "Noticeable", "Strong", "Very strong"],
        value="Noticeable",
        label_visibility="collapsed",
    )

st.markdown(
    f"""
<div class="record-grid">
    <div class="record-chip">
        <div class="record-chip-title">Moment</div>
        <div class="record-chip-value">{html.escape(moment_context)}</div>
    </div>
    <div class="record-chip">
        <div class="record-chip-title">Felt intensity</div>
        <div class="record-chip-value">{html.escape(intensity)}</div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

analyse = st.button(
    "Make a little room",
    type="primary",
    use_container_width=False,
)


# ---------------------------------------------------------------------------
# Gemini
# ---------------------------------------------------------------------------

def get_api_key() -> Optional[str]:
    try:
        key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        key = None

    if key:
        return str(key).strip()

    env_key = os.getenv("GEMINI_API_KEY")
    return env_key.strip() if env_key else None


def analyse_moment(
    feeling_text: str,
    state_value: str,
    context_value: str,
    intensity_value: str,
) -> SanctuaryPeaceResponse:
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. Add GEMINI_API_KEY to "
            "Streamlit Secrets."
        )

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are the reflective mindfulness engine inside The Cosmic Sanctuary.

Moment context: {context_value}
Internal state: {state_value}
Felt intensity: {intensity_value}

The person's own words:
---
{feeling_text}
---

Create a concise response that feels human, spacious, grounded and specific
to what they wrote.

Important requirements:
- Do not diagnose.
- Do not present yourself as a therapist or medical professional.
- Do not claim to treat, cure, or prevent any condition.
- Do not make assumptions about hidden trauma, disorders, or motives.
- Do not use fear, guilt, pressure, or mystical certainty.
- The main message should be short but meaningful, around 1 to 3 sentences.
- Explicitly keep the perspective scientifically grounded: Earth is one shared
  physical environment with a common atmosphere, oceans and interconnected
  ecological systems, regardless of political borders.
- Do not use the planetary perspective to dismiss the person's immediate
  feelings.
- Give 2 to 4 small, ordinary, zero-pressure things they can take away.
  Examples may include changing posture, looking at a distant object, stepping
  outside, drinking water, slowing an activity, writing one sentence, taking a
  quiet pause, or contacting someone they trust.
- Avoid prescribing exercise, supplements, medication, therapy, or medical care.
- If the writing indicates immediate danger or self-harm, do not attempt to
  solve it with grounding alone. Encourage contacting local emergency services
  or a trusted person and seeking immediate human support.
- Music notes are optional descriptive production guidance only and must not
  imply a medical effect.

Return ONLY the SanctuaryPeaceResponse schema.
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SanctuaryPeaceResponse,
        ),
    )

    parsed = getattr(response, "parsed", None)
    if parsed is not None:
        if isinstance(parsed, SanctuaryPeaceResponse):
            return parsed
        return SanctuaryPeaceResponse.model_validate(parsed)

    raw = getattr(response, "text", None)
    if not raw:
        raise RuntimeError("Gemini returned an empty response.")

    return SanctuaryPeaceResponse.model_validate_json(raw)


# ---------------------------------------------------------------------------
# Analysis output
# ---------------------------------------------------------------------------

if analyse:
    if not feeling.strip():
        st.warning("Give the moment a few words first. They do not need to be polished.")
    else:
        with st.spinner("Listening..."):
            try:
                response = analyse_moment(
                    feeling_text=feeling.strip(),
                    state_value=state,
                    context_value=moment_context,
                    intensity_value=intensity,
                )
                st.session_state["sanctuary_analysis"] = response.model_dump()

            except ValidationError:
                st.error(
                    "The response did not satisfy the Sanctuary's structured "
                    "output contract. Nothing partial was displayed."
                )
            except RuntimeError as exc:
                st.error(str(exc))
            except Exception:
                st.error(
                    "The Sanctuary could not complete the analysis right now. "
                    "Please try again in a moment."
                )


analysis_data = st.session_state.get("sanctuary_analysis")

if analysis_data:
    try:
        analysis = SanctuaryPeaceResponse.model_validate(analysis_data)

        st.markdown(
            '<div class="sanctuary-canvas analysis">',
            unsafe_allow_html=True,
        )

        st.markdown(
            """
<div class="analysis-kicker">A little perspective</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
<div class="analysis-message">
    {html.escape(analysis.uplifting_environmental_phrase)}
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
<div class="takeaway">
    <div class="takeaway-title">Take away</div>
    <div class="takeaway-text">
        {html.escape(analysis.micro_peace_action)}
    </div>
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
<div class="mix" style="margin-top:18px;">
    <div class="mix-title">Your ambient profile</div>
    <div class="mix-text">
        {html.escape(analysis.music_mix_profile)}
    </div>
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown("</div>", unsafe_allow_html=True)

    except ValidationError:
        st.session_state.pop("sanctuary_analysis", None)

st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    """
<div style="
    text-align:center;
    color:rgba(229,229,234,.20);
    font-size:9px;
    letter-spacing:.18em;
    text-transform:uppercase;
    padding:90px 0 20px;
">
    One planet. Shared atmosphere. One small moment.
</div>
""",
    unsafe_allow_html=True,
)
