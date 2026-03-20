import argparse
import sys
from config import ConfigManager
from logger import Logger
#from Visual import Visual
#from visualZOOM import VisualZoom
from visual3d import Visual3D
from visVivaE import VisVivaEarth
from  visVivaM import VisVivaMoon

"""
change the viz = Visual() part around line 119 to use the other visual classes:
--> viz = Visual3d(vis_viva.radii, vis_viva.velocities, vis_viva.semiMajorAxis, inclination)
            viz.run()
--> viz = VisualZoom(vis_viva.radii, vis_viva.velocities, vis_viva.semiMajorAxis)
            viz.run()
--> viz = Visual(vis_viva.radii, vis_viva.velocities, vis_viva.semiMajorAxis)
            viz.run()
"""

def setup_configuration():
    """Set up initial configuration"""
    config = ConfigManager("settings.conf")

    # Logging configuration
    config.create_key_value("log_file_path", "logs/application.log", "Log file location")
    config.create_key_value("write_to_file", "true", "Enable/disable file logging")
    config.create_key_value("write_to_console", "true", "Enable/disable console logging")
    config.create_key_value("log_level", "DEBUG", "Logging level")

    # Earth-Sun orbital parameters
    config.create_key_value("earth_sun_semi_major_axis", "149.6e9", "Earth-Sun semi-major axis in meters")
    config.create_key_value("earth_sun_eccentricity", "0.0167", "Earth-Sun orbital eccentricity")
    config.create_key_value("earth_sun_inclination", "7.155", "Earth-Sun orbital inclination in degrees")
    config.create_key_value("earth_sun_num_points", "100", "Number of points to calculate in orbit")
    config.create_key_value("sun_mass", "1.989e30", "Sun mass in kg")
    config.create_key_value("earth_mass", "5.97e24", "Earth mass in kg")

    # Earth-Moon orbital parameters
    config.create_key_value("earth_moon_semi_major_axis", "384.4e6", "Earth-Moon semi-major axis in meters")
    config.create_key_value("earth_moon_eccentricity", "0.0549", "Earth-Moon orbital eccentricity")
    config.create_key_value("earth_moon_inclination", "5.145", "Earth-Moon orbital inclination in degrees")
    config.create_key_value("earth_moon_num_points", "100", "Number of points to calculate in orbit")
    config.create_key_value("moon_mass", "7.346e22", "Moon mass in kg")

    # Gravitational constant
    config.create_key_value("gravitational_constant", "6.67430e-11", "Universal gravitational constant")

    return config


def get_available_systems():
    """Get list of available orbital systems"""
    return ["Earth/Sun System", "Earth/Moon System", "Full System"]


def display_menu(available_systems):
    """Display selection menu"""
    print("\n" + "=" * 50)
    print("ORBITAL VISUALIZATION SYSTEM")
    print("=" * 50)
    print("Available orbital systems:")
    for i, system in enumerate(available_systems, 1):
        print(f"{i}. {system}")
    print(f"{len(available_systems) + 1}. Exit")
    print("=" * 50)


def get_user_choice(available_systems):
    """Get user's choice for orbital system visualization"""
    while True:
        try:
            display_menu(available_systems)
            choice = input("\nEnter your choice (number or name): ").strip()

            # Check if it's a number
            if choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(available_systems):
                    return available_systems[choice_num - 1]
                elif choice_num == len(available_systems) + 1:
                    return "EXIT"
                else:
                    print("Invalid choice. Please try again.")
            else:
                # Check if it's a valid system name
                if choice in available_systems:
                    return choice
                elif choice.upper() == "EXIT" or choice.upper() == "QUIT":
                    return "EXIT"
                else:
                    print(f"'{choice}' not found. Available options: {', '.join(available_systems)}")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            return "EXIT"
        except Exception as e:
            print(f"Error: {e}. Please try again.")


def run_visualization(system_type, config, logger):
    """Run the orbital visualization for the selected system"""
    try:
        print(f"\n{'-' * 60}")
        print(f"Initializing visualization for: {system_type}")
        print(f"{'-' * 60}")

        logger.info(f"Starting visualization for {system_type}")

        if system_type == "Earth/Sun System":
            # Get parameters from config
            G = float(config.get_value("gravitational_constant"))
            M = float(config.get_value("sun_mass"))
            a = float(config.get_value("earth_sun_semi_major_axis"))
            e = float(config.get_value("earth_sun_eccentricity"))
            inclination = float(config.get_value("earth_sun_inclination"))
            num_points = int(config.get_value("earth_sun_num_points"))

            # Create VisVivaEarth instance and calculate orbital data
            vis_vivaE = VisVivaEarth(G, M, a, e, num_points, logger)
            vis_vivaE.getVelocity()

            # Optional: print orbital parameters
            # vis_viva.printVal()

            vizE = Visual3D(vis_vivaE.radii, vis_vivaE.velocities, vis_vivaE.semiMajorAxis, inclination)
            vizE.run()

            logger.info(f"Visualization for {system_type} completed")

        elif system_type == "Earth/Moon System":
            # Get parameters from config
            G = float(config.get_value("gravitational_constant"))
            M = float(config.get_value("earth_mass"))
            a = float(config.get_value("earth_moon_semi_major_axis"))
            e = float(config.get_value("earth_moon_eccentricity"))
            inclination = float(config.get_value("earth_moon_inclination"))
            num_points = int(config.get_value("earth_moon_num_points"))

            vis_vivaM = VisVivaMoon(G, M, a, e, num_points, logger)
            vis_vivaM.getVelocity()

            vizM = Visual3D(vis_vivaM.radii, vis_vivaM.velocities, vis_vivaM.semiMajorAxis, inclination)
            vizM.run()

            logger.info(f"Visualization for {system_type} completed")

        elif system_type == "Full System":
            print("\nFull System visualization will be implemented in the future.")
            logger.info("Full System visualization requested but not yet implemented")

    except Exception as e:
        print(f"Error running visualization for {system_type}: {e}")
        logger.error(f"Error running visualization for {system_type}: {e}")


def main():
    """Main application entry point"""
    # Create configuration manager
    config = setup_configuration()

    # Create logger (depends on config)
    logger = Logger(config)

    # Log application startup
    logger.info("Logging new session...")

    # Create argument parser
    parser = argparse.ArgumentParser(
        prog='main',
        description='Orbital Visualization System for Celestial Bodies',
        epilog='Example usage: python main.py --verbose'
    )

    # Add arguments
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--version',
        action='store_true',
        help='Program version'
    )

    # Parse arguments
    args = parser.parse_args()

    # Get available systems
    available_systems = get_available_systems()

    # Process the arguments
    if args.verbose:
        print(f"Verbose mode enabled")

    if args.version:
        print(f"Orbital Visualization System Version 2.0, Logan Macgowan, Copyright 2025")
        return 0

    # Interactive mode
    try:
        while True:
            choice = get_user_choice(available_systems)

            if choice == "EXIT":
                print("Goodbye!")
                break
            else:
                run_visualization(choice, config, logger)

            # Ask if user wants to continue
            continue_choice = input("\nWould you like to visualize another system? (y/n): ").strip().lower()
            if continue_choice not in ['y', 'yes']:
                print("Goodbye!")
                break

    except KeyboardInterrupt:
        print("\n\nGoodbye!")

    logger.info("Application finished successfully")
    return 0


if __name__ == '__main__':
    sys.exit(main())