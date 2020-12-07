# COMP702 - Evacuation Simulation
# Lukasz Przybyla

import sys

import webbrowser, tornado

from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.ModularVisualization import PageHandler
from mesa.visualization.ModularVisualization import SocketHandler
from mesa.visualization.UserParam import UserSettableParameter

import config
from simulation import *
import cProfile
# Current directory
CURRENT_DIR = config.CURRENT_DIR


# Cell size in pixels
CELL_SIZE = 25

# Extend the page handler class to include the list
# of available environments as local_includes
class MyPageHandler(PageHandler):
    def get(self):
        elements = self.application.visualization_elements
        for i, element in enumerate(elements):
            element.index = i
        self.render(
            "modular_template.html",
            port=self.application.port,
            model_name=self.application.model_name,
            description=self.application.description,
            package_includes=self.application.package_includes,
            local_includes=envList,
            scripts=self.application.js_code,
        )

# Extend the socket handler class to modify the messages and message-related behaviour
class MySocketHandler(SocketHandler):


    # A function that computes the line of sight between all cells and stores
    # the results in a 4D array [x1, y1, x2, y2]
    def computeVisibilityArr(self):
        # Determine array size
        w = self.application.model.grid.width
        h = self.application.model.grid.height
        # Check if precomputed visibility file exists
        path = "assets/" + self.application.model.envName + "_visArray.npy"
        envPath = "assets/" + self.application.model.envName + ".json"
        if os.path.isfile(path):
            log("Loading visibility array from file (" + path + ")")
            arr = np.load(path)
        # Otherwise, recompute visibility and create file
        else:
            log("Visibility array file outdated or missing. Recomputing visibility array")
            # Preinitialise an empty array of size gridWidth x gridHeight x gridWidth x gridHeight
            arr = np.zeros((w, h, w, h), dtype=bool)

            # Compute visibility between all cells
            for i in range(w):
                self.write_message({"type": "env_loading",
                                    "progress": i / w * 100})
                for j in range(h):
                    for k in range(w):
                        for l in range(j, h):
                            value = checkVisibility(self.application.model.grid, (i, j), (k, l))
                            arr[i][j][k][l] = value
                            arr[k][l][i][j] = value
            # Save to a file
            np.save(path, arr)
        self.application.model.grid.visibilityArray = arr
        return self.application.model.grid.visibilityArray

    # Customized model state message
    @property
    def viz_state_message(self):
        return {"type": "viz_state",
                "data": self.application.render_model(),
                "envName": self.application.model.envName}

    # Sends message indicating end of run and sending results
    def end_message(self):
        results = self.application.model.results
        return {"type": "end",
                "results": results}

    # Customised behaviour upon receiving a message
    def on_message(self, message):
        if self.application.verbose:
            log("\n" + str(message))
        msg = tornado.escape.json_decode(message)

        # Proceed with the next step of the simulation
        if msg["type"] == "get_step":
            if self.ready:
                self.application.model.step()
                # cProfile.runctx('self.application.model.step()', globals(), locals())
                if self.application.model.running:
                    self.write_message(self.viz_state_message)
                else:
                    self.write_message(self.end_message())
                    self.ready = False

        # Interrupt the simulation
        elif msg["type"] == "interrupt":
            self.application.model.interrupted = True
            self.ready = False
            self.application.model.step()
            self.write_message(self.end_message())

        # Reset the simulation
        elif msg["type"] == "reset":
            if not msg["suppressLog"]:
                self.application.reset_model()
            else:
                self.application.reset_model(suppressLog=True)
            self.ready = True
            # Refresh visuals if displayed
            if msg["mode"] != "Batch":
                self.write_message(self.viz_state_message)

        # Reload the visuals
        elif msg["type"] == "reload":
            # If there was an environment specified, use it
            envName = self.application.model.envName
            # Clear the fire and agent lists
            self.application.model_kwargs["fireList"] = []
            self.application.model_kwargs["agents"] = []
            if envName != "None":
                self.write_message({"type": "clear_canvas",
                                    "envName": envName,
                                    "envArea": self.application.model.area,
                                    "dimensions": [envList[envName]["gridWidth"],
                                                   envList[envName]["gridHeight"],
                                                   envList[envName]["gridWidth"] * CELL_SIZE,
                                                   envList[envName]["gridHeight"] * CELL_SIZE]})
                self.application.reset_model()
                self.write_message({"type": "env_ready"})
                # Send a list of exits to the JS controller
                exitList = self.application.model.exits
                self.write_message({"type": "exit_list",
                                    "list": exitList})
                self.write_message(self.viz_state_message)
            # If no environment specified yet, use the placeholder
            else:
                self.write_message({"type": "clear_canvas",
                                    "envName": envName,
                                    "dimensions": [24,
                                                   20,
                                                   24 * CELL_SIZE,
                                                   20 * CELL_SIZE]})
                self.write_message({"type": "load_placeholder"})
                self.write_message({"type": "env_ready"})

        # Update parameters based on user input
        elif msg["type"] == "submit_param":
            param = msg["param"]
            value = msg["value"]

            if param == "envName":
                # Clear the fire and agent lists
                self.application.model_kwargs["fireList"] = []
                self.application.model_kwargs["agents"] = []
                # Load new environment
                self.application.reset_model(newEnvironment=value)
                # Resize canvas
                if value != "None":
                    self.write_message({"type": "clear_canvas",
                                        "envName": value,
                                        "envArea": self.application.model.area,
                                        "dimensions": [envList[value]["gridWidth"],
                                                       envList[value]["gridHeight"],
                                                       envList[value]["gridWidth"] * CELL_SIZE,
                                                       envList[value]["gridHeight"] * CELL_SIZE]})
                    # Send a list of exits to the JS controller
                    exitList = self.application.model.exits
                    self.write_message({"type": "exit_list",
                                        "list": exitList})
                    # Update visuals
                    self.write_message(self.viz_state_message)

                    # Compute nearest exits and visibility array for each cell
                    self.application.model_kwargs["visibilityArray"] = list(self.computeVisibilityArr())
                    self.write_message({"type": "env_ready"})

            if param == "timeLimit":
                self.application.model_kwargs["timeLimit"] = value
                self.application.model.timeLimit = value
                if value == None:
                    log("Time limit set to: " + str(self.application.model.timeLimit))
                else:
                    log("Time limit set to: " + str(self.application.model.timeLimit) + " steps")


            if param == "fireSettings":
                if not value["fireEnabled"]:
                    # If fire disabled, empty the list
                    self.application.model.fireList = []
                    pass
                elif value["randomFire"]:
                    # If random fire required, call the relevant function
                    self.application.model.fireList = []
                    self.application.model.randomFire()
                else:
                    # If specific fire locations provided, update the model's list
                    self.application.model.fireList = []
                    for location in value["fireLocations"]:
                        coords = location[1:-1].split(', ')
                        self.application.model.fireList.append((int(coords[0]), int(coords[1])))
                for fire in self.application.model.fireList:
                    self.application.model.placeFire(fire)
                # Update model settings and visuals
                self.application.model_kwargs["fireList"] = self.application.model.fireList
                self.application.reset_model(suppressLog = True)
                self.write_message(self.viz_state_message)

            if param == "agentList":
                agentList = value
                self.application.model.agentList = []
                for agentData in agentList:
                    # For adult agents
                    if agentData["type"] in ["Adult", "Elderly", "Disabled"]:
                        # Reformat the known exit list
                        knownExits = {}
                        exitData = agentData["knownExits"]
                        for exit in exitData:
                            knownExits[((int(exit[1]), int(exit[2])), exit[0])] = True
                        # Create agent parameter dict and add it to the model's list
                        agent = {"mode": agentData["mode"],
                                 "type": agentData["type"],
                                 "ID": agentData["ID"],
                                 "knownExits": knownExits,
                                 "preferredStrategy": agentData["preferredStrategy"],
                                 "fitness": agentData["fitness"],
                                 "startingLocation": (int(agentData["x"]), int(agentData["y"]))
                                 }
                    # For child agents
                    else:
                        # Create agent parameter dict and add it to the model's list
                        agent = {"mode": agentData["mode"],
                                 "type": agentData["type"],
                                 "ID": agentData["ID"],
                                 "guardians": agentData["guardians"],
                                 "startingLocation": (int(agentData["x"]), int(agentData["y"]))
                                 }

                    self.application.model.agentList.append(agent)
                # Update model settings and visuals
                self.application.model_kwargs["agents"] = self.application.model.agentList
                self.application.reset_model(suppressLog = True)
                self.write_message(self.viz_state_message)
                guardianDict = {}
                for agent in self.application.model.activeAgents:
                    if agent.type == "Child" and agent.mode == "Batch":
                        guardianDict[agent.unique_id] = agent.guardians
                self.write_message({"type": "update_guardians",
                                    "list": guardianDict})



        # Attempt to place an object
        elif msg["type"] == "place_obj":
            # Extract parameters from message
            objectClass = msg["object"]
            location = (int(msg["x"]), int(msg["y"]))
            # Determine objects that can't be in the same cell with the specified class
            if objectClass == "Fire":
                objectList = ["Adult", "Child", "Exit", "Fire"]
            elif objectClass == "Agent":
                objectList = ["Adult", "Child", "Exit", "Fire", "Obstacle"]
            # Determine whether placement is possible and send a return message to JS controller
            if self.application.model.grid.cellAvailable(location, objectList):
                log("Cell free. Sending message")
                self.write_message({"type": "place_" + objectClass.lower() + "_succ",
                                    "location": str(location)})
            else:
                log("Cell occupied. Sending message")
                self.write_message({"type": "place_" + objectClass.lower() + "_fail",
                                    "location": str(location)})

        # remove an object
        elif msg["type"] == "remove_obj":
            # Extract parameters from message
            objectClass = msg["object"]
            location = (int(msg["x"]), int(msg["y"]))
            # Get the object
            object = self.application.model.grid.getObject(location, objectClass)
            # Remove object from the grid and from the schedule
            log("Removing " + objectClass + " '" + object.unique_id + "' from location " + str(location))
            self.application.model.grid.remove_agent(object)
            self.application.model.schedule.remove(object)
            self.write_message(self.viz_state_message)

        # Check cell for an object
        elif msg["type"] == "check_for_obj":
            # Extract parameters from message
            if msg["object"] == "Agent":
                objectClasses = ["Adult", "Child"]
            elif msg["object"] == "Adult":
                objectClasses = ["Adult"]
            location = (int(msg["x"]), int(msg["y"]))
            for item in objectClasses:
                # Check for the object
                object = self.application.model.grid.getObject(location, item)
                if object:
                    objectClass = item
                    break
            # Send an appropriate reply and select object if present
            if object:
                if msg["object"] == "Agent":
                    self.application.model.grid.selectObject(object)
                    self.write_message({"type": "selected_agent",
                                        "ID": object.unique_id})
                    self.write_message(self.viz_state_message)
                else:
                    self.write_message({"type": "selected_agent",
                                        "ID": object.unique_id})
            elif len(self.application.model.grid.selected) > 0:
                if msg["object"] == "Agent":
                    self.application.model.grid.selectObject(None)
                    self.write_message({"type": "clear_selection"})
                    self.write_message(self.viz_state_message)

        # Send list of empty cells (suitable for agent placement) on request
        elif msg["type"] == "request_empty_cells":
            cellList = [];
            objectList = ["Adult", "Child", "Exit", "Fire", "Obstacle"]
            for i in range(self.application.model.grid.width):
                for j in range(self.application.model.grid.height):
                    if self.application.model.grid.cellAvailable((i, j), objectList):
                        cellList.append((i, j))
            self.write_message({"type": "empty_cells",
                                "cell_list": cellList})

        # Clear selection
        elif msg["type"] == "clear_selection":
            self.application.model.grid.selectObject(None)
            self.write_message({"type": "clear_selection"})
            self.write_message(self.viz_state_message)


        # Inform if the message does not fall into any of the above categories
        else:
            if self.application.verbose:
                log("Unexpected message!")

# Extend the server class to override some of the server methods
class MyModularServer(ModularServer):

    # Replace the default page and socket handlers with the extended classes
    page_handler = (r"/", MyPageHandler)
    socket_handler = (r"/ws", MySocketHandler)

    # Adjust static handler settings to plug a custom template
    static_handler = (
        r"/static/(.*)",
        tornado.web.StaticFileHandler,
        {"path": CURRENT_DIR + "/templates"},
    )

    # These two are to get rid of errors related to favicon.ico and robots.txt
    favicon_handler = (
        r"/(favicon\.ico)",
        tornado.web.StaticFileHandler,
        {"path": CURRENT_DIR + "/templates"},
    )

    robots_handler = (
        r"/(robots\.txt)",
        tornado.web.StaticFileHandler,
        {"path": CURRENT_DIR + "/templates"},
    )

    # Re-define the local handler and the handler list to replace the default values
    local_handler = (r"/local/(.*)", tornado.web.StaticFileHandler, {"path": CURRENT_DIR})
    handlers = [page_handler, socket_handler, static_handler,
                local_handler, favicon_handler, robots_handler]

    # Customised reset behaviour (restart with updated parameters)
    def reset_model(self, **kwargs):
        newEnvironment = kwargs.get("newEnvironment", "None")
        suppressLog = kwargs.get("suppressLog", False)

        # Copy previous model parameters
        model_params = {}
        for key, val in self.model_kwargs.items():
            if isinstance(val, UserSettableParameter):
                if (
                        val.param_type == "static_text"
                ):  # static_text is never used for setting params
                    continue
                model_params[key] = val.value
            else:
                model_params[key] = val
        # If new environment specified, use it
        if newEnvironment != "None":
            gridWidth = envList[newEnvironment]["gridWidth"]
            gridHeight = envList[newEnvironment]["gridHeight"]
            visualPlan = CanvasGrid(portrayal, gridWidth, gridHeight, gridWidth * CELL_SIZE, gridHeight * CELL_SIZE)
            self.visualization_elements = [visualPlan]
            model_params["envName"] = newEnvironment
        # If no new environment specified, check if there was previously selected environment
        else:
            try:
                newEnvironment = self.model.envName
                gridWidth = envList[newEnvironment]["gridWidth"]
                gridHeight = envList[newEnvironment]["gridHeight"]
                visualPlan = CanvasGrid(portrayal, gridWidth, gridHeight, gridWidth * CELL_SIZE, gridHeight * CELL_SIZE)
                self.visualization_elements = [visualPlan]
                model_params["envName"] = newEnvironment
            except:
                pass

        # Suppress logging of simulation setup if requested
        model_params["suppress"] = suppressLog

        # Restart the simulation
        self.model = self.model_cls(**model_params)

# A function that defines the visual representations for agents environment elements

def portrayal(object):

    if object.__class__.__name__ == 'Tile':
        portrayal = {"Shape": "rect",
                     "Filled": "true",
                     "w": 1,
                     "h": 1,
                     "Layer": 0,
                     "Color": "white"}

        if not object.inside:
            portrayal["Color"] = "#404040"
            return portrayal
        else:
            portrayal["Color"] = "white"
            if object.type == "room":
                portrayal["Color"] = "#fffebd";
            elif object.type == "corridor":
                portrayal["Color"] = "#dcd6bf";
            return portrayal

    elif object.__class__.__name__ == 'Cell':
        file_name = 'assets/wall_'
        if object.walls > 0:
            if object.walls % 2 != 0:
                file_name += 't'

            if object.walls % 4 > 1:
                file_name += 'r'

            if object.walls % 8 > 3:
                file_name += 'b'

            if object.walls > 7:
                file_name += 'l'

            file_name += '.png'

            portrayal = {"Shape": file_name,
                         "walls": object.walls,
                         "inside": object.inside,
                         "Layer": 1}

            return portrayal

    elif object.__class__.__name__ == "Exit":
        portrayal = {"Shape": "Exit",
                     "Exit": object.unique_id}

        portrayal["Layer"] = 5
        return portrayal

    elif object.__class__.__name__ == "Obstacle":
        portrayal = {"Shape": "rect",
                     "Filled": "true",
                     "Color": "#663300",
                     "h": 0.9,
                     "w": 0.9}

        portrayal["Layer"] = 3
        return portrayal

    elif object.__class__.__name__ == "Sign":
        portrayal = {"Shape": "arrowHead",
                     "Filled": "true",
                     "Color": "green",
                     "scale": 0.7,
                     "Direction": object.direction,
                     "Points to": object.exit}
        if object.direction == "north":
            portrayal["heading_x"] = 0
            portrayal["heading_y"] = 1
        elif object.direction == "east":
            portrayal["heading_x"] = 1
            portrayal["heading_y"] = 0
        elif object.direction == "south":
            portrayal["heading_x"] = 0
            portrayal["heading_y"] = -1
        elif object.direction == "west":
            portrayal["heading_x"] = -1
            portrayal["heading_y"] = 0
        portrayal["Layer"] = 5
        return portrayal

    elif object.__class__.__name__ == "Fire":

        portrayal = {"Shape": "Fire",
                     "Layer": 4}

        return portrayal

    elif object.__class__.__name__ == "Smoke":
        portrayal = {"Shape": "Smoke",
                     "Layer": 3}

        return portrayal

    elif object.__class__.__name__ in ['Adult', 'Child']:
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "Color": "orange",
                     "r": 0.8,
                     "ID": object.unique_id,
                     "Type": object.type,
                     "State": object.state}

        portrayal["Layer"] = 5

        if object.type == "Adult":
            portrayal["Fitness"] = object.fitness
            if object.fitness == "Unfit":
                portrayal["Color"] = "#cc8500"
        elif object.type == "Elderly":
            portrayal["Shape"] = "Elderly"
        elif object.type == "Disabled":
            portrayal["Shape"] = "Disabled"
        elif object.type == "Child":
            portrayal["Color"] = "#ff1aff"
            portrayal["r"] = 0.5
            if object.state == "FOLLOWING":
                if object.followedGuardian != None:
                    portrayal["Followed guardian"] = object.followedGuardian.unique_id
                else:
                    portrayal["Followed guardian"] = "none"

        if object.__class__.__name__ == "Adult":
            if len(object.ledChildren) > 0:
                portrayal["State"] = "LEADING-" + object.state
                portrayal["Led children"] = object.ledChildren

        if object.selected:
            if object.type == "Child":
                portrayal["r"] = 0.55
            else:
                portrayal["r"] = 0.9
            portrayal["Shape"] = 'circle'
            portrayal["Color"] = 'green'

        portrayal["Intoxication"] = str(object.intoxication) + " / 60"
        return portrayal


gridWidth = envList["test_env_1"]["gridWidth"]
gridHeight = envList["test_env_1"]["gridHeight"]

# Place all elements on the canvas grid
visualPlan = CanvasGrid(portrayal, gridWidth, gridHeight, gridWidth * CELL_SIZE, gridHeight * CELL_SIZE)

# Define the server parameters and port
server = MyModularServer(SimulationEngine,
                         [visualPlan],
                         "Evacuation Simulation",
                         {"envList": envList,
                         "envName": "None",
                         "fireList": [],
                         "agents": [],
                         "timeLimit": timeLimit,
                         "visibilityArray": [],
                         "suppress": False})

port = 8521  # The default
server.port = port

# Adjust server instance settings to plug a custom template
server.settings["template_path"] = CURRENT_DIR + "/templates"

# Suppress the printing of automatic tornado messages
server.verbose = False

# Confirm that the server is now ready for model initialization
config.serverReady = True

# Launch the server
while True:
    try:
        server.launch()
    except KeyboardInterrupt:
        if not server.model.running:
            log("\nEND\n")
            sys.exit()
        else:
            continue
    except:
        # If port busy, increment by 1
        server.port += 1