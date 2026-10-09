from datetime import datetime
import requests

def get_bvg_departures(start, destination, bus_line):
    try:
        response = requests.get(
            "https://v6.bvg.transport.rest/locations",
            params={
                "query": start,
                "results": 3,
                "addresses": False,
                "poi": False
            },
            timeout=20
        )
        response.raise_for_status()
        stations = response.json()
        
        if not stations:
            raise ValueError("No matching station found.")
            
        station = stations[0]
        print(f"Departures from: {station['name']}")
        
        response = requests.get(
            f"https://v6.bvg.transport.rest/stops/{station['id']}/departures",
            params={"duration": 30, "results": 5},
            timeout=20
        )
        response.raise_for_status()
        
        for departure in response.json()["departures"]:
            line = departure["line"]["name"]
            direction = departure.get("direction", "")
            
            if departure.get("cancelled"):
                continue
                
            timestamp = departure.get("when") or departure.get("plannedWhen")
            if not timestamp:
                continue
                
            try:
                time = datetime.fromisoformat(timestamp).strftime('%H:%M')
                if 'Hauptbahnhof' in direction:
                    print(f"{time}  {line} → Hauptbahnhof")
                elif 'S+U Hauptbahnhof' in direction:
                    print(f"{time}  {line} → Hauptbahnhof")
            except ValueError:
                continue
    
    except Exception as e:
        print(f"Error fetching BVG data: {e}")
        return None

def main():
    start = "Bundeswehrkrankenhaus, Berlin"
    destination = "Hauptbahnhof, Berlin"
    bus_line = "120"
    
    print(f"Fetching bus departures for {bus_line} from {start} to {destination}...")
    get_bvg_departures(start, destination, bus_line)

if __name__ == "__main__":
    main()