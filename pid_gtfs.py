import csv
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class TripStop:
    """
    Class representing one public transport connection between two stops.
    There can be different instances of this class between the same stop IDs.
    This is representing the many connection during the day.
    There is ID of origin, ID of current stop, distance and time between them.
    """
    stop_id_from: str
    stop_id_to: str
    distance_km: float
    distance_min: float

    def __eq__(self, other): 
        if not isinstance(other, TripStop):
            return NotImplemented

        return self.stop_id_from == other.stop_id_from and self.stop_id_to == other.stop_id_to


@dataclass
class Trip:
    """
    One public transport trip consists out of many TripStop instances.
    """
    id: str
    trip_stops: list = field(default_factory=list)  # TripStop
    frequency: int = 1


@dataclass
class Connection:
    """
    This class represents a connection to stop with stop_id and stop_name.
    Each stop must have original ID, but can share names.
    There is the distance to this stop in km and minutes.
    The distance is the average from all relevant TripStops.
    """
    stop_id: str
    stop_name: str
    distance_km: float
    distance_min: float


@dataclass
class StopId:
    """
    Public transport stop represented by unique ID, name, the GPS,
    and all the connections it has with different stops by stop_id.
    """
    id: str
    name: str
    lon: float
    lat: float
    connections: dict = field(default_factory=dict)  # stop_id: Connection


@dataclass
class Stop:
    """
    This is the main information hiding class.
    It represents a stop with unique name. 
    Each stop with unique name can incorporate more stop IDs.
    The position is the middle of all StopIds GPS coordinates.
    And there are the connections the Stop has to different Stops ny name.
    """
    name: str
    lon: float = 0.0
    lat: float = 0.0
    ids: list = field(default_factory=list)  # StopId
    connections: dict = field(default_factory=dict)  # name: Connection


class PidGtfs:
    def __init__(self):
        self._results: dict = {}

    def calculate(self, start_hour: int = 0, stop_hour: int = 48, trip_frequency_min: int = 1,
                  input_stops: str = "gtfs/stops.txt", input_stop_times: str = "gtfs/stop_times.txt"):
        print(f"Load all stop IDs from {input_stops}")
        stop_ids = self._parse_stop_ids(input_stops)

        print(f"Load all trips between stops from {input_stop_times}")
        trips = self._parse_trips(input_stop_times, start_hour, stop_hour)

        print(f"Process trips")
        trips_len_before = len(trips)
        trips = self._process_trips(trips, trip_frequency_min)
        trips_len_after = len(trips)
        print(f"Trips length before was {trips_len_before}, after processing is {trips_len_after}")

        print("Fill stop IDs with connections, this can take some time")
        self._fill_stop_ids(stop_ids, trips)

        print("Prepare final Stop classes from stop IDs")
        stops = self._prepare_stops(stop_ids)

        print("Parse the relevant results to JSON")
        self._to_result_json(stops)

    def get_results(self) -> dict:
        return self._results

    def save(self, results_json: str = "output/stop_connections.json"):
        with open(results_json, 'w', encoding="utf8") as f:
            json.dump(self._results, f, ensure_ascii=False, sort_keys=True, indent=4)

    def load(self, results_json: str = "output/stop_connections.json"):
        with open(results_json, encoding="utf8") as f:
            self._results = json.load(f)

    def _parse_stop_ids(self, input_stops: str) -> dict:
        with open(input_stops, encoding="utf8") as f:
            csv_reared = csv.reader(f, delimiter=',', quotechar='"')

            columns = next(csv_reared)
            if len(columns) != 11 or columns[0] != "stop_id" or columns[-1] != "platform_code":
                raise Exception(f"Wrong file content: {columns}")

            stop_ids = {}
            for columns in csv_reared:
                id = columns[0]
                name = columns[1].strip('"')
                latitude = columns[2]
                longitude = columns[3]

                stop_ids[id] = StopId(id=id, name=name, lon=float(longitude), lat=float(latitude))

        return stop_ids

    def _parse_trips(self, input_stop_times: str, start_hour: int, stop_hour: int) -> dict:
        with open(input_stop_times, encoding="utf8") as f:
            line = f.readline()
            line = line.strip()
            columns = line.split(",")
            if len(columns) != 9 or columns[0] != "trip_id" or columns[-1] != "shape_dist_traveled":
                raise Exception(f"Wrong file content: {columns}")

            trips = {}
            last_stop_id = None
            last_departure_time = None
            last_traveled = None
            id_ignore = None

            for line in f:
                line = line.strip()
                columns = line.split(",")

                id = columns[0]
                #arrival_time = columns[1]
                departure_time = columns[2]
                stop_id = columns[3]
                traveled = columns[-1]

                if id_ignore != id:
                    if not id in trips:
                        # Prepare new trip, if is in the time period
                        (h, m, s) = departure_time.split(":")
                        if start_hour < int(h) < stop_hour:
                            trips[id] = Trip(id=id)
                        else:
                            id_ignore = id
                    
                    else:
                        # Append each stop to existing trip
                        distance_km = float(traveled) - float(last_traveled)
                        (h, m, s) = departure_time.split(":")
                        t_1 = float(h) * 60 + float(m) + float(s) / 60
                        (h, m, s) = last_departure_time.split(":")
                        t_2 = float(h) * 60 + float(m) + float(s) / 60
                        distance_min = t_1 - t_2
                        trips[id].trip_stops.append(TripStop(stop_id_from=last_stop_id, stop_id_to=stop_id, distance_km=distance_km, distance_min=distance_min))

                last_stop_id = stop_id
                last_departure_time = departure_time
                last_traveled = traveled

        return trips

    def _process_trips(self, trips: dict, trip_frequency_min: int) -> dict:
        """There are a lot of trips with the same stops -> eliminate them and count the frequency"""
        trips_new = {}

        for trip in trips.values():
            for trip_new in trips_new.values():
                if trip.trip_stops == trip_new.trip_stops:
                    # If equal, join the two
                    average_trip_stops = []
                    for i in range(len(trip.trip_stops)):
                        average_trip_stops.append(TripStop(stop_id_from=trip.trip_stops[i].stop_id_from, stop_id_to=trip.trip_stops[i].stop_id_to, 
                                                           distance_km=(trip.trip_stops[i].distance_km + trip_new.trip_stops[i].distance_km) / 2, 
                                                           distance_min=(trip.trip_stops[i].distance_min + trip_new.trip_stops[i].distance_min) / 2))
                    trip_new.trip_stops = average_trip_stops
                    trip_new.frequency += 1
                    break
            else:
                # If the trip was not found, add it to the new list
                trips_new[trip.id] = trip

        trips_new_filtered = {}
        for key, trip in trips_new.items():
            if trip.frequency >= trip_frequency_min:
                trips_new_filtered[key] = trip

        return trips_new_filtered

    def _fill_stop_ids(self, stop_ids: dict, trips: dict):
        progress_step = 10.0
        progress_next = progress_step
        length = len(stop_ids)
        counter = 0

        for stop_id in stop_ids.values():
            for trip in trips.values():
                for trip_stop in trip.trip_stops:
                    if trip_stop.stop_id_from == stop_id.id:
                        if not trip_stop.stop_id_to in stop_id.connections:
                            stop_id.connections[trip_stop.stop_id_to] = Connection(stop_id=trip_stop.stop_id_to, stop_name=stop_ids[trip_stop.stop_id_to].name,
                                                                                   distance_km=trip_stop.distance_km, distance_min=trip_stop.distance_min)
                        else:
                            stop_id.connections[trip_stop.stop_id_to].distance_km = (stop_id.connections[trip_stop.stop_id_to].distance_km + trip_stop.distance_km) / 2
                            stop_id.connections[trip_stop.stop_id_to].distance_min = (stop_id.connections[trip_stop.stop_id_to].distance_min + trip_stop.distance_min) / 2

            counter += 1
            if (counter / length) * 100.0 >= progress_next:
                print(f"    - {progress_next}%")
                progress_next += progress_step

    def _prepare_stops(self, stop_ids: dict) -> dict:
        stops = {}
        for stop_id in stop_ids.values():
            if not stop_id.name in stops:
                stops[stop_id.name] = Stop(name=stop_id.name)
                stops[stop_id.name].lon = stop_id.lon
                stops[stop_id.name].lat = stop_id.lat
            else:
                stops[stop_id.name].lon = (stops[stop_id.name].lon + stop_id.lon) / 2
                stops[stop_id.name].lat = (stops[stop_id.name].lat + stop_id.lat) / 2

            stops[stop_id.name].ids.append(stop_id)

            for connection in stop_id.connections.values():
                stops[stop_id.name].connections[connection.stop_name] = connection

        return stops

    def _to_result_json(self, stops: dict):
        self._results = {}
        for stop in stops.values():
            if len(stop.connections) > 0:
                self._results[stop.name] = {"longitude": stop.lon, "latitude": stop.lat, "connections": {}}
                for connection in stop.connections.values():
                    self._results[stop.name]["connections"][connection.stop_name] = {"distance_km": connection.distance_km, "distance_min": connection.distance_min}
