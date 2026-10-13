"""Print upcoming BVG departures from a Berlin stop towards Hauptbahnhof.

Uses the public BVG REST API (https://v6.bvg.transport.rest, no API key needed):
1. Look up the start stop by name.
2. Fetch its next departures and print those heading to Hauptbahnhof.

Requires the `requests` package. Run with:
    python departures_clean.py

Edit the constants below to change the stop or target direction.
"""

from datetime import datetime
import requests

API_URL = "https://v6.bvg.transport.rest"

# Values shown in the header line; START is also used for the stop lookup.
START = "Bundeswehrkrankenhaus, Berlin"
DESTINATION = "Hauptbahnhof, Berlin"
BUS_LINE = "120"

# Departures whose direction contains this text are printed.
DIRECTION_FILTER = "Hauptbahnhof"


def get_bvg_departures(start):
    """Print departures from `start` heading towards DIRECTION_FILTER.

    Prints one line per matching departure as "HH:MM  <line> → Hauptbahnhof".
    Network/API errors are caught and printed, not raised.
    """
    try:
        # Step 1: resolve the stop name to a station. Only stations are
        # requested (no addresses or points of interest); the best match is used.
        response = requests.get(
            f"{API_URL}/locations",
            params={"query": start, "results": 1, "addresses": False, "poi": False},
            timeout=20,
        )
        response.raise_for_status()
        stations = response.json()
        if not stations:
            raise ValueError("No matching station found.")

        station = stations[0]
        print(f"Departures from: {station['name']}")

        # Step 2: fetch departures for the next 30 minutes, at most 5.
        # The direction filter is applied after this cap, so fewer than
        # 5 lines (or none) may be printed.
        response = requests.get(
            f"{API_URL}/stops/{station['id']}/departures",
            params={"duration": 30, "results": 5},
            timeout=20,
        )
        response.raise_for_status()

        for departure in response.json()["departures"]:
            if departure.get("cancelled"):
                continue
            if DIRECTION_FILTER not in departure.get("direction", ""):
                continue

            # Prefer the real-time time ("when"); fall back to the schedule.
            timestamp = departure.get("when") or departure.get("plannedWhen")
            if not timestamp:
                continue

            try:
                time = datetime.fromisoformat(timestamp).strftime("%H:%M")
            except ValueError:
                continue  # Skip departures with an unparseable timestamp.

            print(f"{time}  {departure['line']['name']} → {DIRECTION_FILTER}")

    except (requests.RequestException, ValueError, KeyError) as e:
        print(f"Error fetching BVG data: {e}")


def main():
    print(f"Fetching bus departures for {BUS_LINE} from {START} to {DESTINATION}...")
    get_bvg_departures(START)


if __name__ == "__main__":
    main()
