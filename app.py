"""Streamlit web app showing upcoming BVG departures from a Berlin stop.

Reuses the fetch functions from departures_clean.py. Run locally with:
    streamlit run app.py
"""

import streamlit as st

from departures_clean import (
    DIRECTION_FILTER,
    FETCH_ERRORS,
    START,
    find_station,
    get_departures,
)

st.set_page_config(page_title="BVG Departures", page_icon="🚌")


# Streamlit re-runs this whole script on every interaction, so cache API
# results for 60 seconds to avoid calling the API each time.
@st.cache_data(ttl=60)
def load_departures(stop, direction_filter):
    """Return (station name, departures) for `stop`, filtered by direction."""
    station = find_station(stop)
    return station["name"], get_departures(station["id"], direction_filter)


st.title("🚌 BVG Departures")

with st.sidebar:
    stop = st.text_input("Stop", value=START)
    direction_filter = st.text_input("Direction contains", value=DIRECTION_FILTER)
    if st.button("Refresh"):
        load_departures.clear()

if not stop.strip():
    st.warning("Enter a stop name in the sidebar.")
    st.stop()

try:
    station_name, departures = load_departures(stop.strip(), direction_filter.strip())
except FETCH_ERRORS as e:
    st.error(f"Error fetching BVG data: {e}")
    st.stop()

st.subheader(f"Departures from: {station_name}")

if departures:
    st.dataframe(
        departures,
        hide_index=True,
        column_config={
            "time": "Time",
            "line": "Line",
            "direction": "Direction",
        },
    )
else:
    st.info(f"No departures towards “{direction_filter}” in the next 30 minutes.")

st.caption(
    "Shows the next 5 departures within 30 minutes (live times where available), "
    "filtered by direction. Data: v6.bvg.transport.rest."
)
