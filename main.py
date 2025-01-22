import streamlit as st
import pandas as pd
import plotly.express as px
import altair as alt
import os
import re

# -------------------------------------
# 1) CONFIGURATION & DATA LOADING
# -------------------------------------
CSV_PATH = "coins.csv"
IMAGES_FOLDER = "Muslim Conquerors"

# Load dataset
df = pd.read_csv(CSV_PATH)

# Convert numerical columns properly
df["Weight (g)"] = pd.to_numeric(df["Weight (g)"], errors="coerce")
df["Dimension (mm)"] = pd.to_numeric(df["Dimension (mm)"], errors="coerce")

# Fill missing values for specific columns with "Unknown"
for col in ["Ruler (or Issuer)", "Reign", "Metal", "Mint", "Date of Issue"]:
    df[col].fillna("Unknown", inplace=True)

# Fill missing numerical values with 0
for col in ["Weight (g)", "Dimension (mm)"]:
    df[col].fillna(0, inplace=True)

# -------------------------------------
# 2) IMAGE MATCHING FUNCTION
# -------------------------------------
images_dict = {}
pattern = re.compile(r"(\d+\.\d+)[_\s-]*.*\.png$", re.IGNORECASE)  # Matches "10.1 Fakruddin Mubarak Shah .png"

for filename in os.listdir(IMAGES_FOLDER):
    match = pattern.match(filename)
    if match:
        coin_no = match.group(1)  # Extract "10.1"
        if coin_no not in images_dict:
            images_dict[coin_no] = {"front": None, "back": None}
        
        lower_name = filename.lower()
        if " re " in lower_name or lower_name.endswith(" re.png") or " re." in lower_name:
            images_dict[coin_no]["back"] = os.path.join(IMAGES_FOLDER, filename)
        else:
            images_dict[coin_no]["front"] = os.path.join(IMAGES_FOLDER, filename)

# -------------------------------------
# 3) STREAMLIT UI
# -------------------------------------
st.set_page_config(page_title="Digital Coin Museum", layout="wide")
st.title("🪙 Digital Coin Museum")

# Sidebar Filters
st.sidebar.header("🔍 Filter Coins")
selected_ruler = st.sidebar.selectbox("Select Ruler", ["All"] + sorted(df["Ruler (or Issuer)"].unique()))
selected_metal = st.sidebar.selectbox("Select Metal", ["All"] + sorted(df["Metal"].unique()))

# Filter Data
filtered_df = df.copy()
if selected_ruler != "All":
    filtered_df = filtered_df[filtered_df["Ruler (or Issuer)"] == selected_ruler]
if selected_metal != "All":
    filtered_df = filtered_df[filtered_df["Metal"] == selected_metal]

# -------------------------------------
# 4) DATAFRAME DISPLAY
# -------------------------------------
st.subheader("📜 Coin Database")
st.dataframe(filtered_df)

# -------------------------------------
# 5) VISUALIZATIONS
# -------------------------------------
st.subheader("📊 Coin Data Insights")

# Distribution of coin weight
fig1 = px.histogram(filtered_df, x="Weight (g)", nbins=20, title="Distribution of Coin Weights", marginal="rug")
st.plotly_chart(fig1, use_container_width=True)

# Scatter plot of weight vs. dimensions
fig2 = px.scatter(
    filtered_df, x="Weight (g)", y="Dimension (mm)",
    color="Metal", size="Weight (g)", hover_data=["Ruler (or Issuer)"],
    title="Coin Weight vs. Dimension"
)
st.plotly_chart(fig2, use_container_width=True)

# Altair chart for distribution
alt_chart = alt.Chart(filtered_df).mark_bar().encode(
    x=alt.X("Metal:N", title="Metal Type"),
    y=alt.Y("count()", title="Count"),
    color="Metal"
).properties(title="Metal Type Distribution")

st.altair_chart(alt_chart, use_container_width=True)

# -------------------------------------
# 6) DISPLAY COINS WITH IMAGES
# -------------------------------------
st.subheader("🖼️ Coin Details with Images")

for idx, row in filtered_df.iterrows():
    coin_no = str(row["Coin No."])

    # Display textual details
    st.markdown(f"### Coin No. {coin_no}")
    st.write(f"**Ruler:** {row['Ruler (or Issuer)']}")
    st.write(f"**Reign:** {row['Reign']}")
    st.write(f"**Metal:** {row['Metal']}")
    st.write(f"**Weight (g):** {row['Weight (g)']}")
    st.write(f"**Dimension (mm):** {row['Dimension (mm)']}")
    st.write(f"**Mint:** {row['Mint']}")
    st.write(f"**Date of Issue:** {row['Date of Issue']}")

    # Retrieve image paths
    front_path = images_dict.get(coin_no, {}).get("front")
    back_path = images_dict.get(coin_no, {}).get("back")

    # Show images side by side
    col1, col2 = st.columns(2)
    with col1:
        if front_path and os.path.exists(front_path):
            st.image(front_path, caption=f"{coin_no} (Front)", use_column_width=True)
        else:
            st.warning("Front image not found.")
    with col2:
        if back_path and os.path.exists(back_path):
            st.image(back_path, caption=f"{coin_no} (Back)", use_column_width=True)
        else:
            st.warning("Back image not found.")

    st.markdown("---")