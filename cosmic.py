"""
THE COSMIC SANCTUARY
====================
A single-file Streamlit mindfulness experience.

Phase 1  — an immersive scroll portal: a photoreal Three.js Earth that slowly
           rotates, shrinks as you scroll, and seamlessly crossfades into a
           Swiss-style line-art brain.
Phase 2  — a quiet canvas to name your emotional load and write what you're
           carrying, sent to Gemini for a short, therapeutic reflection.

Setup
-----
    pip install streamlit google-genai pydantic

Add your Gemini key one of these ways:
    1) Environment variable:  export GOOGLE_API_KEY="your-key-here"
    2) .streamlit/secrets.toml:  GOOGLE_API_KEY = "your-key-here"
    3) Paste it into the "Connect your Gemini API key" box inside the app.

Run:
    streamlit run cosmic.py
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

    /* Streamlit widgets restyled to match the sanctuary */
    .stTextArea textarea {
        background: #101014 !important;
        border: 1px solid #1e1e24 !important;
        border-radius: 16px !important;
        color: #e5e5ea !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 1rem !important;
        padding: 1.1rem !important;
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
# 3. PHASE 1 — THE SCROLL PORTAL (Three.js Earth -> Swiss brain line art)
#    Fully self-contained: rendered inside its own scrolling component, so it
#    needs no access to the outer page — robust on any device or browser.
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
    transform: translateY(18px);
    transition: opacity 1s ease, transform 1s ease;
    font-size: clamp(1.25rem, 4vw, 2.05rem);
    font-weight: 300;
    letter-spacing: 0.01em;
    line-height: 1.55;
    max-width: 540px;
    text-shadow: 0 2px 26px rgba(0,0,0,0.65);
  }
  .line.show p { opacity: 1; transform: translateY(0); }
  .line.final p {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 400;
    font-size: clamp(1.35rem, 4.5vw, 2.2rem);
  }
</style>
</head>
<body>
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
    <div class="line final" data-i="3"><p>Leave whatever you are carrying right here.</p></div>
  </div>

</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
(function () {
  var canvas = document.getElementById('globeCanvas');
  var wrap = document.getElementById('globeWrap');
  var brain = document.getElementById('brainSvg');
  var hint = document.querySelector('.hint');
  var storyEl = document.getElementById('story');

  var scene, camera, renderer, earth, atmosphere, stars, clock;
  var ready = false;

  function initThree() {
    if (typeof THREE === 'undefined') { return; }

    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);
    camera.position.z = 3.1;

    renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

    var loader = new THREE.TextureLoader();
    var dayMap = loader.load('https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg');
    var bumpMap = loader.load('https://unpkg.com/three-globe/example/img/earth-topology.png');
    var specMap = loader.load('https://unpkg.com/three-globe/example/img/earth-water.png');

    var geo = new THREE.SphereGeometry(1, 64, 64);
    var mat = new THREE.MeshPhongMaterial({
      map: dayMap,
      bumpMap: bumpMap,
      bumpScale: 0.045,
      specularMap: specMap,
      specular: new THREE.Color(0x3b4d66),
      shininess: 9
    });
    earth = new THREE.Mesh(geo, mat);
    scene.add(earth);

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
    atmosphere = new THREE.Mesh(glowGeo, glowMat);
    scene.add(atmosphere);

    var starGeo = new THREE.BufferGeometry();
    var starCount = 900;
    var positions = new Float32Array(starCount * 3);
    for (var i = 0; i < starCount; i++) {
      var r = 40 + Math.random() * 60;
      var th = Math.random() * Math.PI * 2;
      var ph = Math.acos((Math.random() * 2) - 1);
      positions[i * 3] = r * Math.sin(ph) * Math.cos(th);
      positions[i * 3 + 1] = r * Math.sin(ph) * Math.sin(th);
      positions[i * 3 + 2] = r * Math.cos(ph);
    }
    starGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    var starMat = new THREE.PointsMaterial({ color: 0xffffff, size: 0.14, transparent: true, opacity: 0.55 });
    stars = new THREE.Points(starGeo, starMat);
    scene.add(stars);

    scene.add(new THREE.AmbientLight(0x445577, 0.9));
    var sun = new THREE.DirectionalLight(0xffffff, 1.35);
    sun.position.set(5, 3, 5);
    scene.add(sun);

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
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }

  function animate() {
    requestAnimationFrame(animate);
    var dt = Math.min(clock.getDelta(), 0.05);
    earth.rotation.y += dt * 0.06;
    atmosphere.rotation.y = earth.rotation.y;
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

  // ---- scroll-driven progress (fully internal to this component) ----
  function onScroll() {
    var scrollTop = document.documentElement.scrollTop || document.body.scrollTop;
    var max = storyEl.scrollHeight - window.innerHeight;
    var progress = max > 0 ? Math.min(Math.max(scrollTop / max, 0), 1) : 0;

    // globe never exceeds its inset box (clean margins at every size)
    var scale = 1.0 - progress * 0.72;
    scale = Math.max(scale, 0.28);
    wrap.style.transform = 'scale(' + scale + ')';

    var crossStart = 0.72, crossEnd = 0.98;
    var cp = (progress - crossStart) / (crossEnd - crossStart);
    cp = Math.min(Math.max(cp, 0), 1);
    canvas.style.opacity = String(1 - cp);
    brain.style.opacity = String(cp);
    setBrainDraw(cp);

    hint.classList.toggle('hidden', progress > 0.05);
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
})();
</script>
</body>
</html>
"""

components.html(SCROLL_PORTAL_HTML, height=760, scrolling=True)


# ============================================================================
# 4. PYDANTIC CONTRACT + GEMINI CALL
# ============================================================================

class SanctuaryPeaceResponse(BaseModel):
    uplifting_environmental_phrase: str = Field(
        description="A deeply comforting, poetic phrase connecting the user's specific worry "
                    "to the timeless beauty of the earth and cosmos."
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
    "happening on the same small, unified world as everyone else's. Do not diagnose, do not "
    "give clinical or medical advice, do not mention therapy or medication. Keep every field "
    "short -- a phrase or a sentence, never an essay."
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
