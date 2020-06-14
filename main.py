PATH_DATA = "gtfs/"
PATH_STOPS = PATH_DATA + "stops.txt"


def main():
    with open(PATH_STOPS, encoding="utf8") as f:
        line = f.readline()
        print(line)


if __name__ == "__main__":
    main()
