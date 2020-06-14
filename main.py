import csv
from dataclasses import dataclass, field
from datetime import datetime
import json


PATH_DATA = "gtfs/"
PATH_STOPS = PATH_DATA + "stops.txt"
PATH_CONNETIONS = PATH_DATA + "stop_times.txt"


@dataclass
class TripStop:
    stop_id_from: str
    stop_id_to: str
    distance_km: float
    distance_s: float


@dataclass
class Trip:
    id: str
    stops: list = field(default_factory=list)  # TripStop


@dataclass
class Connection:
    stop_id: str
    stop_name: str
    distance_km: float
    distance_s: float


@dataclass
class StopId:
    id: str
    name: str
    lon: float
    lat: float
    connections: dict = field(default_factory=dict)  # stop_id: Connection


@dataclass
class Stop:
    name: str
    lon: float = 0.0
    lat: float = 0.0
    ids: list = field(default_factory=list)  # StopId
    connections: dict = field(default_factory=dict)  # name: Connection


def parse_stop_ids():
    with open(PATH_STOPS, encoding="utf8") as f:
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


def parse_trips():
    with open(PATH_CONNETIONS, encoding="utf8") as f:
        line = f.readline()
        line = line.strip()
        columns = line.split(",")
        if len(columns) != 9 or columns[0] != "trip_id" or columns[-1] != "shape_dist_traveled":
            raise Exception(f"Wrong file content: {columns}")

        trips = {}
        last_stop_id = None
        last_departure_time = None
        last_traveled = None

        for line in f:
            line = line.strip()
            columns = line.split(",")

            id = columns[0]
            #arrival_time = columns[1]
            departure_time = columns[2]
            stop_id = columns[3]
            traveled = columns[-1]

            if not id in trips:
                trips[id] = Trip(id=id)
            else:
                distance_km = float(traveled) - float(last_traveled)
                (h, m, s) = departure_time.split(":")
                t_1 = int(h) * 3600 + int(m) * 60 + int(s)
                (h, m, s) = last_departure_time.split(":")
                t_2 = int(h) * 3600 + int(m) * 60 + int(s)
                distance_s = t_1 - t_2
                trips[id].stops.append(TripStop(stop_id_from=last_stop_id, stop_id_to=stop_id, distance_km=distance_km, distance_s=float(distance_s)))

            last_stop_id = stop_id
            last_departure_time = departure_time
            last_traveled = traveled

    return trips


def main():
    print("Load all stop IDs")
    stop_ids = parse_stop_ids()

    print("Load all trips between stops")
    trips = parse_trips()

    print("Fill stop IDs with connections")
    for stop_id in stop_ids.values():
        for trip in trips.values():
            for trip_stop in trip.stops:
                if trip_stop.stop_id_from == stop_id.id:
                    if not trip_stop.stop_id_to in stop_id.connections:
                        stop_id.connections[trip_stop.stop_id_to] = Connection(stop_id=trip_stop.stop_id_to, stop_name=stop_ids[trip_stop.stop_id_to].name, distance_km=trip_stop.distance_km, distance_s=trip_stop.distance_s)
                    else:
                        stop_id.connections[trip_stop.stop_id_to].distance_km = (stop_id.connections[trip_stop.stop_id_to].distance_km + trip_stop.distance_km) / 2
                        stop_id.connections[trip_stop.stop_id_to].distance_s = (stop_id.connections[trip_stop.stop_id_to].distance_s + trip_stop.distance_s) / 2

    print("Prepare Stops")
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

    print("Save the structure to JSON")
    json_data = {}
    for stop in stops.values():
        if len(stop.connections) > 0:
            json_data[stop.name] = {"longitude": stop.lon, "latitude": stop.lat, "connections": {}}
            for connection in stop.connections.values():
                json_data[stop.name]["connections"][connection.stop_name] = {"distance_km": connection.distance_km, "distance_s": connection.distance_s}

    with open('data.json', 'w', encoding="utf8") as outfile:
        json.dump(json_data, outfile, ensure_ascii=False, sort_keys=True, indent=4)


if __name__ == "__main__":
    main()
