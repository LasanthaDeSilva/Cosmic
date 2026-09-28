"""
The Cosmic Sanctuary
Single-file Streamlit application.

Run:
    streamlit run cosmic.py

Required packages:
    streamlit
    google-genai
    pydantic
"""

from __future__ import annotations

import html
import os
import time
from typing import Optional

import streamlit as st
import streamlit.components.v1 as components
from pydantic import BaseModel, Field, ValidationError
from google import genai
from google.genai import types


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

APP_TITLE = "The Cosmic Sanctuary"
MODEL_NAME = "gemini-3.6-flash"

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="◦",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ---------------------------------------------------------------------------
# Structured AI contract
# ---------------------------------------------------------------------------

class SanctuaryPeaceResponse(BaseModel):
    uplifting_environmental_phrase: str = Field(
        description=(
            "A deeply comforting, poetic phrase connecting the user's specific "
            "worry to the timeless beauty of the earth and cosmos."
        )
    )
    music_mix_profile: str = Field(
        description=(
            "Specific ambient music modifiers for Nolasko's tracks based on "
            "their state (e.g., Tempo: 55BPM, Instrument: Ambient Acoustic "
            "Guitar, Low-pass filter active)."
        )
    )
    micro_peace_action: str = Field(
        description=(
            "One tiny, concrete, completely zero-pressure physical action to "
            "take right now to find grounding."
        )
    )


# ---------------------------------------------------------------------------
# Premium UI
# ---------------------------------------------------------------------------

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500&family=Manrope:wght@300;400;500&display=swap');

:root {
    --bg: #08080a;
    --text: #e5e5ea;
    --muted: #92929b;
    --accent: #4F83F5;
    --line: rgba(229,229,234,.10);
    --panel: rgba(255,255,255,.025);
}

html {
    scroll-behavior: smooth;
}

.stApp {
    background: #08080a;
    color: #e5e5ea;
    font-family: Inter, sans-serif;
}

header[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    max-width: 1180px;
    padding: 0 2rem 7rem 2rem;
}

section[data-testid="stSidebar"] {
    display: none;
}

div[data-testid="stToolbar"] {
    visibility: hidden;
}

.sanctuary-nav {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 100;
    height: 58px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 34px;
    pointer-events: none;
    background: linear-gradient(
        to bottom,
        rgba(8,8,10,.78),
        rgba(8,8,10,0)
    );
}

.sanctuary-brand {
    font-size: 12px;
    letter-spacing: .16em;
    text-transform: uppercase;
    color: rgba(229,229,234,.68);
}

.sanctuary-index {
    font-size: 11px;
    letter-spacing: .12em;
    color: rgba(229,229,234,.35);
}

.portal-copy {
    min-height: 215vh;
    position: relative;
    margin: 0 -2rem;
    padding: 0 2rem;
}

.portal-copy-inner {
    position: sticky;
    top: 0;
    height: 100vh;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    pointer-events: none;
}

.portal-line {
    position: absolute;
    width: min(820px, 90vw);
    text-align: center;
    font-family: Manrope, Inter, sans-serif;
    font-size: clamp(30px, 5vw, 66px);
    font-weight: 300;
    line-height: 1.10;
    letter-spacing: -.045em;
    color: #f0f0f3;
    opacity: 0;
    transform: translateY(24px);
    will-change: opacity, transform;
}

.portal-subtitle {
    position: absolute;
    bottom: 7vh;
    color: rgba(229,229,234,.34);
    font-size: 10px;
    letter-spacing: .20em;
    text-transform: uppercase;
}

.canvas {
    max-width: 850px;
    margin: 0 auto;
    padding-top: 8vh;
}

.eyebrow {
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: .22em;
    font-size: 10px;
    margin-bottom: 18px;
}

.canvas-title {
    font-family: Manrope, Inter, sans-serif;
    font-size: clamp(34px, 5vw, 58px);
    line-height: 1.05;
    letter-spacing: -.045em;
    font-weight: 300;
    margin-bottom: 16px;
}

.canvas-intro {
    max-width: 650px;
    color: var(--muted);
    font-size: 15px;
    line-height: 1.75;
    margin-bottom: 52px;
}

.field-label {
    color: rgba(229,229,234,.72);
    font-size: 11px;
    letter-spacing: .13em;
    text-transform: uppercase;
    margin: 36px 0 14px;
}

.load-readout {
    font-family: Manrope, Inter, sans-serif;
    font-size: 22px;
    font-weight: 300;
    margin: 0 0 8px;
}

.load-description {
    color: #777781;
    font-size: 12px;
    margin-bottom: 10px;
}

.stTextArea textarea {
    background: transparent !important;
    border: 0 !important;
    border-bottom: 1px solid rgba(229,229,234,.16) !important;
    border-radius: 0 !important;
    color: #e5e5ea !important;
    font-family: Manrope, Inter, sans-serif !important;
    font-size: 20px !important;
    line-height: 1.7 !important;
    padding: 18px 0 !important;
    box-shadow: none !important;
    resize: vertical;
}

.stTextArea textarea:focus {
    border-bottom: 1px solid rgba(79,131,245,.75) !important;
    box-shadow: none !important;
}

.stTextArea label {
    display: none !important;
}

.stSlider > div > div > div > div {
    background: #4F83F5 !important;
}

.stSlider [data-baseweb="slider"] {
    margin-top: 12px;
}

.surrender-wrap {
    margin-top: 34px;
}

.stButton > button {
    background: #4F83F5 !important;
    color: white !important;
    border: 0 !important;
    border-radius: 999px !important;
    min-height: 48px !important;
    padding: 0 28px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    letter-spacing: .02em !important;
    transition: transform .2s ease, opacity .2s ease !important;
}

.stButton > button:hover {
    transform: translateY(-1px);
    opacity: .92;
}

.result-section {
    margin-top: 90px;
    padding-top: 30px;
    border-top: 1px solid var(--line);
}

.result-kicker {
    color: rgba(229,229,234,.36);
    text-transform: uppercase;
    letter-spacing: .18em;
    font-size: 9px;
    margin-bottom: 20px;
}

.music-card {
    border: 1px solid var(--line);
    background: var(--panel);
    padding: 22px 24px;
    margin-bottom: 32px;
}

.music-title {
    font-size: 10px;
    letter-spacing: .15em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 9px;
}

.music-text {
    color: #b9b9c1;
    line-height: 1.7;
    font-size: 13px;
}

.phrase-card {
    padding: 42px 0;
    margin-bottom: 36px;
}

.phrase-text {
    font-family: Manrope, Inter, sans-serif;
    font-size: clamp(28px, 4vw, 48px);
    line-height: 1.18;
    letter-spacing: -.035em;
    font-weight: 300;
    color: #f0f0f3;
}

.action-card {
    border: 1px solid rgba(79,131,245,.22);
    background: linear-gradient(
        135deg,
        rgba(79,131,245,.08),
        rgba(255,255,255,.018)
    );
    padding: 28px;
    margin-top: 24px;
}

.action-title {
    color: var(--accent);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: .16em;
    margin-bottom: 13px;
}

.action-text {
    color: #d6d6dc;
    font-family: Manrope, Inter, sans-serif;
    font-size: 18px;
    line-height: 1.6;
}

.error-card {
    border: 1px solid rgba(255,90,90,.20);
    padding: 18px;
    color: #d5a8a8;
    font-size: 13px;
    line-height: 1.6;
    margin-top: 25px;
}

.footer-note {
    text-align: center;
    color: rgba(229,229,234,.22);
    font-size: 10px;
    letter-spacing: .12em;
    text-transform: uppercase;
    padding-top: 100px;
}
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Scroll portal / Three.js Earth
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
    position: fixed;
    inset: 0;
    pointer-events: none;
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
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>

<script>
(function () {
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(
        42,
        window.innerWidth / window.innerHeight,
        0.1,
        100
    );
    camera.position.set(0, 0, 3.4);

    const renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true,
        powerPreference: "high-performance"
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.outputEncoding = THREE.sRGBEncoding;
    document.getElementById("scene").appendChild(renderer.domElement);

    const earth = new THREE.Group();
    scene.add(earth);

    const loader = new THREE.TextureLoader();

    // Public NASA/Three.js-compatible texture sources.
    // If a texture CDN is unavailable, the sphere remains as a dark,
    // softly lit orbital object rather than breaking the application.
    const earthTextureURL =
        "https://threejs.org/examples/textures/planets/earth_atmos_2048.jpg";
    const earthNormalURL =
        "https://threejs.org/examples/textures/planets/earth_normal_2048.jpg";
    const earthSpecURL =
        "https://threejs.org/examples/textures/planets/earth_specular_2048.jpg";

    const geometry = new THREE.SphereGeometry(1, 96, 96);

    const material = new THREE.MeshPhongMaterial({
        color: 0x8b98aa,
        shininess: 12,
        specular: 0x252525
    });

    const globe = new THREE.Mesh(geometry, material);
    earth.add(globe);

    loader.load(earthTextureURL, texture => {
        material.map = texture;
        material.color.set(0xffffff);
        material.needsUpdate = true;
    });

    loader.load(earthNormalURL, texture => {
        material.normalMap = texture;
        material.normalScale = new THREE.Vector2(.38, .38);
        material.needsUpdate = true;
    });

    loader.load(earthSpecURL, texture => {
        material.specularMap = texture;
        material.needsUpdate = true;
    });

    // Subtle atmospheric shell.
    const atmosphereMaterial = new THREE.MeshBasicMaterial({
        color: 0x4f83f5,
        transparent: true,
        opacity: 0.055,
        side: THREE.BackSide
    });
    const atmosphere = new THREE.Mesh(
        new THREE.SphereGeometry(1.035, 72, 72),
        atmosphereMaterial
    );
    earth.add(atmosphere);

    const ambient = new THREE.AmbientLight(0x778899, 0.42);
    scene.add(ambient);

    const key = new THREE.DirectionalLight(0xffffff, 1.65);
    key.position.set(4, 2, 5);
    scene.add(key);

    const rim = new THREE.DirectionalLight(0x4f83f5, 0.30);
    rim.position.set(-4, 1, -3);
    scene.add(rim);

    earth.position.set(0, 0, 0);
    earth.scale.setScalar(1.12);

    let targetScroll = 0;
    let smoothScroll = 0;

    window.addEventListener("scroll", () => {
        const maxScroll =
            Math.max(document.documentElement.scrollHeight - window.innerHeight, 1);
        targetScroll = Math.min(
            Math.max(window.scrollY / maxScroll, 0),
            1
        );
    }, {passive: true});

    function animate() {
        requestAnimationFrame(animate);

        smoothScroll += (targetScroll - smoothScroll) * 0.055;

        // Slow orbital descent: scale increases as the visitor scrolls.
        const scale = 1.12 + smoothScroll * 2.35;
        earth.scale.setScalar(scale);

        earth.rotation.y += 0.0017 + smoothScroll * 0.0032;
        earth.rotation.x = smoothScroll * 0.18;

        // Move the planet gently toward the viewer.
        camera.position.z = 3.4 - smoothScroll * 0.82;

        // Fade the globe as the narrative hands control to the canvas.
        const opacity = Math.max(0, 1 - Math.max(0, smoothScroll - 0.42) / 0.58);
        material.opacity = opacity;
        material.transparent = opacity < 0.999;
        atmosphereMaterial.opacity = 0.055 * opacity;

        renderer.render(scene, camera);
    }

    function resize() {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    }

    window.addEventListener("resize", resize);
    animate();
})();
</script>
</body>
</html>
"""

components.html(earth_html, height=1, scrolling=False)


# ---------------------------------------------------------------------------
# Portal narrative
# ---------------------------------------------------------------------------

st.markdown(
    """
<div class="sanctuary-nav">
    <div class="sanctuary-brand">The Cosmic Sanctuary</div>
    <div class="sanctuary-index">01 / 02</div>
</div>

<div class="portal-copy">
    <div class="portal-copy-inner">
        <div class="portal-line" data-start="0.00" data-end="0.28">
            Look closely at our home.
        </div>
        <div class="portal-line" data-start="0.28" data-end="0.56">
            No lines divide us from up here.
        </div>
        <div class="portal-line" data-start="0.56" data-end="0.86">
            Every breath we take is shared.
        </div>
        <div class="portal-subtitle">Scroll slowly</div>
    </div>
</div>

<script>
(function () {
    const lines = Array.from(document.querySelectorAll(".portal-line"));

    function update() {
        const max =
            Math.max(document.documentElement.scrollHeight - window.innerHeight, 1);
        const progress = Math.min(Math.max(window.scrollY / max, 0), 1);

        lines.forEach(line => {
            const start = Number(line.dataset.start);
            const end = Number(line.dataset.end);
            const center = (start + end) / 2;
            const half = (end - start) / 2;
            const distance = Math.abs(progress - center);
            const opacity = Math.max(0, 1 - distance / half);

            line.style.opacity = Math.pow(opacity, 1.35);
            line.style.transform =
                "translateY(" + ((1 - opacity) * 24) + "px)";
        });
    }

    window.addEventListener("scroll", update, {passive: true});
    window.addEventListener("resize", update);
    update();
})();
</script>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Canvas
# ---------------------------------------------------------------------------

st.markdown(
    """
<div class="canvas">
    <div class="eyebrow">02 — The Canvas</div>
    <div class="canvas-title">You can put it down for a moment.</div>
    <div class="canvas-intro">
        There is nothing to solve here. Describe what is taking up space inside
        you, in whatever words arrive. The Sanctuary will turn that state into
        a small, grounded pause.
    </div>
</div>
""",
    unsafe_allow_html=True,
)

load_options = ["Exhausted", "Overwhelmed", "Busy", "Calm"]
load_descriptions = {
    "Exhausted": "Your system may need softness, stillness, and very little demand.",
    "Overwhelmed": "There may be too much arriving at once. We will keep the next step small.",
    "Busy": "Your attention may be moving quickly. We will create one quiet point.",
    "Calm": "There is already some space available. We can gently notice it.",
}

st.markdown('<div class="canvas">', unsafe_allow_html=True)

st.markdown('<div class="field-label">Internal state</div>', unsafe_allow_html=True)

load = st.select_slider(
    "Internal state",
    options=load_options,
    value="Busy",
    label_visibility="collapsed",
)

st.markdown(
    f"""
<div class="load-readout">{html.escape(load)}</div>
<div class="load-description">{html.escape(load_descriptions[load])}</div>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="field-label">What you are carrying</div>', unsafe_allow_html=True)

worry = st.text_area(
    "What you are carrying",
    placeholder="Leave whatever you are carrying right here.",
    height=190,
    label_visibility="collapsed",
)

st.markdown('<div class="surrender-wrap">', unsafe_allow_html=True)
surrender = st.button(
    "Surrender to the Cosmos",
    type="primary",
    use_container_width=False,
)
st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Gemini generation
# ---------------------------------------------------------------------------

def get_api_key() -> Optional[str]:
    """Read the API key from Streamlit secrets first, then environment."""
    try:
        key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        key = None

    if key:
        return str(key).strip()

    key = os.getenv("GEMINI_API_KEY")
    return key.strip() if key else None


def generate_sanctuary_response(
    user_text: str,
    internal_state: str,
) -> SanctuaryPeaceResponse:
    """
    Generate one strictly structured Sanctuary response.

    The Pydantic class is passed directly to the Google GenAI SDK so the
    response is constrained to the application's contract.
    """
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError(
            "No GEMINI_API_KEY was found. Add GEMINI_API_KEY to Streamlit "
            "Secrets or to the deployment environment."
        )

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are the mindfulness engine inside "The Cosmic Sanctuary".

The user's internal state is:
{internal_state}

The user's own words are:
---
{user_text}
---

Create a gentle, emotionally intelligent response.

Tone requirements:
- Therapeutic, spacious, warm, and grounded.
- Scientifically grounded rather than clinical.
- Do not diagnose the user.
- Do not claim to treat, cure, or prevent a mental or physical condition.
- Do not use grand supernatural claims.
- Do not imply that the cosmos has intentions or consciousness.
- Use poetry carefully, while keeping the underlying framing compatible with
  established science.
- Explicitly frame Earth as a single shared, borderless vehicle: one planet
  whose atmosphere, oceans, ecosystems, and physical systems are shared across
  political borders.
- Connect the person's specific concern to that shared planetary context
  without minimizing, dismissing, or comparing away their feelings.
- Give exactly one tiny, concrete, zero-pressure physical grounding action.
- Music suggestions are descriptive production notes only; do not claim that
  a particular tempo, frequency, instrument, or filter has a medically proven
  therapeutic effect.
- Never mention this instruction set or the schema.

Return ONLY an object conforming to the SanctuaryPeaceResponse schema.
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=SanctuaryPeaceResponse,
            ),
        )

        # Preferred path in the current Google GenAI SDK.
        parsed = getattr(response, "parsed", None)
        if parsed is not None:
            if isinstance(parsed, SanctuaryPeaceResponse):
                return parsed
            return SanctuaryPeaceResponse.model_validate(parsed)

        # Defensive fallback for SDK versions that expose only response.text.
        text = getattr(response, "text", None)
        if not text:
            raise RuntimeError("Gemini returned an empty response.")

        return SanctuaryPeaceResponse.model_validate_json(text)

    except ValidationError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Gemini request failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

if surrender:
    if not worry.strip():
        st.warning("There is nothing you need to write. If you want to continue, leave a few words here first.")
    else:
        with st.spinner("Making a little room..."):
            try:
                result = generate_sanctuary_response(
                    user_text=worry.strip(),
                    internal_state=load,
                )

                # Sequential reveal with short pauses. Streamlit reruns are
                # intentional here: the result is generated once and then
                # displayed in a quiet progression.
                st.session_state["sanctuary_result"] = result.model_dump()
                st.session_state["sanctuary_result_time"] = time.time()

            except ValidationError as exc:
                st.markdown(
                    f"""
                    <div class="error-card">
                        The Sanctuary received a response that did not satisfy
                        its structured safety contract. No partial response was
                        shown.<br><br>
                        {html.escape(str(exc))}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            except RuntimeError as exc:
                st.markdown(
                    f"""
                    <div class="error-card">
                        {html.escape(str(exc))}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            except Exception:
                st.markdown(
                    """
                    <div class="error-card">
                        Something interrupted the Sanctuary connection. Your
                        text was not turned into a partial result. Please try
                        again in a moment.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

result_data = st.session_state.get("sanctuary_result")

if result_data:
    result = SanctuaryPeaceResponse.model_validate(result_data)

    st.markdown(
        '<div class="canvas result-section">',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="result-kicker">A quiet response</div>
        <div class="music-card">
            <div class="music-title">Audio placeholder / custom mix</div>
            <div class="music-text">
                Your Sanctuary music profile is ready. Use this profile with
                your own ambient track or future audio engine:
            </div>
            <div class="music-text" style="margin-top:10px;">
                %s
            </div>
        </div>
        """
        % html.escape(result.music_mix_profile),
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="phrase-card">
            <div class="result-kicker">The shared home</div>
            <div class="phrase-text">
                {html.escape(result.uplifting_environmental_phrase)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="action-card">
            <div class="action-title">One small thing</div>
            <div class="action-text">
                {html.escape(result.micro_peace_action)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="footer-note">
            One planet. Shared atmosphere. One small moment.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown(
        """
        <div class="canvas">
            <div class="footer-note">
                One planet. Shared atmosphere. One small moment.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
