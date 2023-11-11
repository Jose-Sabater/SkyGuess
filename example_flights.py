import logging
from flights import Flight

logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    flight_instance = Flight(55.52863052257191, 11.909179687500002, degrees=1)
    closest_flights = flight_instance.get_closest_flights(2)
