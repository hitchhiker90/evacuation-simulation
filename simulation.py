# COMP702 - Evacuation Simulation
# Lukasz Przybyla

import time, math, random, os
from datetime import datetime
import json
from heapq import heappush, heappop
import numpy as np

from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.batchrunner import BatchRunner

import config

## Constant simulation parameters

# Size of the grid cell (in cm)
CELL_SIZE = 60

# Number of time steps before smoke/fire spread:
FIRE_SPREAD_STEPS = 80
SMOKE_SPREAD_STEPS = 16

# Opposing directions
OPPOSITE_DIR = {"north": "south",
                "south": "north",
                "east": "west",
                "west": "east",
                None: None}


## Simulation environments

envList = {}

# Load the json files containing the environment
for filename in os.listdir(os.getcwd() + "/assets/"):
    if filename.endswith(".json"):
        # Set up empty list for environment components
        exitList = []
        obstacleList = []
        signList = []
        path = "assets/" + filename
        envName = filename[:-5]
        # Extract all environment elements
        with open(path) as json_file:
            environment = json.load(json_file)
            # Extract the building plan
            floor_plan = environment["plan"]

            # Set up grid dimentions
            gridWidth = len(floor_plan[0])
            gridHeight = len(floor_plan)

            # Calculate area inside the building
            area = 0
            for row in floor_plan:
                for cell in row:
                    if cell['inside']:
                        area += (CELL_SIZE / 100) ** 2

            # Extract exits
            exits = environment["exits"]
            for exit in exits:
                exitList.append(((exit["x_coord"], exit["y_coord"]),
                                 exit["ID"]))

            # Extract obstacles
            obstacles = environment["obstacles"]
            for obstacle in obstacles:
                obstacleList.append((obstacle["x_coord"], obstacle["y_coord"]))

            # Extract signs
            signs = environment["signs"]
            for sign in signs:
                signList.append(((sign["x_coord"],
                                  sign["y_coord"]),
                                 sign["direction"],
                                 sign["exit_ID"]))

        # Create a dict of environment elements and add it to the environment dict.
        envDict = {}
        envDict["floor_plan"] = floor_plan
        envDict["gridWidth"] = gridWidth
        envDict["gridHeight"] = gridHeight
        envDict["area"] = round(area, 2)
        envDict["exits"] = exitList
        envDict["obstacles"] = obstacleList
        envDict["signs"] = signList

        envList[envName] = envDict


# A variable to store the time limit:
timeLimit = None

# A global variable to suppress logging if required
suppressLog = False

## FUNCTIONS
# A function that prints to a log file and to the console
logContent = ""
def log(input):
    pass
    global suppressLog, logContent
    if not suppressLog:
        logContent += str(input) + "\n"
        # print(input)

# Compute Manhattan distance between two cells:
def manDist(start, end):
    return abs(start[0] - end[0]) + abs(start[1] - end[1])

# Compute Euclidean distance between two cells:
def eucDist(start, end):
    return math.sqrt((start[0] - end[0])**2 + (start[1] - end[1])**2)

# Compute path between two cells with A* search
# using Manhattan distance as heuristic for cost from current cell to goal
def computePath(grid, start, goal, knownFires, knownHeat, knownObstacles, **kwargs):
    # Set the path end to the coordinates of the goal
    end = goal[0]
    # An argument to ignore agents if required
    ignoreAgents = kwargs.get("ignoreAgents", False)
    childTarget = kwargs.get("childTarget", False)
    #If start and target location are the same, return appropriate information
    if start == end:
        path = ["reached"]
        return path
    if not ignoreAgents:
        log("Computing path to " + str(goal[1]))
        obstacleClasses = ["Heat", "Child", "Adult", "Smoke"]
    else:
        log("Computing ideal evacuation path to " + str(goal[1]))
        obstacleClasses = []

    # Recursively check if a path not blocked by fire exists
    if len(knownFires) > 0 and ignoreAgents == False:
        testPath = computePath(grid, start, goal, knownFires, [], [],
                                   ignoreAgents=True)
        if testPath == ["blocked"]:
            return testPath

    while True:
        openList = []
        heappush(openList, (manDist(start, end), 0, start, None))
        closedList = {}
        path = []
        while len(openList) > 0:
            [f, c, curr, parent] = heappop(openList)
            neighbors = grid.getObject(curr, "Cell").neighbors
            for neighbor in neighbors:
                cell = neighbors[neighbor]
                blocked = False
                used = False
                hot = False
                blockingObjects = []
                for obj in grid.get_cell_list_contents(cell):
                    if obj.__class__.__name__ in obstacleClasses[1:]\
                            or cell in knownFires or cell in knownObstacles:
                        blocked = True
                        if obj.__class__.__name__ in obstacleClasses[1:]:
                            blockingObjects.append(obj.__class__.__name__)
                    if len(obstacleClasses) > 0:
                        if cell in knownHeat:
                            hot = True
                if cell == end:
                    if blockingObjects == ["Child"] and childTarget:
                        blocked = False
                    if not blocked and not hot:
                        closedList[curr] = parent
                        closedList[cell] = curr
                        while True:
                            path.append(cell)
                            cell = closedList[cell]
                            if closedList[cell] == None:
                                break
                        path.reverse()
                        log("PATH: " + str(path))
                        return path
                nextH = manDist(cell, end)
                nextC = c + 1
                nextF = nextC + nextH
                for entry in openList:
                    if cell in entry:
                        if nextF < entry[0]:
                            entry[:] = [nextF, nextC, cell, curr]
                        used = True
                        break
                if not blocked and not used and not hot:
                    if cell not in closedList:
                        heappush(openList, [nextF, nextC, cell, curr])
            closedList[curr] = parent
        if len(obstacleClasses) > 0:
            del(obstacleClasses[-1])
        else:
            path = ["blocked"]
            log("PATH: " + str(path))
            return path


# Function that takes pixel coordinates and returns cell coordinates
def getCellCoords(x, y, slope, swapped):
    if slope < 0:
        if swapped == True:
            return (math.floor((y - 1) / CELL_SIZE), math.floor((x) / CELL_SIZE))
        else:
            return (math.floor(x / CELL_SIZE), math.floor((y - 1) / CELL_SIZE))
    else:
        if swapped == True:
            return (math.floor(y / CELL_SIZE), math.floor(x / CELL_SIZE))
        else:
            return (math.floor(x / CELL_SIZE), math.floor(y / CELL_SIZE))


# Function that adds cells to the line of sight
def addToLine(x, y, slope, swapped, result, orientation, acrossCell):
    corner = False

    # Check whether the LOS crosses the cell on or very close to a corner
    if (x % CELL_SIZE < 2 or x % CELL_SIZE > CELL_SIZE - 2)\
            and (y % CELL_SIZE < 2 or y % CELL_SIZE > CELL_SIZE - 2):
                corner = True

    if swapped:
        if orientation == "x":
            result.append((getCellCoords(x, y, slope, swapped), "y", slope, corner, swapped, acrossCell))
        else:
            result.append((getCellCoords(x, y, slope, swapped), "x", slope, corner, swapped, acrossCell))
    else:
        result.append((getCellCoords(x, y, slope, swapped), orientation, slope, corner, swapped, acrossCell))

    if (x % CELL_SIZE < 2 or x % CELL_SIZE > CELL_SIZE - 2)\
            and (y % CELL_SIZE < 2 or y % CELL_SIZE > CELL_SIZE - 2):
        if slope < 0:
            if swapped:
                result.append((getCellCoords(x - 5, y - 5, slope, swapped), "yx", slope, corner, swapped, acrossCell))
                result.append((getCellCoords(x + 5, y + 5, slope, swapped), "xy", slope, corner, swapped, acrossCell))
            else:
                result.append((getCellCoords(x - 5, y - 5, slope, swapped), "xy", slope, corner, swapped, acrossCell))
                result.append((getCellCoords(x + 5, y + 5, slope, swapped), "yx", slope, corner, swapped, acrossCell))
        else:
            if swapped:
                result.append((getCellCoords(x - 5, y + 5, slope, swapped), "yx", slope, corner, swapped, acrossCell))
                result.append((getCellCoords(x + 5, y - 5, slope, swapped), "xy", slope, corner, swapped, acrossCell))
            else:
                result.append((getCellCoords(x - 5, y + 5, slope, swapped), "xy", slope, corner, swapped, acrossCell))
                result.append((getCellCoords(x + 5, y - 5, slope, swapped), "yx", slope, corner, swapped, acrossCell))


# Function that returns the cells crossed by the line of sight between two cells
def bresenhamLine(startX, startY, endX, endY):

    # Convert grid coordinates to pixel coordinates of cell centres:
    startX = startX * CELL_SIZE + CELL_SIZE / 2
    startY = startY * CELL_SIZE + CELL_SIZE / 2
    endX = endX * CELL_SIZE + CELL_SIZE / 2
    endY = endY * CELL_SIZE + CELL_SIZE / 2

    # If agent is in the same cell, return result immediately:
    if startX == endX and startY == endY:
        return [((startX, startY), "xy", 0, False, False)]

    # Set up a list to store the results (list of cell coordinates)
    result = []

    # Find the slope of the line
    try:
        slope = (endY - startY) / (endX - startX)
    except:
        pass

    # If the slope is greater than one, swap x and y and recompute slope
    swapped = False
    if startX == endX or abs(slope) > 1:
        startX, startY = startY, startX
        endX, endY = endY, endX
        slope = (endY - startY) / (endX - startX)
        swapped = True

    # Ensure the line always goes right from the start point by swapping
    # the points if necessary
    if startX > endX:
        startX, endX = endX, startX
        startY, endY = endY, startY

    # If slope is zero, adjust to avoid division by zero
    if slope == 0:
        slope += 0.0001

    # Add current cell to result:
    addToLine(startX, startY, slope, swapped, result, None, True)

    currX = startX
    currY = startY

    # Find out coordinates of crossing the next vertical or horizontal gridline
    currX = currX + (CELL_SIZE / 2)
    currY = round(currY + (CELL_SIZE / 2 * slope))
    if slope > 0:
        error = ("y", currY - math.floor(1 + (currY / CELL_SIZE)) * CELL_SIZE)
    else:
        error = ("y", currY % CELL_SIZE)

    addToLine(currX, currY, slope, swapped, result, error[0], True)


    while True:
        # Find out coordinates of crossing the next vertical or horizontal gridline
        if (error[0] == "y"):
            if error[1] == 0:
                error = ("y", CELL_SIZE)
            newX1 = currX + CELL_SIZE
            newY1 = currY + CELL_SIZE * slope
            length1 = math.sqrt((newY1 - currY)**2 + (newX1 - currX)**2)
            newY2 = currY - error[1]
            newX2 = currX - error[1] / slope
            length2 = math.sqrt((newY2 - currY)**2 + (newX2 - currX)**2)
            if length1 < length2 and length1 != 0:
                length = length1
                currX = newX1
                currY = newY1
                if slope > 0:
                    error = ("y", currY - math.floor(1 + (currY / CELL_SIZE)) * CELL_SIZE)
                else:
                    error = ("y", currY % CELL_SIZE)
            else:
                length = length2
                currX = newX2
                currY = newY2
                error = ("x", currX - math.floor(1 + (currX / CELL_SIZE)) * CELL_SIZE)
        elif (error[0] == "x"):
            newX1 = currX - error[1]
            newY1 = currY - error[1] * slope
            length1 = math.sqrt((newY1 - currY)**2 + (newX1 - currX)**2)
            newY2 = currY + CELL_SIZE
            newX2 = currX + CELL_SIZE / slope
            length2 = math.sqrt((newY2 - currY)**2 + (newX2 - currX)**2)
            if (length1 <= length2):
                length = length1
                currX = newX1
                currY = newY1
                if slope > 0:
                    error = ("y", currY - math.floor(1 + (currY / CELL_SIZE)) * CELL_SIZE)
                else:
                    error = ("y", currY % CELL_SIZE)
            else:
                length = length2
                currX = newX2
                currY = newY2
                error = ("x", currX - math.floor(1 + (currX / CELL_SIZE)) * CELL_SIZE)

        if (currX > endX):
            break

        acrossCell = True
        if length < CELL_SIZE / 2:
            acrossCell = False

        addToLine(currX, currY, slope, swapped, result, error[0], acrossCell)

    return result

# A function that looks up the visibility value between two cells
def isVisible(grid, start, end):
    return grid.visibilityArray[start[0]][start[1]][end[0]][end[1]]

# A function that checks whether the LOS between two cells is blocked by any walls
def checkVisibility(grid, start, end):
    if start == end:
        return True

    lineClear = True
    # Get the list of cells from start's center to end's center
    cellsCrossed = bresenhamLine(start[0], start[1], end[0], end[1])
    basicPath = []
    extendedPath = []
    cellsToCompare = []

    for cell in cellsCrossed:
        if len(cellsCrossed) == 1:
            basicPath.append(cellsCrossed[0])
            break

        if cell[1] in (None, "x", "y"):
            basicPath.append(cell)
        else:
            extendedPath.append(cell)

    if basicPath[0][1] == None:
        for i in range(len(basicPath)):
            currOrientation = basicPath[i][1]
            try:
                nextOrientation = basicPath[i + 1][1]
            except:
                nextOrientation = None
            cellsToCompare.append((basicPath[i], currOrientation, nextOrientation))
    else:
        cellsToCompare.append((basicPath[0], None, basicPath[0][1]))
        for i in range(1, len(basicPath)):
            currOrientation = basicPath[i][1]
            try:
                nextOrientation = basicPath[i + 1][1]
            except:
                nextOrientation = None
            cellsToCompare.append((basicPath[i], currOrientation, nextOrientation))

    for i in range(len(extendedPath)):
        cellsToCompare.append((extendedPath[i], extendedPath[i][1][0], None))
        cellsToCompare.append((extendedPath[i], None, extendedPath[i][1][1]))

    cellsProcessed = []

    # Determine which way (through which borders) the LOS crosses the cells in basic path
    for i in range(len(basicPath)):
        wallsCrossed = 0

        # If entering cell through a vertical line
        if cellsToCompare[i][1] == "y":
            # Going right
            if cellsToCompare[i - 1][0][0][0] < cellsToCompare[i][0][0][0]:
                wallsCrossed += 8
            # Going left
            else:
                wallsCrossed += 2

            # If entering at a corner
            if cellsToCompare[i][0][3] and cellsToCompare[i+1][0][5] \
                    and abs(cellsToCompare[len(basicPath)][0][0][1] - cellsToCompare[0][0][0][1]) != 1:
                # Lower corner
                if cellsToCompare[i + 1][0][0][1] > cellsToCompare[0][0][0][1]:
                    wallsCrossed += 4
                # Upper corner
                else:
                    wallsCrossed += 1

        # If entering cell through a horizontal line
        elif cellsToCompare[i][1] == "x":
            # Going up
            if cellsToCompare[i - 1][0][0][1] < cellsToCompare[i][0][0][1]:
                wallsCrossed += 4
            # Going down
            else:
                wallsCrossed += 1

            # If entering at a corner
            if cellsToCompare[i][0][3] and cellsToCompare[i+1][0][5] \
                    and abs(cellsToCompare[len(basicPath)][0][0][0] - cellsToCompare[0][0][0][0]) != 1:
                # Left corner
                if cellsToCompare[i][0][0][0] > cellsToCompare[0][0][0][0]:
                    wallsCrossed += 8
                # Right corner
                else:
                    wallsCrossed += 2

        # If exiting cell through a vertical line
        if cellsToCompare[i][2] == "y":
            # Going left
            if cellsToCompare[i + 1][0][0][0] < cellsToCompare[i][0][0][0]:
                wallsCrossed += 8
            # Going right
            else:
                wallsCrossed += 2

            # If exiting at a corner
            try:
                if cellsToCompare[i + 1][0][3] and cellsToCompare[i+1][0][5] \
                    and abs(cellsToCompare[len(basicPath)][0][0][1] - cellsToCompare[0][0][0][1]) != 1:
                    # Upper corner
                    if cellsToCompare[i + 2][0][0][1] > cellsToCompare[0][0][0][1]:
                        wallsCrossed += 1
                    # Lower corner
                    else:
                        wallsCrossed += 4
            except:
                pass

        # If exiting cell through a horizontal line
        elif cellsToCompare[i][2] == "x":
            # Going down
            if cellsToCompare[i + 1][0][0][1] < cellsToCompare[i][0][0][1]:
                wallsCrossed += 4
            # Going up
            else:
                wallsCrossed += 1

            # If exiting at a corner
            try:
                if cellsToCompare[i + 1][0][3] and cellsToCompare[i+1][0][5] \
                    and abs(cellsToCompare[len(basicPath)][0][0][0] - cellsToCompare[0][0][0][0]) != 1:
                    # Left corner
                    if cellsToCompare[i + 2][0][0][0] < cellsToCompare[i][0][0][0]:
                        wallsCrossed += 8
                    # Right corner
                    else:
                        wallsCrossed += 2
            except:
                pass

        cellsProcessed.append((cellsToCompare[i][0][0], wallsCrossed))

    # Determine which way (through which borders) the LOS crosses the cells in extended path
    for i in range(len(basicPath), len(cellsToCompare)):
        wallsCrossed = 0
        if cellsToCompare[i][1] == "y":
            if cellsToCompare[0][0][2] < 0 and cellsToCompare[i][0][4]:
                wallsCrossed += 3
            elif cellsToCompare[0][0][2] < 0:
                wallsCrossed += 12
            else:
                wallsCrossed += 9
            cellsProcessed.append((cellsToCompare[i][0][0], wallsCrossed))
        elif cellsToCompare[i][1] == "x":
            if cellsToCompare[0][0][2] < 0 and cellsToCompare[i][0][4]:
                wallsCrossed += 12
            elif cellsToCompare[0][0][2] < 0:
                wallsCrossed += 3
            else:
                wallsCrossed += 6
            cellsProcessed.append((cellsToCompare[i][0][0], wallsCrossed))

    for i in range(len(cellsProcessed)):
        if grid.getObject((cellsProcessed[i][0][0], cellsProcessed[i][0][1]), "Cell").walls & cellsProcessed[i][1] > 0:
            lineClear = False
            return lineClear

    return lineClear


## CLASSES

class Tile():
    def __init__(self, unique_id, properties):
        self.unique_id = unique_id
        self.inside = properties["inside"]
        self.type = properties["type"]
        self.selected = False

class Cell():
    def __init__(self, unique_id, properties):
        self.unique_id = unique_id
        self.inside = properties["inside"]
        self.walls = properties["walls"]
        self.type = properties["type"]
        self.neighbors = {}

class Exit():
    def __init__(self, unique_id):
        self.unique_id = unique_id

class Obstacle():
    def __init__(self, unique_id):
        self.unique_id = unique_id

class Sign():
    def __init__(self, unique_id, direction, exit):
        self.unique_id = unique_id
        self.direction = direction
        self.exit = exit


class Fire(Agent):
    def __init__(self, unique_id, model):
        self.unique_id = unique_id
        self.model = model
        self.duration = 0

    def step(self):
        self.duration += 1
        if self.duration == 1:
            self.generateHeat()
        if self.duration == SMOKE_SPREAD_STEPS:
            self.generateSmoke()
        if self.duration == FIRE_SPREAD_STEPS:
            self.spread()

    def spread(self):
        for el in self.model.grid.get_cell_list_contents([self.pos]):
            if el.__class__.__name__ == "Cell":
                available_cells = []
                for neighbor in el.neighbors:
                    available_cells.append(el.neighbors[neighbor])

        for cell in available_cells:
            burning = False
            for el in self.model.grid.get_cell_list_contents([cell]):
                if el.__class__.__name__ == "Fire":
                    burning = True
                if el.__class__.__name__ == "Smoke":
                    self.model.schedule.remove(el)
                    self.model.grid.remove_agent(el)
            if not burning:
                log("Fire spreading to cell " + str(cell))
                fire = Fire("fire#" + str(self.model.fireCount), self.model)
                self.model.fireCount += 1
                self.model.schedule.add(fire)
                self.model.grid.place_agent(fire, cell)
                self.model.fireList.append(cell)

    def generateSmoke(self):
        for el in self.model.grid.get_cell_list_contents([self.pos]):
            if el.__class__.__name__ == "Cell":
                available_cells = []
                for neighbor in el.neighbors:
                    available_cells.append(el.neighbors[neighbor])

        for cell in available_cells:
            burning = False
            smokeFilled = False
            for el in self.model.grid.get_cell_list_contents([cell]):
                if el.__class__.__name__ == "Smoke":
                    smokeFilled = True
                if el.__class__.__name__ == "Fire":
                    burning = True
            if not burning and not smokeFilled:
                log("Smoke spreading to cell " + str(cell))
                smoke = Smoke("smoke#" + str(self.model.smokeCount), self.model)
                self.model.grid.place_agent(smoke, cell)
                self.model.schedule.add(smoke)
                self.model.smoke.append(cell)
                self.model.smokeCount += 1

    def generateHeat(self):
        for el in self.model.grid.get_cell_list_contents([self.pos]):
            if el.__class__.__name__ == "Cell":
                available_cells = []
                for neighbor in el.neighbors:
                    available_cells.append(el.neighbors[neighbor])

        for cell in available_cells:
            burning = False
            hot = False
            for el in self.model.grid.get_cell_list_contents([cell]):
                if el.__class__.__name__ == "Fire":
                    burning = True
                if el.__class__.__name__ == "Heat":
                    hot = True
            if not burning and not hot:
                log("Heating cell " + str(cell))
                heat = Heat("heat#" + str(self.model.heatCount), self.model)
                self.model.grid.place_agent(heat, cell)
                self.model.hotCells.append(cell)
                self.model.heatCount += 1

class Heat(Agent):
    def __init__(self, unique_id, model):
        self.unique_id = unique_id
        self.model = model

class Smoke(Agent):
    def __init__(self, unique_id, model):
        self.unique_id = unique_id
        self.model = model
        self.duration = 0

    def step(self):
        self.duration += 1
        if self.duration == SMOKE_SPREAD_STEPS:
            self.spread()

    def spread(self):
        for el in self.model.grid.get_cell_list_contents([self.pos]):
            if el.__class__.__name__ == "Cell":
                available_cells = []
                for neighbor in el.neighbors:
                    available_cells.append(el.neighbors[neighbor])

        for cell in available_cells:
            burning = False
            smokeFilled = False
            for el in self.model.grid.get_cell_list_contents([cell]):
                if el.__class__.__name__ == "Smoke":
                    smokeFilled = True
                if el.__class__.__name__ == "Fire":
                    burning = True
            if not burning and not smokeFilled:
                log("Smoke spreading to cell " + str(cell))
                smoke = Smoke("smoke#" + str(self.model.smokeCount), self.model)
                self.model.smokeCount += 1
                self.model.schedule.add(smoke)
                self.model.grid.place_agent(smoke, cell)


### AGENTS

## ADULT
class Adult(Agent):
    def __init__(self, model, type, unique_id, knownExits,
                 preferredStrategy, fitness, startingLocation):

        self.model = model
        self.type = type
        self.fitness = fitness
        self.unique_id = unique_id
        self.startingLocation = startingLocation
        self.patience = 80
        self.children = []
        self.leading = False
        self.ledChildren = []
        self.searchedChild = None
        self.foundChildren = []

        self.moved = False

        self.knownExits = knownExits.copy()

        self.knownSigns = {}
        self.knownFires = []
        self.knownHeat = []
        self.knownObstacles = []

        self.strategy = preferredStrategy

        self.visibleChildren = []
        self.visibleExits = []
        self.visibleSigns = []
        self.visibleObstacles = []
        self.visibleFires = []
        self.visibleHeat = []
        self.visibleAgents = []
        self.visibleCells = []

        self.selected = False

        self.nearestSign = None
        self.routeHistory = []
        self.path = []
        self.explorationDirection = None
        self.waiting = False
        self.waitingTime = 0
        self.waitingTimeForChildren = 0
        self.initDist = 0
        self.optEvacTime = 0
        self.target = None
        self.stuck = False
        self.intoxication = 0
        self.unconscious = False
        self.dead = False
        self.evacuated = False
        if self.type == "Adult":
            if self.fitness == "Fit":
                self.maxSpeed = 2.4
                self.maxFreq = 1
            else:
                self.maxSpeed = 1.2
                self.maxFreq = 2
        elif self.type == "Elderly":
            self.maxSpeed = 0.8
            self.maxFreq = 3
        elif self.type == "Disabled":
            self.maxSpeed = 0.4
            self.maxFreq = 6

        self.freq = self.maxFreq
        if self.freq > 1:
            self.offset = round(random.random() * self.freq)
        else:
            self.offset = 0

        self.previousState = "AT_REST"

        if self.strategy == "familiarExit" and len(self.knownExits) != 0:
            self.state = "EVACUATING"
        else:
            if self.model.grid.getObject(self.startingLocation, "Cell").type == "room":
                self.state = "EXITING_ROOM"
            else:
                self.state = "EXPLORING"


    # Function that checks if and which children are visible
    def locateChildren(self):
        self.visibleChildren = []
        for agentID in self.visibleAgents:
            if agentID in self.children:
                self.visibleChildren.append(agentID)

    # Function that picks the nearest exit from known and available exits:
    def pickExit(self, exits, **kwargs):
        optimalPath = kwargs.get("optimalPath", False)
        visible = kwargs.get("visible", False)
        distances = []
        # If computing optimal path, take all exits into account
        # and ignore all objects/agents, including obstacles
        if optimalPath:
            for exit in exits:
                path = computePath(self.model.grid, self.pos, exit, [], [], [],
                                   ignoreAgents=True)
                if path != ["blocked"]:
                    distances.append((len(path), exit, path))
            # Return the nearest exit
            if len(distances) > 0:
                return (min(distances)[1], min(distances)[2])
            else:
                return None, None

        # Otherwise, consider exit only if it is known to the agent as available
        # And take into account agents and obstacles known to the agent
        else:
            for exit in exits:
                if self.knownExits[exit] or visible:
                    path = computePath(self.model.grid, self.pos, exit,
                                       self.knownFires, self.knownHeat, self.knownObstacles)
                    if path != ["blocked"]:
                        distances.append((len(path), exit, path))
            # Return the nearest exit and path
            if len(distances) > 0:
                return (min(distances)[1], min(distances)[2])
            else:
                return None, None


    # Function that updates the list of currently visible signs and exits
    def updateVisibility(self):
        self.visibleExits = []
        self.visibleSigns = []
        self.visibleObstacles = []
        self.visibleFires = []
        self.visibleHeat = []
        self.visibleAgents = []
        for exit in self.model.exits:
            if isVisible(self.model.grid, (self.pos[0], self.pos[1]), exit[0]):
                self.visibleExits.append(exit)
        for sign in self.model.signs:
            if isVisible(self.model.grid, (self.pos[0], self.pos[1]),
                                         (sign[0][0], sign[0][1])):
                self.visibleSigns.append(sign)
        for obstacle in self.model.obstacles:
            if isVisible(self.model.grid, (self.pos[0], self.pos[1]), obstacle):
                self.visibleObstacles.append(obstacle)
        for fire in self.model.fireList:
            if isVisible(self.model.grid, (self.pos[0], self.pos[1]), fire):
                self.visibleFires.append(fire)
        for heat in self.model.hotCells:
            if isVisible(self.model.grid, (self.pos[0], self.pos[1]), heat):
                self.visibleHeat.append(heat)
        for agent in self.model.activeAgents:
            if agent != self:
                if isVisible(self.model.grid, (self.pos[0], self.pos[1]), agent.pos):
                    self.visibleAgents.append(agent.unique_id)

        # If the agent is selected, update the list of visible cells to be highlighted
        if self.selected:
            for x in range(self.model.grid.width):
                for y in range(self.model.grid.height):
                    cell = self.model.grid.visibilityArray[self.pos[0]][self.pos[1]][x][y]
                    if cell:
                        self.model.grid.getObject((x, y), "Tile").selected = True
                    else:
                        self.model.grid.getObject((x, y), "Tile").selected = False


    # Function that updates the list of known exits
    def updateExits(self):
        for exit in self.visibleExits:
            if exit not in self.knownExits:
                log("\nNew exit found: " + str(exit))
                self.knownExits[exit] = True
                return True

    # Function that updates the list of known signs
    def updateSigns(self):
        for sign in self.visibleSigns:
            if sign not in self.knownSigns:
                log("\nNew sign discovered: " + str(sign))
                # Determine the status of the sign (blocked or not) based on
                # the status of the related exit
                for exit in self.knownExits:
                    if sign[2] == exit[1]:
                        if self.knownExits[exit] == False:
                            self.knownSigns[sign] = False
                            log("Sign leads to a blocked exit, so it will be ignored.")
                            return
                self.knownSigns[sign] = True
                return

    # Function that updates the list of known fires and heat
    def updateFires(self):
        for fire in self.visibleFires:
            if fire not in self.knownFires:
                log("New fire discovered: " + str(fire))
                self.knownFires.append(fire)
        for heat in self.visibleHeat:
            if heat not in self.knownHeat:
                log("Heat discovered: " + str(heat))
                self.knownHeat.append(heat)

    # Function that updates the list of known obstacles
    def updateObstacles(self):
        for obstacle in self.visibleObstacles:
            if obstacle not in self.knownObstacles:
                log("New obstacle discovered: " + str(obstacle))
                self.knownObstacles.append(obstacle)

    # A function that changes the status of currently targeted exit to blocked
    # and either sets the next nearest exit as target or changes the agent's state
    def considerTargetBlocked(self):
        log("Path to " + self.target[1] + " is now considered blocked.")
        self.knownExits[self.target] = False
        # Consider all the signs linked to this exit to be blocked as well
        log("All signs leading to " + self.target[1] +
              " will be ignored from now on.")
        for sign in self.knownSigns:
            if sign[2] == self.target[1]:

                self.knownSigns[sign] = False

        if self.previousState in ["EXPLORING", "FOLLOWING", "EXITING_ROOM"]:
            self.previousState = self.state
            self.state = "EXPLORING"
            log("Switching state to 'EXPLORING'.")
            self.path = []
            self.target = None
            return
        else:
            self.target, self.path = self.pickExit(self.knownExits)
            if self.target != None:
                log("Updated target to " + str(self.target[1]) + " " + str(self.target[0]))
                return self.path
            else:
                log("No known available exits. Switching state to 'EXPLORING'.")
                self.previousState = self.state
                self.state = "EXPLORING"
                self.target = None
                self.path = []
                return []


    # A function that picks an exploration direction at random
    def pickDirection(self, possibleDirections, prevDirection):
        time = 0
        # Make a copy of the list of available directions (not blocked by walls)
        dirs = list(possibleDirections.keys())
        while len(dirs) > 0:
            # Pick a random direction from the list
            direction = random.choice(dirs)
            # Check for blockages and remove blocked cells from the list
            for obj in self.model.grid.get_cell_list_contents(possibleDirections[direction]):
                if obj.__class__.__name__ in ["Obstacle", "Adult", "Child", "Fire", "Heat"]:
                    time += 1
                    dirs.remove(direction)
                    break
            # Try to avoid going back and forth
            if time < len(dirs) and direction == OPPOSITE_DIR[prevDirection]:
                time += 1
                continue
            return direction
        return None

    def reachCorridor(self):
        obstacleClasses = ["Obstacle", "Fire", "Adult", "Child", "Heat", "Smoke"]
        log("Computing path to corridor")
        while True:
            openList = []
            openList.append((self.pos, None))
            closedList = {}
            path = []
            while len(openList) > 0:
                [curr, parent] = openList.pop(0)
                neighbors = self.model.grid.getObject(curr, "Cell").neighbors
                for neighbor in neighbors:
                    cell = neighbors[neighbor]
                    blocked = False
                    used = False
                    for obj in self.model.grid.get_cell_list_contents(cell):
                        if obj.__class__.__name__ in obstacleClasses:
                            blocked = True
                    for entry in openList:
                        if cell in entry:
                            used = True
                            break
                    if self.model.grid.getObject(cell, "Cell").type == "corridor":
                        if not blocked and not used:
                            closedList[curr] = parent
                            closedList[cell] = curr
                            while True:
                                path.append(cell)
                                cell = closedList[cell]
                                if closedList[cell] == None:
                                    break
                            path.reverse()
                            log("PATH: " + str(path))
                            return path
                    if not blocked and not used:
                        if cell not in closedList:
                            openList.append((cell, curr))
                closedList[curr] = parent
            if len(obstacleClasses) > 2:
                del (obstacleClasses[-1])
            else:
                path = ["blocked"]
                log("PATH: " + str(path))
                return path

    def findNearestAdult(self, ratio):
        log("Finding the nearest adult.")
        while True:
            openList = []
            openList.append((self.pos, None))
            closedList = {}
            path = []
            while len(openList) > 0:
                [curr, parent] = openList.pop(0)
                neighbors = self.model.grid.getObject(curr, "Cell").neighbors
                for neighbor in neighbors:
                    cell = neighbors[neighbor]
                    blocked = False
                    used = False
                    hot = False
                    for entry in openList:
                        if cell in entry:
                            used = True
                            break
                    for obj in self.model.grid.get_cell_list_contents(cell):
                        if obj.__class__.__name__ == "Adult" and len(obj.children) < ratio + 1:
                            return obj.unique_id
                    if not used:
                        if cell not in closedList:
                            openList.append((cell, curr))
                closedList[curr] = parent
            log("No suitable adult found.")
            return

    # Funtion that follows the direction of the sign until reaching a wall
    # Then returns the last not-blocked cell on that path

    # A function that changes the status of currently followed sign to blocked
    # and changes the agent's state to EXPLORING
    def considerRouteBlocked(self):
        log("Currently followed route is blocked. Switching state to 'EXPLORING'.")
        for sign in self.routeHistory:
            if sign[2] == self.nearestSign[2]:
                self.knownSigns[sign] = False
        self.previousState = self.state
        self.state = "EXPLORING"
        self.target = None
        return []

    # Function that returns the farthest cell reachable (not blocked by a wall)
    # from the sign by walking in a straight line in the indicated direction
    def routeFromSign(self, sign):
        route = [sign[0]]
        while True:
            last = route[-1]
            try:
                route.append(self.model.grid.getObject(last, "Cell").neighbors[sign[1]])
            except:
                break
        return (last, sign[1])

    # THE MAIN FUNCTION FOR AGENT'S STEP
    def step(self):
        log("\n---\n\nAGENT " + str(self.unique_id) + " step beginning.")
        log("State: " + self.state + "\n")
        # Initial checks
        for el in self.model.grid.get_cell_list_contents(self.pos):
            # Apply effects of fire
            if el.__class__.__name__ == "Fire":
                if not self.unconscious:
                    self.model.activeAgents.remove(self)
                    self.model.activeAgentsCount -= 1
                else:
                    self.model.removedAgents.remove((self, "unconscious"))
                self.dead = True
                self.state = "DEAD"
                self.model.schedule.remove(self)
                self.model.grid.remove_agent(self)
                self.model.removedAgents.append((self, "dead"))
                log(str(self.unique_id) + " died in the fire")
                return

            # Check if the agent is not already unconscious and skip if so
            if self.unconscious:
                log("Agent unconscious.")
                return

            # Apply effects of smoke
            if el.__class__.__name__ == "Smoke":
                self.intoxication += 1
                log("Agent inhaled smoke. Intoxication level: " + str(self.intoxication))
                if self.intoxication >= 60 and self.unconscious == False:
                    self.unconscious = True
                    self.state = "UNCONSCIOUS"
                    self.model.activeAgents.remove(self)
                    self.model.removedAgents.append((self, "unconscious"))
                    self.model.activeAgentsCount -= 1
                    log(str(self.unique_id) + " lost consciousness")
                    continue

        # If leading children, reduce the agent's speed
        currFreq = self.freq

        if self.leading:
            self.freq = max(2, self.maxFreq)
        else:
            self.freq = self.maxFreq

        if self.freq != currFreq:
            if self.freq > 1:
                self.offset = round(random.random() * self.freq)
            else:
                self.offset = 0

        # Check if it's the agent's turn to move
        if (self.model.schedule.steps + self.offset) % self.freq != 0:
            log("Skipping step...")
            return

        # If the agent has moved to accommodate other agent, reset the flag and skip step
        if self.moved == True:
            self.moved = False
            log("Skipping step...")
            return

        # If the agent has children, check if none of them are unconscious or dead and remove these
        for child in self.children:
            if self.model.getAgent(child).unconscious \
                    or self.model.getAgent(child).dead or self.model.getAgent(child).evacuated:
                self.children.remove(child)
                if child in self.foundChildren:
                    self.foundChildren.remove(child)
                if child in self.ledChildren:
                    self.ledChildren.remove(child)

        # Check if all of them are visible
        if len(self.children) > 0:
            self.locateChildren()

            # Check distances to all children and the children the agent is leading
            distancesToChildren = []
            distancesToledChildren = []
            for child in self.children:
                dist = manDist(self.pos, self.model.getAgent(child).pos)
                distancesToChildren.append((dist, child))
                if child in self.ledChildren and child in self.foundChildren:
                    distancesToledChildren.append((dist, child))

            # Check if all children were accounted for, if not, switch state to 'FINDING_CHILDREN'.
            if len(self.foundChildren) < len(self.children):
                if self.state != "FINDING_CHILDREN":
                    self.previousState = self.state
                    self.state = "FINDING_CHILDREN"
                    self.path = []
            else:
                if self.state == "FINDING_CHILDREN":
                    self.state = self.previousState
                    self.previousState = "FINDING_CHILDREN"

            # Update the information about all visible children
            for child in self.visibleChildren:
                if child not in self.foundChildren and manDist(self.pos, self.model.getAgent(child).pos) < 4:
                    log("Found child:" + child)
                    self.waitingTimeForChildren = 0
                    self.foundChildren.append(child)
                    self.searchedChild = None

            for child in self.foundChildren:
                if self.model.getAgent(child).followedGuardian == None:
                    log("Waiting for the child to acknowledge the guardian.")
                    return
                elif self.model.getAgent(child).followedGuardian.unique_id == self.unique_id\
                        and child not in self.ledChildren:
                    log("Leading child:" + child)
                    self.ledChildren.append(child)
                    self.leading = True

            log("\nFound children: " + str(self.foundChildren))
            log("Leading children: " + str(self.ledChildren))

            if len(self.ledChildren) == 0:
                self.leading = False

            # If children are falling behind, wait for them to catch up
            if self.leading:
                if len(distancesToledChildren) > 0 and\
                        (min(distancesToledChildren)[0] > 2 or max(distancesToledChildren)[0] > len(self.ledChildren) + 2):
                    log("Waiting for the children to catch up")
                    self.waitingTimeForChildren += 1
                    if self.waitingTimeForChildren > 20:
                        log("Children considered lost, agent will move to collect them again.")
                        self.foundChildren = []
                    else:
                        return
                    r = random.random()
                    if r < 0.2 and self.waitingTimeForChildren > 20:
                        neighbors = self.model.grid.getObject(self.pos, "Cell").neighbors
                        for neighbor in neighbors:
                            free = True
                            for obj in self.model.grid.get_cell_list_contents(neighbors[neighbor]):
                                if obj.__class__.__name__ in ["Adult", "Child", "Obstacle", "Fire", "Heat", "Exit"]:
                                    free = False
                            if free and self.target != None:
                                log("Moving to a free space to avoid potential blockage.")
                                log("MOVING " + str(neighbor) + ", TO " + str(neighbors[neighbor]))
                                self.model.grid.move_agent(self, neighbors[neighbor])
                                self.path = []
                                return
                else:
                    self.waitingTimeForChildren = 0


            # Check if the children are still active, and if not, remove them from the list

        # If no children (or none left), set leading to false
        else:
            self.leading = False

        # Take action depending on current state
        if self.state == "FINDING_CHILDREN":
            # pick the first (nearest) child to pick up.
            children = self.children.copy()

            if len(self.foundChildren) < len(self.children):
                if self.searchedChild == None:
                    self.path = []
                    for i in range(len(children)):
                        child = children.pop(children.index(min(children)))
                        if child not in self.foundChildren:
                            self.searchedChild = child
                            log("Beginning the process of picking up a child: " + child)
                            break
                else:
                    log("Picking up a child: " + self.searchedChild)
            else:
                log("All children found. Switching back to the previous state: " + self.previousState)
                self.state = self.previousState
                self.previousState = "FINDING_CHILDREN"
                self.target, self.path = self.pickExit(self.knownExits)
                return

            # Compute a path and proceed toward the searched child
            if self.path == []:
                self.path = computePath(self.model.grid, self.pos, (self.model.getAgent(self.searchedChild).pos, self.searchedChild),
                                        self.knownFires, self.knownHeat, self.knownObstacles, childTarget=True)

            next = self.path[0]
            log("Moving towards " + self.searchedChild + "'s location: " + str(self.path[-1]))
            # If there is no possible path, abandon child and save yourself/other children
            if next == "blocked":
                log("Path to " + self.searchedChild + " is now considered blocked.")
                self.children.remove(self.searchedChild)
                if self.searchedChild in self.foundChildren:
                    self.foundChildren.remove(self.searchedChild)
                if self.searchedChild in self.ledChildren:
                    self.ledChildren.remove(self.searchedChild)
                self.path = []
                self.searchedChild = None
                return
            # If currently waiting for other agents to move, attempt to recompute path
            if self.waiting:
                if (self.model.schedule.steps + self.offset) % (5 * self.freq) != 0:
                    log("Previously path was blocked. Waiting.")
                else:
                    log("Path was blocked for 5 moves since the last time it was computed. "
                        + "Attempting to recompute the path.")
                    self.path = computePath(self.model.grid, self.pos, (self.model.getAgent(self.searchedChild).pos, self.searchedChild),
                                            self.knownFires, self.knownHeat, self.knownObstacles, childTarget=True)
                    next = self.path[0]
                    if next == "blocked":
                        return
            # Check whether the next cell is blocked
            blocked = False
            for obj in self.model.grid.get_cell_list_contents(next):
                if obj.__class__.__name__ in ["Adult", "Child", "Obstacle", "Fire", "Heat", "Smoke"]:
                    log("Path blocked by " + obj.__class__.__name__)
                    # If next cell blocked by another agent, wait, and move randomly to avoid blockages
                    if obj.__class__.__name__ in ["Adult", "Child"]:
                        log("Waiting (" + str(self.waitingTime) + ")")
                        self.waiting = True
                        self.waitingTime += self.freq
                        if self.waitingTime > self.patience * 2:
                            log("Child " + self.searchedChild + " is considered permanently lost and will be abandoned.")
                            self.children.remove(self.searchedChild)
                            if self.searchedChild in self.foundChildren:
                                self.foundChildren.remove(self.searchedChild)
                            if self.searchedChild in self.ledChildren:
                                self.ledChildren.remove(self.searchedChild)
                            self.searchedChild = None

                        # Every 10 steps try to get the blocking agent to move out of the way
                        if self.waitingTime % (10 * self.freq) == 0 and obj.moved == False:
                            adjacentToNeighbor = self.model.grid.getObject(obj.pos, "Cell").neighbors
                            for cell in adjacentToNeighbor:
                                if self.model.grid.cellAvailable(adjacentToNeighbor[cell],
                                                                 ["Adult", "Child", "Exit", "Fire", "Heat",
                                                                  "Obstacle"]):
                                    log("Asking agent " + obj.unique_id + " to move out of the way, to cell " + str(
                                        adjacentToNeighbor[cell]) + ".")
                                    if obj.path != None:
                                        obj.path = [obj.pos] + obj.path
                                    self.model.grid.move_agent(obj, adjacentToNeighbor[cell])
                                    obj.moved = True
                                    break

                        blocked = True
                        r = random.random()
                        if r < 0.2 and self.waitingTime > 20:
                            neighbors = self.model.grid.getObject(self.pos, "Cell").neighbors
                            for neighbor in neighbors:
                                free = True
                                for obj in self.model.grid.get_cell_list_contents(neighbors[neighbor]):
                                    if obj.__class__.__name__ in ["Adult", "Child", "Obstacle", "Fire", "Heat", "Exit"]:
                                        free = False
                                if free and self.target != None and self.searchedChild != None:
                                    log("Moving to a free space to avoid potential blockage.")
                                    log("MOVING " + str(neighbor) + ", TO " + str(neighbors[neighbor]))
                                    self.model.grid.move_agent(self, neighbors[neighbor])
                                    self.path = computePath(self.model.grid, self.pos, (self.model.getAgent(self.searchedChild).pos, self.searchedChild),
                                                            self.knownFires, self.knownHeat, self.knownObstacles, childTarget=True)
                                    break
                        break
                    # If next cell blocked by a non-agent, attempt to update path
                    else:
                        self.path = computePath(self.model.grid, self.pos, (self.model.getAgent(self.searchedChild).pos, self.searchedChild),
                                                self.knownFires, self.knownHeat, self.knownObstacles, childTarget=True)
                        next = self.path[0]
                        # If no path possible anymore, end step
                        if next == "blocked":
                            log("No path possible.")
                            blocked = True
                        # If the new path is blocked by an agent, end step
                        elif next != "reached" and next != None:
                            for obj in self.model.grid.get_cell_list_contents(next):
                                if obj.__class__.__name__ in ["Adult", "Child"]:
                                    log("Path blocked by " + obj.__class__.__name__ + ".")
                                    blocked = True
                                    break
            # If possible, move to the next cell
            if not blocked:
                log("MOVING TO " + str(next))
                del (self.path[0])
                self.model.grid.move_agent(self, next)
                # Decrease waiting time counter:
                self.waiting = False
                if self.waitingTime > 0:
                    self.waitingTime -= 2* self.freq

        elif self.state == "EVACUATING":
            # If no target, determine if any eligible exit exists
            if self.target == None:
                self.target, self.path = self.pickExit(self.knownExits)
                if self.target != None:
                    log("Updated target to " + str(self.target[1]) + " " + str(self.target[0]))
                else:
                    log("No known available exits. Switching state to 'EXPLORING'.")
                    self.previousState = self.state
                    self.state = "EXPLORING"
                    self.target = None
                    self.path = []
                    return
            # If state entered with no specified path, compute path
            if self.path == []:
                self.path = computePath(self.model.grid, self.pos, self.target,
                                        self.knownFires, self.knownHeat, self.knownObstacles)
            log("Evacuating to " + str(self.target[1]) + " " + str(self.target[0]))
            next = self.path[0]
            # If there is no possible path, consider exit blocked
            if next == "blocked":
                self.path = self.considerTargetBlocked()
                return
            # If currently waiting for other agents to move, attempt to recompute path
            if self.waiting:
                if (self.model.schedule.steps + self.offset) % (5 * self.freq) != 0:
                    log("Previously path was blocked. Waiting.")
                else:
                    log("Path was blocked for 5 moves since the last time it was computed. "
                    + "Attempting to recompute the path.")
                    self.path = computePath(self.model.grid, self.pos, self.target,
                                            self.knownFires, self.knownHeat, self.knownObstacles)
                    next = self.path[0]
                    if next == "blocked":
                        self.path = self.considerTargetBlocked()
                        return
            # Check whether the next cell is blocked
            blocked = False
            for obj in self.model.grid.get_cell_list_contents(next):
                if obj.__class__.__name__ in ["Adult", "Child", "Obstacle", "Fire", "Heat", "Smoke"]:
                    log("Path blocked by " + obj.__class__.__name__)
                    # If next cell blocked by another agent, wait, and move randomly to avoid blockages
                    if obj.__class__.__name__ in ["Adult", "Child"]:
                        log("Waiting (" + str(self.waitingTime) + ")")
                        self.waiting = True
                        self.waitingTime += self.freq
                        # When waiting limit reached, consider the exit blocked
                        if self.waitingTime > self.patience:
                            self.path = self.considerTargetBlocked()
                        # Every 10 steps try to get the blocking agent to move out of the way
                        if self.waitingTime % (10 * self.freq) == 0 and obj.moved == False:
                            adjacentToNeighbor = self.model.grid.getObject(obj.pos, "Cell").neighbors
                            for cell in adjacentToNeighbor:
                                if self.model.grid.cellAvailable(adjacentToNeighbor[cell], ["Adult", "Child", "Exit", "Fire", "Heat", "Obstacle"]):
                                    log("Asking agent " + obj.unique_id + " to move out of the way, to cell " + str(adjacentToNeighbor[cell]) + ".")
                                    if obj.path != None:
                                        obj.path = [obj.pos] + obj.path
                                    self.model.grid.move_agent(obj, adjacentToNeighbor[cell])
                                    obj.moved = True
                                    break
                        #Move randomly from time to time
                        blocked = True
                        r = random.random()
                        if r < 0.2 and self.waitingTime > 20:
                            neighbors = self.model.grid.getObject(self.pos, "Cell").neighbors
                            for neighbor in neighbors:
                                free = True
                                for obj in self.model.grid.get_cell_list_contents(neighbors[neighbor]):
                                    if obj.__class__.__name__ in ["Adult", "Child", "Obstacle", "Fire", "Heat", "Exit"]:
                                        free = False
                                if free and self.target != None:
                                    log("Moving to a free space to avoid potential blockage.")
                                    log("MOVING " + str(neighbor) + ", TO " + str(neighbors[neighbor]))
                                    self.model.grid.move_agent(self, neighbors[neighbor])
                                    self.path = computePath(self.model.grid, self.pos, self.target,
                                                            self.knownFires, self.knownHeat, self.knownObstacles)
                                    break
                        break
                    # If next cell blocked by a non-agent, attempt to update path
                    else:
                        self.path = computePath(self.model.grid, self.pos, self.target,
                                                self.knownFires, self.knownHeat, self.knownObstacles)
                        next = self.path[0]
                        # If no path possible anymore, end step
                        if next == "blocked":
                            log("No path possible.")
                            blocked = True
                        # If the new path is blocked by an agent, end step
                        elif next != "reached" and next != None:
                            for obj in self.model.grid.get_cell_list_contents(next):
                                if obj.__class__.__name__ in ["Adult", "Child"]:
                                    log("Path blocked by " + obj.__class__.__name__ + ".")
                                    blocked = True
                                    break
            # If possible, move to the next cell
            if not blocked:
                log("MOVING TO " + str(next))
                del(self.path[0])
                self.model.grid.move_agent(self, next)
                # Decrease waiting time counter:
                self.waiting = False
                if self.waitingTime > 0:
                    self.waitingTime -= 2* self.freq

        elif self.state == "EXPLORING":
            if self.model.grid.getObject(self.pos, "Cell").type == "room":
                log("Agent currently in a room. Switching state to 'EXITING ROOM'.")
                self.previousState = self.state
                self.state = "EXITING_ROOM"
                self.explorationDirection = None
                return
            # Check what directions are available from a given position
            possibleDirections = self.model.grid.getObject(self.pos, "Cell").neighbors
            log("Exploring the environment")
            # If there are some visible signs, begin to follow the indicated path
            if len(self.knownSigns) > 0:
                for sign in self.knownSigns:
                    if self.knownSigns[sign]:
                        log("A new viable sign was located. switching state to 'FOLLOWING'")
                        self.previousState = self.state
                        self.state = "FOLLOWING"
                        self.path = []
                        self.target = None
                        return
            # If no direction set, or cannot move further in the current direction, pick a new direction at random
            if self.explorationDirection == None or self.explorationDirection not in possibleDirections:
                self.explorationDirection = self.pickDirection(possibleDirections, self.explorationDirection)
            if self.explorationDirection != None:
                next = possibleDirections[self.explorationDirection]
                blocked = False
                for obj in self.model.grid.get_cell_list_contents(next):
                    if obj.__class__.__name__ in ["Obstacle", "Fire", "Heat"]:
                        blocked = True
                        self.explorationDirection = self.pickDirection(possibleDirections, self.explorationDirection)
                        log("No move possible in the currently followed direction.")
                        break
                    elif obj.__class__.__name__ == "Smoke":
                        inSmoke = False
                        for el in self.model.grid.get_cell_list_contents(self.pos):
                            if el.__class__.__name__ == "Smoke":
                                inSmoke = True
                                break
                        if not inSmoke:
                            self.explorationDirection = self.pickDirection(possibleDirections, self.explorationDirection)
                    elif obj.__class__.__name__ in ["Adult", "Child"]:
                        blocked = True
                        self.explorationDirection = self.pickDirection(possibleDirections, self.explorationDirection)
                        # Try to get the blocking agent to move out of the way with some probability
                        r = random.random()
                        if r < 0.2 and obj.moved == False:
                            adjacentToNeighbor = self.model.grid.getObject(obj.pos, "Cell").neighbors
                            for cell in adjacentToNeighbor:
                                if self.model.grid.cellAvailable(adjacentToNeighbor[cell],
                                                                 ["Adult", "Child", "Exit", "Fire", "Heat",
                                                                  "Obstacle"]):
                                    log("Asking agent " + obj.unique_id + " to move out of the way, to cell " + str(
                                        adjacentToNeighbor[cell]) + ".")
                                    if obj.path != None:
                                        obj.path = [obj.pos] + obj.path
                                    self.model.grid.move_agent(obj, adjacentToNeighbor[cell])
                                    obj.moved = True
                                    break
                        else:

                            blocked = True
                            self.explorationDirection = self.pickDirection(possibleDirections,
                                                                           self.explorationDirection)
                            log("No move possible at the moment. Waiting.")
                            break
                if not blocked:
                    log("MOVING TO " + str(next))
                    self.model.grid.move_agent(self, next)
            else:
                log("No move possible at the moment. Waiting.")


        elif self.state == "EXITING_ROOM":
            if self.stuck:
                self.path = self.reachCorridor()
                next = self.path[0]
                if next == "blocked":
                    log("Currently not able to exit the room.")
                elif next != "reached" and next != None:
                    self.stuck = False
            else:
                if self.model.grid.getObject(self.pos, "Cell").type != "room":
                    log("Exited room. Switching state to 'EXPLORING'.")
                    self.previousState = self.state
                    self.state = "EXPLORING"
                    return
                self.path = self.reachCorridor()
                next = self.path[0]
                if next == "blocked":
                    log("There is no accessible exit from the room.")
                    self.stuck = True
                elif next != "reached" and next != None:
                    blockedByAgent = False
                    for obj in self.model.grid.get_cell_list_contents(next):
                        if obj.__class__.__name__ in ["Adult", "Child"]:
                            blockedByAgent = True
                            log("Path blocked by an agent.")

                            # Try to get the blocking agent to move out of the way with some probability
                            r = random.random()
                            if r < 0.2 and obj.moved == False:
                                adjacentToNeighbor = self.model.grid.getObject(obj.pos, "Cell").neighbors
                                for cell in adjacentToNeighbor:
                                    if self.model.grid.cellAvailable(adjacentToNeighbor[cell],
                                                                     ["Adult", "Child", "Exit", "Fire", "Heat",
                                                                      "Obstacle"]):
                                        log("Asking agent " + obj.unique_id + " to move out of the way, to cell "
                                            + str(adjacentToNeighbor[cell]) + ".")
                                        if obj.path != None:
                                            obj.path = [obj.pos] + obj.path
                                        self.model.grid.move_agent(obj, adjacentToNeighbor[cell])
                                        obj.moved = True
                                        break

                    if not blockedByAgent:
                        log("MOVING TO " + str(next))
                        self.model.grid.move_agent(self, next)

                    # Move randomly from time to time
                    blocked = True
                    r = random.random()
                    if r < 0.2 and self.waitingTime > 20:
                        neighbors = self.model.grid.getObject(self.pos, "Cell").neighbors
                        for neighbor in neighbors:
                            free = True
                            for obj in self.model.grid.get_cell_list_contents(neighbors[neighbor]):
                                if obj.__class__.__name__ in ["Adult", "Child", "Obstacle", "Fire", "Heat", "Exit"]:
                                    free = False
                            if free and self.target != None:
                                log("Moving to a free space to avoid potential blockage.")
                                log("MOVING " + str(neighbor) + ", TO " + str(neighbors[neighbor]))
                                self.model.grid.move_agent(self, neighbors[neighbor])
                                self.path = self.reachCorridor()
                                break


        elif self.state == "FOLLOWING":
            # Create a list of signs visible at a given moment
            signs = []
            # Store the currently followed sign
            oldSign = self.nearestSign
            for sign in self.knownSigns:
                if self.knownSigns[sign]:
                    signs.append((eucDist(self.pos, (sign[0][0], sign[0][1])), sign))
            # If all known signs are known as blocked, switch state to 'EXPLORING'
            if signs == []:
                log("No viable signs to follow at the moment. Switching state to 'EXPLORING'")
                self.previousState = self.state
                self.state = "EXPLORING"
                return
            # Pick the closest sign
            self.nearestSign = min(signs)[1]
            log("Following the emergency exit sign: " + str(self.nearestSign))
            # If no previous path or switching signs, pick a target and path based on the sign
            if self.path == [] or self.path == None or self.nearestSign != oldSign:
                self.target = self.routeFromSign(self.nearestSign)
                self.routeHistory.append(self.nearestSign)
                self.path = computePath(self.model.grid, self.pos, self.target,
                                        self.knownFires, self.knownHeat, self.knownObstacles)
            next = self.path[0]
            log("Route history: " + str(self.routeHistory))
            log("Target: " + str(self.target))
            # If there is no possible path, consider exit blocked
            if next in ["blocked", "reached"]:
                self.path = self.considerRouteBlocked()
                return
            # If currently waiting for other agents to move, attempt to recompute path
            if self.waiting:
                if (self.model.schedule.steps + self.offset) % (5 * self.freq) != 0:
                    log("Previously path was blocked. Waiting.")
                else:
                    log("Path was blocked for 5 moves since the last time it was computed. "
                    + "Attempting to recompute the path.")
                    self.path = computePath(self.model.grid, self.pos, self.target,
                                            self.knownFires, self.knownHeat, self.knownObstacles)
                    next = self.path[0]
                    if next == "blocked":
                        self.path = self.considerTargetBlocked()
                        return
            # Check whether the next cell is blocked
            blocked = False
            for obj in self.model.grid.get_cell_list_contents(next):
                if obj.__class__.__name__ in ["Adult", "Child", "Obstacle", "Fire", "Heat", "Smoke"]:
                    log("Path blocked by " + obj.__class__.__name__)
                    # If path blocked by another agent, wait, and move randomly to avoid blockages
                    if obj.__class__.__name__ in ["Adult", "Child"]:
                        log("Waiting (" + str(self.waitingTime) + ")")
                        self.waiting = True
                        self.waitingTime += self.freq
                        # When waiting limit reached, consider the exit blocked
                        if self.waitingTime > self.patience:
                            self.path = self.considerRouteBlocked()
                        # Every 10 steps try to get the blocking agent to move out of the way
                        if self.waitingTime % (10 * self.freq) == 0 and obj.moved == False:
                            adjacentToNeighbor = self.model.grid.getObject(obj.pos, "Cell").neighbors
                            for cell in adjacentToNeighbor:
                                if self.model.grid.cellAvailable(adjacentToNeighbor[cell], ["Adult", "Child", "Exit", "Fire", "Heat", "Obstacle"]):
                                    log("Asking agent " + obj.unique_id + " to move out of the way, to cell " + str(adjacentToNeighbor[cell]) + ".")
                                    if obj.path != None:
                                        obj.path = [obj.pos] + obj.path
                                    self.model.grid.move_agent(obj, adjacentToNeighbor[cell])
                                    obj.moved = True
                                    break
                        #Move randomly from time to time
                        blocked = True
                        r = random.random()
                        if r < 0.2 and self.waitingTime > 20:
                            neighbors = self.model.grid.getObject(self.pos, "Cell").neighbors
                            for neighbor in neighbors:
                                free = True
                                for obj in self.model.grid.get_cell_list_contents(neighbors[neighbor]):
                                    if obj.__class__.__name__ in ["Adult", "Child", "Obstacle", "Fire", "Heat", "Exit"]:
                                        free = False
                                if free and self.target != None:
                                    log("Moving to a free space to avoid potential blockage.")
                                    log("MOVING " + str(neighbor) + ", TO " + str(neighbors[neighbor]))
                                    self.model.grid.move_agent(self, neighbors[neighbor])
                                    self.path = computePath(self.model.grid, self.pos, self.target,
                                                self.knownFires, self.knownHeat, self.knownObstacles)
                                    break
                        break
                    # If next cell blocked by a non-agent, attempt to update path
                    else:
                        self.path = computePath(self.model.grid, self.pos, self.target,
                                                self.knownFires, self.knownHeat, self.knownObstacles)
                        oldNext = next
                        next = self.path[0]
                        # If no path possible anymore, end step
                        if next == "blocked":
                            log("No path possible.")
                            blocked = True
                        # If the new path is blocked by an agent, end step
                        elif next != "reached" and next != None:
                            for obj in self.model.grid.get_cell_list_contents(next):
                                if obj.__class__.__name__ in ["Adult", "Child"]:
                                    log("Path blocked by " + obj.__class__.__name__ + ".")
                                    blocked = True
            # If possible, move to the next cell
            if not blocked:
                log("MOVING TO " + str(next))
                del (self.path[0])
                self.model.grid.move_agent(self, next)
                # Decrease waiting time counter:
                self.waiting = False
                if self.waitingTime > 0:
                    self.waitingTime -= 2* self.freq


        # Check if the agent has not reached exit
        for el in self.model.grid.get_cell_list_contents(self.pos):
            if el.__class__.__name__ == "Exit":
                self.evacuated = True
                self.model.schedule.remove(self)
                self.model.grid.remove_agent(self)
                self.model.removedAgents.append((self, "evacuated", self.model.schedule.steps + 1))
                self.model.activeAgents.remove(self)
                self.model.activeAgentsCount -= 1

                if self.selected:
                    for x in range(self.model.grid.width):
                        for y in range(self.model.grid.height):
                            self.model.grid.getObject((x, y), "Tile").selected = False
                return

        # Update the lists of objects visible to the agent
        self.updateVisibility()
        log("\nChildren: " + str(self.children))
        log("Visible children: " + str(self.visibleChildren))
        log("\nVisible exits: " + str(self.visibleExits))
        log("Visible signs: " + str(self.visibleSigns))
        log("Visible obstacles: " + str(self.visibleObstacles))
        log("Visible fires: " + str(self.visibleFires))
        log("Visible heat: " + str(self.visibleHeat))
        log("Visible agents: " + str(self.visibleAgents) + "\n")

        # Update list of known exits
        self.updateExits()

        # Update list of known signs
        self.updateSigns()

        # Update list of known obstacles
        self.updateObstacles()

        # Update list of known fire location
        self.updateFires()

        # Print a log of known objects
        log("\nKnown exits: " + str(self.knownExits))
        log("Known signs: " + str(self.knownSigns))
        log("Known obstacle locations: " + str(self.knownObstacles))
        log("Known fire locations: " + str(self.knownFires))
        log("Known heat locations: " + str(self.knownHeat))

        # If at least one exit in sight
        if len(self.visibleExits) > 0 and self.state not in ["FINDING_CHILDREN"]:
            # Update the target if necessary, to aim for the nearest exit
            oldTarget = self.target
            tentativeTarget, tentativePath = self.pickExit(self.visibleExits, visible=True)
            if tentativeTarget != None:
                if tentativeTarget != oldTarget:
                    self.target = tentativeTarget
                log("\nNew viable exit located. Switching state to 'EVACUATING'")
                self.path = tentativePath
                # Change state to 'EVACUATING' to attempt to pursue the new exit
                self.previousState = self.state
                self.state = "EVACUATING"

## CHILD
class Child(Adult):
    def __init__(self, model, type, unique_id, guardians, startingLocation):

        self.model = model
        self.type = type
        self.unique_id = unique_id
        self.guardians = guardians
        self.followedGuardian = None
        self.startingLocation = startingLocation

        self.knownExits = {}

        self.knownFires = []
        self.knownHeat = []
        self.knownObstacles = []

        self.moved = False

        self.visibleGuardians = []
        self.visibleExits = []
        self.visibleSigns = []
        self.visibleObstacles = []
        self.visibleFires = []
        self.visibleHeat = []
        self.visibleAgents = []
        self.visibleCells = []

        self.selected = False

        self.path = []
        self.initDist = 0
        self.optEvacTime = 0
        self.target = None
        self.intoxication = 0
        self.unconscious = False
        self.dead = False
        self.evacuated = False
        self.maxSpeed = 0.8
        self.maxFreq = 3

        self.freq = self.maxFreq
        self.offset = round(random.random() * self.freq)

        self.previousState = "AT_REST"
        self.state = "LOST"

    # Function that checks if a guardian is visible and picks the nearest one
    def locateGuardian(self):
        self.visibleGuardians = []
        visibleGuardians = {}
        for agentID in self.visibleAgents:
            if agentID in self.guardians:
                agent = self.model.getAgent(agentID)
                visibleGuardians[agentID] = round(eucDist(self.pos, agent.pos), 2)

        if len(visibleGuardians) == 0:
            return
        else:
            for el in visibleGuardians.keys():
                self.visibleGuardians.append(el)
            return self.model.getAgent(min(visibleGuardians, key=visibleGuardians.get))



    # THE MAIN FUNCTION FOR CHILD'S STEP
    def step(self):
        log("\n---\n\nAGENT " + str(self.unique_id) + " (CHILD) step beginning.")
        log("State: " + self.state + "\n")
        # Initial checks
        for el in self.model.grid.get_cell_list_contents(self.pos):
            # Apply effects of fire
            if el.__class__.__name__ == "Fire":
                if not self.unconscious:
                    self.model.activeAgents.remove(self)
                    self.model.activeAgentsCount -= 1
                else:
                    self.model.removedAgents.remove((self, "unconscious"))
                self.dead = True
                self.state = "DEAD"
                self.model.schedule.remove(self)
                self.model.grid.remove_agent(self)
                self.model.removedAgents.append((self, "dead"))
                log(str(self.unique_id) + " died in the fire")
                return

            # Check if the agent is not already unconscious and skip if so
            if self.unconscious:
                log("Agent unconscious.")
                return

            # Apply effects of smoke
            if el.__class__.__name__ == "Smoke":
                self.intoxication += 1
                log("Agent inhaled smoke. Intoxication level: " + str(self.intoxication))
                if self.intoxication >= 60 and self.unconscious == False:
                    self.unconscious = True
                    self.state = "UNCONSCIOUS"
                    self.model.activeAgents.remove(self)
                    self.model.removedAgents.append((self, "unconscious"))
                    self.model.activeAgentsCount -= 1
                    log(str(self.unique_id) + " lost consciousness")
                    continue

        # Check if it's the agent's turn to move
        if (self.model.schedule.steps + self.offset) % self.freq != 0:
            log("Skipping step...")
            return

        # If the agent has moved to accommodate other agent, reset the flag and skip step
        if self.moved == True:
            self.moved = False
            log("Skipping step...")
            return

        # Update the lists of objects visible to the agent
        self.updateVisibility()
        self.locateGuardian()
        log("\nGuardians: " + str(self.guardians))
        log("Visible guardians: " + str(self.visibleGuardians))
        log("\nVisible signs: " + str(self.visibleSigns))
        log("Visible obstacles: " + str(self.visibleObstacles))
        log("Visible fires: " + str(self.visibleFires))
        log("Visible heat: " + str(self.visibleHeat))
        log("Visible agents: " + str(self.visibleAgents) + "\n")

        # Update list of known exits
        self.updateExits()

        # Update list of known obstacles
        self.updateObstacles()

        # Update list of known fire location
        self.updateFires()

        # Take action depending on current state
        if self.state == "FOLLOWING":
            log("Following guardian: " + self.followedGuardian.unique_id)
            # If lost sight of guardian, switch state to lost
            if self.followedGuardian.evacuated:
                log("Guardian evacuated. Following to the same exit.")
                self.previousState = self.state
                self.state = "EXITING"
                self.target = self.followedGuardian.target
                return
            if self.followedGuardian.unique_id not in self.visibleGuardians \
                and manDist(self.followedGuardian.pos, self.pos) > len(self.followedGuardian.ledChildren) + 10:
                log("Lost sight of the guardian. Switching state to 'LOST'")
                if self.unique_id in self.followedGuardian.foundChildren:
                    self.followedGuardian.foundChildren.remove(self.unique_id)
                self.previousState = self.state
                self.state = "LOST"
            else:
                self.target = self.followedGuardian.pos
                if self.target != None:
                    if self.path == []:
                        self.path = computePath(self.model.grid, self.pos,
                                                (self.target, self.followedGuardian.unique_id),
                                                self.knownFires, self.knownHeat, self.knownObstacles)
                        if len(self.path) > 12:
                            self.path = computePath(self.model.grid, self.pos,
                                                    (self.target, self.followedGuardian.unique_id),
                                                    self.knownFires, self.knownHeat, self.knownObstacles, ignoreAgents=True)
                    elif self.path[-1] != self.target and self.path != ["blocked"] and self.path != ["reached"]:
                        pathExtension = computePath(self.model.grid, self.path[-1], (self.target, self.followedGuardian.unique_id),
                                            self.knownFires, self.knownHeat, self.knownObstacles, ignoreAgents=True)
                        if pathExtension != ["blocked"] and len(self.path) < 10:
                            for el in pathExtension:
                                self.path.append(el)
                        else:
                            self.path = computePath(self.model.grid, self.pos, (self.target, self.followedGuardian.unique_id),
                                                self.knownFires, self.knownHeat, self.knownObstacles)
                            if len(self.path) > 12:
                                self.path = computePath(self.model.grid, self.pos,
                                                        (self.target, self.followedGuardian.unique_id),
                                                        self.knownFires, self.knownHeat, self.knownObstacles, ignoreAgents=True)
                    next = self.path[0]
                else:
                    log("Lost sight of the guardian. Switching state to 'LOST'")
                    self.followedGuardian = None
                    self.previousState = self.state
                    self.state = "LOST"
                    return
                # If too close to the followed adult move away to avoid blocking him
                if manDist(self.pos, self.followedGuardian.pos) < 2:
                    neighbors = self.model.grid.getObject(self.pos, "Cell").neighbors
                    for neighbor in neighbors:
                        free = True
                        for obj in self.model.grid.get_cell_list_contents(neighbors[neighbor]):
                            if obj.__class__.__name__ in ["Adult", "Child", "Obstacle", "Fire", "Heat", "Exit"]:
                                free = False
                        if free and self.target != None:
                            log("Moving away from the followed guardian to keep reasonable distance.")
                            log("MOVING " + str(neighbor) + ", TO " + str(neighbors[neighbor]))
                            self.model.grid.move_agent(self, neighbors[neighbor])
                            self.path = []
                            return
                else:
                    if next == "blocked" or manDist(self.pos, self.followedGuardian.pos) < 3:
                        log("Cannot get any closer to the guardian.")
                    else:
                        # Check whether the next cell is blocked
                        blocked = False
                        for obj in self.model.grid.get_cell_list_contents(next):
                            if obj.__class__.__name__ in ["Adult", "Child", "Obstacle", "Fire"]:
                                log("Path blocked by " + obj.__class__.__name__)
                                self.path = []
                                blocked = True
                                break
                        if not blocked:
                            log("MOVING TO " + str(next))
                            del (self.path[0])
                            self.model.grid.move_agent(self, next)


        if self.state == "LOST":
            log("Looking for a guardian.")
            nearestGuardian = self.locateGuardian()

            if nearestGuardian != None:
                self.followedGuardian = nearestGuardian
                log("Guardian located: " + self.followedGuardian.unique_id + ". Switching state to 'FOLLOWING'")
                # Change state to following
                self.previousState = self.state
                self.state = "FOLLOWING"
            else:
                log("No guardian in sight. Waiting.")

        if self.state == "EXITING":
            # Check if there's no other guardian in sight
            nearestGuardian = self.locateGuardian()
            if nearestGuardian != None:
                self.followedGuardian = nearestGuardian
                log("Guardian located: " + self.followedGuardian.unique_id + ". Switching state to 'FOLLOWING'")
                # Change state to following
                self.previousState = self.state
                self.state = "FOLLOWING"
            else:
                self.path = computePath(self.model.grid, self.pos, self.target, self.knownFires, self.knownHeat, self.knownObstacles)
                next = self.path[0]
                if next == "blocked":
                    log("Cannot proceed to the exit. Waiting.")
                elif next != "reached" and next != None:
                    # Check whether the next cell is blocked
                    blocked = False
                    for obj in self.model.grid.get_cell_list_contents(next):
                        if obj.__class__.__name__ in ["Adult", "Child", "Obstacle", "Fire"]:
                            log("Path blocked by " + obj.__class__.__name__)
                            self.path = []
                            blocked = True
                            break
                    if not blocked:
                        log("MOVING TO " + str(next))
                        del (self.path[0])
                        self.model.grid.move_agent(self, next)


        # Check if the agent has not reached exit
        for el in self.model.grid.get_cell_list_contents(self.pos):
            if el.__class__.__name__ == "Exit":
                self.evacuated = True
                self.model.schedule.remove(self)
                self.model.grid.remove_agent(self)
                self.model.removedAgents.append((self, "evacuated", self.model.schedule.steps + 1))
                self.model.activeAgents.remove(self)
                self.model.activeAgentsCount -= 1

                if self.selected:
                    for x in range(self.model.grid.width):
                        for y in range(self.model.grid.height):
                            self.model.grid.getObject((x, y), "Tile").selected = False
                return

        # Print a log of known objects
        log("\nKnown exits: " + str(self.knownExits))
        log("Known obstacle locations: " + str(self.knownObstacles))
        log("Known fire locations: " + str(self.knownFires))
        log("Known heat locations: " + str(self.knownHeat))



## GRID
# Set up the simulation environment
class FloorPlan(MultiGrid):
    def __init__(self, width, height, torus, plan, name, exitList, obstacleList, signList):
        super().__init__(width, height, torus)

        # Define the environment name
        self.name = name

        # A variable to store selected item(s)
        self.selected = []

        # Set up the tiles (floor) and cells (walls)
        for i in range(len(plan)):
            for j in range(len(plan[i])):
                tile = Tile("tile#" + str(i * len(plan) + j), plan[i][j])
                self.place_agent(tile, (j, i))
                cell = Cell("cell#" + str(i * len(plan) + j), plan[i][j])
                self.place_agent(cell, (j, i))

        # Pre-compute a list of each cell's neighbours
        for cell_content, cellX, cellY in self.coord_iter():
            for el in cell_content:
                if el.__class__.__name__ != "Cell":
                    continue
                cell = el
                adjacentCells = self.get_neighborhood(pos=cell.pos,
                                                       moore=False,
                                                       include_center=False)
            # Test which neighbouring cells are actually accessible (not separated by a wall)
            for neighbor_coords in adjacentCells:
                neighbor = self.getObject(neighbor_coords, "Cell")
                # For neighbours in the same row
                if cellY == neighbor_coords[1]:
                    # left
                    if cellX > neighbor_coords[0]:
                        if neighbor.walls % 4 <= 1 and cell.walls <= 7:
                            cell.neighbors["west"] = neighbor_coords
                    # right
                    else:
                        if neighbor.walls <= 7 and cell.walls % 4 <= 1:
                            cell.neighbors["east"] = neighbor_coords
                # For neighbours in the same column
                else:
                    # above
                    if cellY < neighbor_coords[1]:
                        if neighbor.walls % 8 <= 3 and cell.walls % 2 == 0:
                            cell.neighbors["north"] = neighbor_coords
                    # below
                    else:
                        if neighbor.walls % 2 == 0 and cell.walls % 8 <= 3:
                            cell.neighbors["south"] = neighbor_coords

        ## EXITS SET-UP
        # Place the exits on the grid
        log("\nPlacing exits in the environment:")
        if len(exitList) > 0:
            for i in range(len(exitList)):
                exit = Exit(exitList[i][1])
                log(exitList[i])
                self.place_agent(exit, exitList[i][0])
        else:
            log("None")

        ## OBSTACLES SET-UP
        # Place the obstacles on the grid
        log("\nPlacing obstacles in the environment:")
        if len(obstacleList) > 0:
            for i in range(len(obstacleList)):
                obstacle = Obstacle("obstacle#" + str(i))
                log(obstacleList[i])
                self.place_agent(obstacle, (obstacleList[i][0], obstacleList[i][1]))
        else:
            log("None")

        ## SIGNS SET-UP
        # Place the emergency exit signs on the grid
        log("\nPlacing signs in the environment:")
        if len(signList) > 0:
            for i in range(len(signList)):
                sign = Sign("sign#" + str(i), signList[i][1], signList[i][2])
                log(signList[i])
                self.place_agent(sign, (signList[i][0][0], signList[i][0][1]))
        else:
            log("None")

    # A function that takes cell coordinates and returns an object
    def getObject(self, coords, type):
        for el in self.get_cell_list_contents(coords):
            if el.__class__.__name__ == type:
                return el

    # A function that checks whether the cell is occupied by an object from a class list
    def cellAvailable(self, coords, objects):
        cell_content = self.get_cell_list_contents([coords])
        available = True
        for el in cell_content:
            if el.__class__.__name__ in objects:
                available = False
                break
            if el.__class__.__name__ == "Cell" and el.inside != 1:
                available = False
                break
        return available

    # A function that selects an object
    def selectObject(self, obj):
        # Clear previous selection
        for item in self.selected:
            self.selected.remove(item)
            item.selected = False
        # If new object indicated, select and remember the new object
        if obj:
            self.selected.append(obj)
            obj.selected = True
            obj.updateVisibility()
            return obj


## SIMULATION
# Set up the agents and step through the simulation.
class SimulationEngine(Model):

    # A class description
    description = "COMP702 - Simulation Evacuation"

    # Initial set-up
    def __init__(self, envList, envName, fireList, agents, timeLimit, visibilityArray, suppress):

        self.envName = envName
        self.interrupted = False

        global suppressLog
        suppressLog = suppress


        # Check whether the server is ready and skip initialization if not
        if not config.serverReady or envName == "None":
            pass
        else:
            global logContent
            logContent = ""
            config.logFilePath = config.CURRENT_DIR + '/logs/log ' + str(datetime.now())[:13] + '-' \
                                 + str(datetime.now())[14:16] + '-' \
                                 + str(datetime.now())[17:19] + '.txt'
            log("\nSimulation environment selected: " + envName)
            log("\n======================================")
            log("SETTING UP THE SIMULATION ENVIRONMENT")
            log("======================================")

            # Get environment variables from the env dict
            env = envList[envName]
            gridWidth = env["gridWidth"]
            gridHeight = env["gridHeight"]
            self.area = env["area"]
            self.exits = env["exits"]
            self.obstacles = env["obstacles"]
            self.signs = env["signs"]

            log("\nFLOOR AREA: " + str(self.area) + "sqm")


            # Set up time limit if passed on, otherwise set it to an unreachable number
            if timeLimit != None:
                self.timeLimit = timeLimit
            else:
                self.timeLimit = 10000

            self.grid = FloorPlan(gridWidth, gridHeight, False, env["floor_plan"], envName,
                                  self.exits, self.obstacles, self.signs)
            self.schedule = RandomActivation(self)

            self.running = True

            # Set up an array to store visibility values
            self.grid.visibilityArray = visibilityArray

            self.idealEvacTimes = []
            # Set up object and agent lists for the model instance
            self.hotCells = []
            self.smoke = []
            # Original list of agents with parameters as dictionaries
            self.agentList = agents
            # List for all agents
            self.allAgents = []
            # List for active agents
            self.activeAgents = []
            # List for removed agents
            self.removedAgents = []

            # Set up counters for the model instance
            self.fireList = list(fireList)
            self.fireCount = 0
            self.heatCount = 0
            self.smokeCount = 0
            self.activeAgentsCount = 0

            ## FIRE SET-UP
            log("\nPlacing fires:")
            if len(self.fireList) == 0:
                log("None")
            for fire in self.fireList:
                log(fire)
                self.placeFire(fire)

            ## AGENT SET-UP
            # Add agents to schedule
            if len(self.agentList) > 0:
                log("\n=====================")
                log("SETTING UP THE AGENTS")
                log("=====================")
            for i in range(len(self.agentList)):
                agentData = self.agentList[i]
                log("\n---\n\nSetting up agent " + agentData["ID"] + ".\n")
                # Set up various types of adult agents
                if agentData["type"] in ["Adult", "Elderly", "Disabled"]:
                    agent = Adult(self,
                                  agentData["type"],
                                  agentData["ID"],
                                  agentData["knownExits"],
                                  agentData["preferredStrategy"],
                                  agentData["fitness"],
                                  agentData["startingLocation"])
                    self.schedule.add(agent)
                    self.grid.place_agent(agent, agentData["startingLocation"])
                    self.allAgents.append(agent)
                    self.activeAgents.append(agent)
                    self.activeAgentsCount += 1

                    agent.mode = agentData["mode"]

                    log("Type: " + agent.type)
                    if agent.type == "Adult":
                        log("Fitness: " + agent.fitness)
                    if agent.strategy == "familiarExit":
                        log("Preferred strategy: " + "go to a familiar exit.")
                    else:
                        log("Preferred strategy: " + "follow the emergency exit signs.")

                    log("Familiar exits: " + str(agent.knownExits) + "\n")
                    nearestExit, optimalPath = agent.pickExit(self.exits, optimalPath=True)
                    log("\nPhysically nearest exit (known or unknown): " + str(nearestExit))
                    if nearestExit != None:
                        agent.initDist = len(optimalPath)
                        agent.optEvacTime = (agent.initDist - 1) * 0.6 / agent.maxSpeed
                        self.idealEvacTimes.append(round(agent.optEvacTime * 4))
                        log("Ideal evacuation time: " + str(round(agent.optEvacTime, 2)) + "s\n")
                    else:
                        log("No exits available")

                    agent.updateVisibility()
                    if agent.state == "EVACUATING":
                        agent.target = agent.pickExit(agent.knownExits)[0]
                    log("\nNearest known exit: " + str(agent.target))
                    log("Initial state: " + agent.state)

                    log("\nChildren: " + str(agent.children))
                    log("Visible children: " + str(agent.visibleChildren))
                    log("\nVisible exits: " + str(agent.visibleExits))
                    log("Visible signs: " + str(agent.visibleSigns))
                    log("Visible obstacles: " + str(agent.visibleObstacles))
                    log("Visible fires: " + str(agent.visibleFires))
                    log("Visible heat: "  + str(agent.visibleHeat) + "\n")
                    agent.updateExits()
                    agent.updateFires()
                    agent.updateObstacles()

                # Set up child agents
                elif agentData["type"] == "Child":
                    agent = Child(self,
                                  agentData["type"],
                                  agentData["ID"],
                                  agentData["guardians"],
                                  agentData["startingLocation"])
                    self.schedule.add(agent)
                    self.grid.place_agent(agent, agentData["startingLocation"])
                    self.allAgents.append(agent)
                    self.activeAgents.append(agent)
                    self.activeAgentsCount += 1

                    agent.mode = agentData["mode"]

                    log("Type: " + agent.type)

                    nearestExit, optimalPath = agent.pickExit(self.exits, optimalPath=True)
                    log("\nPhysically nearest exit: " + str(nearestExit))
                    if nearestExit != None:
                        agent.initDist = len(optimalPath)
                        agent.optEvacTime = (agent.initDist - 1) * 0.6 / agent.maxSpeed
                        self.idealEvacTimes.append(round(agent.optEvacTime * 4))
                        log("Ideal evacuation time: " + str(round(agent.optEvacTime, 2)) + "s\n")
                    else:
                        log("No exits available")

                    agent.updateVisibility()
                    if agent.state == "EVACUATING":
                        agent.target = agent.pickExit(agent.knownExits)[0]
                    log("Initial state: " + agent.state)

                    log("\nGuardians: " + str(agent.guardians))
                    log("Visible guardians: " + str(agent.visibleGuardians))
                    log("\nVisible exits: " + str(agent.visibleExits))
                    log("Visible signs: " + str(agent.visibleSigns))
                    log("Visible obstacles: " + str(agent.visibleObstacles))
                    log("Visible fires: " + str(agent.visibleFires))
                    log("Visible heat: "  + str(agent.visibleHeat) + "\n")
                    agent.updateFires()
                    agent.updateObstacles()

            # Once all agents are loaded, for all children generated as a batch
            # add the nearest adult agent as guardian.

            # Re-compute tha ratio between children and adults
            if len(self.activeAgents) > 0:
                adults = 0
                children = 0
                for agent in self.activeAgents:
                    if agent.type == "Child":
                        children += 1
                    else:
                        adults += 1

                if adults != 0:
                    ratio = math.ceil(children / adults)
                else:
                    ratio = 1

            for agent in self.activeAgents:
                if agent.type == "Child" and agent.mode == "Batch":
                    if len(agent.guardians) == 0:
                        log("Agent " + agent.unique_id + " is a child without a guardian.")
                        tentativeGuardian = agent.findNearestAdult(ratio)
                        if tentativeGuardian != None:
                            agent.guardians.append(tentativeGuardian)
                            self.getAgent(tentativeGuardian).children.append(agent)
                    else:
                        for guardian in agent.guardians:
                            if self.getAgent(guardian) != None and self.getAgent(guardian).type != "Child":
                                self.getAgent(guardian).children.append(agent.unique_id)
                            else:
                                agent.guardians.remove(guardian)
                                tentativeGuardian = agent.findNearestAdult(ratio)
                                if tentativeGuardian != None:
                                    agent.guardians.append(tentativeGuardian)
                                    self.getAgent(tentativeGuardian).children.append(agent)

                elif agent.type == "Child":
                    for guardian in agent.guardians:
                        if self.getAgent(guardian) != None:
                            self.getAgent(guardian).children.append(agent.unique_id)
                        else:
                            agent.guardians.remove(guardian)


            log("\n==========================================")
            log("SET-UP COMPLETE. READY TO START SIMULATION")
            log("==========================================")

    # A function that sets up random fire if necessary
    def randomFire(self):
        if len(self.fireList) > 0:
            return
        log("\nGenerating a random fire location:")
        while True:
            x_coord = random.randint(0, self.grid.width - 1)
            y_coord = random.randint(0, self.grid.height - 1)
            if not self.grid.cellAvailable((x_coord, y_coord), ["Adult", "Child", "Exit", "Fire"]):
                continue
            self.fireList.append((x_coord, y_coord))
            log((x_coord, y_coord))
            return

    ## FIRE SET-UP
    def placeFire(self, fireLocation):
        # Set up initial fire locations
        fire = Fire("fire#" + str(self.fireCount), self)
        self.fireCount += 1
        self.schedule.add(fire)
        self.grid.place_agent(fire, (fireLocation[0], fireLocation[1]))

    # A function that takes an agent ID and returns the agent object
    def getAgent(self, id):
        for el in self.allAgents:
            if el.unique_id == id:
                return el

    # Step function
    def step(self):
        log("\n===\n\nSIMULATION STEP " + str(self.schedule.steps + 1) + "\n")
        if not self.interrupted:
            self.schedule.step()
        if self.activeAgentsCount == 0 \
                or self.schedule.steps == self.timeLimit \
                or self.interrupted:
            self.running = False
            log("\n===\nSIMULATION FINISHED!\n")

            # Set up a dictionary for results and list for evacuation times
            self.results = {"run_time": self.schedule.steps,
                            "total_evac": 0,
                            "adult_evac": 0,
                            "elderly_evac": 0,
                            "disabled_evac": 0,
                            "children_evac": 0,
                            "total_unconsc": 0,
                            "adult_unconsc": 0,
                            "elderly_unconsc": 0,
                            "disabled_unconsc": 0,
                            "children_unconsc": 0,
                            "total_dead": 0,
                            "adult_dead": 0,
                            "elderly_dead": 0,
                            "disabled_dead": 0,
                            "children_dead": 0,
                            "total_active": 0,
                            "adult_active": 0,
                            "elderly_active": 0,
                            "disabled_active": 0,
                            "children_active": 0
                            }
            self.evacTimes = []

            # Determine the cause of ending
            if self.schedule.steps == self.timeLimit:
                log("(Time limit elapsed)\n")
                self.results["cause"] = "time_elapsed"
            elif self.activeAgentsCount == 0:
                log("(No more active agents)\n")
                self.results["cause"] = "no_more_agents"
            elif self.interrupted:
                log("(Interrupted by the user)\n")
                self.results["cause"] = "interrupted"

            log("\nEVACUATED AGENTS:\n")

            for agent in self.removedAgents:
                if agent[1] == "evacuated":
                    self.evacTimes.append(agent[2])
                    log(agent[0].unique_id + " (" +
                          str(round(agent[2] / 4, 2)) + "s / opt: " +
                          str(round(agent[0].optEvacTime, 2)) + "s)")
                    # Increase relevant counters
                    self.results["total_evac"] += 1
                    if agent[0].type == "Adult":
                        self.results["adult_evac"] += 1
                    elif agent[0].type == "Elderly":
                        self.results["elderly_evac"] += 1
                    elif agent[0].type == "Disabled":
                        self.results["disabled_evac"] += 1
                    elif agent[0].type == "Child":
                        self.results["children_evac"] += 1
            log("\n\nUNCONSCIOUS AGENTS:\n")
            for agent in self.removedAgents:
                if agent[1] == "unconscious":
                    log(agent[0].unique_id)
                    # Increase relevant counters
                    self.results["total_unconsc"] += 1
                    if agent[0].type == "Adult":
                        self.results["adult_unconsc"] += 1
                    elif agent[0].type == "Elderly":
                        self.results["elderly_unconsc"] += 1
                    elif agent[0].type == "Disabled":
                        self.results["disabled_unconsc"] += 1
                    elif agent[0].type == "Child":
                        self.results["children_unconsc"] += 1
            log("\n\nDEAD AGENTS:\n")
            for agent in self.removedAgents:
                if agent[1] == "dead":
                    log(agent[0].unique_id)
                    # Increase relevant counters
                    self.results["total_dead"] += 1
                    if agent[0].type == "Adult":
                        self.results["adult_dead"] += 1
                    elif agent[0].type == "Elderly":
                        self.results["elderly_dead"] += 1
                    elif agent[0].type == "Disabled":
                        self.results["disabled_dead"] += 1
                    elif agent[0].type == "Child":
                        self.results["children_dead"] += 1
            log("\n\nACTIVE AGENTS STILL IN THE BUILDING:\n")
            for agent in self.activeAgents:
                self.evacTimes.append(self.schedule.steps)
                log(agent.unique_id)
                # Increase relevant counters
                self.results["total_active"] += 1
                if agent.type == "Adult":
                    self.results["adult_active"] += 1
                elif agent.type == "Elderly":
                    self.results["elderly_active"] += 1
                elif agent.type == "Disabled":
                    self.results["disabled_active"] += 1
                elif agent.type == "Child":
                    self.results["children_active"] += 1

            # Summarise evacuation times
            if len(self.idealEvacTimes) > 0:
                self.results["min-ideal-evac-time"] = min(self.idealEvacTimes)
                sum = 0
                for time in self.idealEvacTimes:
                    sum += time
                self.results["avg-ideal-evac-time"] = round(sum / len(self.idealEvacTimes))
                self.results["max-ideal-evac-time"] = max(self.idealEvacTimes)
            else:
                self.results["min-ideal-evac-time"] = None
                self.results["avg-ideal-evac-time"] = None
                self.results["max-ideal-evac-time"] = None

            if len(self.evacTimes) > 0:
                self.results["min-evac-time"] = min(self.evacTimes)
                sum = 0
                for time in self.evacTimes:
                    sum += time
                self.results["avg-evac-time"] = round(sum / len(self.evacTimes))
                self.results["max-evac-time"] = max(self.evacTimes)
            else:
                self.results["min-evac-time"] = None
                self.results["avg-evac-time"] = None
                self.results["max-evac-time"] = None

        # Flush the log to a file
        with open(config.logFilePath, "a") as logfile:
            global logContent
            logfile.write(logContent)
            logContent = ""

