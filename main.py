import math
import json

from pid_gtfs import PidGtfs


RESULT_STOPS_JSON_FILE = "output/stop_connections.json"


def main():
    pid_gtfs = PidGtfs()

    print(f"Load last results from {RESULT_STOPS_JSON_FILE}, if possible")
    try:
        pid_gtfs.load(RESULT_STOPS_JSON_FILE)
    except:
        print("Error loading last results, must recalculate")
        pid_gtfs.calucate()
        print(f"Saving results to {{RESULT_STOPS_JSON_FILE}}")
        pid_gtfs.save(RESULT_STOPS_JSON_FILE)
    else:
        print("Results loaded")

    results_stops = pid_gtfs.get_results()
    connections = ConnectionsAccess(results_stops)
    # print(connections.get_gps("Na Pískách"))
    # print(connections.get_gps("Bořislavka"))
    # print(connections.get_distance_m("Na Pískách", "Na Pískách"))
    # print(connections.get_distance_m("Na Pískách", "Bořislavka"))
    # print(connections.get_connections("Na Pískách"))

    calculation = PathCalculations(connections)
    calculation.find_all_connections("Na Pískách")


# Source: https://janakiev.com/blog/gps-points-distance-python/
def haversine(gps_1, gps_2):
    R = 6372800  # Earth radius in meters
    lat1, lon1 = gps_1
    lat2, lon2 = gps_2

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi/2)**2 + \
        math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2

    return 2*R*math.atan2(math.sqrt(a), math.sqrt(1 - a))


class ConnectionsAccess():
    def __init__(self, json_data: dict):
        self._json_data = json_data

    def get_stops(self) -> list:
        return list(self._json_data.keys())

    def get_gps(self, stop: str) -> tuple:
        return (self._json_data[stop]["latitude"], self._json_data[stop]["longitude"])

    def get_distance_gps(self, stop_1: str, stop_2: str) -> float:
        (x1, y1) = self.get_gps(stop_1)
        (x2, y2) = self.get_gps(stop_2)
        return ((x1-x2)**2 + (y1-y2)**2)**0.5

    def get_distance_m(self, stop_1: str, stop_2: str) -> float:
        return haversine(self.get_gps(stop_1), self.get_gps(stop_2))

    def get_connections(self, stop: str) -> list:
        return list(self._json_data[stop]["connections"].keys())

    def get_connection_distance_km(self, stop: str, connection: str) -> float:
        return self._json_data[stop]["connections"][connection]["distance_km"]

    def get_connection_distance_min(self, stop: str, connection: str) -> float:
        return self._json_data[stop]["connections"][connection]["distance_min"]

    def get_connections_with_distance_km(self, stop: str) -> list:
        result = []
        for (connection, distances) in self._json_data[stop]["connections"]:
            result.append((connection, distances["distance_km"]))

        return result

    def get_connection_with_distance_min(self, stop: str) -> list:
        result = []
        for connection, distances in self._json_data[stop]["connections"].items():
            result.append((connection, distances["distance_min"]))

        return result


class PathCalculations():
    def __init__(self, connections: ConnectionsAccess):
        self._connections = connections
        self._map = {}  # Dictionary of all stops and if the were processed
        self._stops_queue = []
        self._result = []

    def _initialize_map(self):
        self._map = {}
        for stop in self._connections.get_stops():
            self._map[stop] = True

    def _expand(self):
        current_stop = self._result[-1]
        connections_list = self._connections.get_connections(current_stop[0])
        for connection in connections_list:
            if self._map.get(connection, False):
                # (Name, Total Distance, [Path])
                self._stops_queue.append((connection, round(current_stop[1] + self._connections.get_connection_distance_min(current_stop[0], connection), 1), current_stop[2] + [connection]))
                # Set stops as processed
                self._map[connection] = False

    def find_all_connections(self, stop: str):
        self._initialize_map()
        self._stops_queue = []

        # Set start stop as visited
        self._map[stop] = False
        # Append the start stop to results with zero time
        # (Name, Total Distance, [Path])
        self._stops_queue.append((stop, 0, [stop]))

        while self._stops_queue:
            # Sort
            self._stops_queue.sort(key=lambda tup: tup[1], reverse=True)

            # Safe the closest in result list
            self._result.append(self._stops_queue.pop())

            # Expand the closest
            self._expand()

        with open("output/" + stop + ".json", 'w', encoding="utf8") as f:
            json.dump(self._result, f, ensure_ascii=False, sort_keys=True, indent=4)
            

if __name__ == "__main__":
    print("Running the main script")
    main()
