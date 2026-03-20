class GravityController:
    """
    Controller class that manages the gravitational calculation workflow.
    Coordinates between ConfigManager, Logger, and GravAll components.

    Key Features:

    Initialization & Discovery: Automatically discovers available celestial bodies from your configuration
    CRUD Operations:
        add_celestial_body() - Add new celestial bodies
        remove_celestial_body() - Remove bodies from config
        get_body_info() - Retrieve body configuration
    Calculation Methods:
        calculate_single() - Calculate gravity for one body
        calculate_all() - Calculate for all bodies
        calculate_multiple() - Calculate for specific bodies
        compare_gravities() - Compare multiple bodies (sorted results)
    History & Export:
        Maintains calculation history
        export_results() - Export results to file
        get_calculation_history() - Retrieve past calculations
    Validation:
        validate_body_config() - Ensure bodies have all required parameters
    """

    def __init__(self, config_manager, logger):
        """
        Initialize the controller with configuration and logging dependencies

        Args:
            config_manager: ConfigManager instance for handling configuration
            logger: Logger instance for application logging
        """
        self.config = config_manager
        self.logger = logger
        self.available_bodies = []
        self.calculation_history = []

        # Initialize available celestial bodies
        self._load_available_bodies()

    def _load_available_bodies(self):
        """Discover available celestial bodies from configuration"""
        bodies = set()
        for key in self.config.config_data.keys():
            if "_gConst" in key:
                body_name = key.replace("_gConst", "")
                bodies.add(body_name)

        self.available_bodies = sorted(list(bodies))
        self.logger.info(f"Loaded {len(self.available_bodies)} celestial bodies: {', '.join(self.available_bodies)}")

    def get_available_bodies(self):
        """Return list of available celestial bodies"""
        return self.available_bodies.copy()

    def add_celestial_body(self, name, g_const, mass, dist):
        """
        Add a new celestial body to the configuration

        Args:
            name: Name of the celestial body
            g_const: Gravitational constant (usually 6.67e-11)
            mass: Mass of the body in kg
            dist: Radius squared expression or value

        Returns:
            bool: True if successfully added, False otherwise
        """
        try:
            # Create configuration entries
            success = all([
                self.config.create_key_value(f"{name}_gConst", str(g_const), f"{name} gravitational constant"),
                self.config.create_key_value(f"{name}_mass", str(mass), f"{name} mass"),
                self.config.create_key_value(f"{name}_dist", str(dist), f"{name} radius squared")
            ])

            if success:
                self._load_available_bodies()  # Refresh the list
                self.logger.info(f"Successfully added celestial body: {name}")
                return True
            else:
                self.logger.warning(f"Celestial body {name} may already exist")
                return False

        except Exception as e:
            self.logger.error(f"Error adding celestial body {name}: {str(e)}")
            return False

    def remove_celestial_body(self, name):
        """
        Remove a celestial body from the configuration

        Args:
            name: Name of the celestial body to remove

        Returns:
            bool: True if successfully removed, False otherwise
        """
        try:
            # Remove all configuration entries for this body
            keys_to_remove = [f"{name}_gConst", f"{name}_mass", f"{name}_dist"]

            for key in keys_to_remove:
                self.config.remove_value(key)

            # Rewrite the configuration file
            self.config.write_config()

            # Refresh the available bodies list
            self._load_available_bodies()

            self.logger.info(f"Successfully removed celestial body: {name}")
            return True

        except Exception as e:
            self.logger.error(f"Error removing celestial body {name}: {str(e)}")
            return False

    def calculate_single(self, body_name):
        """
        Calculate gravity for a single celestial body

        Args:
            body_name: Name of the celestial body

        Returns:
            dict: Calculation results or None if error occurred
        """
        from testApophisGravity import GravAll

        if body_name not in self.available_bodies:
            self.logger.error(f"Celestial body '{body_name}' not found")
            return None

        try:
            self.logger.info(f"Starting calculation for {body_name}")

            # Create gravity calculator instance
            grav_calc = GravAll(body_name, self.config, self.logger)
            grav_calc.getGrav()

            # Store results
            result = {
                'body_name': body_name,
                'gravitational_constant': grav_calc.gConst,
                'mass': grav_calc.mass,
                'radius_squared': grav_calc.dist,
                'gravity': grav_calc.get_gravity_value()
            }

            # Add to calculation history
            self.calculation_history.append(result)

            self.logger.info(f"Successfully calculated gravity for {body_name}: {result['gravity']} m/s^2")

            return result

        except Exception as e:
            self.logger.error(f"Error calculating gravity for {body_name}: {str(e)}")
            return None

    def calculate_all(self):
        """
        Calculate gravity for all available celestial bodies

        Returns:
            list: List of calculation results
        """
        results = []

        self.logger.info("Starting batch calculation for all celestial bodies")

        for body in self.available_bodies:
            result = self.calculate_single(body)
            if result:
                results.append(result)

        self.logger.info(f"Completed batch calculation: {len(results)} bodies processed")

        return results

    def calculate_multiple(self, body_names):
        """
        Calculate gravity for multiple specified celestial bodies

        Args:
            body_names: List of celestial body names

        Returns:
            list: List of calculation results
        """
        results = []

        for body in body_names:
            if body in self.available_bodies:
                result = self.calculate_single(body)
                if result:
                    results.append(result)
            else:
                self.logger.warning(f"Skipping unknown celestial body: {body}")

        return results

    def compare_gravities(self, body_names=None):
        """
        Compare gravitational forces of multiple bodies

        Args:
            body_names: List of body names to compare (None = all bodies)

        Returns:
            list: Sorted list of results by gravity (strongest to weakest)
        """
        if body_names is None:
            results = self.calculate_all()
        else:
            results = self.calculate_multiple(body_names)

        # Sort by gravity value (descending)
        sorted_results = sorted(results, key=lambda x: x['gravity'], reverse=True)

        self.logger.info("Gravity comparison completed")

        return sorted_results

    def get_calculation_history(self):
        """Return the history of all calculations performed"""
        return self.calculation_history.copy()

    def clear_history(self):
        """Clear the calculation history"""
        self.calculation_history = []
        self.logger.info("Calculation history cleared")

    def export_results(self, results, filename):
        """
        Export calculation results to a file

        Args:
            results: List of calculation results
            filename: Output file path

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(filename, 'w') as f:
                f.write("Gravitational Force Calculation Results\n")
                f.write("=" * 60 + "\n\n")

                for result in results:
                    f.write(f"Celestial Body: {result['body_name']}\n")
                    f.write(f"  Gravitational Constant (G): {result['gravitational_constant']}\n")
                    f.write(f"  Mass: {result['mass']} kg\n")
                    f.write(f"  Radius Squared: {result['radius_squared']} m^2\n")
                    f.write(f"  Gravitational Force: {result['gravity']} m/s^2\n")
                    f.write("-" * 60 + "\n")

            self.logger.info(f"Results exported to {filename}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting results: {str(e)}")
            return False

    def validate_body_config(self, body_name):
        """
        Validate that a celestial body has all required configuration parameters

        Args:
            body_name: Name of the celestial body to validate

        Returns:
            tuple: (is_valid: bool, missing_keys: list)
        """
        required_keys = [f"{body_name}_gConst", f"{body_name}_mass", f"{body_name}_dist"]
        missing_keys = []

        for key in required_keys:
            if not self.config.get_value(key):
                missing_keys.append(key)

        is_valid = len(missing_keys) == 0

        if is_valid:
            self.logger.info(f"Configuration validation passed for {body_name}")
        else:
            self.logger.warning(f"Configuration validation failed for {body_name}: missing {missing_keys}")

        return is_valid, missing_keys

    def get_body_info(self, body_name):
        """
        Get configuration information for a specific celestial body

        Args:
            body_name: Name of the celestial body

        Returns:
            dict: Body configuration or None if not found
        """
        if body_name not in self.available_bodies:
            return None

        return {
            'name': body_name,
            'gravitational_constant': self.config.get_value(f"{body_name}_gConst"),
            'mass': self.config.get_value(f"{body_name}_mass"),
            'radius_squared': self.config.get_value(f"{body_name}_dist")
        }