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

    print("Calculating all connection paths and times.")
    calculation = PathCalculations(connections, "Na Pískách")
    calculation.find_all_connections()
    calculation.save()


if __name__ == "__main__":
    print("Running the main script")
    main()
