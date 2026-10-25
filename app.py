import html
import json
import math
import re
import urllib.parse
import base64
import mimetypes
import textwrap
from pathlib import Path

import pandas as pd
import streamlit as st

from recommender import get_recommendations, get_dataset_stats, get_available_count, get_areas

st.set_page_config(page_title='TripSense — Mumbai', page_icon='🧭', layout='wide', initial_sidebar_state='expanded')

# -------------------- premium theme --------------------
st.markdown(r'''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@600;700;800&display=swap');
:root{--bg:#f4f7fb;--panel:#fff;--line:#dfe5ee;--text:#172033;--muted:#68758a;--blue:#4169e1;--pink:#ef4f91}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif}
.stApp{background:radial-gradient(circle at 92% 0%,rgba(92,116,235,.10),transparent 25%),radial-gradient(circle at 0% 38%,rgba(239,79,145,.055),transparent 25%),linear-gradient(135deg,#f8fafc 0%,#f2f5fa 55%,#edf2f8 100%);color:var(--text)}
[data-testid="stHeader"]{background:rgba(248,250,252,.88)!important}
[data-testid="stSidebar"]{background:rgba(255,255,255,.96)!important;border-right:1px solid #e3e8f0!important}
[data-testid="stSidebar"]>div:first-child{padding:1.25rem 1.05rem}
.block-container{max-width:1500px;padding:1rem 1.4rem 4rem}

/* Sidebar */
.sidebar-brand{padding:7px 8px 21px}.brand-row{display:flex;align-items:center;gap:12px}
.brand-orb{width:40px;height:40px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#ffd34a,#ff963c);box-shadow:0 8px 28px rgba(255,166,55,.25);font-size:22px}
.brand-name{font-family:'Manrope';font-size:25px;font-weight:800;color:#16213a}.brand-sub{font-size:10px;letter-spacing:1.65px;font-weight:800;color:#8a96a9;margin:6px 0 0 1px}
.sidebar-step{font-size:10px;letter-spacing:1.5px;font-weight:800;color:#8995a8;margin:18px 0 7px 5px}
.sidebar-nav{display:grid;gap:4px;margin:2px 0 10px}.nav-item{padding:10px 12px;border-radius:11px;color:#344054;font-size:13px;font-weight:600}.nav-item.active{background:#eef2ff;color:#2647a8}
.sidebar-note{margin-top:22px;padding:16px 15px;border:1px solid #e1e7ef;border-radius:16px;background:linear-gradient(145deg,#fff,#f6f8fb);color:#68758a;font-size:12px;line-height:1.55;box-shadow:0 8px 24px rgba(31,48,79,.05)}.sidebar-note b{color:#24314a}

/* Hero */
.hero{position:relative;overflow:hidden;min-height:178px;padding:30px 36px 28px;border:1px solid #e3e7ef;border-radius:25px;background:linear-gradient(105deg,#fffaf8,#f7f8ff 52%,#eff1ff);box-shadow:0 20px 55px rgba(39,55,85,.10);margin-bottom:20px}
.hero:after{content:"";position:absolute;inset:0;pointer-events:none;background:linear-gradient(90deg,rgba(255,255,255,.05),rgba(255,255,255,.2))}
.hero-skyline{position:absolute;right:-2%;bottom:-1px;width:52%;height:75%;opacity:.20;background:linear-gradient(180deg,transparent 0 25%,#7485dc 25% 100%);clip-path:polygon(0 100%,0 63%,5% 63%,5% 48%,10% 48%,10% 70%,14% 70%,14% 34%,19% 34%,19% 57%,23% 57%,23% 19%,27% 19%,27% 61%,31% 61%,31% 42%,36% 42%,36% 68%,40% 68%,40% 30%,45% 30%,45% 54%,49% 54%,49% 11%,53% 11%,53% 55%,57% 55%,57% 36%,62% 36%,62% 67%,66% 67%,66% 26%,70% 26%,70% 59%,74% 59%,74% 44%,79% 44%,79% 69%,84% 69%,84% 31%,88% 31%,88% 57%,93% 57%,93% 40%,100% 40%,100% 100%)}
.hero-content{position:relative;z-index:2;max-width:790px}.hero-kicker{font-size:12px;font-weight:800;letter-spacing:1.9px;color:#8b96a9}
.hero h1{font-family:'Manrope';font-size:47px;line-height:1.02;margin:7px 0 8px;color:#172033;letter-spacing:-1.5px}.hero h1 span{background:linear-gradient(90deg,#ef5b72,#7569e8);-webkit-background-clip:text;color:transparent}
.hero p{font-size:15px;color:#66748a;margin:0}.hero-pills{display:flex;gap:8px;flex-wrap:wrap;margin-top:17px}.hero-pill{padding:7px 11px;border-radius:999px;background:rgba(255,255,255,.78);border:1px solid #e0e5ed;font-size:11px;font-weight:800;color:#344054;box-shadow:0 4px 12px rgba(37,52,78,.05)}

/* Filters */
.filter-panel{padding:18px 18px 16px;border:1px solid #e0e6ee;border-radius:22px;background:rgba(255,255,255,.95);box-shadow:0 15px 42px rgba(39,55,85,.08);margin-top:18px}
.filter-title{font-family:'Manrope';font-size:23px;font-weight:800;color:#172033}.filter-sub{font-size:13px;color:#718096;margin-top:3px;margin-bottom:15px}
.filter-box{padding:14px 16px 13px;border:1px solid #e0e6ee;border-radius:17px;background:#f8fafc;min-height:104px}.filter-box.area{background:linear-gradient(145deg,#fff7f5,#fffafa);border-color:#ffd9d2}.filter-box.interest{background:linear-gradient(145deg,#f4f6ff,#f8f9ff);border-color:#d9e0ff}.filter-box.weather{background:linear-gradient(145deg,#f0fbf8,#f7fcfb);border-color:#d3eee5}
.filter-box-title{display:flex;align-items:center;gap:9px;font-size:18px;font-weight:800;color:#172033}.filter-box-sub{font-size:11px;color:#8995a8;margin:3px 0 9px 31px}.filter-icon{font-size:25px}
.active-row{display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:12px 14px;border:1px solid #e0e6ee;border-radius:16px;background:#f8fafc;margin-top:14px}.active-label{font-weight:800;color:#344054;font-size:12px;margin-right:2px}.active-pill{padding:8px 12px;border-radius:999px;border:1px solid #cbd7ff;background:#f1f4ff;color:#2e50b2;font-size:11px;font-weight:800}
[data-testid="stHorizontalBlock"]{gap:12px}.filter-panel [data-testid="stHorizontalBlock"]{gap:14px}

/* Native selectboxes */
[data-testid="stSelectbox"] [data-baseweb="select"]{background:#fff!important;border:1px solid #cfd7e3!important;border-radius:12px!important;box-shadow:0 3px 10px rgba(39,55,85,.04)!important}
[data-testid="stSelectbox"] [data-baseweb="select"] > div{background:#fff!important;border-color:transparent!important;color:#172033!important}
[data-testid="stSelectbox"] [data-baseweb="select"] *{color:#172033!important;-webkit-text-fill-color:#172033!important;opacity:1!important}
[data-testid="stSelectbox"] svg{fill:#7b8799!important;color:#7b8799!important}
[role="listbox"],[role="listbox"] *{background:#fff!important;color:#172033!important;-webkit-text-fill-color:#172033!important}
[role="option"]:hover,[role="option"][aria-selected="true"]{background:#f1f4ff!important;color:#172033!important}

/* Results/cards */
.section-head{display:flex;align-items:end;justify-content:space-between;gap:15px;margin:22px 0 12px}.section-title{font-family:'Manrope';font-size:27px;font-weight:800;color:#172033}.section-sub{color:#738095;font-size:13px;margin-top:3px}.see-count{border:1px solid #ccd7ff;color:#3555b7;border-radius:999px;padding:9px 15px;font-size:11px;font-weight:800;background:#f3f6ff}
.place-shell{position:relative;height:100%}.place-card{height:100%;overflow:hidden;border:1px solid #e0e6ee;border-radius:19px;background:#fff;box-shadow:0 12px 32px rgba(35,52,80,.09);padding:9px;transition:.18s ease}.place-card:hover{transform:translateY(-3px);border-color:#bccaff;box-shadow:0 20px 44px rgba(35,52,80,.14)}
.place-image{height:165px;width:100%;object-fit:cover;border-radius:13px;display:block;background:#eef2f7}.image-placeholder{height:165px;border-radius:13px;background:linear-gradient(135deg,#eef2ff,#fff0f3);display:flex;align-items:center;justify-content:center;font-size:42px}
.rank{position:absolute;left:18px;top:18px;z-index:4;width:35px;height:35px;border-radius:10px;background:#ffc94d;color:#172033;display:flex;align-items:center;justify-content:center;font-weight:900;box-shadow:0 8px 17px rgba(33,46,73,.20)}.rank.alt{background:#6f7be8;color:#fff}
.card-body{padding:12px 8px 6px}.place-name{font-family:'Manrope';font-size:18px;line-height:1.18;font-weight:800;color:#172033;min-height:22px}.badges{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0 7px}.badge{padding:5px 8px;border-radius:999px;background:#f1f4ff;color:#4058a5;font-size:10px;font-weight:800}.place-reason{color:#627087;font-size:12px;line-height:1.48;min-height:36px}.meta{color:#8290a4;font-size:10px;margin-top:10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.card-actions{display:flex;gap:7px;margin-top:10px}.map-link{flex:1;text-align:center;text-decoration:none!important;padding:8px 5px;border:1px solid #d4defa;border-radius:9px;background:#f4f6ff;color:#2e50a9!important;font-size:10px;font-weight:800}.map-link:hover{background:#eaf0ff;border-color:#b9c9f8}.popular{color:#c88700;font-size:10px;font-weight:800;margin-left:4px}.alt-card{border-color:#d8e2fb;background:linear-gradient(145deg,#fbfcff,#f6f8fd)}
.empty-photo{height:165px;border-radius:13px;background:linear-gradient(135deg,#eef2ff,#fff1f4);display:flex;align-items:center;justify-content:center;flex-direction:column;gap:4px;color:#8b96a9}.empty-photo .icon{font-size:36px}.empty-photo small{font-size:9px}

/* Native buttons: single clean control */
[data-testid="stButton"]{border:0!important;background:transparent!important;box-shadow:none!important;padding:0!important}
[data-testid="stButton"]>div{border:0!important;background:transparent!important;box-shadow:none!important;padding:0!important}
[data-testid="stButton"] button{width:100%!important;background:#fff!important;color:#26334a!important;-webkit-text-fill-color:#26334a!important;border:1px solid #d7deea!important;border-radius:11px!important;box-shadow:0 3px 10px rgba(39,55,85,.05)!important;font-weight:800!important}
[data-testid="stButton"] button *{color:#26334a!important;-webkit-text-fill-color:#26334a!important;background:transparent!important;border:0!important}
[data-testid="stButton"] button:hover{background:#f2f5ff!important;border-color:#bdcaff!important}
.note{padding:14px 16px;border-radius:15px;background:#f8fafc;border:1px solid #e1e7ef;color:#68758a;font-size:12px;line-height:1.55}
[data-testid="stExpander"]{border-color:#e0e6ee!important;background:#fff!important;border-radius:15px!important}
@media(max-width:1250px){.place-image,.image-placeholder,.empty-photo{height:150px}}@media(max-width:900px){.hero h1{font-size:38px}.hero{padding:28px}.hero-skyline{opacity:.12}.filter-box{min-height:96px}}

/* Functional sidebar + action controls */
.sidebar-action-wrap [data-testid="stButton"]{width:100%!important}
.sidebar-action-wrap [data-testid="stButton"] button{
 width:100%!important;min-height:42px!important;text-align:left!important;
 justify-content:flex-start!important;padding:9px 13px!important;
 border:1px solid transparent!important;border-radius:11px!important;
 background:transparent!important;color:#344054!important;
 -webkit-text-fill-color:#344054!important;box-shadow:none!important;
 font-size:13px!important;font-weight:700!important
}
.sidebar-action-wrap [data-testid="stButton"] button:hover{background:#f3f5fb!important;border-color:#e3e8f0!important}
.sidebar-action-wrap.active [data-testid="stButton"] button{background:#eef2ff!important;border-color:#dfe6ff!important;color:#2647a8!important;-webkit-text-fill-color:#2647a8!important}
.sidebar-interest-wrap [data-testid="stButton"] button{
 width:100%!important;min-height:38px!important;text-align:left!important;
 justify-content:flex-start!important;padding:7px 12px!important;
 border:1px solid transparent!important;border-radius:10px!important;
 background:transparent!important;color:#344054!important;
 -webkit-text-fill-color:#344054!important;box-shadow:none!important;
 font-size:12px!important;font-weight:600!important
}
.sidebar-interest-wrap [data-testid="stButton"] button:hover{background:#f7f8fc!important;border-color:#e6eaf0!important}
.page-panel{background:#fff;border:1px solid #e0e6ee;border-radius:22px;padding:26px;box-shadow:0 15px 42px rgba(39,55,85,.08);margin-top:18px}
.page-title{font-family:'Manrope';font-size:30px;font-weight:800;color:#172033;margin-bottom:5px}
.page-subtitle{font-size:13px;color:#718096;margin-bottom:20px}
.saved-card{border:1px solid #e0e6ee;border-radius:16px;background:#fff;padding:14px 16px;margin-bottom:10px;color:#172033}
.saved-card-title{font-weight:800;font-size:15px}.saved-card-meta{font-size:11px;color:#718096;margin-top:5px}
.empty-state{text-align:center;padding:42px 20px;border:1px dashed #ccd5e3;border-radius:16px;background:#f8fafc;color:#718096}
.card-native-actions{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:8px}
.card-native-actions [data-testid="stButton"] button{min-height:38px!important;padding:7px 8px!important;font-size:10px!important}

/* Rain/weather messaging — deliberately high-contrast and visually separated */
.weather-warning{
    display:flex;
    align-items:flex-start;
    gap:14px;
    margin:18px 0 20px;
    padding:17px 20px;
    border:1.5px solid #f2b84b;
    border-left:6px solid #f59e0b;
    border-radius:16px;
    background:linear-gradient(135deg,#fff8e7 0%,#fff3cf 100%);
    box-shadow:0 8px 24px rgba(245,158,11,.12);
}
.weather-warning-icon{
    flex:0 0 auto;
    width:38px;
    height:38px;
    display:flex;
    align-items:center;
    justify-content:center;
    border-radius:11px;
    background:#f59e0b;
    color:#fff;
    font-size:20px;
    box-shadow:0 5px 12px rgba(245,158,11,.22);
}
.weather-warning-title{
    color:#8a4b00!important;
    font-family:'Manrope',sans-serif;
    font-size:17px;
    line-height:1.2;
    font-weight:800;
    margin-bottom:4px;
}
.weather-warning-text{
    color:#6b4a16!important;
    font-size:12px;
    line-height:1.55;
    font-weight:600;
}

.no-results-banner{
    display:flex;
    align-items:center;
    gap:14px;
    margin:18px 0 20px;
    padding:16px 20px;
    border:1.5px solid #e5b83b;
    border-left:6px solid #d89b00;
    border-radius:15px;
    background:linear-gradient(135deg,#fff9df 0%,#fff4bd 100%);
    box-shadow:0 8px 22px rgba(180,135,0,.10);
}
.no-results-icon{
    flex:0 0 auto;
    width:38px;
    height:38px;
    border-radius:11px;
    display:flex;
    align-items:center;
    justify-content:center;
    background:#f0b323;
    color:#fff;
    font-size:20px;
    box-shadow:0 5px 12px rgba(180,135,0,.20);
}
.no-results-title{
    color:#704b00!important;
    font-family:'Manrope',sans-serif;
    font-size:16px;
    line-height:1.25;
    font-weight:800;
    margin-bottom:3px;
}
.no-results-text{
    color:#5f4a19!important;
    font-size:12px;
    line-height:1.5;
    font-weight:600;
}

.alternative-section{
    margin:28px 0 14px;
    padding:17px 20px;
    border:1.5px solid #c9d3ff;
    border-left:6px solid #6675e8;
    border-radius:16px;
    background:linear-gradient(135deg,#f2f5ff 0%,#eef0ff 100%);
    box-shadow:0 8px 24px rgba(92,105,210,.10);
}
.alternative-title{
    display:flex;
    align-items:center;
    gap:8px;
    color:#273c9c!important;
    font-family:'Manrope',sans-serif;
    font-size:20px;
    line-height:1.25;
    font-weight:800;
}
.alternative-sub{
    color:#52627d!important;
    font-size:12px;
    line-height:1.55;
    font-weight:600;
    margin-top:5px;
}

</style>''', unsafe_allow_html=True)

def render_html(content):
    return st.markdown(textwrap.dedent(str(content)).strip(), unsafe_allow_html=True)

DATA = pd.read_csv('data/mumbai_places.csv')
stats = get_dataset_stats()

CATEGORY_ICONS = {
    'Religious':'🛕','Nature':'🌿','Heritage':'🏛️','Food':'🍴','Beach':'🏖️','Wildlife':'🦁',
    'Shopping':'🛍️','Nightlife':'🎵','Entertainment':'🎭','Museum':'🏛️','Scenic':'📸','Sports':'⚽','Art':'🎨'
}
WEATHER_LABELS={'Any':'🌤️  Any','Sunny':'☀️  Sunny','Rainy':'🌧️  Rainy'}
areas=get_areas()

if 'shown_count' not in st.session_state: st.session_state.shown_count=6
if 'active_filters' not in st.session_state: st.session_state.active_filters=None
if 'has_searched' not in st.session_state: st.session_state.has_searched=False
if 'page' not in st.session_state: st.session_state.page='discover'
if 'saved_places' not in st.session_state: st.session_state.saved_places=[]
if 'itinerary' not in st.session_state: st.session_state.itinerary=[]



def esc(v): return html.escape(str(v))
def maps_url(name, area='Mumbai'):
    return 'https://www.google.com/maps/search/?api=1&query='+urllib.parse.quote_plus(f'{name}, {area}, Mumbai')
def route_url(name, origin):
    return 'https://www.google.com/maps/dir/?api=1&origin='+urllib.parse.quote_plus(str(origin))+ '&destination='+urllib.parse.quote_plus(f'{name}, Mumbai')

# The image library is local when download_images.py has been run. A small JSON
# manifest can also provide a remote image for a place that has a verified source.
IMAGE_DIR=Path('data/images')
IMAGE_MANIFEST=Path('data/image_sources.json')
IMAGE_ACCURACY_OVERRIDES=Path('data/image_accuracy_overrides.json')

def _slug(name):
    s=re.sub(r'[^a-z0-9]+','_',str(name).lower()).strip('_')
    return s or 'place'

@st.cache_data(ttl=3600, show_spinner=False)
def get_image(name, category, area=''):
    """Return a browser-safe image source.

    Streamlit does not expose arbitrary files under data/images/ as public
    browser URLs.  The old implementation returned a filesystem-relative
    path (e.g. data/images/cafe_madras.jpg), which caused broken-image icons
    in the HTML cards.  Local images are therefore embedded as data URIs.
    Verified remote manifest URLs are used only as a fallback.
    """
    # 0. Accuracy overrides: verified place-specific images always win.
    # This lets us correct a bad local image without deleting the user's existing image library or manifest.
    if IMAGE_ACCURACY_OVERRIDES.exists():
        try:
            overrides=json.loads(IMAGE_ACCURACY_OVERRIDES.read_text(encoding='utf-8'))
            entry=overrides.get(str(name))
            src=entry.get('url') if isinstance(entry,dict) else entry
            if isinstance(entry, dict) and entry.get('block'):
                return None
            if src:
                return src
        except Exception:
            pass

    # 1. Existing verified manifest
    if IMAGE_MANIFEST.exists():
        try:
            data=json.loads(IMAGE_MANIFEST.read_text(encoding='utf-8'))
            src=data.get(str(name),{}).get('url') if isinstance(data.get(str(name)),dict) else data.get(str(name))
            if src: return src
        except Exception:
            pass

    # 2. Local image library
    slug=_slug(name)
    for ext in ('jpg','jpeg','png','webp'):
        p=IMAGE_DIR/f'{slug}.{ext}'
        if p.exists() and p.stat().st_size>5000:
            try:
                mime=mimetypes.guess_type(p.name)[0] or 'image/jpeg'
                encoded=base64.b64encode(p.read_bytes()).decode('ascii')
                return f'data:{mime};base64,{encoded}'
            except Exception:
                pass

    return None


def budget_icon(level):
    s=str(level).lower()
    if 'free' in s: return 'Free'
    if 'budget' in s or 'low' in s: return '₹'
    if 'mid' in s or 'medium' in s: return '₹₹'
    if 'premium' in s or 'luxury' in s or 'high' in s: return '₹₹₹'
    return '₹₹'


def render_card(row, rank, alternative=False):
    name=str(row.get('name','Place')); category=str(row.get('primary_category','Mumbai')); area=str(row.get('area','Mumbai'))
    image=get_image(name,category,area)
    popularity=row.get('popularity_score','')
    popular=False
    try: popular=float(popularity)>=8
    except Exception: pass
    duration=row.get('duration_hours','')
    env=str(row.get('indoor_outdoor',''))
    budget=budget_icon(row.get('budget_level',''))
    reason=str(row.get('reason','A relevant match for your preferences.'))
    if image:
        image_html=f'<img class="place-image" src="{esc(image)}" alt="{esc(name)}" loading="lazy">'
    else:
        image_html=f'<div class="empty-photo"><div class="icon">{CATEGORY_ICONS.get(category,"📍")}</div><small>Place photo not yet in local library</small></div>'
    meta=f'🌿 {esc(env)}  •  ⏱️ {esc(duration)} hrs  •  💰 {esc(budget)}'
    if popular: meta += '  •  ⭐ Popular'
    route=route_url(name,area) if area and area!='nan' else ''
    action=maps_url(name,area)
    rank_cls='alt' if alternative else ''
    return f'''<div class="place-shell"><div class="rank {rank_cls}">{rank}</div><div class="place-card {"alt-card" if alternative else ""}">{image_html}<div class="card-body"><div class="place-name">{esc(name)}{' <span class="popular">⭐ Popular</span>' if popular else ''}</div><div class="badges"><span class="badge">📍 {esc(area)}</span><span class="badge">{CATEGORY_ICONS.get(category,"🏷️")} {esc(category)}</span></div><div class="place-reason">{'🌧️ ' if alternative else ''}{esc(reason)}</div><div class="meta">{meta}</div><div class="card-actions"><a class="map-link" href="{action}" target="_blank">🗺️ Open in Google Maps ↗</a>{f'<a class="map-link" href="{route}" target="_blank">🚕 Route from {esc(area)}</a>' if route else ''}</div></div></div></div>'''

# -------------------- sidebar navigation --------------------
with st.sidebar:
    st.markdown(
        '<div class="sidebar-brand"><div class="brand-row"><div class="brand-orb">🧭</div>'
        '<div class="brand-name">TripSense</div></div>'
        '<div class="brand-sub">MUMBAI TRAVEL INTELLIGENCE</div></div>',
        unsafe_allow_html=True
    )
    st.markdown('<div class="sidebar-step">EXPLORE</div>', unsafe_allow_html=True)

    def sidebar_page_button(key, label, icon):
        active = st.session_state.page == key
        cls = "sidebar-action-wrap active" if active else "sidebar-action-wrap"
        st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
        clicked = st.button(f"{icon}  {label}", key=f"sidebar_page_{key}", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        if clicked:
            st.session_state.page = key
            st.rerun()

    sidebar_page_button("discover", "Discover", "🏠")
    sidebar_page_button("saved", "Saved Places", "🔖")
    sidebar_page_button("itinerary", "My Itinerary", "🗺️")
    sidebar_page_button("about", "About", "ℹ️")

    st.markdown('<div class="sidebar-step" style="margin-top:22px">EXPLORE BY INTEREST</div>', unsafe_allow_html=True)
    for c in stats['categories']:
        st.markdown('<div class="sidebar-interest-wrap">', unsafe_allow_html=True)
        if st.button(f'{CATEGORY_ICONS.get(c,"✨")}  {c}', key=f"sidebar_interest_{c}", use_container_width=True):
            st.session_state.page = "discover"
            st.session_state.main_interest = f'{CATEGORY_ICONS.get(c,"✨")}  {c}'
            st.session_state.shown_count = 8
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="sidebar-note"><b>💡 About TripSense</b><br><br>'
        'Personalized recommendations combine semantic relevance, weather suitability and popularity.'
        '<br><br><b>📍 Area + weather</b><br>Choose them in the main control panel.</div>',
        unsafe_allow_html=True
    )

# -------------------- functional sidebar pages --------------------
if st.session_state.page == "saved":
    st.markdown(
        '<div class="page-panel"><div class="page-title">🔖 Saved Places</div>'
        '<div class="page-subtitle">Places you saved while exploring Mumbai.</div>',
        unsafe_allow_html=True
    )
    if not st.session_state.saved_places:
        st.markdown(
            '<div class="empty-state"><div style="font-size:36px">🔖</div>'
            '<b>No saved places yet</b><br>'
            'Tap Save on any recommendation and it will appear here.</div>',
            unsafe_allow_html=True
        )
    else:
        for place in st.session_state.saved_places:
            st.markdown(
                f'<div class="saved-card"><div class="saved-card-title">📍 {esc(place["name"])}</div>'
                f'<div class="saved-card-meta">{esc(place["area"])} • {esc(place["category"])}</div></div>',
                unsafe_allow_html=True
            )
            if st.button("🗑️ Remove", key=f"remove_saved_{place['name']}", use_container_width=False):
                st.session_state.saved_places = [x for x in st.session_state.saved_places if x["name"] != place["name"]]
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

if st.session_state.page == "itinerary":
    st.markdown(
        '<div class="page-panel"><div class="page-title">🗺️ My Itinerary</div>'
        '<div class="page-subtitle">Places you have added to your Mumbai plan.</div>',
        unsafe_allow_html=True
    )
    if not st.session_state.itinerary:
        st.markdown(
            '<div class="empty-state"><div style="font-size:36px">🗺️</div>'
            '<b>Your itinerary is empty</b><br>'
            'Add places from the recommendation cards to build your plan.</div>',
            unsafe_allow_html=True
        )
    else:
        for i, place in enumerate(st.session_state.itinerary, 1):
            st.markdown(
                f'<div class="saved-card"><div class="saved-card-title">{i}. 📍 {esc(place["name"])}</div>'
                f'<div class="saved-card-meta">{esc(place["area"])} • {esc(place["category"])}</div></div>',
                unsafe_allow_html=True
            )
            if st.button("✕ Remove", key=f"remove_itinerary_{place['name']}", use_container_width=False):
                st.session_state.itinerary = [x for x in st.session_state.itinerary if x["name"] != place["name"]]
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

if st.session_state.page == "about":
    st.markdown(
        '<div class="page-panel"><div class="page-title">ℹ️ About TripSense</div>'
        '<div class="page-subtitle">Mumbai Travel Intelligence</div>'
        '<p style="color:#627087;line-height:1.7">'
        'TripSense recommends Mumbai places using semantic relevance, weather suitability, '
        'area filtering and popularity. Use Explore by Interest for quick discovery, '
        'Save to bookmark places, and Add to itinerary to build a personal plan.'
        '</p></div>',
        unsafe_allow_html=True
    )
    st.stop()

# -------------------- hero + controls --------------------
st.markdown('''<div class="hero"><div class="hero-skyline"></div><div class="hero-content"><div class="hero-kicker">MUMBAI TRAVEL INTELLIGENCE</div><h1>Explore Mumbai <span>Differently.</span></h1><p>Find places that match your interests, your area and today’s weather.</p><div class="hero-pills"><span class="hero-pill">⭐ Personalized recommendations</span><span class="hero-pill">☁️ Weather-aware</span><span class="hero-pill">📍 Area-wise results</span></div></div></div>''',unsafe_allow_html=True)

areas=get_areas()
area_options=[f'📍  {a}' for a in areas]
weather_options=list(WEATHER_LABELS.values())

# Large three-part preference panel — no food-type sub-filter.
st.markdown('''<div class="filter-panel"><div class="filter-title">🎚️ Find your perfect Mumbai experience</div><div class="filter-sub">Set your preferences below to get personalized recommendations.</div>''',unsafe_allow_html=True)
f1,f2,f3=st.columns([1,1,1])
with f1:
    st.markdown('<div class="filter-box area"><div class="filter-box-title"><span class="filter-icon">📍</span> Area</div><div class="filter-box-sub">Select one area</div>',unsafe_allow_html=True)
    area_label=st.selectbox('Area',area_options,index=0,key='main_area',label_visibility='collapsed')
    area=area_label.split('  ',1)[1]
    st.markdown('</div>',unsafe_allow_html=True)
with f2:
    st.markdown('<div class="filter-box interest"><div class="filter-box-title"><span class="filter-icon">🎯</span> Interest</div><div class="filter-box-sub">What are you in the mood for?</div>',unsafe_allow_html=True)
    interest_options=[f'{CATEGORY_ICONS.get(c,"✨")}  {c}' for c in stats['categories']]
    interest_label=st.selectbox('Interest',interest_options,index=0,key='main_interest',label_visibility='collapsed')
    interest=interest_label.split('  ',1)[1]
    st.markdown('</div>',unsafe_allow_html=True)
with f3:
    st.markdown('<div class="filter-box weather"><div class="filter-box-title"><span class="filter-icon">🌦️</span> Weather</div><div class="filter-box-sub">Filter by weather conditions</div>',unsafe_allow_html=True)
    weather_label=st.selectbox('Weather',weather_options,index=0,key='main_weather',label_visibility='collapsed')
    weather=weather_label.split('  ',1)[1]
    st.markdown('</div>',unsafe_allow_html=True)
st.markdown('</div>',unsafe_allow_html=True)

filters=(interest,area,weather)
# Controls are live: Streamlit reruns whenever a selection changes.
previous_filters=st.session_state.get('last_filters')
if previous_filters is not None and previous_filters != filters:
    st.session_state.shown_count=8
st.session_state.active_filters=filters
st.session_state.last_filters=filters
st.session_state.has_searched=True

# Active filter strip matching the reference design.
st.markdown(f'''<div class="active-row"><span class="active-label">Active filters:</span><span class="active-pill">📍 {esc(area)}</span><span class="active-pill">{CATEGORY_ICONS.get(interest,"✨")} {esc(interest)}</span><span class="active-pill">{WEATHER_LABELS.get(weather,weather)}</span></div>''',unsafe_allow_html=True)

active_interest,active_area,active_weather=st.session_state.active_filters
results=get_recommendations(active_interest,weather=active_weather,area=active_area,top_k=st.session_state.shown_count)
if results.empty:
    st.markdown(
        '<div class="no-results-banner">'
        '<div class="no-results-icon">⚠️</div>'
        '<div>'
        '<div class="no-results-title">No matching places found</div>'
        '<div class="no-results-text">Try “Anywhere in Mumbai”, another interest, or a different weather setting.</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.stop()

direct=results[results.recommendation_type=='Direct match'].copy()
alts=results[results.recommendation_type=='Weather-friendly alternative'].copy()
available=get_available_count(active_interest, active_area)
# Only show the current page of direct recommendations. The See more button
# below increases this value, so it now has real visible effect.
direct_display = direct.head(st.session_state.shown_count).copy()

# The selected interest always comes first. Rainy-weather alternatives are
# deliberately rendered in a separate section so they are never mistaken
# for direct matches.
# Only show a rain warning when the displayed direct matches actually
# include outdoor or partly-outdoor destinations. Indoor-only interests
# such as Museum should not trigger a generic warning.
show_rain_warning = False
if active_weather == "Rainy" and not direct_display.empty and "indoor_outdoor" in direct_display.columns:
    environment_values = (
        direct_display["indoor_outdoor"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.casefold()
    )
    show_rain_warning = environment_values.str.contains("outdoor", na=False).any()

if show_rain_warning:
    st.markdown(
        '<div class="weather-warning">'
        '<span class="weather-warning-icon">🌧️</span>'
        '<div><div class="weather-warning-title">Weather warning</div>'
        '<div class="weather-warning-text">Some of these matches are outdoor or partly-outdoor destinations and may be less suitable in rainy weather. Check current conditions before visiting.</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )

# ------------------------------------------------------------
# DIRECT MATCHES
# ------------------------------------------------------------
st.markdown(
    f'<div class="section-head"><div><div class="section-title">✨ Top picks for {esc(active_interest)}</div><div class="section-sub">These places directly match your selected interest.</div></div><div class="see-count">See all recommendations ({available}) →</div></div>',
    unsafe_allow_html=True,
)

for start in range(0,len(direct_display),4):
    cols=st.columns(4)
    batch=direct_display.iloc[start:start+4]
    for offset,(col,(_,row)) in enumerate(zip(cols,batch.iterrows())):
        with col:
            render_html(render_card(row,start+offset+1,False))
            place_key = str(row.get('name','Place'))
            place_payload = {"name": place_key, "area": str(row.get('area','Mumbai')), "category": str(row.get('primary_category','Mumbai'))}
            st.markdown('<div class="card-native-actions">', unsafe_allow_html=True)
            a1, a2 = st.columns(2)
            with a1:
                saved_now = any(x["name"] == place_key for x in st.session_state.saved_places)
                if st.button("🔖 Saved" if saved_now else "🔖 Save", key=f"save_direct_{start}_{offset}_{place_key}", use_container_width=True):
                    if not saved_now:
                        st.session_state.saved_places.append(place_payload)
                    st.rerun()
            with a2:
                added_now = any(x["name"] == place_key for x in st.session_state.itinerary)
                if st.button("🗺️ Added" if added_now else "🗺️ Add to itinerary", key=f"itin_direct_{start}_{offset}_{place_key}", use_container_width=True):
                    if not added_now:
                        st.session_state.itinerary.append(place_payload)
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------
# WEATHER-FRIENDLY ALTERNATIVES — SEPARATE SECTION
# ------------------------------------------------------------
if active_weather == "Rainy" and not alts.empty:
    st.markdown(
        '<div class="alternative-section">'
        '<div class="alternative-title">🌧️ Better options for rainy weather</div>'
        '<div class="alternative-sub">These do not replace your selected interest. They are separate indoor or weather-friendly suggestions that may be more comfortable today.</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    for start in range(0,len(alts),4):
        cols=st.columns(4)
        batch=alts.iloc[start:start+4]
        for offset,(col,(_,row)) in enumerate(zip(cols,batch.iterrows())):
            with col:
                render_html(render_card(row,start+offset+1,True))
                place_key = str(row.get('name','Place'))
                place_payload = {"name": place_key, "area": str(row.get('area','Mumbai')), "category": str(row.get('primary_category','Mumbai'))}
                st.markdown('<div class="card-native-actions">', unsafe_allow_html=True)
                a1, a2 = st.columns(2)
                with a1:
                    saved_now = any(x["name"] == place_key for x in st.session_state.saved_places)
                    if st.button("🔖 Saved" if saved_now else "🔖 Save", key=f"save_alt_{start}_{offset}_{place_key}", use_container_width=True):
                        if not saved_now:
                            st.session_state.saved_places.append(place_payload)
                        st.rerun()
                with a2:
                    added_now = any(x["name"] == place_key for x in st.session_state.itinerary)
                    if st.button("🗺️ Added" if added_now else "🗺️ Add to itinerary", key=f"itin_alt_{start}_{offset}_{place_key}", use_container_width=True):
                        if not added_now:
                            st.session_state.itinerary.append(place_payload)
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

if available>st.session_state.shown_count:
    if st.button('🔽  See more places',use_container_width=True):
        st.session_state.shown_count += 6
        st.rerun()


with st.expander('📊 About the recommendation system'):
    st.write('TripSense combines semantic similarity with weather suitability and popularity. Selecting an area filters candidates before ranking. Direct matches remain category-specific; rainy-day alternatives come from weather-friendly categories.')
    st.write(f"Dataset: {stats.get('total_places', 0)} places across {stats.get('total_areas', 0)} areas and {stats.get('total_categories', 0)} categories.")
