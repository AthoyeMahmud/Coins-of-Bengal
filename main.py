import streamlit as st
import pandas as pd
import plotly.express as px
import altair as alt
import os
import re
import warnings

#Verbose Error Configuration
def configure_app():
    st.set_page_config(page_title="Coins of Bengal", layout="wide")
    st.set_option('client.showErrorDetails', False)
    warnings.filterwarnings("ignore")

#Landing Page
def landing_page(df=None, images_dict=None):
    image_paths = [
        "Muslim Conquerors/9.2 Giasuddin Bahadur Ghazi re .png",
        "Muslim Conquerors/29.5 Shamsuddin Firuz Shah re .png",
        "Muslim Conquerors/1.1 Ikhtiyar Khilji re .png",
        "Muslim Conquerors/2.1 Ali Mardan re .png",
        "Muslim Conquerors/22.6 Ruknuddin Barbak Shah .png"
    ]

    cols = st.columns(len(image_paths))
    for i, path in enumerate(image_paths):
        with cols[i]:
            try:
                st.image(path, use_container_width=True)
            except FileNotFoundError:
                st.error(f"Image not found at: {path}")
    st.markdown("<h2 style='text-align: center;'>Engineer Noorul Islam,<br>Proprietor of the actual museum and the private dataset</h2>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>Dr. Md. Ataur Rahman,<br>Researcher and Archaeologist</h2>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>Athoye Mahmud,<br>Developer</h2>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<small>©️ Published January 2025. All rights reserved.</small>", unsafe_allow_html=True)
    st.markdown("---")
    
#Load and preprocess data
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

        # Function to convert Arabic calendar years to Gregorian
        def convert_to_gregorian(year):
            if year < 1202:
                return year + 622  # Approximate conversion
            return year

        # Apply the conversion to the "Date of Issue" column
        df['Date of Issue'] = df['Date of Issue'].apply(lambda x: convert_to_gregorian(int(x)) if str(x).isdigit() else x)

        return df
    except FileNotFoundError:
            st.error(f"Error: CSV file not found at: {csv_path}")
            return None

#Image matching
def match_images(images_folder):
    images_dict = {}
    if not os.path.exists(images_folder):
        st.error(f"Error: Image folder not found at: {images_folder}")
        return images_dict
    
    pattern = re.compile(r"(\d+\.\d+)[_\s-]*.*\.png$", re.IGNORECASE)
    for filename in os.listdir(images_folder):
        match = pattern.match(filename)
        if match:
            coin_no = match.group(1)
            if coin_no not in images_dict:
                images_dict[coin_no] = {"front": None, "back": None}
            lower_name = filename.lower()
            if " re " in lower_name or lower_name.endswith(" re.png") or " re." in lower_name:
                images_dict[coin_no]["back"] = os.path.join(images_folder, filename)
            else:
                images_dict[coin_no]["front"] = os.path.join(images_folder, filename)
    return images_dict

def sidebar_filters(df):
    st.sidebar.header("🔍 Filter Coins")
    
    if df is not None:
        # Ruler filter with a dropdown
        selected_ruler = st.sidebar.selectbox("Select Ruler", ["All"] + sorted(df["Ruler (or Issuer)"].unique()))
        
        # Metal filter with multiselect
        selected_metals = st.sidebar.multiselect("Select Metal", options=["All"] + sorted(df["Metal"].unique()), default=["All"])
        
        # Improved Reign filter with a range slider
        reigns = sorted(df["Reign"].unique())
        if reigns:
            # Extract years from reign strings
            years = [int(y.split('–')[0]) for y in reigns if '–' in y]
            if years:
                min_year = min(years)
                max_year = max(years)
                selected_years = st.sidebar.slider(
                    "Select Reign Years",
                    min_value=min_year,
                    max_value=max_year,
                    value=(min_year, max_year)
                )
        
        # Weight filter with a slider
        weight_range = st.sidebar.slider(
            "Select Weight Range (g)",
            min_value=float(df["Weight (g)"].min()),
            max_value=float(df["Weight (g)"].max()),
            value=(0.0, float(df["Weight (g)"].max()))
        )
        
        # Apply filters
        filtered_df = df.copy()
        
        if selected_ruler != "All":
            filtered_df = filtered_df[filtered_df["Ruler (or Issuer)"] == selected_ruler]
        
        if "All" not in selected_metals:
            filtered_df = filtered_df[filtered_df["Metal"].isin(selected_metals)]
        
        # Apply reign filter
        if reigns and years:
            filtered_df = filtered_df[
                filtered_df["Reign"].apply(
                    lambda x: selected_years[0] <= int(x.split('–')[0]) <= selected_years[1]
                )
            ]

        filtered_df = filtered_df[(filtered_df["Weight (g)"] >= weight_range[0]) & (filtered_df["Weight (g)"] <= weight_range[1])]
        return filtered_df
    return None

#Display data
def display_data(df, images_dict):
    st.subheader("📜 Coin Database")
    st.dataframe(df, use_container_width=True)
    st.markdown("---")

#Visualizations
def display_visualizations(df, images_dict):
    st.subheader("📊 Coin Data Insights")

    if df is not None and not df.empty:

        # Filter out rows where "Weight (g)" is zero or NaN
        df_filtered = df[df["Weight (g)"].notna() & (df["Weight (g)"] != 0)]
        fig1 = px.histogram(df_filtered, x="Weight (g)", nbins=20, title="Distribution of Coin Weights", marginal="rug")

        # Make titles and axis labels bolder
        fig1.update_layout(
            title_font=dict(size=24),
            xaxis_title="Weight (g)",
            yaxis_title="Count",
            xaxis_title_font=dict(size=18),
            yaxis_title_font=dict(size=18)
        )
        st.plotly_chart(fig1, use_container_width=True)

        fig2 = px.scatter(
            df, x="Weight (g)", y="Dimension (mm)", color="Metal",
            size="Weight (g)", hover_data=["Ruler (or Issuer)"], title="Coin Weight vs. Dimension"
        )

        # Make titles and axis labels bolder
        fig2.update_layout(
            title_font=dict(size=24),
            xaxis_title="Weight (g)",
            yaxis_title="Dimension (mm)",
            xaxis_title_font=dict(size=18),
            yaxis_title_font=dict(size=18)
        )
        st.plotly_chart(fig2, use_container_width=True)

        alt_chart = alt.Chart(df).mark_bar().encode(
            x=alt.X("Metal:N", title="Metal Type"),
            y=alt.Y("count()", title="Count"),
            color="Metal"
        ).properties(title="Metal Type Distribution")

        # Make titles and axis labels bolder
        alt_chart = alt_chart.configure_title(
            fontSize=24,
            font="Arial",
            color="black"
        ).configure_axis(
            labelFontSize=18,
            titleFontSize=18,
            titleFont="Arial",
            titleColor="black"
        )
        st.altair_chart(alt_chart, use_container_width=True)

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
        fig3.update_layout(
            title_font=dict(size=24),
            xaxis_title="Number of Coins",
            yaxis_title="Ruler",
            xaxis_title_font=dict(size=18),
            yaxis_title_font=dict(size=18)
        )
        fig3.update_layout(yaxis=dict(categoryorder="total ascending"), xaxis=dict(showgrid=True))
        # Show plot in Streamlit
        st.plotly_chart(fig3)  # Use Streamlit to display the plot

    else:
        st.warning("No data to create visualizations")

#Display coins with images
def display_coins_with_images(df, images_dict):
    st.subheader("🖼️ Coin Details with Images")
    if df is not None and not df.empty:
        for idx, row in df.iterrows():
            coin_no = str(row["Coin No."])
            st.markdown(f"### Coin No. {coin_no}")
            st.markdown(f"<h2 style='font-size:24px; font-weight:bold;'>Ruler: {row['Ruler (or Issuer)']}</h2>", unsafe_allow_html=True)
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
                    st.image(front_path, caption=f"{coin_no} (Front)", use_container_width=True)
                else:
                    st.warning("Front image not found.")
            with col2:
                if back_path and os.path.exists(back_path):
                    st.image(back_path, caption=f"{coin_no} (Back)", use_container_width=True)
                else:
                    st.warning("Back image not found.")
            st.markdown("---")
    else:
        st.warning("No coins to display.")

#Main function
def main():
    configure_app()
    st.title("🪙 Coins of Bengal, A Digital Coin Museum", anchor="center")

    # Navigation
    pages = {
        "Home": landing_page,
        "Data": display_data,
        "Visualizations": display_visualizations,
        "Coin Catalog": display_coins_with_images
    }

    st.sidebar.title("🧭 Navigation")
    selection = st.sidebar.radio("⤵️ Go to", list(pages.keys()))

    # Load data and images
    df = load_data("coins.csv")
    images_dict = match_images("Muslim Conquerors")
    filtered_df = sidebar_filters(df)

    # Display selected page
    if selection == "Home":
        pages[selection]()
    else:
        pages[selection](filtered_df, images_dict)

if __name__ == "__main__":
    main()
