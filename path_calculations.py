import math
import json


# Source: https://janakiev.com/blog/gps-points-distance-python/
def _haversine(gps_1: tuple, gps_2: tuple) -> float:
    """
    Calculate distance in meters between two GPS coordinates.
    Takes 2x (latitude, longitude), return meters between them.
    """
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
    """
    Class enables simple access to JSON connection data.
    """

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
        return _haversine(self.get_gps(stop_1), self.get_gps(stop_2))

    def get_connections(self, stop: str) -> list:
        return list(self._json_data[stop]["connections"].keys())

    def get_connection_distance_km(self, stop: str, connection: str) -> float:
        return self._json_data[stop]["connections"][connection]["distance_km"]

    def get_connection_distance_min(self, stop: str, connection: str) -> float:
        return self._json_data[stop]["connections"][connection]["distance_min"]


class PathCalculations():
    """
    Class calculates all paths in connection stops.
    It saves sorted JSON with all the available connections 
    from a stop.
    """

    def __init__(self, connections: ConnectionsAccess, stop: str):
        self._connections = connections
        self._map = {}  # Dictionary of all stops and if the were processed
        self._stops_queue = []
        self._result = []
        self._start_stop = stop

    def find_all_connections(self):
        """
        Breadth-first search throudh all the stops.
        Saves them in ascending order.
        """
        self._initialize_map()
        self._stops_queue = []

        # Set start stop as visited
        self._map[self._start_stop] = False
        # Append the start stop to results with zero time
        # (Name, Total Distance, [Path])
        self._stops_queue.append((self._start_stop, 0, [self._start_stop]))

        while self._stops_queue:
            # Sort
            self._stops_queue.sort(key=lambda tup: tup[1], reverse=True)

            # Safe the closest in result list
            self._result.append(self._stops_queue.pop())

            # Expand the closest
            self._expand()

    def get_results(self) -> dict:
        return self._result

    def save(self, results_json: str = ""):
        if results_json == "":
            results_json = "output/" + self._start_stop + ".json"

        with open(results_json, 'w', encoding="utf8") as f:
            json.dump(self._result, f, ensure_ascii=False, sort_keys=True, indent=4)

    def load(self, results_json: str = ""):
        if results_json == "":
            results_json = "output/" + self._start_stop + ".json"

        with open(results_json, encoding="utf8") as f:
            self._result = json.load(f)

    def _initialize_map(self):
        """
        Set all stops as true.
        """
        self._map = {}
        for stop in self._connections.get_stops():
            self._map[stop] = True

    def _expand(self):
        """
        Expand the last stop from results, add to queue.
        """
        current_stop = self._result[-1]
        connections_list = self._connections.get_connections(current_stop[0])
        for connection in connections_list:
            if self._map.get(connection, False):
                # (Name, Total Distance, [Path])
                self._stops_queue.append((connection, round(current_stop[1] + self._connections.get_connection_distance_min(current_stop[0], connection), 1), current_stop[2] + [connection]))
                # Set stops as processed
                self._map[connection] = False
