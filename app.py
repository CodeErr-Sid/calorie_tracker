import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# Load Excel data
@st.cache_data
def load_data():
    df = pd.read_excel("food_data.xlsx")
    df.columns = [c.strip() for c in df.columns]
    return df

data = load_data()

st.set_page_config(page_title="Calorie Tracker", layout="wide")

# Styling (keep your existing style or adjust)
st.markdown("""
<style>
    body {
        background-color: #0E1117;
        color: #FAFAFA;
        font-family: 'Inter', sans-serif;
    }
    .block-container {padding-top: 2rem;}
    h1, h2, h3, label, .stMarkdown, .stNumberInput label {color: #FAFAFA !important;}
    div[data-baseweb="select"] > div {
        background-color: #1E1E1E;
        color: #FAFAFA;
        border-radius: 6px;
        border: 1px solid #333;
    }
    div[data-testid="column"] > div > button {
        background-color: #2B2B2B !important;
        color: #FFFFFF !important;
        border: 1px solid #444 !important;
        border-radius: 50% !important;
        height: 28px !important;
        width: 28px !important;
        font-size: 14px !important;
        line-height: 1px !important;
        margin: 0 !important;
    }
    div[data-testid="column"] > div > button:hover {
        background-color: #555 !important;
        border-color: #666 !important;
    }
    .food-name {
        font-size: 14px;
        color: #FAFAFA;
        font-weight: 500;
    }
    .serving-label {
        font-size: 13px;
        color: #BBB;
    }
</style>
""", unsafe_allow_html=True)

st.title("🍽️ Daily Calorie Tracker")
st.caption("Add meals throughout the day. Your inputs are saved until you reset.")

meals = ["Meal 1", "Meal 2", "Meal 3", "Meal 4", "Meal 5", "Add On"]

# Initialize the session state dict for meals if not exists
if "meal_servings" not in st.session_state:
    st.session_state["meal_servings"] = {meal: {} for meal in meals}

# Reset button
if st.button("🔄 Reset All Meals"):
    st.session_state["meal_servings"] = {meal: {} for meal in meals}
    for meal in meals:
        st.session_state[f"items_{meal}"] = []

# Show meal sections
for meal in meals:
    st.markdown(f"### {meal}")

    # Select items, preselect from session state keys for that meal
    pre_selected = list(st.session_state["meal_servings"][meal].keys())
    items = st.multiselect(
    f"Select items for {meal}",
    options=data["Protein Options"].dropna().unique(),
    default=st.session_state.get(f"items_{meal}", []),
    key=f"items_{meal}"
    )

    # Sync meal_servings dict keys with multiselect
    # Remove unselected items
    for removed_item in list(st.session_state["meal_servings"][meal].keys()):
        if removed_item not in items:
            del st.session_state["meal_servings"][meal][removed_item]

    # Add new items with default serving 1 if not present
    for new_item in items:
        if new_item not in st.session_state["meal_servings"][meal]:
            st.session_state["meal_servings"][meal][new_item] = 1

    # Render inline serving controls
    for item in items:
        key = f"{meal}_{item}_servings"

        c1, c2, c3, c4 = st.columns([3, 0.5, 0.5, 1])
        with c1:
            st.markdown(f"<div class='food-name'>{item}</div>", unsafe_allow_html=True)
        with c2:
            if st.button("➖", key=f"minus_{meal}_{item}"):
                current = st.session_state["meal_servings"][meal].get(item, 1)
                st.session_state["meal_servings"][meal][item] = max(0, current - 1)
        with c3:
            if st.button("➕", key=f"plus_{meal}_{item}"):
                current = st.session_state["meal_servings"][meal].get(item, 0)
                st.session_state["meal_servings"][meal][item] = current + 1
        with c4:
            servings = st.session_state["meal_servings"][meal].get(item, 0)
            st.markdown(f"<div class='serving-label'>{servings} serving(s)</div>", unsafe_allow_html=True)

# Calculate totals dynamically
total_cal, total_pro, total_fat, total_carb = 0, 0, 0, 0
for meal in meals:
    for item, servings in st.session_state["meal_servings"][meal].items():
        row = data[data["Protein Options"] == item].iloc[0]
        total_cal += row["Calories"] * servings
        total_pro += row["Protein"] * servings
        total_fat += row["Fat"] * servings
        total_carb += row["Carb"] * servings

# Show totals
st.markdown("---")
st.markdown("## 📈 Daily Summary")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Calories", f"{total_cal:.0f}")
c2.metric("Protein (g)", f"{total_pro:.1f}")
c3.metric("Fat (g)", f"{total_fat:.1f}")
c4.metric("Carbs (g)", f"{total_carb:.1f}")

# ---------------------------------------
# Download summary as image
# ---------------------------------------
def create_table_image(cal, pro, fat, carb):
    width, height = 480, 260
    bg_color = (14, 17, 23)
    text_color = (250, 250, 250)
    accent_color = (255, 165, 0)
    line_color = (70, 70, 70)
    
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Fonts (default)
    title_font = ImageFont.load_default()
    header_font = ImageFont.load_default()
    value_font = ImageFont.load_default()

    # Title
    draw.text((20, 20), "Daily Calorie & Macro Summary", fill=accent_color, font=title_font)

    # Draw table headers
    headers = ["Metric", "Amount"]
    x_offsets = [40, 300]
    y_start = 60
    row_height = 35

    # Header row
    for i, h in enumerate(headers):
        draw.text((x_offsets[i], y_start), h, fill=(200, 200, 200), font=header_font)
    
    # Draw line under header
    draw.line([(30, y_start + 22), (width - 30, y_start + 22)], fill=line_color, width=1)

    # Data rows
    data = [
        ("Calories", f"{cal:.0f} kcal"),
        ("Protein", f"{pro:.1f} g"),
        ("Fat", f"{fat:.1f} g"),
        ("Carbohydrates", f"{carb:.1f} g")
    ]

    for idx, (metric, value) in enumerate(data):
        y = y_start + 22 + (idx + 1) * row_height
        # Metric name
        draw.text((x_offsets[0], y), metric, fill=text_color, font=value_font)
        # Value (right aligned-ish)
        draw.text((x_offsets[1], y), value, fill=text_color, font=value_font)

        # Draw line below each row except last
        if idx < len(data) - 1:
            draw.line([(30, y + row_height - 10), (width - 30, y + row_height - 10)], fill=line_color, width=1)

    # Footer with timestamp
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    draw.text((20, height - 10), f"Generated: {now_str}", fill=(180, 180, 180), font=value_font)

    return img

# Prepare image bytes once so button is ready to use immediately
img = create_table_image(total_cal, total_pro, total_fat, total_carb)
buf = BytesIO()
img.save(buf, format="PNG")
image_bytes = buf.getvalue()

st.download_button(
    label="📥 Download Summary as Image",
    data=image_bytes,
    file_name=f"calorie_summary_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png",
    mime="image/png",
)