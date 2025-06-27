
import streamlit as st

# Page config
st.set_page_config(page_title="Workforce Planning Portal", layout="wide")

# Custom CSS for dark mode + branding
st.markdown("""
    <style>
        body, .css-18e3th9, .css-1d391kg {
            background-color: #1e1e1e !important;
            color: white;
        }
        .stButton > button {
            background-color: #ff4b2b;
            color: white;
            border: none;
            padding: 0.5rem 1.25rem;
            font-size: 1rem;
            border-radius: 6px;
        }
        .stButton > button:hover {
            background-color: #ff6b4b;
            transition: 0.3s;
        }
        .stTextInput > div > input {
            background-color: #333;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

# Hero section
st.markdown("""
    <div style='background: linear-gradient(90deg, #ff4b2b, #ff416c); padding: 2rem; border-radius: 0 0 20px 20px;'>
        <h1 style='color: white; font-size: 2.5rem;'>Welcome to the Workforce Planning Portal</h1>
        <p style='color: white; font-size: 1.1rem;'>Find insights. Build smarter headcount plans. Forecast with confidence.</p>
    </div>
""", unsafe_allow_html=True)

# Search bar
st.markdown("### 🔍 Quick Access")
st.text_input("Search for teams, headcount plans, or dashboards...", placeholder="e.g., Marketing Q2 forecast")

# Dashboard categories
st.markdown("### 📂 Browse by Section")
cols = st.columns(3)
with cols[0]:
    st.button("📊 Headcount Adjustments")
    st.button("📈 Forecasting")
with cols[1]:
    st.button("🧮 Recruiter Capacity")
    st.button("📌 Hiring Plan by Level")
with cols[2]:
    st.button("📉 Finance Overview")
    st.button("📊 Success Metrics")
