import requests
import re               # regex for parsing response text
import numpy as np
from datetime import datetime, timedelta
from asteroid import Asteroid

class AsteroidDatabase:
    URL = "https://ssd.jpl.nasa.gov/api/horizons.api"

    KNOWN_MASSES = {
        "Apophis": 2.664e-20,
        "Bennu": 8.737e-23,
        "Ryugu": 1.515e-22,
        "Ceres": 4.739e-16,
        "Vesta": 1.304e-16,
    }

    KNOWN_RADII = {
        "Apophis": 1.19e-9,
        "Bennu": 2.83e-10,
        "Ryugu": 4.72e-10,
        "Ceres": 6.33e-7,
        "Vesta": 3.61e-7,
    }

    def _query_horizons(self, asteroidName, date):
        # API requires STOP_TIME to be later than START_TIME
        start = date
        stop = (datetime.strptime(date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')

        params = {
            'format': 'text',  # text is easier to parse than json
            'COMMAND': f"'{asteroidName}'",  # asteroid name in quotes
            'OBJ_DATA': 'YES',
            'MAKE_EPHEM': 'YES',
            'EPHEM_TYPE': 'ELEMENTS',  # we want orbital elements
            'CENTER': '500@10',  # heliocentric Sun-centered
            'START_TIME': start,  # today's date
            'STOP_TIME': stop,  # one day later
            'STEP_SIZE': '1d',
            'OUT_UNITS': 'AU-D',  # AU and days
        }
        response = requests.get(self.URL, params=params)

        if response.status_code != 200:
            raise Exception(f"Horizons API error: {response.status_code}")
        return response.text

    def _parse_elements(self, raw_response):
        pass

    def _get_mass(self, name):
        pass


    def _get_radius(self, name):
        pass

    def fetch(self, asteroidName, epoch=None):
        # Get today's date if no epoch provided
        if epoch is None:
            date = datetime.today().strftime('%Y-%m-%d')
        elif isinstance(epoch, str):
            date = epoch  # already formatted string
        else:
            date = epoch.strftime('%Y-%m-%d')  # datetime object

        # Query NASA
        raw = self._query_horizons(asteroidName, date)

        # TEMPORARY — print raw response so we can write the parser
        print(raw)
        return None  # stop here for now


        # Parse elements
        elements = self._parse_elements(raw)

        # Get mass and radius
        mass = self._get_mass(asteroidName)
        radius = self._get_radius(asteroidName)

        # Create and return Asteroid object
        return Asteroid.from_orbital_elements(
            name=asteroidName,
            mass=mass,
            radius=radius,
            **elements  # unpacks a, e, i, Omega, omega, M
        )


