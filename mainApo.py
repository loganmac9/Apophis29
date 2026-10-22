import argparse
import sys
import numpy as np
import time
import traceback
from config import ConfigManager
from logger import Logger
from celestData import CelestData
#from rk4_integrator import RK4Integrator
from dop853_integrator import DOP853Integrator
from simulation import Simulation
from visualizer import Visualizer
from asteroid_database import AsteroidDatabase
from rocket import Rocket
from interception import InterceptionCalculator
from mission_runner import MissionRunner


def setup_configuration():
    """Set up initial configuration"""
    config = ConfigManager("settings.conf")

    # Logging configuration
    config.create_key_value("log_file_path", "logs/application.log", "Log file location")
    config.create_key_value("write_to_file", "true", "Enable/disable file logging")
    config.create_key_value("write_to_console", "true", "Enable/disable console logging")
    config.create_key_value("log_level", "DEBUG", "Logging level")

    return config


def get_available_systems():
    """Get list of available orbital systems"""
    return ["Full System (Integrator Method)"]


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

        if system_type == "Full System (Integrator Method)":
            print("\nFull System Starting.")

            # defines the ecliptic, inclination
            # Masses in solar masses
            M_sun = 1.0
            M_moon = 3.694e-8
            M_earth = 3.003e-6  # Earth/Sun mass ratio
            moon_inc = np.radians(5.145)
            v_moon = 0.2148

            # Mass in kg, radius in m, position in km, and velocity in m/s.
            sun = CelestData(
                name="Sun",
                mass=M_sun,
                radius=0.00465,  # Now in AU
                position=np.array([0.0, 0.0, 0.0]),
                velocity=np.array([0.0, 0.0, 0.0])
                # Zeros in position and velocity arrays because I'm taking the sun as stationary.
            )
            earth = CelestData(
                name="Earth",
                mass=M_earth,
                radius=4.259e-5,  # AU
                position=np.array([1.0, 0.0, 0.0]),  # AU
                velocity=np.array([0.0, 2 * np.pi, 0.0])  # 2π AU/year = circular orbit
                # Position in the x-axis plane(distance from the sun [x,y,z]).
                # Orbital velocity(avg - 2pi(r)/T) in the y-axis plane(perpendicular to the x-axis plane. Think x,y,z graph).
            )
            moon = CelestData(
                name="Moon",
                mass=M_moon,
                radius=1.161e-5,
                position=earth.position + np.array([0.00257, 0.0, 0.0]),
                velocity=earth.velocity + np.array([
                    0.0,
                    v_moon * np.cos(moon_inc),  # y component
                    v_moon * np.sin(moon_inc)  # z component — inclination
                ])
            )
            # Build the Rocket spec — Falcon 9 second stage real numbers, converted to AU/M☉/year
            rocket = Rocket(
                name="Rocket",
                radius=1.24e-14,
                dry_mass=2.011e-27,  # solar masses
                fuel_mass=4.659e-26,  # solar masses
                max_thrust=3.126e-24,  # AU·M☉/year²
                exhaust_vel=0.7404,  # AU/year
                position=earth.position + np.array([4.258e-5, 0.0, 0.0]),
                velocity=earth.velocity.copy(),
                reactor_power=1e-10,  # placeholder — refine later
                reactor_fuel_mass=1.25696e-28,
                drone_mode='fixed',  # or 'dynamic'
                drone_capacity=10,
            )

            """
                Note about not having enough fuel: I dont intend for the rocket to be exactly like the falcon 9. 
                I probably want enough fuel to get to the asteroid belt and then have 5-10% when returning. 
                With the electric drones providing thrust we dont need to think of extra mass on the return trip. 
                But in the future I will be interested on how long the capture to a lagrange point will take. 
                For now 5-10% of fuel remaining after the trip is my goal. 
                This will need to be dynamic depending on the target asteroid's distance. 
                I probably will want to show and tell this before launch. 
                Showing how much fuel is estimated to get to the target asteroid and 
                then how much fuel has been allotted for the 5-10% threshold.
            """

            # ---------------------------------------------------------------------------
            # Asteroid database set up:
            dataB = AsteroidDatabase()
            asteroidName = input("Enter an asteroid name: ")
            asteroid = dataB.fetch(asteroidName)
            if asteroid is None:
                print(f"Could not find asteroid: {asteroidName}")
                return
            print(asteroid)
            # ---------------------------------------------------------------------------

            # Planning simulation — Rocket NOT included here.
            # InterceptionCalculator only needs Rocket as a spec sheet (fuel, thrust),
            # not as a body that needs to move in this simulation.
            bodies = [sun, earth, moon, asteroid]
            integrator = DOP853Integrator()
            start = time.time()
            # before the planning simulation
            initial_states = {b.name: (b.position.copy(), b.velocity.copy()) for b in bodies}

            # ---------------------------------------------------------------------------
            # Run Sim:
            sim = Simulation(bodies, integrator)
            sim.run(t_total=5.0, dt=1 / (8766 * 4))  # tighter step needed for Moon
            end = time.time()
            print(f"Simulation took: {end - start:.1f} seconds")
            data = sim.get_results()
            # ---------------------------------------------------------------------------

            # ---------------------------------------------------------------------------
            # Interception Starts:
            # restore sets t=0, before InterceptionCalculator runs
            for b in bodies:
                pos, vel = initial_states[b.name]
                b.position = pos.copy()
                b.velocity = vel.copy()

            # Plan the mission
            calc = InterceptionCalculator(rocket, asteroid, bodies, data)
            mission_plan = calc.plan_mission()

            if mission_plan is None:
                print("Mission planning failed.")
                return

            print(f"Mission plan computed successfully for {asteroid.name}")

            runner = MissionRunner(sun, earth, moon, asteroid, rocket, mission_plan, integrator)
            merged_data = runner.run_full_mission()
            if merged_data is not None:
                 viz = Visualizer(merged_data, mission_plan)
                 viz.run()

    except Exception as e:
        print(f"\nError running visualization for {system_type}: {e}")
        # prints the file name, line number and call chain to the console.
        traceback.print_exc()
        logger.error(
            f"Error running visualization for {system_type}: {e}\n"
            # returns the same text as a string, so the log file gets it too.
            f"{traceback.format_exc()}"
        )

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