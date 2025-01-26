import streamlit as st
import pandas as pd
import plotly.express as px
import altair as alt
import os
import re
import warnings

# --- Configuration ---
def configure_app():
    st.set_page_config(page_title="Coins of Bengal", layout="wide")
    st.set_option('client.showErrorDetails', False)
    warnings.filterwarnings("ignore")

# --- Landing Page ---
def landing_page():
    image_paths = [
        "Muslim Conquerors/9.2 Giasuddin Bahadur Ghazi re .jpg",
        "Muslim Conquerors/29.5 Shamsuddin Firuz Shah re .jpg",
        "Muslim Conquerors/2.1 Ali Mardan re .jpg",
        "Muslim Conquerors/1.1 Ikhtiyar Khilji re .jpg",
        "Muslim Conquerors/22.6 Ruknuddin Barbak Shah .jpg"
    ]

    cols = st.columns(len(image_paths))
    for i, path in enumerate(image_paths):
        with cols[i]:
            try:
                st.image(path, use_column_width=True)
            except FileNotFoundError:
                st.error(f"Image not found at: {path}")
    st.markdown("<h2 style='text-align: center;'>Engineer Noorul Islam, Proprietor of the actual museum and the private dataset <br>Athoye Mahmud, Developer<br>Tahmina Muha Armin, Developer</h2>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    #st.markdown("-")
    
# --- Load and preprocess data ---
@st.cache_data
def load_data(csv_path):
    try:
        df = pd.read_csv(csv_path)
        # Standardize column names
        df.rename(columns=lambda x: x.strip(), inplace=True)
        df.rename(columns={
            "Coin No.": "Coin No.",
            "Ruler": "Ruler (or Issuer)",
            "Weight": "Weight (g)",
            "Dimensions": "Dimension (mm)",
        }, inplace=True)

        df["Weight (g)"] = pd.to_numeric(df["Weight (g)"], errors="coerce")
        df["Dimension (mm)"] = pd.to_numeric(df["Dimension (mm)"], errors="coerce")

        for col in ["Ruler (or Issuer)", "Reign", "Metal", "Mint", "Date of Issue"]:
            df[col].fillna("Unknown", inplace=True)
        for col in ["Weight (g)", "Dimension (mm)"]:
            df[col].fillna(0, inplace=True)
        return df
    except FileNotFoundError:
            st.error(f"Error: CSV file not found at: {csv_path}")
            return None

# --- Image matching ---
def match_images(images_folder):
    images_dict = {}
    if not os.path.exists(images_folder):
        st.error(f"Error: Image folder not found at: {images_folder}")
        return images_dict
    
    pattern = re.compile(r"(\d+\.\d+)[_\s-]*.*\.jpg$", re.IGNORECASE)
    for filename in os.listdir(images_folder):
        match = pattern.match(filename)
        if match:
            coin_no = match.group(1)
            if coin_no not in images_dict:
                images_dict[coin_no] = {"front": None, "back": None}
            lower_name = filename.lower()
            if " re " in lower_name or lower_name.endswith(" re.jpg") or " re." in lower_name:
                images_dict[coin_no]["back"] = os.path.join(images_folder, filename)
            else:
                images_dict[coin_no]["front"] = os.path.join(images_folder, filename)
    return images_dict

# --- Sidebar filters ---
def sidebar_filters(df):
    st.sidebar.header("🔍 Filter Coins")
    if df is not None:
        selected_ruler = st.sidebar.selectbox("Select Ruler", ["All"] + sorted(df["Ruler (or Issuer)"].unique()))
        selected_metal = st.sidebar.selectbox("Select Metal", ["All"] + sorted(df["Metal"].unique()))
        filtered_df = df.copy()
        if selected_ruler != "All":
            filtered_df = filtered_df[filtered_df["Ruler (or Issuer)"] == selected_ruler]
        if selected_metal != "All":
            filtered_df = filtered_df[filtered_df["Metal"] == selected_metal]
        return filtered_df
    return None


# --- Display data ---
def display_data(df):
    st.subheader("📜 Coin Database")
    if df is not None:
        st.dataframe(df)
    else:
        st.warning("No data to display.")

# --- Visualizations ---
def display_visualizations(df):
    st.subheader("📊 Coin Data Insights")
    if df is not None and not df.empty:
        fig1 = px.histogram(df, x="Weight (g)", nbins=20, title="Distribution of Coin Weights", marginal="rug")
        st.plotly_chart(fig1, use_container_width=True)

        fig2 = px.scatter(
            df, x="Weight (g)", y="Dimension (mm)", color="Metal",
            size="Weight (g)", hover_data=["Ruler (or Issuer)"], title="Coin Weight vs. Dimension"
        )
        st.plotly_chart(fig2, use_container_width=True)

        alt_chart = alt.Chart(df).mark_bar().encode(
            x=alt.X("Metal:N", title="Metal Type"),
            y=alt.Y("count()", title="Count"),
            color="Metal"
        ).properties(title="Metal Type Distribution")
        st.altair_chart(alt_chart, use_container_width=True)
        
        # Convert "Date of Issue" to numeric (for proper plotting)
        df["Date of Issue"] = pd.to_numeric(df["Date of Issue"], errors="coerce")
        # Group by "Date of Issue" to count the number of coins issued per year
        coin_timeline = df.groupby("Date of Issue").size().reset_index(name="Coin Count")
        # Plot using Plotly
        fig2 = px.line(
            coin_timeline,
            x="Date of Issue",
            y="Coin Count",
            markers=True,
            title="📆 Coin Issuance Timeline",
            labels={"Date of Issue": "Year", "Coin Count": "Number of Coins Issued"},
            line_shape="linear"
        )
        # Enhance appearance
        fig2.update_traces(line=dict(width=3))
        fig2.update_layout(xaxis=dict(showgrid=True), yaxis=dict(showgrid=True))
        # Show plot in Streamlit
        st.plotly_chart(fig2)  # Use Streamlit to display the plot

        # Count number of coins per ruler
        ruler_counts = df["Ruler (or Issuer)"].value_counts().reset_index()
        ruler_counts.columns = ["Ruler (or Issuer)", "Coin Count"]
        # Plot using Plotly
        fig3 = px.bar(
            ruler_counts,
            x="Coin Count",
            y="Ruler (or Issuer)",
            orientation="h",
            title="🏛 Number of Coins Issued per Ruler",
            labels={"Coin Count": "Number of Coins", "Ruler (or Issuer)": "Ruler"},
            text_auto=True
        )
        # Improve appearance
        fig3.update_layout(yaxis=dict(categoryorder="total ascending"), xaxis=dict(showgrid=True))
        # Show plot in Streamlit
        st.plotly_chart(fig3)  # Use Streamlit to display the plot

    else:
        st.warning("No data to create visualizations")

# --- Display coins with images ---
def display_coins_with_images(df, images_dict):
    st.subheader("🖼️ Coin Details with Images")
    if df is not None and not df.empty:
        for idx, row in df.iterrows():
            coin_no = str(row["Coin No."])
            st.markdown(f"### Coin No. {coin_no}")
            st.write(f"**Ruler:** {row['Ruler (or Issuer)']}")
            st.write(f"**Reign:** {row['Reign']}")
            st.write(f"**Metal:** {row['Metal']}")
            st.write(f"**Weight (g):** {row['Weight (g)']}")
            st.write(f"**Dimension (mm):** {row['Dimension (mm)']}")
            st.write(f"**Mint:** {row['Mint']}")
            st.write(f"**Date of Issue:** {row['Date of Issue']}")

            front_path = images_dict.get(coin_no, {}).get("front")
            back_path = images_dict.get(coin_no, {}).get("back")

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
    else:
        st.warning("No coins to display.")


# --- Main function ---
def main():
    configure_app()
    st.title("🪙 Digital Coin Museum", anchor="center")
    landing_page()
    df = load_data("coins.csv")
    images_dict = match_images("Muslim Conquerors")
    filtered_df = sidebar_filters(df)
    display_data(filtered_df)
    display_visualizations(filtered_df)
    display_coins_with_images(filtered_df, images_dict)


if __name__ == "__main__":
    main()
