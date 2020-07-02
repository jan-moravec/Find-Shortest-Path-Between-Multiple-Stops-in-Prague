from pid_gtfs import PidGtfs
from path_calculations import ConnectionsAccess, PathCalculations
from transfer_count import update_path_with_transfer_count


RESULT_STOPS_JSON_FILE = "output/connections.json"
RESULT_TRIPS_JSON_FILE = "output/trips.json"
RESULT_TEXT_FILE = "output/results.txt"


def main():
    pid_gtfs = PidGtfs()

    print(f"Load last results from {RESULT_STOPS_JSON_FILE} and {RESULT_TRIPS_JSON_FILE}, if possible")
    try:
        pid_gtfs.load(RESULT_STOPS_JSON_FILE, RESULT_TRIPS_JSON_FILE)
    except:
        print("Error loading last results, must recalculate")
        pid_gtfs.calculate(16, 18, 6)
        print(f"Saving results to {RESULT_STOPS_JSON_FILE} and {RESULT_TRIPS_JSON_FILE}")
        pid_gtfs.save(RESULT_STOPS_JSON_FILE, RESULT_TRIPS_JSON_FILE)
    else:
        print("Results loaded")

    results_stops = pid_gtfs.get_results()
    result_trips = pid_gtfs.get_trips()

    print("Creating class for accessing results")
    connections = ConnectionsAccess(results_stops)

    print("Calculating all connection paths and times")
    start_stops = ["Na Pískách", "Kudrnova", "Branické náměstí", "Sídliště Malešice"]
    all_paths = get_all_paths(connections, start_stops)

    print("Updating with minimum transfers needed")
    update_path_with_transfer_count(all_paths, result_trips)

    print("Evaluating stops - the lower score the better")
    stops = connections.get_stops()
    #scores = evaluate_paths(stops, all_paths, 2, sum)
    scores = evaluate_paths(stops, all_paths, 2, score_function)

    print("Printing results")
    for (index, value) in enumerate(scores):
        print(f"{index + 1}. {value[0]} ({value[1]})")

        for path in all_paths:
            print(f"\t - {path[value[0]]['transfers']} transfers, path:  {path[value[0]]['path']}")

        if index == 20:
            break

    print("Saving results to file")
    with open(RESULT_TEXT_FILE, "w", encoding="utf8") as f:
        for (index, value) in enumerate(scores):
            f.write(f"{index + 1}. {value[0]} ({value[1]})\n")

            for path in all_paths:
                f.write(f"\t - {path[value[0]]['transfers']} transfers, path:  {path[value[0]]['path']}\n")

            f.write("\n")


def get_all_paths(connections: ConnectionsAccess, start_stops: list):
    """
    Takes connections class and start stops list, finds all connections for each
    start stop in a list and returns the result as a list of dictionaries.
    """
    all_paths = []
    for start_stop in start_stops:
        calculation = PathCalculations(connections, start_stop)
        calculation.find_all_connections()
        calculation.save()

        results_list = calculation.get_results()
        results_dict = {}
        for (stop, distance, path) in results_list:
            results_dict[stop] = {"distance_min": distance, "path": path, "transfers": "unknown"}

        all_paths.append(results_dict)

    return all_paths


def evaluate_paths(stops: list, all_paths: list, transfer_minutes: float, score_function):
    """
    Evaluates paths, returning a sorted tuple with the stop name and score.
    The lower score the better -> meaning its closer to everybody.

    Takes all available stops, calculated paths, time it takes to make a transfer in minutes
    and score function for calculation score out of distances.
    """
    scores = []
    for stop in stops:
        distances = []

        for path in all_paths:
            if not stop in path:
                break
            distances.append(path[stop]["distance_min"] + path[stop]["transfers"] * transfer_minutes)

        if len(distances) == len(all_paths):
            score = score_function(distances)
            scores.append((stop, score))

    scores.sort(key=lambda tup: tup[1])

    return scores


def score_function(values: list):
    """
    This function is more fair than simple sum. 
    It takes into account also the deviation between each distance,
    so nobody should be traveling more than the others.
    """
    sum_value = sum(values)
    mean_value = sum_value / len(values)
    deviations = [(x - mean_value)**2 for x in values]

    return sum_value + sum(deviations)**0.5


if __name__ == "__main__":
    print("Running the main script")
    main()
