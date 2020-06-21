from pid_gtfs import PidGtfs
from path_calculations import ConnectionsAccess, PathCalculations


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

    print("Creating class for accessing results")
    connections = ConnectionsAccess(results_stops)

    print("Calculating all connection paths and times")
    start_stops = ["Na Pískách", "Kudrnova", "Branické náměstí", "Sídliště Malešice"]
    all_paths = get_all_paths(connections, start_stops)

    print("Evaluating stops")
    stops = connections.get_stops()
    #scores = evaluate_paths(stops, all_paths, sum)
    scores = evaluate_paths(stops, all_paths, score_function)

    print("Printing results")
    for (index, value) in enumerate(scores):
        print(f"{index}: {value[0]}")

        for path in all_paths:
            print(f"\t - {path[value[0]]['path']}")

        if index == 20:
            break


def get_all_paths(connections: ConnectionsAccess, start_stops: list):
    all_paths = []
    for start_stop in start_stops:
        calculation = PathCalculations(connections, start_stop)
        calculation.find_all_connections()
        calculation.save()

        results_list = calculation.get_results()
        results_dict = {}
        for (stop, distance, path) in results_list:
            results_dict[stop] = {"distance_min": distance, "path": path}

        all_paths.append(results_dict)

    return all_paths


def evaluate_paths(stops: list, all_paths: list, score_function):
    scores = []
    for stop in stops:
        distances = []

        for path in all_paths:
            if not stop in path:
                break
            distances.append(path[stop]["distance_min"])

        if len(distances) == len(all_paths):
            score = score_function(distances)
            scores.append((stop, score))

    scores.sort(key=lambda tup: tup[1])
    return scores


def score_function(values: list):
    sum_value = sum(values)
    mean_value = sum_value / len(values)
    deviations = [(x - mean_value)**2 for x in values]

    return sum_value + sum(deviations)**0.5


if __name__ == "__main__":
    print("Running the main script")
    main()
