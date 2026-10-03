import argparse
import sys
import numpy as np
import time
from config import ConfigManager
from logger import Logger
#from Visual import Visual
#from visualZOOM import VisualZoom
from visual3d import Visual3D
from visVivaE import VisVivaEarth
from visVivaM import VisVivaMoon
from celestData import CelestData
from rk4_integrator import RK4Integrator
from dop853_integrator import DOP853Integrator
from simulation import Simulation
from visualizer import Visualizer
from asteroid import Asteroid
from asteroid_database import AsteroidDatabase
from rocket import Rocket
from interception import InterceptionCalculator
from mission_runner import MissionRunner


"""
    Note about not having enough fuel: I dont intend for the rocket to be exactly like the falcon 9. I probably want enough fuel to get to the asteroid belt and then have 5-10% when returning. With the electric drones providing thrust we dont need to think of extra mass on the return trip. But in the future I will be interested on how long the capture to a lagrange point will take. For now 5-10% of fuel remaining after the trip is my goal. This will need to be dynamic depending on the target asteroid's distance. I probably will want to show and tell this before launch. Showing how much fuel is estimated to get to the target asteroid and then how much fuel has been allotted for the 5-10% threshold.
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
    return ["Earth/Sun System (Vis-Viva)", "Earth/Moon System (Vis-Viva)", "Full System (Integrator Method)"]


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

        if system_type == "Earth/Sun System (Vis-Viva)":
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

        elif system_type == "Earth/Moon System (Vis-Viva)":
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

        elif system_type == "Full System (Integrator Method)":
            print("\nFull System Starting.")
            print(f"*******************RK integrator need to be put into user methods*******************")
            # Time
            t_total = 5.0  # 5 years
            dt = 1 / 8766  # 1 hour in years (8766 hours per year)

            # Masses in solar masses
            M_sun = 1.0
            M_rock = 2.761e-25  # Rocket/Sun mass ratio

            M_moon = 3.694e-8
            moon_inc = np.radians(5.145)
            v_moon = 0.2148

            # Earth — defines the ecliptic, zero inclination
            earth_inc = 0.0
            M_earth = 3.003e-6  # Earth/Sun mass ratio

            # Apophis — 3.3° inclination to ecliptic
            apo_inc = np.radians(3.3)
            v_apo = 1.0552 * 2 * np.pi
            M_apo = 2.664e-20  # Apophis/Sun mass ratio

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
            rocket = CelestData(
                name="Rocket",
                mass=M_rock,
                radius=1.24e-14,
                position=earth.position + np.array([4.258e-5, 0.0, 0.0]),  # Earth surface in AU
                velocity=earth.velocity.copy()
                # Position in the x-axis plane(distance from the sun). Based off the Falcon 9 rocket.
                # .copy() gives rocket its own independent array in memory
                # Without it, rocket and earth share the same array —
                # if one moves, the other would move with it
                # velocity=earth.velocity + np.array([0.0, 0.0, 0.0]) etc...
            )

            # initial positions before simulation runs
            # print(earth.position)
            # print(moon.position)

            dataB = AsteroidDatabase()
            asteroidName = input("Enter an asteroid name: ")
            asteroid = dataB.fetch(asteroidName)
            if asteroid is None:
                print(f"Could not find asteroid: {asteroidName}")
                exit()
            print(asteroid)

            # Planning simulation — Rocket NOT included here.
            # InterceptionCalculator only needs Rocket as a spec sheet (fuel, thrust),
            # not as a body that needs to move in this simulation.
            bodies = [sun, earth, moon, asteroid]

            integrator = DOP853Integrator()
            start = time.time()
            sim = Simulation(bodies, integrator)
            sim.run(t_total=5.0, dt=1 / (8766 * 4))  # tighter step needed for Moon
            end = time.time()
            print(f"Simulation took: {end - start:.1f} seconds")
            data = sim.get_results()

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

            # Run planning simulation
            sim = Simulation(bodies, integrator)
            sim.run(t_total=5.0, dt=1 / (8766 * 4))
            data = sim.get_results()  # ← right after sim.run()

            # Plan the mission
            calc = InterceptionCalculator(rocket, asteroid, bodies, data)
            mission_plan = calc.plan_mission()

            if mission_plan is None:
                print("Mission planning failed.")
                exit()

            print(f"Mission plan computed successfully for {asteroid.name}")

            runner = MissionRunner(sun, earth, moon, asteroid, rocket, mission_plan, integrator)
            merged_data = runner.run_full_mission()
            if merged_data is not None:
                 viz = Visualizer(merged_data, mission_plan)
                 viz.run()

            logger.info("Running full system")

    except Exception as e:
        print(f"Error running visualization for {system_type}: {e}")
        logger.error(f"Error running visualization for {system_type}: {e}")

# Debug:
# Earth's position after the simulation verifying its movement:
#trajectory = data.get_trajectory("Earth")
#print(f"Earth start: {trajectory[0]}")
#print(f"Earth end:   {trajectory[-1]}")
#print(f"Total steps: {len(trajectory)}")

# Checking energy results:
#results = sim.get_results()
#print(f"Initial energy: {results.energies[0]:.6e}")
#print(f"Final energy:   {results.energies[-1]:.6e}")
#print(f"Total energies stored: {len(results.energies)}")

# Manual drift calculation
#e0 = results.energies[0]
#ef = results.energies[-1]
#manual_drift = abs((ef - e0) / e0) * 100
#print(f"Manual drift calculation: {manual_drift:.15f}%")
#print(f"Difference: {abs(ef - e0):.6e} J")

# simulation just computed:
#
# 8,766 time steps (one per hour for a year)
# 5 bodies per step
# 20 gravitational pair calculations per step
# 4 derivative evaluations per step (RK4)
# Total: roughly 700,000 gravitational calculations
#




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