

def update_path_with_transfer_count(all_paths, trips):
    """
    Takes all paths list with dictionary and updates them with transfers needed from trips 
    """
    for paths in all_paths:
        for path in paths.values():
            path["transfers"] = get_transfer_count(path["path"], trips)


def get_transfer_count(path, connections):
    index = 0
    transfer_count = 0

    if len(path) <= 2:
        return 0

    while True:
        index += find_most_direct_stop_count(path, index, connections)
        if path[index] == path[-1]:
            break
        else:
            transfer_count += 1

    return transfer_count


def find_most_direct_stop_count(path, path_index, connections):
    direct_length_max = 0
    for connection in connections:
        connection_index = 0
        while connection_index < len(connection):
            if connection[connection_index] == path[path_index]:
                direct_match = 1
                while True:
                    if connection_index + direct_match >= len(connection) or path_index + direct_match >= len(path):
                        break

                    if connection[connection_index + direct_match] == path[path_index + direct_match]:
                        direct_match += 1
                    else:
                        break

                direct_length = direct_match - 1
                if direct_length > direct_length_max:
                    direct_length_max = direct_length

                break

            else:
                connection_index += 1

        if path_index + direct_length_max == len(path) - 1:
            break  # We are in the target stop

    if direct_length_max == 0:
        direct_length_max = 1  # This should never happen, but...

    return direct_length_max
