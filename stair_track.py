import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from streamlit_option_menu import option_menu

# Constants
TOTAL_HEIGHT_KINABALU = 13435  # Height of Gunung Kinabalu in feet
HEIGHT_PER_FLIGHT = 8          # Each flight is roughly 8 feet
TOTAL_FLIGHTS_KINABALU = TOTAL_HEIGHT_KINABALU / HEIGHT_PER_FLIGHT  # Total flights
DATA_FILE = 'stairs_data.csv'

# Function to load data
def load_data():
    if os.path.exists(DATA_FILE):
        data = pd.read_csv(DATA_FILE, parse_dates=["Date"])
        data['Date'] = pd.to_datetime(data['Date']).dt.date  # Convert to date only
        return data
    else:
        return pd.DataFrame(columns=["Date", "Flights"])

# Function to save data
def save_data(data):
    data['Date'] = pd.to_datetime(data['Date']).dt.date  # Ensure date-only format before saving
    data.to_csv(DATA_FILE, index=False)

# Function to calculate averages
def calculate_averages(data):
    if not data.empty:
        data['Week'] = data['Date'].dt.isocalendar().week
        data['Month'] = data['Date'].dt.month
        
        daily_avg = data.groupby('Date')['Flights'].sum().mean()
        weekly_avg = data.groupby('Week')['Flights'].sum().mean()
        monthly_avg = data.groupby('Month')['Flights'].sum().mean()
    else:
        daily_avg, weekly_avg, monthly_avg = 0, 0, 0
    return daily_avg, weekly_avg, monthly_avg

# Predict completion date based on current progress
def predict_completion_date(data):
    if not data.empty:
        total_flights_climbed = data['Flights'].sum()
        daily_avg = data.groupby('Date')['Flights'].sum().mean()
        if daily_avg > 0:
            remaining_flights = TOTAL_FLIGHTS_KINABALU - total_flights_climbed
            days_to_completion = remaining_flights / daily_avg
            completion_date = datetime.today() + timedelta(days=days_to_completion)
            return completion_date.strftime('%Y-%m-%d'), int(days_to_completion)
    return None, None

# Edit or delete data
def modify_data(data):
    if not data.empty:
        st.subheader("Edit or Delete Data")
        date_to_modify = st.selectbox("Select Date to Edit/Delete", data["Date"].astype(str))  # Date as string
        if date_to_modify:
            row = data[data["Date"].astype(str) == date_to_modify]
            st.write(f"Current Data for {date_to_modify}: {row['Flights'].values[0]} flights")
            
            # Edit the data
            if st.button("Edit Data"):
                new_flights = st.number_input("New number of flights", value=int(row['Flights'].values[0]))
                data.loc[data["Date"].astype(str) == date_to_modify, "Flights"] = new_flights
                st.success("Data updated successfully!")
                save_data(data)
            
            # Delete the data
            if st.button("Delete Data"):
                data = data[data["Date"].astype(str) != date_to_modify]
                st.success(f"Data for {date_to_modify} deleted.")
                save_data(data)
    return data


# Function to display metrics in a card-like style
def display_card(title, value, unit=None):
    st.markdown(
        f"""
        <div style="background-color: #2b2b2b; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 8px rgba(0,0,0,0.1); text-align: center;">
            <h4 style="color: #fafafa;">{title}</h4>
            <h1 style="color: #adadad; font-size: 36px; margin: ;">{value}</h1>
            {"<h6 style='color: #fafafa;'>" + unit + "</h6>" if unit else ""}
        </div>
        """,
        unsafe_allow_html=True
    )

# Main layout
st.set_page_config(page_title="Stair Trek 🧗‍♂️🏔️", layout="wide")
st.title("Stair Trek 🧗‍♂️🏔️")
st.write("Track your progress toward climbing the height of Gunung Kinabalu!")

# Sidebar menu for tabs
selected = option_menu(
    menu_title="Main Menu",  # required
    options=["Dashboard", "Data Entry", "Historical Data"],  # required
    icons=["bar-chart", "pencil-square", "archive"],  # optional
    menu_icon="cast",  # optional
    default_index=0,  # optional
    orientation="horizontal",
)

# Load existing data
data = load_data()

# Dashboard Tab
if selected == "Dashboard":
    st.header("Dashboard")
    

    # Row 1: Comparison chart (left) and Averages graphs (right)
    col_left, col_right = st.columns(2, gap="medium", )

    with col_left:
        # Comparison graph: Height Climbed vs Gunung Kinabalu
        with st.container(border=True):
            st.subheader("Progress")
            total_flights = data['Flights'].sum()
            height_climbed = total_flights * HEIGHT_PER_FLIGHT
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=['Your Progress'],
                y=[height_climbed],
                name='Height Climbed',
                marker_color='lightskyblue'
            ))
            fig.add_trace(go.Bar(
                x=['Gunung Kinabalu'],
                y=[TOTAL_HEIGHT_KINABALU],
                name='Gunung Kinabalu',
                marker_color='lightgreen'
            ))
            fig.update_layout(title="Comparison: Your Climb vs Gunung Kinabalu",
                            yaxis=dict(title='Height (in feet)'),
                            xaxis=dict(title='Comparison'),
                            showlegend=False,
                            yaxis_range=[0, TOTAL_HEIGHT_KINABALU])
            st.plotly_chart(fig)

    with col_right:
        # Display averages in 3 stacked plots: Daily, Weekly, Monthly patterns
        with st.container(border=True):
            st.subheader("Averages Over Time")
            daily_avg, weekly_avg, monthly_avg = calculate_averages(data)

            if not data.empty:
                daily_fig = px.line(data.groupby('Date')['Flights'].sum().reset_index(), x='Date', y='Flights',
                                    title='Daily Flights Pattern')
                weekly_fig = px.line(data.groupby('Week')['Flights'].sum().reset_index(), x='Week', y='Flights',
                                    title='Weekly Flights Pattern')
                monthly_fig = px.line(data.groupby('Month')['Flights'].sum().reset_index(), x='Month', y='Flights',
                                    title='Monthly Flights Pattern')
                
                st.plotly_chart(daily_fig)
                st.plotly_chart(weekly_fig)
                st.plotly_chart(monthly_fig)

    

    # Row 2: Display Progress Metrics
    with st.container(border=True):
        st.subheader("Progress")
        col_1, col_2, col_3 = st.columns(3)
        progress = total_flights / TOTAL_FLIGHTS_KINABALU * 100
        
        with col_1:
            display_card("Flights Climbed", total_flights, "flights")

        with col_2:
            display_card("Height Climbed", f"{height_climbed:.2f}", "feet")

        with col_3:
            display_card("Progress", f"{progress:.2f}%", None)

        # Progress bar
        st.progress(progress / 100) 

    

    # Row 3: Completion Prediction Metrics
    with st.container(border=True):
        st.subheader("Predictions")
        completion_date, days_remaining = predict_completion_date(data)

        col_1_completion, col_2_completion = st.columns(2)

        with col_1_completion:
            display_card("Estimated Completion Date", completion_date if completion_date else "N/A")

        with col_2_completion:
            display_card("Days Remaining", days_remaining if days_remaining else "N/A", "days")

    

    # Row 4: Display Averages Metrics
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
        today = st.date_input("Date", datetime.today()).strftime('%Y-%m-%d')  # Only keep the date part
        flights = st.number_input("Number of flights climbed today", min_value=0, step=1)

        # Add data to the table
        if st.button("Add Entry"):
            if today in data['Date'].astype(str).values:  # Check date string, no time part
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

# Historical Data
elif selected == "Historical Data":
    st.header("Historical Data")

    # Display data
    st.subheader("Flight of Stairs History")
    st.write(data)
    
    # Add a reset button to clear all data
    if st.button("Reset Data"):
        data = pd.DataFrame(columns=["Date", "Flights"])
        save_data(data)
        st.warning("All data has been reset.")
