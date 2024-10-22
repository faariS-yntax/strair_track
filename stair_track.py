import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from streamlit_option_menu import option_menu

# Constants
TOTAL_HEIGHT_KINABALU_FT = 13435  # Height in feet
TOTAL_HEIGHT_KINABALU_M = 4095    # Height in meters
HEIGHT_PER_FLIGHT_FT = 8          # Each flight in feet
HEIGHT_PER_FLIGHT_M = 2.4         # Each flight in meters
DATA_FILE = 'stairs_data.csv'

# Function to get heights based on selected unit
def get_heights(unit='ft'):
    if unit == 'ft':
        return TOTAL_HEIGHT_KINABALU_FT, HEIGHT_PER_FLIGHT_FT
    return TOTAL_HEIGHT_KINABALU_M, HEIGHT_PER_FLIGHT_M

# Function to load data
def load_data():
    if os.path.exists(DATA_FILE):
        data = pd.read_csv(DATA_FILE, parse_dates=["Date"])
        data['Date'] = pd.to_datetime(data['Date']).dt.date
        return data
    return pd.DataFrame(columns=["Date", "Flights"])

# Function to save data
def save_data(data):
    data['Date'] = pd.to_datetime(data['Date']).dt.date
    data.to_csv(DATA_FILE, index=False)

# Function to calculate averages
def calculate_averages(data):
    if not data.empty:
        data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
        data['Week'] = data['Date'].dt.isocalendar().week
        data['Month'] = data['Date'].dt.month
        
        daily_avg = data.groupby('Date')['Flights'].sum().mean()
        weekly_avg = data.groupby('Week')['Flights'].sum().mean()
        monthly_avg = data.groupby('Month')['Flights'].sum().mean()
    else:
        daily_avg, weekly_avg, monthly_avg = 0, 0, 0
        
    return daily_avg, weekly_avg, monthly_avg

# Enhanced prediction function with trend analysis
def predict_completion_date(data, previous_completion_date=None):
    if data.empty:
        return None, None, None, 0
    
    total_flights_climbed = data['Flights'].sum()
    daily_avg = data.groupby('Date')['Flights'].sum().mean()
    
    if daily_avg > 0:
        total_height, height_per_flight = get_heights(st.session_state.unit)
        total_flights_needed = total_height / height_per_flight
        remaining_flights = total_flights_needed - total_flights_climbed
        days_to_completion = remaining_flights / daily_avg
        completion_date = datetime.today() + timedelta(days=days_to_completion)
        
        # Calculate trend
        if previous_completion_date:
            previous_date = datetime.strptime(previous_completion_date, '%Y-%m-%d')
            trend = (previous_date - completion_date).days
        else:
            trend = 0
            
        # Calculate performance score (0-100)
        target_daily_avg = total_flights_needed / 365  # Assuming one year target
        performance_score = min((daily_avg / target_daily_avg) * 100, 100)
        
        return completion_date.strftime('%Y-%m-%d'), int(days_to_completion), trend, performance_score
    
    return None, None, None, 0

# Function to analyze progress
def analyze_progress(data):
    if data.empty or len(data) < 2:
        return "Not enough data for analysis"
    
    latest_date = data['Date'].max()
    latest_flights = data[data['Date'] == latest_date]['Flights'].iloc[0]
    previous_date = data[data['Date'] < latest_date]['Date'].max()
    previous_flights = data[data['Date'] == previous_date]['Flights'].iloc[0]
    
    daily_change = latest_flights - previous_flights
    daily_change_pct = (daily_change / previous_flights) * 100 if previous_flights > 0 else 0
    
    if daily_change > 0:
        return f"📈 Great progress! You climbed {daily_change} more flights than your previous entry ({daily_change_pct:.1f}% increase)"
    elif daily_change < 0:
        return f"📉 You climbed {abs(daily_change)} fewer flights than your previous entry ({abs(daily_change_pct):.1f}% decrease)"
    return "➡️ Same number of flights as your previous entry"

# Function to modify data
def modify_data(data):
    if not data.empty:
        st.subheader("Edit or Delete Data")
        date_to_modify = st.selectbox("Select Date to Edit/Delete", data["Date"].astype(str))
        if date_to_modify:
            row = data[data["Date"].astype(str) == date_to_modify]
            st.write(f"Current Data for {date_to_modify}: {row['Flights'].values[0]} flights")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Edit Data"):
                    new_flights = st.number_input("New number of flights", value=int(row['Flights'].values[0]))
                    data.loc[data["Date"].astype(str) == date_to_modify, "Flights"] = new_flights
                    st.success("Data updated successfully!")
                    save_data(data)
            
            with col2:
                if st.button("Delete Data"):
                    data = data[data["Date"].astype(str) != date_to_modify]
                    st.success(f"Data for {date_to_modify} deleted.")
                    save_data(data)
    return data

# Main layout
st.set_page_config(page_title="Stair Trek 🧗‍♂️🏔️", layout="wide")
st.title("Stair Trek 🧗‍♂️🏔️")

# Initialize session state for unit preference
if 'unit' not in st.session_state:
    st.session_state.unit = 'ft'
if 'previous_completion_date' not in st.session_state:
    st.session_state.previous_completion_date = None

# Unit selection in sidebar
st.sidebar.title("Settings")
st.session_state.unit = st.sidebar.radio("Select Unit", ['ft', 'm'])

# Custom CSS for uniform card styling
st.markdown("""
    <style>
    .card {
        background-color: #2b2b2b; 
        padding: 15px; 
        border-radius: 10px; 
        box-shadow: 2px 2px 8px rgba(0,0,0,0.1); 
        text-align: center; 
        height: 200px;
        margin: 10px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .card h4 {
        color: #fafafa;
        margin-bottom: 10px;
    }
    .card h1 {
        color: #adadad;
        font-size: 36px;
        margin: 0;
    }
    .card h6 {
        color: #fafafa;
    }
    </style>
""", unsafe_allow_html=True)

# Function to display metrics in a card-like style
def display_card(title, value, unit=None, color=None):
    color_style = f"color: {color};" if color else ""
    st.markdown(
        f"""
        <div class="card">
            <h4>{title}</h4>
            <h1 style="{color_style}">{value}</h1>
            {"<h6>" + unit + "</h6>" if unit else ""}
        </div>
        """,
        unsafe_allow_html=True
    )

# Sidebar menu for tabs
selected = option_menu(
    menu_title="Main Menu",
    options=["Dashboard", "Data Entry", "Historical Data"],
    icons=["bar-chart", "pencil-square", "archive"],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
)

# Load existing data
data = load_data()

# Dashboard Tab
if selected == "Dashboard":
    st.header("Dashboard")
    
    # Row 1: Progress Analysis
    with st.container(border=True):
        st.subheader("Progress Insights")
        if not data.empty:
            progress_analysis = analyze_progress(data)
            st.write(progress_analysis)
            
            completion_date, days_remaining, trend, performance_score = predict_completion_date(
                data, st.session_state.previous_completion_date)
            
            if performance_score > 0:
                if performance_score >= 90:
                    st.success(f"🌟 Outstanding progress! You're performing at {performance_score:.1f}% of target pace!")
                elif performance_score >= 70:
                    st.info(f"👍 Good progress! You're performing at {performance_score:.1f}% of target pace.")
                else:
                    st.warning(f"💪 Keep pushing! You're at {performance_score:.1f}% of target pace.")

    # Row 2: Visualization columns
    col_left, col_right = st.columns(2)

    with col_left:
        # Progress comparison graph
        with st.container(border=True):
            st.subheader("Progress")
            total_height, height_per_flight = get_heights(st.session_state.unit)
            total_flights = data['Flights'].sum()
            height_climbed = total_flights * height_per_flight
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=['Your Progress'],
                y=[height_climbed],
                name='Height Climbed',
                marker_color='lightskyblue'
            ))
            fig.add_trace(go.Bar(
                x=['Gunung Kinabalu'],
                y=[total_height],
                name='Gunung Kinabalu',
                marker_color='lightgreen'
            ))
            fig.update_layout(
                title=f"Comparison: Your Climb vs Gunung Kinabalu ({st.session_state.unit})",
                yaxis=dict(title=f'Height ({st.session_state.unit})'),
                xaxis=dict(title='Comparison'),
                showlegend=False,
                yaxis_range=[0, total_height]
            )
            st.plotly_chart(fig)

    with col_right:
        # Averages graphs
        with st.container(border=True):
            st.subheader("Averages Over Time")
            daily_avg, weekly_avg, monthly_avg = calculate_averages(data)

            if not data.empty:
                daily_fig = px.line(
                    data.groupby('Date')['Flights'].sum().reset_index(),
                    x='Date',
                    y='Flights',
                    title='Daily Flights Pattern'
                )
                weekly_fig = px.line(
                    data.groupby('Week')['Flights'].sum().reset_index(),
                    x='Week',
                    y='Flights',
                    title='Weekly Flights Pattern'
                )
                monthly_fig = px.line(
                    data.groupby('Month')['Flights'].sum().reset_index(),
                    x='Month',
                    y='Flights',
                    title='Monthly Flights Pattern'
                )
                
                st.plotly_chart(daily_fig)
                st.plotly_chart(weekly_fig)
                st.plotly_chart(monthly_fig)

    # Row 3: Progress Metrics
    with st.container(border=True):
        st.subheader("Progress")
        col_1, col_2, col_3 = st.columns(3)
        progress = (height_climbed / total_height) * 100
        
        with col_1:
            display_card("Flights Climbed", total_flights, "flights")
        
        with col_2:
            display_card("Height Climbed", f"{height_climbed:.2f}", st.session_state.unit)
        
        with col_3:
            display_card("Progress", f"{progress:.2f}%")

        st.progress(progress / 100)

    # Row 4: Completion Prediction
    with st.container(border=True):
        st.subheader("Predictions")
        col_1_completion, col_2_completion = st.columns(2)
        
        completion_color = None
        if trend > 0:
            completion_color = "red"
        elif trend < 0:
            completion_color = "green"
        
        with col_1_completion:
            display_card(
                "Estimated Completion Date",
                completion_date if completion_date else "N/A",
                color=completion_color
            )
            if trend:
                trend_text = f"{'🔴 +' if trend > 0 else '🟢 -'}{abs(trend)} days change"
                st.write(trend_text)

        with col_2_completion:
            display_card(
                "Days Remaining",
                days_remaining if days_remaining else "N/A",
                "days",
                color=completion_color
            )

    # Row 5: Averages
    with st.container(border=True):
        st.subheader("Averages")
        col_1_avg, col_2_avg, col_3_avg = st.columns(3)

        with col_1_avg:
            display_card("Daily Average", f"{daily_avg:.2f}", "flights")

        with col_2_avg:
            display_card("Weekly Average", f"{weekly_avg:.2f}", "flights")

        with col_3_avg:
            display_card("Monthly Average", f"{monthly_avg:.2f}", "flights")

# Data Entry Tab
elif selected == "Data Entry":
    st.header("Data Entry")
    
    # Add today's data
    with st.container(border=True):
        st.subheader("Add Today's Flights")
        today = st.date_input("Date", datetime.today()).strftime('%Y-%m-%d')
        flights = st.number_input("Number of flights climbed today", min_value=0, step=1)

        if st.button("Add Entry"):
            if today in data['Date'].astype(str).values:
                st.warning("You've already added data for today.")
            else:
                new_entry = pd.DataFrame({"Date": [today], "Flights": [flights]})
                data = pd.concat([data, new_entry], ignore_index=True)
                save_data(data)
                st.success("Entry added!")
                st.balloons()

    # Edit or delete data
    with st.container(border=True):
        data = modify_data(data)

# Historical Data Tab
elif selected == "Historical Data":
    st.header("Historical Data")

    # Display data
    st.subheader("Flight of Stairs History")
    st.dataframe(data, use_container_width=True)
    
    # Reset button
    if st.button("Reset Data"):
        data = pd.DataFrame(columns=["Date", "Flights"])
        save_data(data)
        st.warning("All data has been reset.")