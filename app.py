import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import base64
from pathlib import Path

# -----------------------------
# LOAD DATA
# -----------------------------
@st.cache_data
def load_data():
    df = pd.read_excel("food_data.xlsx")
    df.columns = [c.strip() for c in df.columns]
    return df

data = load_data()

st.set_page_config(page_title="Calorie Tracker", layout="wide")

# -----------------------------
# TOPBAR LOGO (base64 embed) + STYLING
# -----------------------------
logo_path = Path("logo.png")
logo_b64 = None
if logo_path.exists():
    logo_b64 = base64.b64encode(logo_path.read_bytes()).decode()

st.markdown(
    f"""
<style>
    /* HIDE STREAMLIT DEFAULT HEADER */
    header[data-testid="stHeader"] {{
        display: none !important;
    }}

    /* GLOBAL FONT AND BACKGROUND */
    html, body, [class*="st-"] {{
        font-family: 'Baskerville', serif !important;
        background-color: #0d3b2e !important;
        color: #e8cc99 !important;
    }}

    /* ensure main content is pushed below sticky topbar */
.block-container {{
    padding-top: 50px !important;  /* reduced space above logo */
    background-color: #0d3b2e !important;
}}


    /* Custom Top Bar */
    .custom-topbar {{
        width: 100%;
        background-color: #0d3b2e;
        border-bottom: 1px solid #165e4b;
        text-align: center;
        padding: 12px 0;
        position: sticky;
        top: 0;
        z-index: 9999;
        display: flex;
        justify-content: center;
        align-items: center;
    }}
    .custom-topbar img {{
        height: 64px;
        width: auto;
        display: inline-block;
        margin: 0 12px;
    }}
    .custom-topbar .title {{
        font-size: 20px;
        color: #e8cc99;
        margin-left: 8px;
        font-weight: 600;
    }}

    /* Dropdowns */
    div[data-baseweb="select"] > div {{
        background-color: #165e4b !important;
        color: #e8cc99 !important;
        border-radius: 6px !important;
        border: 1px solid #26705b !important;
    }}

    /* Plus / Minus Buttons */
    div[data-testid="column"] > div > button {{
        background-color: #26705b !important;
        color: #e8cc99 !important;
        border: 1px solid #358c71 !important;
        border-radius: 50% !important;
        height: 30px !important;
        width: 30px !important;
        font-size: 16px !important;
        line-height: 1px !important;
    }}
    div[data-testid="column"] > div > button:hover {{
        background-color: #3da081 !important;
        border-color: #52bca3 !important;
        color: #fff !important;
    }}

    button[kind="secondary"]:hover, .stDownloadButton button:hover {{
        # background-color: #1f6e5b !important;
        color: #fff !important;
        border-color: #3da081 !important;
    }}

    /* Food Name & Serving Label */
    .food-name {{
        font-size: 15px;
        color: #e8cc99;
        font-weight: 600;
    }}
    .serving-label {{
        font-size: 13px;
        color: #d8b87f;
    }}

    /* Sidebar (if used) */
    section[data-testid="stSidebar"] {{
        background-color: #0d3b2e !important;
        color: #e8cc99 !important;
        border-right: 1px solid #165e4b !important;
    }}

    /* Metric box values */
    [data-testid="stMetricValue"] {{
        color: #e8cc99 !important;
    }}

    /* small responsive tweak for the topbar on very small screens */
    @media (max-width: 480px) {{
        .custom-topbar img {{ height: 44px; }}
        .custom-topbar .title {{ font-size: 16px; }}
        .block-container {{ padding-top: 90px !important; }}
    }}
</style>
""",
    unsafe_allow_html=True,
)

# render custom topbar (embed base64 image so raw HTML shows image reliably)
if logo_b64:
    st.markdown(
        f"""
        <div class="custom-topbar">
            <img src="data:image/png;base64,{logo_b64}" alt="Logo">

        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    # fallback - show topbar with text and a helpful error
    st.markdown(
        """
        <div class="custom-topbar">
            <div style="display:flex; align-items:center; gap:12px;">

            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.error("logo.png not found — please make sure 'logo.png' is present in the app folder (filename is case-sensitive).")

# -----------------------------
# APP CONTENT
# -----------------------------

st.markdown(
    """
    <div style="
        text-align: left;
        font-size: 36px;
        font-weight: 700;
        color: #e8cc99;
        margin-top: 40px;
        margin-bottom: 10px;
        font-family: 'Baskerville', serif;
    ">
        🍽️ Daily Calorie Tracker
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style="
        text-align: left;
        color: #d8b87f;
        font-size: 16px;
        margin-bottom: 35px;
        font-family: 'Baskerville', serif;
    ">
        Add meals throughout the day - your inputs are saved until you reset.
    </p>
    """,
    unsafe_allow_html=True
)


meals = ["Meal 1", "Meal 2", "Meal 3", "Meal 4", "Meal 5", "Add On"]

# Initialize session state
if "meal_servings" not in st.session_state:
    st.session_state["meal_servings"] = {meal: {} for meal in meals}

# Reset button
if st.button("🔄 Reset All Meals"):
    st.session_state["meal_servings"] = {meal: {} for meal in meals}
    for meal in meals:
        st.session_state[f"items_{meal}"] = []

# -----------------------------
# MEAL SECTIONS
# -----------------------------
for meal in meals:
    st.markdown(f"### {meal}")

    items = st.multiselect(
        f"Select items for {meal}",
        options=data["Protein Options"].dropna().unique(),
        default=st.session_state.get(f"items_{meal}", []),
        key=f"items_{meal}"
    )

    # Keep state in sync
    for removed_item in list(st.session_state["meal_servings"][meal].keys()):
        if removed_item not in items:
            del st.session_state["meal_servings"][meal][removed_item]

    for new_item in items:
        if new_item not in st.session_state["meal_servings"][meal]:
            st.session_state["meal_servings"][meal][new_item] = 1

    # Inline serving controls
    for item in items:
        c1, c2, c3, c4 = st.columns([3, 0.5, 0.5, 1])
        with c1:
            st.markdown(f"<div class='food-name'>{item}</div>", unsafe_allow_html=True)
        with c2:
            if st.button("➖", key=f"minus_{meal}_{item}"):
                st.session_state["meal_servings"][meal][item] = max(0, st.session_state["meal_servings"][meal][item] - 1)
        with c3:
            if st.button("➕", key=f"plus_{meal}_{item}"):
                st.session_state["meal_servings"][meal][item] += 1
        with c4:
            servings = st.session_state["meal_servings"][meal][item]
            st.markdown(f"<div class='serving-label'>{servings} serving(s)</div>", unsafe_allow_html=True)

# -----------------------------
# TOTAL CALCULATION
# -----------------------------
total_cal, total_pro, total_fat, total_carb = 0, 0, 0, 0
for meal in meals:
    for item, servings in st.session_state["meal_servings"][meal].items():
        row = data[data["Protein Options"] == item].iloc[0]
        total_cal += row["Calories"] * servings
        total_pro += row["Protein"] * servings
        total_fat += row["Fat"] * servings
        total_carb += row["Carb"] * servings

# -----------------------------
# SUMMARY
# -----------------------------
st.markdown("---")
st.markdown("## 📈 Daily Summary")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Calories", f"{total_cal:.0f}")
c2.metric("Protein (g)", f"{total_pro:.1f}")
c3.metric("Fat (g)", f"{total_fat:.1f}")
c4.metric("Carbs (g)", f"{total_carb:.1f}")

# -----------------------------
# DOWNLOAD SUMMARY IMAGE (RICH, BRANDED)
# -----------------------------
def create_table_image_from_state(df, meal_state, logo_path=Path("logo.png")):
    # Colors
    bg_hex = "#0d3b2e"
    text_hex = "#e8cc99"
    accent_hex = "#ffd780"
    line_hex = "#165e4b"
    subtext_hex = "#d8b87f"

    # Convert hex to RGB
    def hx(h): return tuple(int(h.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    bg, text_col, accent, line_col, subtext = map(hx, [bg_hex, text_hex, accent_hex, line_hex, subtext_hex])

    # Build meal data
    rows = []
    overall = {"cal": 0, "pro": 0, "fat": 0, "carb": 0}
    for meal, items in meal_state.items():
        meal_rows, meal_tot = [], {"cal": 0, "pro": 0, "fat": 0, "carb": 0}
        if items:
            for item_name, servings in items.items():
                match = df[df["Protein Options"] == item_name]
                if not match.empty:
                    r = match.iloc[0]
                    cal, pro, fat, carb = [float(r.get(k, 0)) * servings for k in ["Calories", "Protein", "Fat", "Carb"]]
                else:
                    cal = pro = fat = carb = 0
                meal_rows.append((item_name, servings, cal, pro, fat, carb))
                for k, v in zip(["cal", "pro", "fat", "carb"], [cal, pro, fat, carb]):
                    meal_tot[k] += v
        rows.append((meal, meal_rows, meal_tot))
        for k in overall:
            overall[k] += meal_tot[k]

    # Layout
    img_w = 1100
    left_pad, right_pad = 40, 40
    top_area, per_item_h, meal_header_h, meal_footer_h, gap, min_bottom = 160, 30, 36, 28, 18, 60
    total_items = sum(len(m[1]) if m[1] else 1 for m in rows)
    content_h = total_items * per_item_h + len(rows) * (meal_header_h + meal_footer_h) + (len(rows)-1)*gap
    img_h = top_area + content_h + min_bottom

    img = Image.new("RGB", (img_w, img_h), bg)
    draw = ImageDraw.Draw(img)

    # Fonts
    try:
        title_font = ImageFont.truetype("DejaVuSerif-Bold.ttf", 28)
        header_font = ImageFont.truetype("DejaVuSerif.ttf", 18)
        regular_font = ImageFont.truetype("DejaVuSerif.ttf", 14)
    except Exception:
        title_font = header_font = regular_font = ImageFont.load_default()

    def textsize_safe(text, font):
        """Backwards compatible text size helper."""
        if hasattr(draw, "textbbox"):
            bbox = draw.textbbox((0, 0), text, font=font)
            return bbox[2] - bbox[0], bbox[3] - bbox[1]
        else:
            return draw.textsize(text, font=font)

    y = 18
    # Logo
    try:
        if logo_path.exists():
            logo_img = Image.open(logo_path).convert("RGBA")
            max_logo_h = 64
            ratio = max_logo_h / float(logo_img.height)
            new_w, new_h = int(logo_img.width * ratio), int(logo_img.height * ratio)
            logo_small = logo_img.resize((new_w, new_h))
            logo_x = (img_w - new_w) // 2
            img.paste(logo_small, (logo_x, y), logo_small)
            y += new_h + 8
    except Exception:
        pass

    # Title
    title_text = "🍽️ Daily Calorie Tracker"
    w_title, h_title = textsize_safe(title_text, title_font)
    draw.text(((img_w - w_title) / 2, y), title_text, fill=text_col, font=title_font)
    y += h_title + 6

    # Timestamp
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    w_ts, h_ts = textsize_safe(ts, regular_font)
    draw.text(((img_w - w_ts) / 2, y), ts, fill=subtext, font=regular_font)
    y += h_ts + 12
    draw.line([(left_pad, y), (img_w - right_pad, y)], fill=line_col, width=2)
    y += 12

    # Table headers
    col_x = [
        left_pad + 4,
        left_pad + int((img_w - left_pad - right_pad) * 0.55),
        left_pad + int((img_w - left_pad - right_pad) * 0.72),
        left_pad + int((img_w - left_pad - right_pad) * 0.84),
        left_pad + int((img_w - left_pad - right_pad) * 0.95),
    ]
    headers = ["Item (servings)", "Calories", "Protein (g)", "Fat (g)", "Carb (g)"]
    for cx, txt in zip(col_x, headers):
        draw.text((cx, y), txt, fill=accent, font=header_font)
    y += meal_header_h

    # Meals
    for meal_name, meal_rows, meal_tot in rows:
        draw.text((left_pad, y - 2), f"{meal_name}", fill=text_col, font=header_font)
        y += per_item_h
        if meal_rows:
            for item_name, servings, cal, pro, fat, carb in meal_rows:
                draw.text((col_x[0], y), f"{item_name} x{servings}", fill=text_col, font=regular_font)
                for i, val in zip(col_x[1:], [cal, pro, fat, carb]):
                    draw.text((i, y), f"{val:.1f}", fill=text_col, font=regular_font)
                y += per_item_h
        else:
            draw.text((col_x[0], y), "—", fill=subtext, font=regular_font)
            y += per_item_h
        # Meal total
        draw.line([(left_pad, y - 6), (img_w - right_pad, y - 6)], fill=line_col, width=1)
        draw.text((col_x[0], y + 2), f"{meal_name} total:", fill=accent, font=regular_font)
        for i, val in zip(col_x[1:], [meal_tot["cal"], meal_tot["pro"], meal_tot["fat"], meal_tot["carb"]]):
            draw.text((i, y + 2), f"{val:.1f}", fill=accent, font=regular_font)
        y += meal_footer_h + gap

    # Overall totals
    draw.line([(left_pad, y - 8), (img_w - right_pad, y - 8)], fill=line_col, width=2)
    y += 6
    draw.text((left_pad, y), "Overall Total:", fill=accent, font=header_font)
    for i, val in zip(col_x[1:], [overall["cal"], overall["pro"], overall["fat"], overall["carb"]]):
        draw.text((i, y), f"{val:.1f}", fill=text_col, font=header_font)
    y += 36

    footer = "Generated by Calorie Tracker"
    wf, hf = textsize_safe(footer, regular_font)
    draw.text(((img_w - wf) / 2, img_h - 30), footer, fill=subtext, font=regular_font)
    return img


# --- create & download image ---
img = create_table_image_from_state(data, st.session_state["meal_servings"], logo_path=Path("logo.png"))
buf = BytesIO()
img.save(buf, format="PNG")
image_bytes = buf.getvalue()

st.download_button(
    label="📥 Download Summary as Image",
    data=image_bytes,
    file_name=f"calorie_summary_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png",
    mime="image/png",
)

# Prepare image bytes using the live state (do not alter existing style above)
img = create_table_image_from_state(data, st.session_state["meal_servings"], logo_path=Path("logo.png"))
buf = BytesIO()
img.save(buf, format="PNG")
image_bytes = buf.getvalue()



