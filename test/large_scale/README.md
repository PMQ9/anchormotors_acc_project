# Large Scale Simulations (NGSIM)

The file ```simulation.ipynb``` shows several simulations of 25 cars where the first car follows a trajectory from the NGSIM dataset.

The results are tested where 0%, 5%, 10%, 25%, 50%, 75%, and 100% of the cars are running a Python implementation of our controller. Other vehicles are running the [Intelligent Driver Model](https://traffic-simulation.de/info/info_IDM.html). 

Running the notebook will reevaluate the simulations.

## File Descriptions
```controller.py```: Defines our controller, Intelligent Driver Model, and trajectory following controller in Python

```car.py```: Defines the car dynamics and stores information for a single vehicle in a simulation

```simulation.py```: Defines the full simulation of multiple vehicles and generates helpful plots and metrics

All NGSIM data must be added the ```ngsim_data``` folder prior to running the simulation.