# Evacuation Simulation

![UI screenshot](assets\Screenshot_1.png)

## Contents

- [Summary](#Summary)
- [Features](#Features)
- [Requirements](#Requirements)
- [Starting the application](#Starting-the-application)
- [Attribution](#Attribution)


## Summary

This application was developed for my MSc project, as part of my degree programme at University of Liverpool in Summer 2020.

The purpose of the project was to design and development of a web application capable of simulating an evacuation process of a residential building. The application allows the specification of the number and type of residents and facilitate visualisations of individual evacuation events, as well as scheduling batches of simulations.

The back end (simulation environment and agent logic) was implemented using Python 3.7, with the help of [Mesa](https://github.com/projectmesa/mesa), an agent-based modelling library for Python. The front end consists of a GUI and visuals developed in JavaScript, created by modifying and extending the existing canvas-based visualisation capabilities of Mesa.  


## Features

The application allows the user to select an environment in the form of a building plan with specified rooms, corridors, exits and signs pointing to the exits, as well as obstacles, place a number of agents of different types within the environment (by specifying population parameters as well as individually) and simulate the evacuation process. The application also supports explicit simulation of fire and smoke that have effect on the evacuating agents.

![Simulation environment](assets\Screenshot_2.png)

The simulation is agent-based, with the behaviour of each agent defined independently, based on their type, parameters, state, preferred strategy and what they can perceive in the environment. The agents can belong to different age groups (children, adults, elderly) and different levels of mobility (people with lower fitness and with reduced mobility). Different groups are characterised by different walking speeds and, in the case of children, entirely different behaviour logic.


## Requirements

To run the application, you need to have a distribution of Python (tested with Python 3.7 and 3.8), with the Mesa package installed (developed and tested with Mesa 0.8.7, which was the default version at the time), e.g. with 

``` shell
$ pip install mesa
```

All other dependencies should be installed with Mesa, if not already present.


## Starting the application

After unzipping the submission file, open the command-line interface and navigate to the folder containing the extracted files. The folder will have the file structure indicated below. To run the application, simply run the `server.py` file with the appropriate version of Python 3, e.g. with 

``` shell
$ python server.py
```
or
``` shell
$ python3 server.py
```

The browser should be automatically opened, if that does not happen, open the browser and enter the URL displayed in the console - typically it will be 'http://127.0.0.1:8521', but consecutive port numbers will be tried and used if the default is not available.

Tested on Win10 and Ubuntu 20.04.


## Attribution

This application uses the library [Mesa](https://github.com/projectmesa/mesa), available under the [Apache 2.0 license](http://www.apache.org/licenses/LICENSE-2.0).

Mesa's repository contains the following attribution notices:

```
Copyright 2020 Core Mesa Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

Some of the files included in this project are modified versions of Mesa's source files. This is indicated on a per file basis at the top of each such file.