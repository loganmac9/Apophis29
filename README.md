*--Apophis Asteroid Simulation--*

Description:
"Apophis" is a simulation program to simulate the relationship between the Earth, Moon, Sun and asteroid(s).

In the future the program will navigate how to capture an asteroid, more specifically 99942 Apophis(https://en.wikipedia.org/wiki/99942_Apophis).
The user will be able to choose from a catalog of asteroids of which they wish to travel to and "capture."
The asteroid will then be moved to a suitable location(potentially a lagrange point(https://en.wikipedia.org/wiki/Lagrange_point)) for theoretical exploitation.

Part 1(Completed):
Currently the two-body systems, Earth-Sun and Earth-Moon are developed and have graphical representations built with the "Vis-viva"(https://en.wikipedia.org/wiki/Vis-viva_equation).
The N-body systems are in development using 8th order Runge-Kutta/DoPRI(https://en.wikipedia.org/wiki/Runge%E2%80%93Kutta_methods).

Part 2: 8th order adaptive Runge-kutta/DOPRI(https://en.wikipedia.org/wiki/Dormand%E2%80%93Prince_method) consists currently of celestData.py, gravity.py, stateVector.py, testMain2.py, rk4_inntegrator.py, and simulationData.py

------------------------------------------------------------------------------------------------------------

Execution:
Run testMain2.py
Initialized for the visual3d class(importing Visual3D)
Includes debug statements for Part 2 developmnt.
