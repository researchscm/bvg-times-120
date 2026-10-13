"""Print upcoming BVG departures from a Berlin stop towards Hauptbahnhof.

Uses the public BVG REST API (https://v6.bvg.transport.rest, no API key needed):
1. Look up the start stop by name.
2. Fetch its next departures and print those heading to Hauptbahnhof.

Requires the `requests` package. Run with:
    python departures_clean.py

Edit the constants below to change the stop or target direction.
`find_station` and `get_departures` return data instead of printing,
so they can be reused (e.g. by the Streamlit app in app.py).
"""

from datetime import datetime
import requests

API_URL = "https://v6.bvg.transport.rest"

# Values shown in the header line; START is also used for the stop lookup.
START = "Bundeswehrkrankenhaus, Berlin"
DESTINATION = "Hauptbahnhof, Berlin"
BUS_LINE = "120"

# Departures whose direction contains this text are shown.
DIRECTION_FILTER = "Hauptbahnhof"

# Errors that the fetch functions can raise for network/API problems.
FETCH_ERRORS = (requests.RequestException, ValueError, KeyError)


def find_station(query):
    """Return the best-matching station for `query` as a dict with "id" and "name".

    Only stations are requested (no addresses or points of interest).
    Raises one of FETCH_ERRORS on failure.
    """
    response = requests.get(
        f"{API_URL}/locations",
        params={"query": query, "results": 1, "addresses": False, "poi": False},
        timeout=20,
    )
    response.raise_for_status()
    stations = response.json()
    if not stations:
        raise ValueError("No matching station found.")
    return stations[0]


def get_departures(station_id, direction_filter=DIRECTION_FILTER):
    """Return upcoming departures from `station_id` towards `direction_filter`.

    Each departure is a dict: {"time": "HH:MM", "line": ..., "direction": ...}.
    Covers the next 30 minutes, at most 5 departures. The direction filter is
    applied after this cap, so fewer than 5 (or none) may be returned.
    Raises one of FETCH_ERRORS on failure.
    """
    response = requests.get(
        f"{API_URL}/stops/{station_id}/departures",
        params={"duration": 30, "results": 5},
        timeout=20,
    )
    response.raise_for_status()

    departures = []
    for departure in response.json()["departures"]:
        direction = departure.get("direction") or ""
        if departure.get("cancelled") or direction_filter not in direction:
            continue

        # Prefer the real-time time ("when"); fall back to the schedule.
        timestamp = departure.get("when") or departure.get("plannedWhen")
        if not timestamp:
            continue

        try:
            # Timestamps carry Berlin's UTC offset; only reformat, don't convert.
            time = datetime.fromisoformat(timestamp).strftime("%H:%M")
        except ValueError:
            continue  # Skip departures with an unparseable timestamp.

        departures.append(
            {"time": time, "line": departure["line"]["name"], "direction": direction}
        )
    return departures


def get_bvg_departures(start):
    """Print departures from `start` heading towards DIRECTION_FILTER.

    Prints one line per matching departure as "HH:MM  <line> → Hauptbahnhof".
    Network/API errors are caught and printed, not raised.
    """
    try:
        station = find_station(start)
        print(f"Departures from: {station['name']}")
        for departure in get_departures(station["id"]):
            print(f"{departure['time']}  {departure['line']} → {DIRECTION_FILTER}")
    except FETCH_ERRORS as e:
        print(f"Error fetching BVG data: {e}")


def main():
    print(f"Fetching bus departures for {BUS_LINE} from {START} to {DESTINATION}...")
    get_bvg_departures(START)


if __name__ == "__main__":
    main()
