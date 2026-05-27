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
        "Psyche": 1.415e-14,  # solar masses — ~2.72×10¹⁹ kg
    }

    KNOWN_RADII = {
        "Apophis": 1.19e-9,
        "Bennu": 2.83e-10,
        "Ryugu": 4.72e-10,
        "Ceres": 6.33e-7,
        "Vesta": 3.61e-7,
        "Psyche": 1.47e-6,  # AU — ~220 km radius
    }

    HORIZONS_IDS = {
        "Apophis": "99942",
        "Psyche": "2000016",
        "Bennu": "2101955",
        "Ryugu": "2162173",
        "Ceres": "2000001",
        "Vesta": "2000004",
    }

    def _query_horizons(self, asteroidName, date):
        # API requires STOP_TIME to be later than START_TIME
        start = date
        stop = (datetime.strptime(date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')

        # Look up Horizons ID if known, otherwise try name directly
        horizons_id = self.HORIZONS_IDS.get(asteroidName, asteroidName)

        params = {
            'format': 'text',  # text is easier to parse than json
            'COMMAND': f"'{horizons_id}'",  # asteroid name in quotes
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

    def _parse_physical(self, raw_response):
        # Try to extract GM and RAD from response
        gm_match = re.search(r'GM=\s*([\d.E+\-]+)', raw_response)
        rad_match = re.search(r'RAD=\s*([\d.E+\-]+)', raw_response)

        mass = None
        radius = None

        if gm_match:
            # GM in km³/s² → convert to solar masses
            # GM_sun = 1.327e11 km³/s²
            GM_sun = 1.327e11
            gm = float(gm_match.group(1))
            mass = gm / GM_sun

        if rad_match:
            # RAD in km → convert to AU
            # 1 AU = 1.496e8 km
            rad_km = float(rad_match.group(1))
            radius = rad_km / 1.496e8

        return mass, radius

    def _parse_elements(self, raw_response):
        # Extract method of doing parse:
        # Has error handling.
        # \s* allows optional space before and after = sign.

        def extract(key):
            if len(key) == 1:
                # Single letter — add space before to avoid false matches
                # e.g. "A=" could match "MA=" without the space
                pattern = rf'\s{key}\s*=\s*([\d.E+\-]+)'
            else:
                # Multi-letter keys are specific enough
                pattern = rf'{key}\s*=\s*([\d.E+\-]+)'

            match = re.findall(pattern, raw_response)
            if not match:
                raise ValueError(f"Could not find {key} in Horizons response")
            return float(match[0])

        return {
            'a': extract('A'),
            'e': extract('EC'),
            'i': extract('IN'),
            'Omega': extract('OM'),
            'omega': extract('W'),
            'M': extract('MA')
        }

        '''
        # Can be hardcoded because I'll always want the below values:
        # Looking for EC, OM, W, IN, A, MA all followed by =
        # EC= matches the key literally
        # \s* matches any spaces after the equals sign
        # [\d.E+\-]+ matches the number including decimals and scientific notation
        patternEC = rf'EC=\s*([\d.E+\-]+)'

        # Finding the values of the above in raw_response with the pattern.
        numberEC = re.findall(patternEC, raw_response)
        # convert to float.
        # [0] for the first element in the findall list.
        EC = float(numberEC[0])

        patternOM = rf'OM=\s*([\d.E+\-]+)'
        numberOM = re.findall(patternOM, raw_response)
        OM = float(numberOM[0])

        # More specific — looks for W with space before it
        patternW = rf'\sW=\s*([\d.E+\-]+)'
        numberW = re.findall(patternW, raw_response)
        W = float(numberW[0])

        patternIN = rf'IN=\s*([\d.E+\-]+)'
        numberIN = re.findall(patternIN, raw_response)
        IN = float(numberIN[0])

        # More specific — looks for W with space before it
        patternA = rf'\sA=\s*([\d.E+\-]+)'
        numberA = re.findall(patternA, raw_response)
        A = float(numberA[0])

        patternMA = rf'MA=\s*([\d.E+\-]+)'
        numberMA = re.findall(patternMA, raw_response)
        MA = float(numberMA[0])

        # Dictionary Return: a, e, i, Omega, omega, M
        elements = {'a': A, 'e': EC, 'i': IN, 'Omega': OM, 'omega': W, 'M': MA}
        return elements
        '''

    def _get_mass(self, name):
        # reasonable small asteroid estimate (Solar Masses)
        estimate = 1e-20

        # Loop through and try to find the name in "KNOWN_MASSES"
        # [key, value] -> "[apophis, 2.664e-20]"
        for known_name, mass in self.KNOWN_MASSES.items():
            if known_name.lower() in name.lower():
                return mass
        # Not sure what to put or handle an estimate?
        print(f'Mass for {name} not found. \n Returning an estimate')
        return estimate

    def _get_radius(self, name):
        # reasonable small asteroid estimate (AU)
        estimate = 1e-9

        # Loop through and try to find the name in "KNOWN_MASSES"
        # [key, value] -> "[apophis, 2.664e-20]"
        for known_name, radius in self.KNOWN_RADII.items():
            if known_name.lower() in name.lower():
                return radius
        # Not sure what to put or handle an estimate?
        print(f'Radius for {name} not found. \n Returning an estimate')
        return estimate

    def fetch(self, asteroidName, epoch=None):
        # Normalize name — strips whitespace, capitalizes properly
        # "apophis" → "Apophis", "16 psyche" → "16 Psyche"
        asteroidName = asteroidName.strip().title()

        # Get today's date if no epoch provided
        if epoch is None:
            date = datetime.today().strftime('%Y-%m-%d')
        elif isinstance(epoch, str):
            date = epoch  # already formatted string
        else:
            date = epoch.strftime('%Y-%m-%d')  # datetime object

        # Query NASA
        raw = self._query_horizons(asteroidName, date)

        # Parse elements
        elements = self._parse_elements(raw)

        # Try to get physical parameters from response
        auto_mass, auto_radius = self._parse_physical(raw)

        # Fall back to known dictionaries or estimates if not found
        mass = auto_mass if auto_mass else self._get_mass(asteroidName)
        radius = auto_radius if auto_radius else self._get_radius(asteroidName)

        # Create and return Asteroid object
        return Asteroid.from_orbital_elements(
            name=asteroidName,
            mass=mass,
            radius=radius,
            **elements  # unpacks a, e, i, Omega, omega, M
        )


