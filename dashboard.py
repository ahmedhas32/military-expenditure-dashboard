import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Military Expenditure Dashboard", layout="wide")
st.title("🛡️ World Bank Military Expenditure (% of GDP)")

st.markdown("**Upload your World Bank CSV** (the exact format you showed — years as columns)")

uploaded_file = st.file_uploader("Choose CSV file", type="csv")

if uploaded_file is not None:
    df_wide = pd.read_csv(uploaded_file)
    df_wide = df_wide.dropna(axis=1, how="all")
    
    year_cols = [col for col in df_wide.columns if str(col).strip().isdigit()]
    
    if not year_cols:
        st.error("Could not find year columns.")
    else:
        id_vars = ["Country Name"]
        for col in ["Country Code", "Indicator Name", "Indicator Code"]:
            if col in df_wide.columns:
                id_vars.append(col)
        
        df_long = pd.melt(
            df_wide,
            id_vars=id_vars,
            value_vars=year_cols,
            var_name="Year",
            value_name="Value"
        )
        
        df_long["Year"] = pd.to_numeric(df_long["Year"])
        df_long = df_long.dropna(subset=["Value"])
        
        if "Indicator Name" in df_long.columns and df_long["Indicator Name"].nunique() > 1:
            indicators = sorted(df_long["Indicator Name"].unique())
            selected_indicators = st.multiselect("Select Indicator(s)", indicators, default=indicators)
            df_long = df_long[df_long["Indicator Name"].isin(selected_indicators)]
        
        countries = sorted(df_long["Country Name"].unique())
        selected_countries = st.multiselect(
            "Select Countries",
            options=countries,
            default=["United States", "Germany", "United Kingdom", "Saudi Arabia", "Egypt, Arab Rep.", "United Arab Emirates"]
        )
        
        min_year = int(df_long["Year"].min())
        max_year = int(df_long["Year"].max())
        year_range = st.slider("Year Range", min_year, max_year, (min_year, max_year))
        
        filtered = df_long[
            (df_long["Country Name"].isin(selected_countries)) &
            (df_long["Year"] >= year_range[0]) &
            (df_long["Year"] <= year_range[1])
        ]
        
        if filtered.empty:
            st.warning("No data matches your selection.")
        else:
            col1, col2, col3 = st.columns(3)
            avg_pct = filtered["Value"].mean()
            latest_year = filtered["Year"].max()
            latest = filtered[filtered["Year"] == latest_year]
            highest_country = latest.loc[latest["Value"].idxmax(), "Country Name"] if not latest.empty else "—"
            highest_value = latest["Value"].max() if not latest.empty else 0
            
            col1.metric("Average % of GDP", f"{avg_pct:.2f}%")
            col2.metric(f"Highest in {latest_year}", highest_country)
            col3.metric(f"Peak Value {latest_year}", f"{highest_value:.2f}%")
            
            left, right = st.columns([2, 1])
            
            with left:
                line_fig = px.line(
                    filtered, x="Year", y="Value", color="Country Name",
                    title="Military Expenditure (% of GDP) Over Time",
                    markers=True, hover_data={"Value": ":.2f"}
                )
                st.plotly_chart(line_fig, width='stretch')   # ← updated
                
            with right:
                bar_fig = px.bar(
                    latest, x="Country Name", y="Value",
                    title=f"Comparison in {latest_year}",
                    color="Country Name", text="Value"
                )
                bar_fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
                st.plotly_chart(bar_fig, width='stretch')   # ← updated
            
            st.subheader("Data Table")
            pivot = filtered.pivot_table(
                index="Year", columns="Country Name", values="Value", aggfunc="first"
            ).round(2)
            st.dataframe(pivot, width='stretch')   # ← updated
            
            csv_download = filtered.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Filtered Data",
                data=csv_download,
                file_name="military_expenditure_filtered.csv",
                mime="text/csv"
            )