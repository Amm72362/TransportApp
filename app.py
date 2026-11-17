import sqlite3
import pandas as pd
import streamlit as st

# Setup Page
st.set_page_config(page_title="Transport System", layout="wide")
st.title("🚛 Transport & Fleet Management System")

# Database Connection
conn = sqlite3.connect("transport_quick.db", check_same_thread=False)
c = conn.cursor()

# Create Tables
c.execute(
    "CREATE TABLE IF NOT EXISTS vehicles (id INTEGER PRIMARY KEY, plate TEXT, model TEXT, status TEXT DEFAULT 'Available')"
)
c.execute(
    "CREATE TABLE IF NOT EXISTS drivers (id INTEGER PRIMARY KEY, name TEXT, phone TEXT, status TEXT DEFAULT 'Available')"
)
c.execute(
    "CREATE TABLE IF NOT EXISTS trips (id INTEGER PRIMARY KEY, customer TEXT, route TEXT, fare REAL, vehicle TEXT, driver TEXT, status TEXT DEFAULT 'In Transit')"
)
conn.commit()

# Sidebar Navigation
menu = st.sidebar.radio(
    "Navigation", ["Dashboard", "Dispatch Trip", "Manage Fleet", "Manage Drivers"]
)

# ---------------- DASHBOARD ----------------
if menu == "Dashboard":
    st.subheader("📊 Business Overview")

    rev = pd.read_sql("SELECT SUM(fare) as total FROM trips", conn).iloc[0][
        "total"
    ] or 0.0
    active_trips = len(
        pd.read_sql("SELECT * FROM trips WHERE status='In Transit'", conn)
    )
    fleet_count = len(pd.read_sql("SELECT * FROM vehicles", conn))

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Revenue", f"${rev:,.2f}")
    col2.metric("Active Trips", active_trips)
    col3.metric("Total Vehicles", fleet_count)

    st.write("---")
    st.subheader("Current Active Dispatches")
    trips_df = pd.read_sql("SELECT * FROM trips", conn)
    st.dataframe(trips_df, use_container_width=True)

# ---------------- DISPATCH TRIP ----------------
elif menu == "Dispatch Trip":
    st.subheader("📦 Dispatch New Cargo / Trip")

    vehicles = pd.read_sql(
        "SELECT plate FROM vehicles WHERE status='Available'", conn
    )["plate"].tolist()
    drivers = pd.read_sql(
        "SELECT name FROM drivers WHERE status='Available'", conn
    )["name"].tolist()

    with st.form("trip_form"):
        customer = st.text_input("Customer Name")
        route = st.text_input("Route (e.g., New York -> Chicago)")
        fare = st.number_input("Fare / Price ($)", min_value=0.0)
        selected_vehicle = st.selectbox("Assign Vehicle", vehicles if vehicles else ["No Available Vehicles"])
        selected_driver = st.selectbox("Assign Driver", drivers if drivers else ["No Available Drivers"])

        submitted = st.form_submit_button("Dispatch Trip")
        if submitted:
            if vehicles and drivers:
                c.execute(
                    "INSERT INTO trips (customer, route, fare, vehicle, driver) VALUES (?,?,?,?,?)",
                    (customer, route, fare, selected_vehicle, selected_driver),
                )
                c.execute(
                    "UPDATE vehicles SET status='In Transit' WHERE plate=?",
                    (selected_vehicle,),
                )
                c.execute(
                    "UPDATE drivers SET status='On Duty' WHERE name=?",
                    (selected_driver,),
                )
                conn.commit()
                st.success("Trip dispatched successfully!")
                st.rerun()
            else:
                st.error("Please add an available vehicle and driver first!")

# ---------------- MANAGE FLEET ----------------
elif menu == "Manage Fleet":
    st.subheader("🚚 Add New Vehicle")
    with st.form("vehicle_form"):
        plate = st.text_input("Plate Number")
        model = st.text_input("Vehicle Model (e.g. Volvo Truck)")
        if st.form_submit_button("Save Vehicle"):
            c.execute(
                "INSERT INTO vehicles (plate, model) VALUES (?,?)", (plate, model)
            )
            conn.commit()
            st.success(f"Vehicle {plate} Added!")
            st.rerun()

    st.write("### All Vehicles")
    st.dataframe(
        pd.read_sql("SELECT * FROM vehicles", conn), use_container_width=True
    )

# ---------------- MANAGE DRIVERS ----------------
elif menu == "Manage Drivers":
    st.subheader("👨‍✈️ Register New Driver")
    with st.form("driver_form"):
        name = st.text_input("Driver Name")
        phone = st.text_input("Phone Number")
        if st.form_submit_button("Save Driver"):
            c.execute(
                "INSERT INTO drivers (name, phone) VALUES (?,?)", (name, phone)
            )
            conn.commit()
            st.success(f"Driver {name} Registered!")
            st.rerun()

    st.write("### All Drivers")
    st.dataframe(
        pd.read_sql("SELECT * FROM drivers", conn), use_container_width=True
    )
