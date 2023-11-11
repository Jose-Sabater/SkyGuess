"""This module contains the Flight class which is used to get flight details."""
import logging
import math
from pyproj import Proj, transform, CRS, Transformer
from flightradar import init_fr_api

# add file logging
# Create a logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # Set the logging level

# Create a file handler
file_handler = logging.FileHandler("./logs/flight.log", mode="a")
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)

# Create a stream handler for console output
console_handler = logging.StreamHandler()


logger.addHandler(file_handler)
logger.addHandler(console_handler)


class Coord:
    """Class to handle coordinates in EPSG:3857"""

    def __init__(self, lat: float, long: float, coord: str = "wgs84"):
        """Initializes the class with some coordinates in EPSG:4326"""
        if coord == "wgs84":
            self.long = long
            self.lat = lat
        elif coord == "mercator":
            self.lat, self.long = self._to_wgs84(lat=lat, long=long)

    def two_point_square(self, degrees: float = 0.6) -> str:
        """Returns coordinates in the format y1,y2,x1,x2"""
        # lat_wgs84, long_wgs84 = self.to_wgs84()
        # y1 = lat_wgs84 + degrees / 2
        # y2 = lat_wgs84 - degrees / 2
        # x1 = long_wgs84 + degrees / 2
        # x2 = long_wgs84 - degrees / 2
        y1 = self.lat + degrees / 4
        y2 = self.lat - degrees / 4
        x1 = self.long - degrees / 2
        x2 = self.long + degrees / 2
        return f"{y1},{y2},{x1},{x2}"

    def get_corners(self, degrees: float = 0.6) -> list[float]:
        """Returns a list of tuples containing the corners of a rectangle"""
        # Calculate the corners of the rectangle
        top_left = (self.lat + degrees / 4, self.long - degrees / 2)
        top_right = (self.lat + degrees / 4, self.long + degrees / 2)
        bottom_left = (self.lat - degrees / 4, self.long - degrees / 2)
        bottom_right = (self.lat - degrees / 4, self.long + degrees / 2)

        # Return the corners as a list of tuples
        return [top_left, top_right, bottom_right, bottom_left]

    def _to_wgs84(self, lat: float, long: float) -> tuple[float]:
        """Conversion from EPSG:3857(mercator) to EPSG:4326(WGS84)"""
        x = long
        y = lat
        lon = x / 20037508.34 * 180.0
        lat = y / 20037508.34 * 180.0
        lat = (
            180 / math.pi * (2 * math.atan(math.exp(lat * math.pi / 180)) - math.pi / 2)
        )

        return lat, lon

    def to_mercator(self, lat: float, long: float) -> tuple[float]:
        """Conversion from EPSG:4326 to EPSG:3857"""
        if not (-90 <= lat <= 90 and -180 <= long <= 180):
            raise ValueError("Invalid latitude or longitude values")

        transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
        x, y = transformer.transform(long, lat)
        return x, y


class Flight:
    """Create a flight object with the closest flights in the area. using FlightRadar24 API"""

    def __init__(self, lat, long, degrees: float = 0.6):
        self.lat = lat
        self.long = long
        self.fr_api = init_fr_api()
        self.flights = []
        self._get_flight_details(degrees=degrees)
        logging.info("Initialized Flight class. with lat: %s, long: %s", lat, long)

    def _get_flight_details(self, degrees: float = 0.6) -> list[dict]:
        """Get the flight details in the area."""
        # Get the square coordinates
        two_point_square = Coord(self.lat, self.long).two_point_square(degrees)
        # Get the flights in the area
        flights = self.fr_api.get_flights(bounds=two_point_square)
        for flight in flights:
            self.flights.append(self.fr_api.get_flight_details(flight))
        logging.info(f"{len(self.flights)} flights in the area.")

    def get_closest_flights(self, n_flights: int = 1):
        """Get the closest flights based on the most recent trail point and closest euclidean distance."""
        if not self.flights:
            return []

        # Calculate and assign distance for each flight
        for flight in self.flights:
            top_trail_point = flight["trail"][0]
            distance = self._calculate_euclidean_distance(
                top_trail_point["lat"], top_trail_point["lng"], self.lat, self.long
            )
            flight["euc_distance"] = distance

        # Sort flights by distance
        sorted_flights = sorted(self.flights, key=lambda f: f["euc_distance"])

        # Check if the number of flights is less than n_flights
        if len(sorted_flights) < n_flights:
            logging.warning(
                f"Number of flights in the area is less than selected: {n_flights}."
            )

        for sorted_flight in sorted_flights:
            logging.info(
                f"Flight: {sorted_flight['identification']['callsign']} with distance: {sorted_flight['euc_distance']}"
            )

        # Return the top n closest flights
        return sorted_flights[:n_flights]

    def get_flight_based_on_direction(self, direction: str) -> dict:
        """Get the flight based on the direction of the plane."""
        # Cardinal directions mapped to angles
        cardinal_directions = {
            "N": 0,
            "NE": 45,
            "E": 90,
            "SE": 135,
            "S": 180,
            "SW": 225,
            "W": 270,
            "NW": 315,
        }

        # Convert cardinal direction to angle
        target_angle = cardinal_directions.get(direction.upper())
        if target_angle is None:
            raise ValueError(
                "Invalid cardinal direction. Choose from N, NE, E, SE, S, SW, W, NW."
            )

        closest_flight = None
        smallest_angle_difference = float("inf")

        for flight in self.flights:
            flight_angle = self.calculate_angle(
                self.lat,
                self.long,
                flight["trail"][0]["lat"],
                flight["trail"][0]["lng"],
            )
            angle_difference = min(
                abs(flight_angle - target_angle), 360 - abs(flight_angle - target_angle)
            )

            if angle_difference < smallest_angle_difference:
                smallest_angle_difference = angle_difference
                closest_flight = flight

        return closest_flight

    @staticmethod
    def _calculate_euclidean_distance(
        flight_lat: float, flight_long: float, lat: float, long: float
    ):
        """Calculate the euclidean distance between two points"""
        return math.sqrt((flight_lat - lat) ** 2 + (flight_long - long) ** 2)

    @staticmethod
    def calculate_angle(lat1, long1, lat2, long2):
        """Calculate the angle from one point to another."""
        dLon = long2 - long1
        x = math.cos(math.radians(lat2)) * math.sin(math.radians(dLon))
        y = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - math.sin(
            math.radians(lat1)
        ) * math.cos(math.radians(lat2)) * math.cos(math.radians(dLon))
        angle = math.atan2(x, y)
        angle = math.degrees(angle)
        angle = (angle + 360) % 360
        return angle
