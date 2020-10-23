/**
COMP702 - Evacuation simulation
Lukasz Przybyla
This file handles most of the UI elements and functionalities, including
 the control over the progress of the simulation runs and batch schedules
 and the handling and exchange of messages with the Python model.
A heavily modified version of the default Mesa's runcontrol.js.
 */

/*
 * Variable definitions
 */

// GUI elements

// Environment selection
const envForm = document.getElementById("env-choice");
const envLabel = document.getElementById("env-label-name");
const envDropdown = document.getElementById("env-dropdown");
const envLoadBtn = document.getElementById("env-load-btn");

// Mode selection
const singleModeBtn = document.getElementById("single-mode-btn");
const batchModeBtn = document.getElementById("batch-mode-btn");

const singleModeElems = document.getElementsByClassName("single-mode-el");
const batchModeElems = document.getElementsByClassName("batch-mode-el");

// Batch schedule
var scheduleRows = document.getElementsByClassName("schedule-row");
var scheduleSubRows = document.getElementsByClassName("schedule-sub-row");
const scheduleBody = document.getElementById("schedule-body");
const deleteScheduleEntryBtn = document.getElementById("delete-schedule-entry-btn");
var currentRun = null;
var currentRunCount = 1;
var totalRuns = 0;
var scheduleRunning = false;
var scheduleFinished = null;

// Settings
const settingDivs = document.getElementsByClassName("setting");

// Get all individual setting elements
const settingElems = [];
for (var i = 0; i < settingDivs.length; i++) {
    settingElems.push(... settingDivs[i].children);
}

const settingsBtns = document.getElementsByClassName("settings-btn");

// Simulation parameter settings
const timeLimitCheckbox = document.getElementById("time-limit-checkbox");
const timeLimitInput = document.getElementById("time-limit-input");
const fireCheckbox = document.getElementById("fire-checkbox");
const addFireBtn = document.getElementById("add-fire-btn");
const removeFireBtn = document.getElementById("remove-fire-btn");
const randomFireRadio = document.getElementById("random-fire-radio");
const placeFireRadio = document.getElementById("place-fire-radio");
const fireList = document.getElementById("fire-list");

// Generate agents (batch)
const agentsBatchBtn = document.getElementById("agents-batch-btn");

const populationNumberRadio = document.getElementById("population-number-radio");
const populationNumberInput = document.getElementById("population-number-input");
const populationDensityRadio = document.getElementById("population-density-radio");
const populationDensityInput = document.getElementById("population-density-input");

const populationElderlyCheckbox = document.getElementById("elderly-checkbox");
const populationElderlySlider = document.getElementById("elderly-slider");
const populationElderlySliderLabel = document.getElementById("elderly-slider-label");
const populationDisabledCheckbox = document.getElementById("disabled-checkbox");
const populationDisabledSlider = document.getElementById("disabled-slider");
const populationDisabledSliderLabel = document.getElementById("disabled-slider-label");
const populationChildrenCheckbox = document.getElementById("children-checkbox");
const populationChildrenSlider = document.getElementById("children-slider");
const populationChildrenSliderLabel = document.getElementById("children-slider-label");

const populationFitnessSlider = document.getElementById("population-fitness-slider");
const populationFitnessSliderLabel = document.getElementById("population-fitness-slider-label");

const populationStrategySlider = document.getElementById("population-strategy-slider");
const populationStrategySliderLabelLeft = document.getElementById("population-strategy-slider-label-left");
const populationStrategySliderLabelRight = document.getElementById("population-strategy-slider-label-right");

const generateAgentsBtn = document.getElementById("agents-batch-exec-btn");

// Add individual agents
const agentsIndivTab = document.getElementById("agents-indiv-tab");
const agentsIndivBtn = document.getElementById("agents-indiv-btn");

const agentDetailsLabel = document.getElementById("agent-details-label");

const agentNameInput = document.getElementById("agent-name-input");
const agentTypeDropdown = document.getElementById("agent-type-dropdown");
const agentFitnessDropdown = document.getElementById("agent-fitness-dropdown");
const agentStrategyDropdown = document.getElementById("agent-strategy-dropdown");

const agentExitsGroup = document.getElementById("exits-group");
const agentExitsDropdown = document.getElementById("known-exits-dropdown");
const agentAddExitBtn = document.getElementById("known-exits-add-btn");
const agentRemoveExitBtn = document.getElementById("known-exits-remove-btn");
const agentExitList = document.getElementById("exits-list");

const agentGuardiansGroup = document.getElementById("guardians-group");
const agentAddGuardianBtn = document.getElementById("guardian-add-btn");
const agentRemoveGuardianBtn = document.getElementById("guardian-remove-btn");
const agentGuardianList = document.getElementById("guardian-list");


const placeAgentBtn = document.getElementById("place-agent-btn");
const updateAgentBtn = document.getElementById("update-agent-btn");
const deleteAgentBtn = document.getElementById("delete-agent-btn");

// Results
const resultsBtn = document.getElementById("results-btn");

const initEnvName = document.getElementById("init-env-name");
const initArea = document.getElementById("init-area");
const initTimeLimit = document.getElementById("init-time-limit");
const initFire = document.getElementById("init-fire");
const initAgentNumber = document.getElementById("init-agents-number");
const initDensity = document.getElementById("init-density");
const initAdults = document.getElementById("init-adults");
const initElderly = document.getElementById("init-elderly");
const initDisabled = document.getElementById("init-disabled");
const initChildren = document.getElementById("init-children");
const initFitness = document.getElementById("init-fitness");
const initStrategy = document.getElementById("init-strategy");
const initMinTime = document.getElementById("init-min-time");
const initAvgTime = document.getElementById("init-avg-time");
const initMaxTime = document.getElementById("init-max-time");

const resultRunTime = document.getElementById("result-run-time");
const resultCause = document.getElementById("result-cause");
const resultAgentsEvac = document.getElementById("result-agents-evac");
const resultAdultsEvac = document.getElementById("result-adults-evac");
const resultElderlyEvac = document.getElementById("result-elderly-evac");
const resultDisabledEvac = document.getElementById("result-disabled-evac");
const resultChildrenEvac = document.getElementById("result-children-evac");
const resultAgentsUnconsc = document.getElementById("result-agents-unconsc");
const resultAdultsUnconsc = document.getElementById("result-adults-unconsc");
const resultElderlyUnconsc = document.getElementById("result-elderly-unconsc");
const resultDisabledUnconsc = document.getElementById("result-disabled-unconsc");
const resultChildrenUnconsc = document.getElementById("result-children-unconsc");
const resultAgentsDead = document.getElementById("result-agents-dead");
const resultAdultsDead = document.getElementById("result-adults-dead");
const resultElderlyDead = document.getElementById("result-elderly-dead");
const resultDisabledDead = document.getElementById("result-disabled-dead");
const resultChildrenDead = document.getElementById("result-children-dead");
const resultAgentsActive = document.getElementById("result-agents-active");
const resultAdultsActive = document.getElementById("result-adults-active");
const resultElderlyActive = document.getElementById("result-elderly-active");
const resultDisabledActive = document.getElementById("result-disabled-active");
const resultChildrenActive = document.getElementById("result-children-active");
const resultMinTime = document.getElementById("result-min-time");
const resultAvgTime = document.getElementById("result-avg-time");
const resultMaxTime = document.getElementById("result-max-time");

// Execution buttons etc.
const runBtn = document.getElementById("sim-run-btn");
const stopBtn = document.getElementById("sim-stop-btn");
const timer = document.getElementById("sim-timer");
const scheduleAddBtn = document.getElementById("schedule-add-btn");
const scheduleCount = document.getElementById("schedule-count");
const scheduleExecBtn = document.getElementById("schedule-exec-btn");
const scheduleTimes = document.getElementById("schedule-times");
const scheduleStopBtn = document.getElementById("batch-stop-btn");



// Interaction modes
const modes = {"placeFireModeOn": false,
               "placeAgentModeOn": false,
               "addGuardianModeOn": false};
const modeBtns = [addFireBtn, placeAgentBtn, agentAddGuardianBtn];


// Simulation parameters
var currentMode = "Single";

var currentEnv = "None";
var storedEnv;

var cellSize = 0;
var gridWidth = 0;
var gridHeight = 0;

var schedule = [];

// Time limit (in steps; divide by 4 to get seconds)
var timeLimitEnabled = false;
var timeLimit = null;

// Fire settings
var fireEnabled = false;
var randomFire = false;
var fireLocations = [];

// Exit list
var exitList = [];

// Agent list
var agentList = [];


// Array to save the setting state
var enabledSettings = [];

// Currently selected object(s)
var selectedObj = [];

// Settings for generating agent batch
var useDensity = false;
var populationCount = 0;
var populationDensity = 0;
var elderlyPercentage = 0;
var disabledPercentage = 0;
var childrenPercentage = 0;
var adultCount = 0;
var elderlyCount = 0;
var disabledCount = 0;
var childrenCount = 0;
// Percentage of fit agents among adults
var populationFitness = 50;
// Percentage of agents choosing familiar exit
var strategyRatio = 50;

// JS Controller and visualisation elements

const controller = new ModelController();
const vizElements = [];
var recentData = null

/**
 * Helper functions
 */

// A function that converts timesteps to time in hh:mm:ss format
function stepsToTime (steps) {
    if (steps == null) {
        steps = 0;
    }
    var min = Math.floor(steps / 4 / 60);
    var sec = Math.round(steps / 4 % 3600 % 60);

    values = [min, sec];

    for (var i = 0; i < values.length; i++) {
        if (values[i] < 10) {
            values[i] = "0" + values[i];
        }
    }

    return values[0] + ":" + values[1];

}function stepsToTimeFloor (steps) {
    if (steps == null) {
        steps = 0;
    }
    var min = Math.floor(steps / 4 / 60);
    var sec = Math.floor(steps / 4 % 3600 % 60);

    values = [min, sec];

    for (var i = 0; i < values.length; i++) {
        if (values[i] < 10) {
            values[i] = "0" + values[i];
        }
    }

    return values[0] + ":" + values[1];
}

// A function that computes an average of a list
function getAvg(arr) {
    const total = arr.reduce((sum, x) => sum + x, 0);
    return Math.round(total / arr.length * 100) / 100;
}

// A version of the function that computes an average of a list for evacuation times
// Discards values that are null or 0 (when no times were measured) to avoid skewing the average
function getEvacTimeAvg(arr) {
    var total = 0;
    var count = 0;
    for (var i = 0; i < arr.length; i++) {
        if (arr[i] != null && arr[i] != 0) {
            total += arr[i];
            count++;
        }
    }
    return Math.round(total / count * 100) / 100;
}

// A function that disables GUI elements
function disableElems (elems) {
    for (var i = 0; i < elems.length; i++) {
        elems[i].disabled = true;
    }
}

// A function that enables GUI elements
function enableElems (elems) {
    for (var i = 0; i < elems.length; i++) {
        elems[i].disabled = false;
    }
}

// A function that clears interaction mode (add fire etc.)
function clearMode() {
    for (var i = 0; i < modeBtns.length; i++) {
        modeBtns[i].classList.remove("active-btn");
    }
    for (var [key, value] of Object.entries(modes)) {
        modes[key] = false;
    }
}

// Clear selection as well
function clearSelection() {
    if (selectedObj.length > 0) {
        send({"type": "clear_selection"});
    }
}

// Functions that send model parameters defined by the user

function updateTimeLimit() {
    send({"type": "submit_param",
      "param": "timeLimit",
      "value": timeLimit});
}

function updateFires() {
    send({"type": "submit_param",
          "param": "fireSettings",
          "value": {"fireEnabled": fireEnabled,
                    "randomFire": randomFire,
                    "fireLocations": fireLocations}});
}


// Function that checks ID for availability
function idTaken(id) {
    for (var i = 0; i < agentList.length; i++) {
        if (agentList[i]["ID"] == id) {
            return true;
        }
    }
    return false;
}

function updateAgents() {
    send({"type": "submit_param",
          "param": "agentList",
          "value": agentList});
    updatePlaceholderID();
}

// Update the ID placeholder based on agent count
function updatePlaceholderID() {
    var next = agentList.length + 1;
    do {
        var text = "agent#"
        if (next < 10) {
            text += "00" + next.toString();
        } else if (next < 100) {
            text += "0" + next.toString();
        } else {
            text += next.toString();
        }
        next++;
    } while (idTaken(text));

    agentNameInput.placeholder = text;
}

// Create a dictionary with agent parameters and add it to agent list
const createAgent = function(location) {
    // Update GUI
    enableElems([runBtn]);

    // Check for any text in 'Name / ID' - if none, use the placeholder
    if (agentNameInput.value != "") {
        var id = (' ' + agentNameInput.value).slice(1);
    } else {
        var id = (' ' + agentNameInput.placeholder).slice(1);
    }

    location = location.slice(1,-1).split(", ");

    if (agentTypeDropdown.value != "Child") {

        // Create an array of known exits
        var exitArray = [];
        for (var i = 0; i < agentExitList.length; i++) {
            var exit = agentExitList[i].innerHTML.split(" ");
            var exitName = exit[0];
            var exitCoords = exit[1].slice(1,-1).split(",");
            var x = exitCoords[0];
            var y = exitCoords[1];
            exitArray.push([exitName, x, y]);
        }

        // Create agent data dictionary and add it to list of agents
        var agent = {"mode": "Single",
                     "type": agentTypeDropdown.value,
                     "ID": id,
                     "guardians": [],
                     "knownExits": exitArray,
                     "preferredStrategy": agentStrategyDropdown.value,
                     "fitness": agentFitnessDropdown.value,
                     "x": location[0],
                     "y": location[1]
        };
        agentList.push(agent);

    } else {

        // Create an array of guardians
        var guardianArray = [];
        for (var i = 0; i < agentGuardianList.length; i++) {
            var guardian = agentGuardianList[i].innerHTML;
            guardianArray.push(guardian);
        }

        // Create agent data dictionary and add it to list of agents
        var agent = {"mode": "Single",
                     "type": agentTypeDropdown.value,
                     "ID": id,
                     "guardians": guardianArray,
                     "knownExits": [],
                     "preferredStrategy": agentStrategyDropdown.value,
                     "fitness": agentFitnessDropdown.value,
                     "x": location[0],
                     "y": location[1]
        };
        agentList.push(agent);
    }
}

// Function that creates a batch of agents
function generateAgents(cellList) {
    // Update GUI0
    disableElems([generateAgentsBtn])
    if (currentMode == "Single") {
        enableElems([runBtn]);

        // Determine number of agents
        if (useDensity) {
            populationCount = Math.round(populationDensity * currentEnvArea);
        } else {
            populationDensity = Math.round(populationCount/currentEnvArea * 1000) / 1000;
        }

        // Determine counts for different agent types
        elderlyCount = Math.round(elderlyPercentage / 100 * populationCount);
        disabledCount = Math.round(disabledPercentage / 100 * populationCount);
        childrenCount = Math.round(childrenPercentage / 100 * populationCount);

        // Make sure the counts don't exceed total population count
        if (elderlyCount + disabledCount + childrenCount > populationCount) {
            var r = Math.random();
            if (r < 0.33) {
                elderlyCount--;
            } else if (r < 0.66) {
                disabledCount--;
            } else {
                childrenCount--;
            }
        }
        // Assign the remaining agents to be regular adults and determine fit/unfit counts
        adultCount = populationCount - (elderlyCount + disabledCount + childrenCount);
    }

    var fitAdultCount = Math.round(populationFitness / 100 * adultCount);

    // Randomly select numbers for agents to choose familiar exit (based on indicated distribution)
    var familiarExitCount = Math.round(strategyRatio / 100 * (populationCount - childrenCount));
    var familiarExitNums = [];
    while (familiarExitNums.length < familiarExitCount) {
        var r = Math.floor(Math.random() * (populationCount - childrenCount));
        if (!familiarExitNums.includes(r)) {
            familiarExitNums.push(r);
        }
    }
    // Select cells for agent population at random
    var selectedCells = [];
    for (var i = 0; i < populationCount; i++) {
        var x = Math.floor(Math.random() * cellList.length);
        var cell = cellList.splice(x, 1);
        selectedCells.push(cell);
    }

    var type = "Adult"
    var fitness = "Fit"

    for (var i = 0; i < populationCount; i++) {

        // Assign type
        if (i == fitAdultCount) {
            fitness = "Unfit";
        }
        if (i == adultCount) {
            type = "Elderly";
        }
        if (i == adultCount + elderlyCount) {
            type = "Disabled";
        }
        if (i == adultCount + elderlyCount + disabledCount) {
            type = "Child";
        }

        // Create an ID
        var id = "agent#";
        var j = i + 1;
        if (j < 10) {
            id += "00" + j.toString();
        } else if (j < 100) {
            id += "0" + j.toString();
        } else {
            id += j.toString();
        }

        // Get location from the random list
        var location = selectedCells.pop()[0];

        if (type != "Child") {

            // Add one known exit by random
            var r = Math.floor(Math.random() * exitList.length);
            if (exitList.length > 0) {
                var exit = exitList[r];
                var exitArray = [[exit[1], exit[0][0], exit[0][1]]];
            } else {
                var exitArray = [];
            }

            // Assign strategy
            var strategy = "followSigns"
            if (familiarExitNums.includes(i)) {
                strategy = "familiarExit"
            }

            // Create agent dict and add to the list
            var agent = {"mode": "Batch",
                         "type": type,
                         "ID": id,
                         "guardians": [],
                         "knownExits": exitArray,
                         "preferredStrategy": strategy,
                         "fitness": fitness,
                         "x": location[0],
                         "y": location[1]
            };

        } else {

            // Create agent dict and add to the list
            var agent = {"mode": "Batch",
                         "type": type,
                         "ID": id,
                         "guardians": [],
                         "knownExits": exitArray,
                         "preferredStrategy": strategy,
                         "fitness": fitness,
                         "x": location[0],
                         "y": location[1]
            };

        }

        agentList.push(agent);
    }

    updateAgents();
}

// Function that starts an individual run within a scheduled batch
const startScheduleRun = function (runNumber) {

    // Set up all the parameters based on the specified run
    currentEnv = schedule[runNumber]["env"];
    currentEnvArea = schedule[runNumber]["area"];
    timeLimitEnabled = schedule[runNumber]["time_limit_enabled"];
    timeLimit = schedule[runNumber]["time_limit"];
    fireEnabled = schedule[runNumber]["fire"];
    populationCount = schedule[runNumber]["agents"];
    populationDensity = schedule[runNumber]["density"];
    adultCount = schedule[runNumber]["adults"];
    elderlyCount = schedule[runNumber]["elderly"];
    disabledCount = schedule[runNumber]["disabled"];
    childrenCount = schedule[runNumber]["children"];
    populationFitness = schedule[runNumber]["fitness"];
    strategyRatio = schedule[runNumber]["strategy"];

    // Generate the agents (will start automatically upon receiving the list of available cells)
    agentList = [];
    send({"type": "request_empty_cells"});
}

// A function that updates results after the run is finished
function printParams(params) {
    initEnvName.innerHTML = params["env"];
    initArea.innerHTML = params["area"] + " m<sup>2</sup>";

    if (params["time_limit"]) {
        initTimeLimit.innerHTML = stepsToTime(params["time_limit"])
    } else {
        initTimeLimit.innerHTML = "-";
    }

    if (params["fire"]) {
        initFire.innerHTML = "YES";
    } else {
        initFire.innerHTML = "NO";
    }

    initAgentNumber.innerHTML = params["agents"];
    initDensity.innerHTML = params["density"] + " person / m<sup>2</sup>";
    initAdults.innerHTML = params["adults"];
    initElderly.innerHTML = params["elderly"];
    initDisabled.innerHTML = params["disabled"];
    initChildren.innerHTML = params["children"];
    initFitness.innerHTML = params["fitness"] + "%";
    if (parseInt(strategyRatio) >= 50) {
        initStrategy.innerHTML = "Go to a familiar exit (" + params["strategy"] + "%)";
    } else {
        initStrategy.innerHTML = "Follow exit signs (" + (100 - params["strategy"]).toString() + "%)";
    }
}

// A function that updates results after the run is finished
function printResults(results) {
    document.getElementById("results-label").innerHTML = "<span>Simulation results</span>";

    if (results == null) {
        var resultElems = document.getElementsByClassName("final-result");
        for (var i = 0; i < resultElems.length; i++) {
            resultElems[i].innerHTML = "";
        }
        return;
    }

    resultRunTime.innerHTML = stepsToTime(results["run_time"]);
    if (results["cause"] == "no_more_agents") {
        resultCause.innerHTML = "No active agents left";
    } else if (results["cause"] == "interrupted") {
        resultCause.innerHTML = "Interrupted by the user";
    } else {
        resultCause.innerHTML = "Time limit reached";
    }

    resultAgentsEvac.innerHTML = results["total_evac"];
    resultAdultsEvac.innerHTML = results["adult_evac"];
    resultElderlyEvac.innerHTML = results["elderly_evac"];
    resultDisabledEvac.innerHTML = results["disabled_evac"];
    resultChildrenEvac.innerHTML = results["children_evac"];
    resultAgentsUnconsc.innerHTML = results["total_unconsc"];
    resultAdultsUnconsc.innerHTML = results["adult_unconsc"];
    resultElderlyUnconsc.innerHTML = results["elderly_unconsc"];
    resultDisabledUnconsc.innerHTML = results["disabled_unconsc"];
    resultChildrenUnconsc.innerHTML = results["children_unconsc"];
    resultAgentsDead.innerHTML = results["total_dead"];
    resultAdultsDead.innerHTML = results["adult_dead"];
    resultElderlyDead.innerHTML = results["elderly_dead"];
    resultDisabledDead.innerHTML = results["disabled_dead"];
    resultChildrenDead.innerHTML = results["children_dead"];
    resultAgentsActive.innerHTML = results["total_active"];
    resultAdultsActive.innerHTML = results["adult_active"];
    resultElderlyActive.innerHTML = results["elderly_active"];
    resultDisabledActive.innerHTML = results["disabled_active"];
    resultChildrenActive.innerHTML = results["children_active"];

    initMinTime.innerHTML = stepsToTime(results["min-ideal-evac-time"]);

    if (results["avg-ideal-evac-time"] != 0 && results["avg-ideal-evac-time"] != null) {
        initAvgTime.innerHTML = stepsToTime(results["avg-ideal-evac-time"]);
    } else {
        initAvgTime.innerHTML = "-";
    }
    if (results["max-ideal-evac-time"] != 0 && results["max-ideal-evac-time"] != null) {
        initMaxTime.innerHTML = stepsToTime(results["max-ideal-evac-time"]);
    } else {
        initMaxTime.innerHTML = "-";
    }

    if (results["cause"] != "no_more_agents") {
        resultAvgTime.innerHTML = "> ";
        resultMaxTime.innerHTML = "> ";
    } else {
        resultAvgTime.innerHTML = "";
        resultMaxTime.innerHTML = "";
    }

    if (results["min-evac-time"] != 0 && results["min-evac-time"] != null) {
        if (results["total_evac"] == 0) {
            resultMinTime.innerHTML = "> ";
        } else {
            resultMinTime.innerHTML = "";
        }
        resultMinTime.innerHTML += stepsToTime(results["min-evac-time"]);
    } else {
        resultMinTime.innerHTML = "-";
    }
    if (results["avg-evac-time"] != 0 && results["avg-evac-time"] != null) {
        resultAvgTime.innerHTML += stepsToTime(results["avg-evac-time"]);
    } else {
        resultAvgTime.innerHTML = "-";
    }
    if (results["max-evac-time"] != 0 && results["max-evac-time"] != null) {
        resultMaxTime.innerHTML += stepsToTime(results["max-evac-time"]);
    } else {
        resultMaxTime.innerHTML = "-";
    }
}

// A function that prints aggregate, average results
function printAvgResults(resultArray) {
    if (resultArray.length > 0) {
        document.getElementById("results-label").innerHTML = "<span>Simulation results (aggregate of " + resultArray.length + ")</span>";
    } else {
        document.getElementById("results-label").innerHTML = "<span>Simulation results</span>";
    }
    aggregateResults = {}

    if (resultArray.length == 0) {
        var resultElems = document.getElementsByClassName("final-result");
        for (var i = 0; i < resultElems.length; i++) {
            resultElems[i].innerHTML = "";
        }
        return;
    }

    for (var i = 0; i < resultArray.length; i++) {
        Object.keys(resultArray[i]).forEach(key => {
            if (!aggregateResults[key]) {
                aggregateResults[key] = [resultArray[i][key]]
            } else {
                aggregateResults[key].push(resultArray[i][key])
            }
        });
    }

    resultRunTime.innerHTML = stepsToTime(getAvg(aggregateResults["run_time"]));

    causes = {
        "no_more_agents": 0,
        "interrupted": 0,
        "time_elapsed": 0
    }

    for (var i = 0; i < aggregateResults["cause"].length; i++) {
        if (aggregateResults["cause"][i] == "no_more_agents") {
            causes["no_more_agents"]++;
        } else if (aggregateResults["cause"][i] == "interrupted") {
            causes["interrupted"]++;
        } else {
            causes["time_elapsed"]++;
        }
    }

    resultCause.innerHTML = "";
    if (causes["no_more_agents"] != 0) {
        resultCause.innerHTML += "no_more_agents: " + causes["no_more_agents"] + "<br>";
    }
    if (causes["interrupted"] != 0) {
        resultCause.innerHTML += "interrupted: " + causes["interrupted"] + "<br>";
    }
    if (causes["time_elapsed"] != 0) {
        resultCause.innerHTML += "time_elapsed: " + causes["time_elapsed"] + "<br>";
    }

    resultAgentsEvac.innerHTML = getAvg(aggregateResults["total_evac"]);
    resultAdultsEvac.innerHTML = getAvg(aggregateResults["adult_evac"]);
    resultElderlyEvac.innerHTML = getAvg(aggregateResults["elderly_evac"]);
    resultDisabledEvac.innerHTML = getAvg(aggregateResults["disabled_evac"]);
    resultChildrenEvac.innerHTML = getAvg(aggregateResults["children_evac"]);
    resultAgentsUnconsc.innerHTML = getAvg(aggregateResults["total_unconsc"]);
    resultAdultsUnconsc.innerHTML = getAvg(aggregateResults["adult_unconsc"]);
    resultElderlyUnconsc.innerHTML = getAvg(aggregateResults["elderly_unconsc"]);
    resultDisabledUnconsc.innerHTML = getAvg(aggregateResults["disabled_unconsc"]);
    resultChildrenUnconsc.innerHTML = getAvg(aggregateResults["children_unconsc"]);
    resultAgentsDead.innerHTML = getAvg(aggregateResults["total_dead"]);
    resultAdultsDead.innerHTML = getAvg(aggregateResults["adult_dead"]);
    resultElderlyDead.innerHTML = getAvg(aggregateResults["elderly_dead"]);
    resultDisabledDead.innerHTML = getAvg(aggregateResults["disabled_dead"]);
    resultChildrenDead.innerHTML = getAvg(aggregateResults["children_dead"]);
    resultAgentsActive.innerHTML = getAvg(aggregateResults["total_active"]);
    resultAdultsActive.innerHTML = getAvg(aggregateResults["adult_active"]);
    resultElderlyActive.innerHTML = getAvg(aggregateResults["elderly_active"]);
    resultDisabledActive.innerHTML = getAvg(aggregateResults["disabled_active"]);
    resultChildrenActive.innerHTML = getAvg(aggregateResults["children_active"]);

    initMinTime.innerHTML = stepsToTime(getEvacTimeAvg(aggregateResults["min-ideal-evac-time"]));

    if (getEvacTimeAvg(aggregateResults["avg-ideal-evac-time"]) != 0) {
        initAvgTime.innerHTML = stepsToTime(getEvacTimeAvg(aggregateResults["avg-ideal-evac-time"]));
    } else {
        initAvgTime.innerHTML = "-";
    }
    if (getEvacTimeAvg(aggregateResults["max-ideal-evac-time"]) != 0) {
        initMaxTime.innerHTML = stepsToTime(getEvacTimeAvg(aggregateResults["max-ideal-evac-time"]));
    } else {
        initMaxTime.innerHTML = "-";
    }

    if (getEvacTimeAvg(aggregateResults["min-evac-time"]) != 0) {
        resultMinTime.innerHTML = stepsToTime(getEvacTimeAvg(aggregateResults["min-evac-time"]));
    } else {
        resultMinTime.innerHTML = "-";
    }
    if (getEvacTimeAvg(aggregateResults["avg-evac-time"]) != 0) {
        resultAvgTime.innerHTML = stepsToTime(getEvacTimeAvg(aggregateResults["avg-evac-time"]));
    } else {
        resultAvgTime.innerHTML = "-";
    }
    if (getEvacTimeAvg(aggregateResults["max-evac-time"]) != 0) {
        resultMaxTime.innerHTML = stepsToTime(getEvacTimeAvg(aggregateResults["max-evac-time"]));
    } else {
        resultMaxTime.innerHTML = "-";
    }
}


/**
 * A ModelController that defines the model state.
 */
function ModelController(tick = 0, running = false, finished = false) {
    this.tick = tick;

    this.running = running;
    this.finished = finished;

    /** Start the model and keep it running until stopped */
    this.start = function start() {

        // Define fps depending on mode
        if (currentMode == "Single") {
            this.fps = 4;
            updateAgents();
        } else {
            this.fps = 1000;
            updateFires();
        }

        this.tick = 0;
        this.running = true;

        // Enable the timer
        timer.classList.remove("inactive");

        // Send user parameters
        updateTimeLimit();

        this.reset(false);
        this.step();

    }

    /** Stop the model */
    this.stop = function stop() {
        this.running = false;
        this.tick = 0;
    }

    /**
     * Step the model one step ahead.
     *
     * If the model is in a running state this function will be called repeatedly
     * after the visualization elements are rendered. */
    this.step = function step() {
        this.tick += 1;
        if (!controller.finished) {
            send({type: "get_step", step: this.tick});
        }

        // Update the timer
        if (currentMode == "Single") {
            timer.innerHTML = stepsToTimeFloor(this.tick);
            if (timeLimitEnabled) {
                timer.innerHTML += "/" + stepsToTimeFloor(timeLimit);
            }
        } else {
            timer.innerHTML = currentRunCount + "/" + totalRuns + " (" + stepsToTimeFloor(this.tick);
            if (timeLimitEnabled) {
                timer.innerHTML += "/" + stepsToTimeFloor(timeLimit);
            }
            timer.innerHTML += ")";
        }
    }

    // Reset the model and visualization state
    this.reset = function reset(suppressLog) {
        // Reset all the visualizations
        if (this.finished) {
            this.finished = false;
        }
        clearTimeout(this.timeout);
        send({type: "reset",
              suppressLog:suppressLog,
              mode:currentMode});
    }

    // Reload the visualisation (includes canvas resizing)
    this.reload = function reload() {
        fireLocations = [];
        send({ type: "reload" });
    }

    /** Stops the model and put it into a finished state */
    this.done = function done() {
        clearSelection();

        this.stop();
        this.finished = true;
        
        // Disable and reset the timer
        timer.classList.add("inactive");

        this.reset(true);

        var trig = new Event('change');
        agentsIndivTab.dispatchEvent(trig);
    }

    /**
     * Render visualisation elements with new data.
     * @param {any[]} data Model state data passed to the visualization elements
     */
    this.render = function render(data) {
        if (currentMode == "Single") {
            if (this.tick == 0) {
                vizElements.forEach((element, index) => element.init(data[index], false));
            } else {
                vizElements.forEach((element, index) => element.render(data[index], false));
            }
        }
        if (this.running) {
            clearTimeout(this.timeout);
            this.timeout = setTimeout(() => this.step(), 1000 / this.fps);
        }
    }
}

/*
 * Websocket opening and message handling
 */

/** Open the websocket connection; support TLS-specific URLs when appropriate */
const ws = new WebSocket(
    (window.location.protocol === "https:" ? "wss://" : "ws://") +
    location.host +
    "/ws"
);

/**
 * Parse and handle an incoming message on the WebSocket connection.
 * @param {string} message - the message received from the WebSocket
 */
ws.onmessage = function (message) {
    const msg = JSON.parse(message.data);
    const canvasParent = document.getElementById("canvas-parent");
    const backgroundCanvas = document.getElementById("background-canvas");
    const backgroundCtx = backgroundCanvas.getContext('2d');
    const canvas = document.getElementById("canvas");
    const ctx = canvas.getContext('2d');
    const interactionCanvas = document.getElementById("interaction-handler");
    switch (msg["type"]) {
        case "load_placeholder":
            // Load a placeholder image
            console.log(msg);
            var img = new Image();
            img.addEventListener('load', function () {
                ctx.drawImage(img, 0, 0);
            }, false);
            img.src = '/local/assets/placeholder.png';
            break;
        case "env_loading":
            console.log(msg);
            var progress = msg["progress"]
            document.getElementById("loading-percents").innerHTML = parseInt(progress) + "%";
            break;
        case "env_ready":
            console.log(msg);
            document.getElementById("loading-bckgrnd").classList.add("hidden");
            document.getElementById("loading-info").classList.add("hidden");
            document.getElementById("loading-percents").innerHTML = "";
            if (scheduleFinished == false && scheduleRunning) {
                envLabel.innerHTML = schedule[currentRun]['env'];
                startScheduleRun(currentRun);
            }
            break;
        case "viz_state":
            if (currentMode == "Single") {
                // Update visualization state in single mode
                console.log(msg);
                if (msg["envName"] != "None") {
                    envLabel.innerHTML = msg["envName"];
                }
                recentData = msg["data"]
                controller.render(msg["data"]);
                currentEnv = envLabel.innerHTML;
            } else {
                // In batch mode, progress without rendering anything
                console.log(msg);
                controller.render([]);
            }
            break;
        case "place_fire_succ":
            console.log(msg);
            var coords = msg["location"];
            fireLocations.push(coords);
            fireList.innerHTML += "<option class='fire-list-entry'>" + coords + "</option>";
            updateFires();
            break;
        case "place_fire_fail":
            console.log(msg);
            alert("Cannot place a fire in that cell.");
            break;
        case "place_agent_succ":
            console.log(msg);
            var coords = msg["location"];
            // Create agent based on input settings and specified location, then update the model
            createAgent(coords);
            updateAgents();
            break;
        case "place_agent_fail":
            console.log(msg);
            alert("Cannot place an agent in that cell.");
            break;
        case "selected_agent":
            console.log(msg);
            if (modes["addGuardianModeOn"]) {
                for (var i = 0; i < agentList.length; i++) {
                    if (["Adult", "Elderly", "Disabled"].includes(agentList[i]["type"]) && agentList[i]["ID"] == msg['ID']) {
                        if (selectedObj.length > 0) {
                            if (!selectedObj[0]["guardians"].includes(msg['ID'])) {
                                selectedObj[0]["guardians"].push(msg['ID']);
                                console.log(agentList)
                                agentGuardianList.innerHTML += "<option value='" + msg['ID'] +
                                                                "' class='guardian-list-entry'>" + msg['ID'] + "</option>";
                                enableElems([agentGuardianList]);
                            }
                        } else {
                            var inList = false;
                            for (var j = 0; j < agentGuardianList.children.length; j++) {
                                if (agentGuardianList.children.item(i).innerText == msg["ID"]) {
                                    inList = true;
                                }
                            }
                            if (!inList) {
                                agentGuardianList.innerHTML += "<option value='" + msg['ID'] +
                                                                "' class='guardian-list-entry'>" + msg['ID'] + "</option>";
                                enableElems([agentGuardianList]);
                            }
                        }
                    }
                }

            } else {
                // Otherwise, selected agent
                // Clear previous selection
                selectedObj = [];
                for (var i = 0; i < agentList.length; i++) {
                    if (["Adult", "Elderly", "Disabled", "Child"].includes(agentList[i]["type"]) && agentList[i]["ID"] == msg['ID']) {
                        selectedObj.push(agentList[i]);
                    }
                    // Open individual agent details
                    var trig = new Event('click');
                    agentsIndivBtn.dispatchEvent(trig);
                }
                // Update GUI with agent information
                if (controller.running == false) {
                    enableElems([updateAgentBtn, deleteAgentBtn, agentExitList, agentGuardianList]);
                } else {
                    disableElems([updateAgentBtn, deleteAgentBtn, agentExitList, agentGuardianList]);
                }
                disableElems([placeAgentBtn]);
                agent = selectedObj[0];
                agentDetailsLabel.innerHTML = `Agent<span style='color:red;'>` + agent['ID'] + `</span>details`;
                agentNameInput.value = agent["ID"];
                agentTypeDropdown.value = agent["type"];
                var trig = new Event('change');
                agentTypeDropdown.dispatchEvent(trig);
                agentFitnessDropdown.value = agent["fitness"];
                agentStrategyDropdown.value = agent["preferredStrategy"];
                agentExitList.innerHTML = "";
                agentGuardianList.innerHTML = "";
                if (agent["type"] != "Child") {
                    for (var i = 0; i < agent["knownExits"].length; i++) {
                        var exit = agent["knownExits"][i][0] + " (" + agent["knownExits"][i][1] + "," + agent["knownExits"][i][2] + ")"
                        agentExitList.innerHTML += "<option class='exit-list-entry'>" + exit + "</option>";
                    }
                } else {
                    for (var i = 0; i < agent["guardians"].length; i++) {
                        var guardian = agent["guardians"][i]
                        agentGuardianList.innerHTML += "<option class='guardian-list-entry'>" + guardian + "</option>";
                    }
                }
            }
            break;
        case "selected_child":
            console.log(msg);
            break;
        case "clear_selection":
            console.log(msg);
            // Clear selection
            selectedObj = [];
            // Update GUI
            disableElems([updateAgentBtn, deleteAgentBtn]);
            agentNameInput.value = "";
            var trig = new Event('change');
            agentsIndivTab.dispatchEvent(trig);
            agentDetailsLabel.innerHTML = "Agent details";
            break;
        case "empty_cells":
            console.log(msg);
            emptyCells = msg["cell_list"];
            // Populate the environment with agents
            generateAgents(emptyCells);
            if (currentMode == "Batch") {
                // When in batch mode, (re)start the controller
                controller.start();
            }
            break;
        case "end":
            // We have reached the end of the model
            console.log(msg);
            if (currentMode == "Single") {
                // In single mode, this means end of simulation
                controller.done();
                // Update the GUI
                runBtn.classList.remove("hidden");
                stopBtn.classList.add("hidden");
                timer.classList.add("hidden");
                timer.classList.add("inactive");// Re-enable the settings
                for (var i = enabledSettings.length - 1; i >= 0; i--) {
                    elem = enabledSettings.pop();
                    elem.disabled = false;
                }
                enableElems([envDropdown]);
                if (currentMode == "Single") {
                    enableElems([batchModeBtn, generateAgentsBtn]);
                } else {
                    enableElems([singleModeBtn]);
                }
                // Print results
                printResults(msg["results"]);
                // Open the results tab
                var trig = new Event('click');
                resultsBtn.dispatchEvent(trig);
            } else {
                // In batch mode, progress to next run or end the batch run
                controller.stop();
                // Update the results in the UI
                schedule[currentRun]["finished"] = true;
                schedule[currentRun]["results"] = msg["results"];
                // Determine the next run
                scheduleFinished = true;
                for (var i = 0; i < schedule.length; i++) {
                    if (!schedule[i]["deleted"]  && !schedule[i]["finished"]) {
                        currentRun = i;
                        currentRunCount++;
                        scheduleFinished = false;
                        break;
                    }
                }

                // Continue to the next run if not finished and not interrupted
                if (!scheduleFinished && scheduleRunning) {
                    if (envLabel.innerHTML == schedule[currentRun]["env"]) {
                    // If the same environment is used, continue
                        startScheduleRun(currentRun);
                    } else {
                    // Send environment update request
                        send({"type": "submit_param",
                              "param": "envName",
                              "value": schedule[currentRun]["env"]});
                    }

                } else {
                    // Otherwise, finish the batch run
                    controller.done();

                    // Update the GUI
                    enableElems([singleModeBtn, deleteScheduleEntryBtn]);
                    scheduleStopBtn.classList.add("hidden");
                    timer.classList.add("hidden");
                    timer.classList.add("inactive");
                    scheduleAddBtn.classList.remove("hidden");
                    scheduleTimes.classList.remove("hidden");
                    scheduleCount.classList.remove("hidden");
                    scheduleExecBtn.classList.remove("hidden");

                    // Re-enable the settings
                    for (var i = enabledSettings.length - 1; i >= 0; i--) {
                        elem = enabledSettings.pop();
                        elem.disabled = false;
                    }
                }
            }
            break;
        case "clear_canvas":
            // The environment has changed, so the canvas needs to be cleared
            console.log(msg);
            const [gw, gh, cw, ch] = msg["dimensions"];
            currentEnv = msg["envName"];
            currentEnvArea = msg['envArea'];
            gridWidth = gw;
            gridHeight = gh;
            populationNumberInput.max = Math.floor(currentEnvArea * 1.7);
            if (currentMode == "Single") {
                interactionCanvas.width = cw;
                interactionCanvas.height = ch;
                canvas.width = cw;
                canvas.height = ch;
                backgroundCanvas.width = cw;
                backgroundCanvas.height = ch;
                canvasParent.style = "height:" + ch + "px; width:" + cw + "px;";
                // If recentData is not empty, send a final signal to the renderer to remove the
                // mouseover event handler on the interaction_canvas
                if (recentData != null) {
                    vizElements[0].render(recentData[0], true);
                }
                vizElements.forEach(element => element.reset(cw, ch, gw, gh));
                document.getElementById("loading-bckgrnd").style = "height:" + ch + "px; width:" + cw + "px;";
                document.getElementById("loading-bckgrnd").classList.remove("hidden");
                document.getElementById("loading-info").classList.remove("hidden");
            }
            // Update GUI
            if (currentEnv != "None") {
                enableElems([envDropdown, agentsBatchBtn, timeLimitCheckbox, fireCheckbox, scheduleAddBtn]);
                if (currentMode == "Single") {
                    enableElems([batchModeBtn, agentsIndivBtn, generateAgentsBtn])
                }
            }
            updatePlaceholderID();
            break;
        case "model_params":
            // Reset everything using the user parameters
            console.log(msg);
            controller.reload();
            break;
        case "exit_list":
            console.log(msg);
            // Clear previous exits
            agentExitsDropdown.innerHTML = "<option value=\"None\" disabled selected>Select an exit</option>";
            agentExitList.innerHTML = "";
            // Update the list of exits available to the agents in the UI
            exitList = msg["list"];
            for (var i = 0; i < exitList.length; i++) {
                agentExitsDropdown.innerHTML += "<option value=\'" + exitList[i][1] + " (" + exitList[i][0] + ") \'>"
                    + exitList[i][1] + " (" + exitList[i][0] + ")</option>";
            }
            break;
        case "update_guardians":
            console.log(msg)
            guardianUpdates = msg["list"]
            for (var i = 0; i < agentList.length; i++) {
                if (agentList[i]["ID"] in guardianUpdates) {
                    agentList[i]["guardians"] = guardianUpdates[agentList[i]["ID"]]
                }
            }
            if (!controller.running) {
                enableElems([generateAgentsBtn])
            }
            break
        default:
            // There shouldn't be any other message
            console.log("Unexpected message.");
            console.log(msg);
    }
};

/**
 * Turn an object into a string to send to the server, and send it.
 * @param {string} message - The message to send to the Python server
 */
const send = function (message) {
    const msg = JSON.stringify(message);
    ws.send(msg);
};


/*
 * Functions that process user input
 */

// Wait for the UI to load
document.addEventListener('DOMContentLoaded', function() {

    /*
     *  Environment selection
     */

    // Update the environment if requested
    const envSelectInput = function (e) {
        // Prevent page reload
        e.preventDefault();
        // Clear any active buttons and selection
        clearMode();
        clearSelection();
        // Get the environment name
        let envName = envDropdown.value
        if (envName != currentEnv) {
            // Reset fire and agent lists
            fireLocations = [];
            agentList = [];
            // Send environment update request
            send({"type": "submit_param",
                  "param": "envName",
                  "value": envName});
            // Update GUI
            envLabel.innerHTML = envName;
            currentEnv = envName;
            disableElems([envLoadBtn, runBtn]);
            enableElems([agentsBatchBtn, timeLimitCheckbox, fireCheckbox]);
            if (currentMode == "Single") {
                enableElems([batchModeBtn, agentsIndivBtn])
            } else {
                enableElems([singleModeBtn])
            }
            fireList.innerHTML = "";

        } else {}
    }

    // Disable the 'load environment' button if currently loaded environment selected
    const envSelectDisable = function (e) {
        envName = envDropdown.value
        if (envName == envLabel.innerHTML) {
            envLoadBtn.disabled = true;
        } else {
            envLoadBtn.disabled = false;
        }
    }

    /*
     *  Mode selection
     */


    // Function that switches the UI to single mode
    const modeSelectSingle = function (e) {
        clearMode();
        agentList = [];

        currentMode = "Single";
        currentEnv = storedEnv;
        send({"type": "submit_param",
                  "param": "envName",
                  "value": currentEnv});



        // Update the GUI
        enableElems([batchModeBtn]);
        disableElems([singleModeBtn, runBtn]);
        if (currentEnv != "None") {
            enableElems([agentsIndivBtn]);
            updateFires();
        }
        if (fireCheckbox.checked == true) {
            enableElems([placeFireRadio]);
        }
        // Toggle the UI elements between single and batch mode
        for (var i = 0; i < batchModeElems.length; i++) {
            batchModeElems[i].classList.add("hidden");
        }
        for (var i = 0; i < singleModeElems.length; i++) {
            singleModeElems[i].classList.remove("hidden");
        }

        controller.reload();

    }

    // Function that switches the UI to batch mode
    const modeSelectBatch = function (e) {
        clearMode();
        clearSelection();

        currentMode = "Batch";
        storedEnv = currentEnv;

        // Update the GUI
        disableElems([batchModeBtn, agentsIndivBtn, generateAgentsBtn]);
        enableElems([singleModeBtn]);
        if (fireCheckbox.checked == true) {
            disableElems([placeFireRadio]);
            randomFireRadio.checked = true;
            toggleRandomFire();
        }
        // Toggle the buttons between single and batch mode
        for (var i = 0; i < singleModeElems.length; i++) {
            singleModeElems[i].classList.add("hidden");
        }
        for (var i = 0; i < batchModeElems.length; i++) {
            batchModeElems[i].classList.remove("hidden");
        }

        if (agentsIndivBtn.classList.contains("active")) {
            var trig = new Event('click');
            agentsBatchBtn.dispatchEvent(trig);
        }

        controller.reload();



    }

    /*
     *  Batch schedule
     */

    // Function that selects a schedule row
    const selectScheduleRow = function (e) {
        // Remove previous selections
        for (var i = 0; i < scheduleRows.length; i++) {
            scheduleRows[i].classList.remove("selected-row");
        }
        for (var i = 0; i < scheduleSubRows.length; i++) {
            scheduleSubRows[i].classList.remove("selected-row");
        }
        // Select row
        if (e.target.parentElement.classList.contains("schedule-row") ||
            e.target.parentElement.classList.contains("schedule-sub-row")) {
            e.target.parentElement.classList.add("selected-row");
        }

        if (e.target.parentElement.classList.contains("schedule-row") && e.target.parentElement.children.item(1).innerHTML > 1) {
            var runs = e.target.parentElement.getAttribute("data-runs").split(",");
            var run = runs[0];
            printParams(schedule[run]);
            var resultArray = [];
            for (var i = 0; i < runs.length; i++) {
                if (schedule[runs[i]]["results"] != null) {
                    resultArray.push(schedule[runs[i]]["results"])
                }
            }
            printAvgResults(resultArray);
        } else if (e.target.parentElement.classList.contains("schedule-row")) {
            var run = e.target.parentElement.getAttribute("data-runs");
            printParams(schedule[run]);
            printResults(schedule[run]["results"])
        } else {
            var run = e.target.parentElement.getAttribute("data-run");
            printParams(schedule[run]);
            printResults(schedule[run]["results"])
        }

        var trig = new Event('click');
        resultsBtn.dispatchEvent(trig);0

    }

    // Function that expands/collapses schedule row with multiple runs
    const toggleScheduleRow = function (e) {
        var row = e.target.parentElement;

        if (row.classList.contains("expanded")) {
            row.children.item(0).innerHTML = "▶";
            row.classList.remove("expanded");
            for (var i = 0; i < row.children.item(1).innerHTML; i++) {
                row.parentNode.removeChild(row.nextSibling);
            }
        } else {
            row.children.item(0).innerHTML = "▼";
            row.classList.add("expanded");
            var runCount = row.children.item(1).innerHTML;

            for (var i = runCount; i > 0; i--) {
                var rowCopy = row.cloneNode(true);
                rowCopy.setAttribute("class", "schedule-sub-row");
                rowCopy.removeAttribute("data-runs");
                rowCopy.setAttribute("data-run", row.getAttribute("data-runs").split(',')[i - 1]);
                rowCopy.children.item(0).innerHTML = "↳";
                rowCopy.children.item(1).innerHTML = "(" + i + ".)";
                row.insertAdjacentElement('afterend', rowCopy);
                rowCopy.addEventListener('click', selectScheduleRow);
            }
        }
    }

    const deleteScheduleEntry = function (e) {
        for (var i = 0; i < scheduleRows.length; i++) {
            if (scheduleRows[i].classList.contains("selected-row")) {
                while (scheduleRows[i].nextSibling && scheduleRows[i].nextSibling.classList.contains("schedule-sub-row")) {
                    scheduleRows[i].nextSibling.remove();
                }
                var runNumbers = scheduleRows[i].getAttribute("data-runs");
                runNumbers = runNumbers.split(",");
                for (var j = 0; j < runNumbers.length; j++) {
                    schedule[runNumbers[parseInt(j)]]["deleted"] = true;
                }
                scheduleRows[i].remove();

                // Select next row
                if (scheduleRows[i]) {
                    scheduleRows[i].classList.add("selected-row");
                }
            }
        }

        for (var i = 0; i < scheduleSubRows.length; i++) {
            if (scheduleSubRows[i].classList.contains("selected-row")) {
                var previous = scheduleSubRows[i].previousSibling;
                while (!previous.classList.contains("schedule-row")) {
                    previous = previous.previousSibling;
                }
                var count = previous.children.item(1).innerHTML;
                previous.children.item(1).innerHTML = count - 1;
                var runNumber = scheduleSubRows[i].getAttribute("data-run");
                schedule[parseInt(runNumber)]["deleted"] = true;
                scheduleSubRows[i].remove();

                // Update the collective row 'data-runs' attribute
                var runs = previous.getAttribute("data-runs").split(",");
                runs = runs.filter(item => item !== runNumber);
                previous.setAttribute("data-runs", runs);

                // Update the schedule
                var trig = new Event('click');
                previous.children.item(0).dispatchEvent(trig);
                previous.children.item(0).dispatchEvent(trig);

                // Remove the collective row if empty
                for (var j = 0; j < scheduleRows.length; j++) {
                    if (scheduleRows[j].children.item(1).innerHTML == "0") {
                        scheduleRows[j].remove();
                    }
                }

                // Select next row
                if (scheduleSubRows[i]) {
                    scheduleSubRows[i].classList.add("selected-row");
                }
            }
        }

        var scheduleLength = 0
        for (var i = 0; i < schedule.length; i++) {
            if (!schedule[i]["deleted"]) {
                scheduleLength += 1;
            }
        }

        // If schedule is empty, block the execution button
        if (scheduleRows.length == 0 && scheduleSubRows.length == 0) {
            disableElems([scheduleExecBtn]);
        }
    }

    /*
     *  Settings
     */

    // Function that expands and collapses tabs in the menu
    const menuSwitch = function (e) {
        clearMode();
        for (let i = 0; i < settingsBtns.length; i++) {
            settingsBtns[i].classList.remove('active');
            var panel = settingsBtns[i].nextElementSibling;
            if (panel.style.height != "0") {
              panel.style.height = "0";
            }
        }
        this.classList.add("active");
        this.nextElementSibling.style.height = "calc(100% - 3.3*2em)";
    }

    /*
     * Simulation parameters
     */
    const toggleTimeLimit = function (e) {
        if (timeLimitInput.disabled == true) {
            enableElems([timeLimitInput]);
            timeLimitEnabled = true;
            if (timeLimitInput.value != "") {
                timeLimit = Math.round(timeLimitInput.value * 60 * 4);
            } else {
                timeLimit = null;
            }
        } else {
            disableElems([timeLimitInput]);
            timeLimitEnabled = false;
            timeLimit = null;
        }
    }

    const timeLimitKeydown = function (e) {
        if(["+", "-"].includes(e.key)) {
            e.preventDefault();
        } else if (e.key == ".") {
            if (timeLimitInput.value == "") {
                e.preventDefault();
            } else if (timeLimitInput.value.indexOf(".") != -1) {
                e.preventDefault();
            }
        }
    }

    const setTimeLimit = function (e) {
        timeLimit = Math.round(timeLimitInput.value * 60 * 4);
    }

    const toggleFire = function (e) {
        if (fireCheckbox.checked == true) {
            enableElems([randomFireRadio]);
            if (currentMode == "Single") {
                enableElems([placeFireRadio]);
            } else {
                randomFireRadio.checked = true;
                toggleRandomFire();
            }
            if (placeFireRadio.checked == true) {
                enableElems([addFireBtn, fireList]);
            }
            fireEnabled = true;
        } else {
            disableElems([addFireBtn, removeFireBtn, placeFireRadio, randomFireRadio, fireList]);
            fireEnabled = false;
        }
        updateFires();
    }

    const toggleRandomFire = function (e) {
        // Clear any other mode
        clearMode();
        clearSelection();
        if (placeFireRadio.checked) {
            enableElems([addFireBtn, fireList]);
            randomFire = false;
            for (var i = 0; i < fireList.length; i++) {
                fireLocations.push(fireList[i].innerHTML);
                // fireLocations.push(coords);
            }
            updateFires();

        } else {
            disableElems([addFireBtn, removeFireBtn, fireList]);
            fireLocations = [];
            randomFire = true;
            updateFires();
        }
    }

    const addFireMode = function (e) {
        // Clear any other mode
        clearMode();
        clearSelection();

        addFireBtn.classList.add("active-btn");
        modes["placeFireModeOn"] = true;
    }

    const removeFire = function (e) {
        // Clear any other mode
        clearMode();
        clearSelection();
        // Remove fire(s) selected in the list
        options = document.getElementsByClassName("fire-list-entry");
        for (var i = options.length - 1; i >= 0; i--) {
            if (options[i].selected == true) {
                // Extract coordinates
                var coords = options[i].innerHTML.slice(1, -1).split(", ");
                var x = coords[0];
                var y = coords[1];
                // Remove the fire from the list
                var index = fireLocations.indexOf(options[i].innerHTML);
                fireLocations.splice(index, 1);
                options[i].remove();
                // Send a message to remove fire from the model
                send({"type": "remove_obj",
                              "object": "Fire",
                              "x": x.toString(),
                              "y": y.toString()});
            }
        }

        if (fireList.innerHTML == "") {
            disableElems([removeFireBtn]);
        }

    }

    const enableRemoveFireBtn = function (e) {
        // Clear any other mode
        clearMode();
        clearSelection();

        // Enable Fire Remove Button
        enableElems([removeFireBtn]);
    }


    /*
     * Generate agents (batch)
     */

    const togglePopulationSize = function (e) {
        // Clear any other mode
        clearMode();
        clearSelection();

        if (populationNumberRadio.checked) {
            enableElems([populationNumberInput]);
            if (currentMode == "Single") {
                enableElems([generateAgentsBtn])
            }
            disableElems([populationDensityInput]);
            useDensity = false;
        } else {
            enableElems([populationDensityInput]);
            if (currentMode == "Single") {
                enableElems([generateAgentsBtn])
            }
            disableElems([populationNumberInput]);
            useDensity = true;
        }

    }

    const populationNumberKey = function (e) {
        if(["+", "-", "."].includes(e.key)) {
            e.preventDefault();
        }
    }

    const populationDensityKey = function (e) {
        if(["+", "-"].includes(e.key)) {
            e.preventDefault();
        } else if (e.key == ".") {
            if (populationDensityInput.value == "") {
                e.preventDefault();
            } else if (populationDensityInput.value.indexOf(".") != -1) {
                e.preventDefault();
            }
        }
    }

    const toggleElderly = function (e) {
        if (populationElderlyCheckbox.checked) {
            populationElderlySlider.value = Math.min( 100 - (childrenPercentage + disabledPercentage), populationElderlySlider.value);
            elderlyPercentage = parseInt(populationElderlySlider.value);
            populationElderlySliderLabel.innerHTML = populationElderlySlider.value + "%"
            populationElderlySlider.disabled = false;
        } else {
            elderlyPercentage = 0;
            populationElderlySliderLabel.innerHTML = "0%"
            populationElderlySlider.disabled = true;
        }
    }

    const updateElderlyRatio = function (e) {
        populationElderlySlider.value = Math.min( 100 - (childrenPercentage + disabledPercentage), populationElderlySlider.value);
        elderlyPercentage = parseInt(populationElderlySlider.value);
        populationElderlySliderLabel.innerHTML = populationElderlySlider.value + "%"
    }

    const toggleDisabled = function (e) {
        if (populationDisabledCheckbox.checked) {
            populationDisabledSlider.value = Math.min( 100 - (elderlyPercentage + childrenPercentage), populationDisabledSlider.value);
            disabledPercentage = parseInt(populationDisabledSlider.value);
            populationDisabledSliderLabel.innerHTML = populationDisabledSlider.value + "%"
            populationDisabledSlider.disabled = false;
        } else {
            disabledPercentage = 0;
            populationDisabledSliderLabel.innerHTML = "0%"
            populationDisabledSlider.disabled = true;
        }
    }

    const updateDisabledRatio = function (e) {
        populationDisabledSlider.value = Math.min( 100 - (elderlyPercentage + childrenPercentage), populationDisabledSlider.value);
        disabledPercentage = parseInt(populationDisabledSlider.value);
        populationDisabledSliderLabel.innerHTML = populationDisabledSlider.value + "%"
    }

    const toggleChildren = function (e) {
        if (populationChildrenCheckbox.checked) {
            populationChildrenSlider.value = Math.min( 100 - (elderlyPercentage + disabledPercentage), populationChildrenSlider.value);
            childrenPercentage = parseInt(populationChildrenSlider.value);
            populationChildrenSliderLabel.innerHTML = populationChildrenSlider.value + "%"
            populationChildrenSlider.disabled = false;
        } else {
            childrenPercentage = 0;
            populationChildrenSliderLabel.innerHTML = "0%"
            populationChildrenSlider.disabled = true;
        }
    }

    const updateChildrenRatio = function (e) {
        populationChildrenSlider.value = Math.min( 100 - (elderlyPercentage + disabledPercentage), populationChildrenSlider.value);
        childrenPercentage = parseInt(populationChildrenSlider.value);
        populationChildrenSliderLabel.innerHTML = populationChildrenSlider.value + "%"
    }

    const updateFitnessRatio = function (e) {
        populationFitness = populationFitnessSlider.value;
        populationFitnessSliderLabel.innerHTML = populationFitnessSlider.value + "%";
    }

    const updateStrategyRatio = function (e) {
        strategyRatio = populationStrategySlider.value;
        populationStrategySliderLabelLeft.innerHTML = (100 - strategyRatio) + "%";
        populationStrategySliderLabelRight.innerHTML = strategyRatio + "%";
    }

    const requestEmptyCells = function (e) {
        clearMode();
        clearSelection();
        // Remove any previous agents
        agentList = [];
        updateAgents();
        // Check if all the required input was provided
        if (!useDensity) {
            populationCount = populationNumberInput.value;
            if (populationCount == null || populationCount == 0) {
                alert("No value or incorrect value for number of agents provided.");
                disableElems([runBtn]);
                return;
            } else if (populationCount > (currentEnvArea * 1.7)) {
                alert("Specified agent number is too high. Max. number for this environment is "
                    + Math.floor(currentEnvArea * 1.7) + "\n\n (Based on population density of 1.7 person/sqm.)");
                disableElems([runBtn]);
                return;
            } else if (populationCount > 999) {
                alert("Maximum population size is 999 agents.");
                disableElems([runBtn]);
                return;
            }
        } else {
            populationDensity = Number.parseFloat(populationDensityInput.value).toPrecision(4);
            populationCount = Math.round(populationDensityInput.value * currentEnvArea);
            if (populationCount == null || populationCount == 0) {
                alert("No value or incorrect value for occupation density provided.");
                disableElems([runBtn]);
                return;
            } else if (populationDensity > 1.7) {
                alert("Specified occupation density is too high. Max. allowed density is 1.7 person/sqm.");
                disableElems([runBtn]);
                return;
            }
        }
        send({"type": "request_empty_cells"});
    }


    /*
     * Add individual agents
     */

    const updatePlaceBtn = function (e) {
        // Check if all necessary information is there
        if (agentTypeDropdown.value == "None" ||
            (agentFitnessDropdown.value == "None" &&
            agentFitnessDropdown.disabled == false) ||
            (agentStrategyDropdown.value == "None" &&
            agentStrategyDropdown.disabled == false) ||
            selectedObj.length > 0) {
            // Disable 'PLACE AGENT' button
            disableElems([placeAgentBtn]);
        } else {
            enableElems([placeAgentBtn]);
        }
    }

    const toggleAgentOptions = function (e) {
        
        clearMode();
        
        // Toggle fitness dropdown (it only applies to 'Adult' type of agent)
        if (agentTypeDropdown.value == "Adult" && controller.running == false) {
            enableElems([agentFitnessDropdown]);
        } else {
            disableElems([agentFitnessDropdown]);
        }
        
        // Toggle strategy dropdown (it does not apply to children)
        if (agentTypeDropdown.value == "Child" && controller.running == false) {
            disableElems([agentStrategyDropdown]);
            enableElems([placeAgentBtn]);
        } else {
            disableElems([placeAgentBtn]);
            enableElems([agentStrategyDropdown]);
        }

        // Toggle the visibility of familiar exit/guardians setting groups
        if (agentTypeDropdown.value == "Child") {
            agentExitsGroup.classList.add("hidden");
            agentGuardiansGroup.classList.remove("hidden");
        } else {
            agentGuardiansGroup.classList.add("hidden");
            agentExitsGroup.classList.remove("hidden");
        }
    }

    const exitSelected = function (e) {
        // Update GUI
        var exit = agentExitsDropdown.value;
        var known = false;
        for (var i = 0; i < agentExitList.length; i++) {
            if (agentExitList[i].innerHTML == exit) {
                known = true;
                break;
            }
        }
        if (!known) {
            enableElems([agentAddExitBtn]);
        } else {
            disableElems([agentAddExitBtn]);
        }
    }

    const addExit = function (e) {
        enableElems([agentExitList]);
        disableElems([agentAddExitBtn]);
        var exit = agentExitsDropdown.value;
        agentExitList.innerHTML += "<option class='exit-list-entry'>" + exit + "</option>";
    }

    const removeExit = function (e) {
        // Clear any other mode
        clearMode();
        // Remove exit(s) selected in the list
        options = document.getElementsByClassName("exit-list-entry");
        for (var i = options.length - 1; i >= 0; i--) {
            if (options[i].selected == true) {
                // Extract coordinates
                var coords = options[i].innerHTML.split("(")[1].slice(0, -2).split(",");
                var x = coords[0];
                var y = coords[1];
                // Remove the exit from the list
                options[i].remove();
            }
        }
        var selectedExitRemoved = true;
        for (var i = 0; i < agentExitList.length; i++) {
            if (agentExitList[i].innerHTML == agentExitsDropdown.value) {
                selectedExitRemoved = false;
            }
        }
        if (selectedExitRemoved) {
            enableElems([agentAddExitBtn]);
        }

        if (agentExitList.innerHTML == "") {
            disableElems([agentRemoveExitBtn]);
        }
    }

    const enableRemoveExitBtn = function (e) {
        // Clear any other mode
        clearMode();

        // Enable Fire Remove Button
        enableElems([agentRemoveExitBtn]);
    }

    const placeAgentMode = function (e) {
        // Check if all necessary information is there
        if (agentTypeDropdown.value == "None" ||
            (agentFitnessDropdown.value == "None" &&
            agentFitnessDropdown.disabled == false) ||
            (agentStrategyDropdown.value == "None" &&
            agentStrategyDropdown.disabled == false)) {
            alert("Please provide all required information to place the agent.");
        } else if (idTaken(agentNameInput.value)) {
            alert("The Name / ID provided is already in use. Please choose a new one.");
        } else {
            // Clear any other mode
            clearMode();
            clearSelection();

            placeAgentBtn.classList.add("active-btn");
            modes["placeAgentModeOn"] = true;
        }
    }



    const updateAgent = function (e) {
        // Locate the original agent data
        var oldID = selectedObj[0]["ID"]
        for (var i = 0; i < agentList.length; i++) {
            if (agentList[i]["ID"] == oldID) {
                agent = agentList[i];
            }
        }

        // Check for any text in 'Name / ID' to update any changes
        if (agentNameInput.value != "") {
            var id = (' ' + agentNameInput.value).slice(1);
        } else {
            var id = (' ' + agentNameInput.placeholder).slice(1);
        }

        //Check any new name against existing ones
        if (id != oldID && idTaken(id)) {
            alert("The Name / ID provided is already in use. Please choose a new one.");
            return;
        }

        // Create an array of known exits to update any changes
        var exitArray = [];
        for (var i = 0; i < agentExitList.length; i++) {
            var exit = agentExitList[i].innerHTML.split(" ");
            var exitName = exit[0];
            var exitCoords = exit[1].slice(1,-1).split(",");
            var x = exitCoords[0];
            var y = exitCoords[1];
            exitArray.push([exitName, x, y]);
        }

        // Update other parameters
        agent["type"] = agentTypeDropdown.value;
        agent["ID"] = id;
        agent["knownExits"] = exitArray;
        agent["preferredStrategy"] = agentStrategyDropdown.value;
        agent["fitness"] = agentFitnessDropdown.value;

        // Send updates to the model, refresh visuals and reselect agent
        updateAgents();
        send({"type": "check_for_obj",
                      "object": "Agent",
                      "x": agent["x"].toString(),
                      "y": agent["y"].toString()});
    }

    const deleteAgent = function (e) {
        clearSelection();
        id = selectedObj[0]["ID"]
        for (var i = 0; i < agentList.length; i++) {
            if (agentList[i]["ID"] == id) {
                var x = agentList[i]["x"];
                var y = agentList[i]["y"];
                if (["Adult", "Elderly", "Disabled"].includes(agentList[i]["type"])) {
                    var type = "Adult";
                } else {
                    var type = "Child";
                }
                agentList.splice(i, 1);
                updateAgents();
                break;
            }
        }

        // Update GUI if no agents left
        if (agentList.length == 0) {
            disableElems([runBtn]);
        }

        // Remove any mentions of the agent from guardian lists of children
        for (var i = 0; i < agentList.length; i++) {
            if (agentList[i]["type"] == "Child") {
                for (var j = 0; j < agentList[i]["guardians"].length; j++) {
                    if (agentList[i]["guardians"][j] == id) {
                        agentList[i]["guardians"].splice(j, 1);
                    }
                }
            }
        }
    }

    const addGuardianMode = function (e) {
        // Clear any other mode
        clearMode();

        agentAddGuardianBtn.classList.add("active-btn");
        modes["addGuardianModeOn"] = true;

    }

    const removeGuardian = function (e) {
        // Clear any other mode
        clearMode();
        // Remove guardian(s) selected in the list
        options = document.getElementsByClassName("guardian-list-entry");
        console.log(options.length)
        for (var i = (options.length - 1); i >= 0; i--) {
            console.log(i)
            console.log(options[i])
            if (options[i].selected == true) {
                // Extract IDs
                var id = options[i].innerHTML;
                // Remove the exit from the list
                options[i].remove();
                // If an existing child is selected, remove the guardian from that child's guardian list
                if (selectedObj.length > 0) {
                    for (var j = 0; j < selectedObj[0]["guardians"].length; j++) {
                        if (selectedObj[0]["guardians"][j] == id) {
                            selectedObj[0]["guardians"].splice(j, 1)
                        }
                    }
                }
            }
        }

        if (agentGuardianList.innerHTML == "") {
            disableElems([agentRemoveGuardianBtn]);
        }

    }

    const enableRemoveGuardianBtn = function (e) {
        // Clear any other mode
        clearMode();

        // Enable Fire Remove Button
        enableElems([agentRemoveGuardianBtn]);

    }



    /*
     * Results
     */

    /*
     *  Execution buttons etc.
     */

    // Function that starts a single run of the simulation
    const startSingleRun = function (e) {
        clearMode();
        // Check if all the required input was provided

        if (timeLimitEnabled) {
            timeLimit = Math.round(timeLimitInput.value * 60 * 4);
            if (timeLimit == null || timeLimit == 0) {
                alert("Time limit enabled, but no value or incorrect value provided.");
                return;
            } else if (timeLimit > 60 * 60 * 4) {
                alert("Maximum time limit is 60 minutes.");
                return;
            }
        }

        // Update the GUI
        enableElems([resultsBtn]);
        disableElems([envDropdown, singleModeBtn, batchModeBtn, generateAgentsBtn, placeAgentBtn]);
        runBtn.classList.add("hidden");
        stopBtn.classList.remove("hidden");
        timer.classList.remove("hidden");
        if (timeLimit != null) {
            timer.classList.remove("inactive");
        }
        // Remember the enabled settings and disable the GUI
        for (var i = 0; i < settingElems.length; i++) {
            if (settingElems[i].disabled == false) {
                enabledSettings.push(settingElems[i]);
                settingElems[i].disabled = true;
            }
        }

        // Update the 'initial parameters' in results tab

        populationCount = agentList.length;
        populationDensity = Math.round(populationCount/currentEnvArea * 1000) / 1000;

        adultCount = 0;
        elderlyCount = 0;
        disabledCount = 0;
        childrenCount = 0;
        fitCount = 0;
        familiarExitCount = 0;

        for (var i = 0; i < populationCount; i++) {
            if (agentList[i]["type"] == "Adult") {
                adultCount++;
                if (agentList[i]["fitness"] == "Fit") {
                    fitCount++;
                }
                if (agentList[i]["preferredStrategy"] == "familiarExit") {
                    familiarExitCount++;
                }
            } else if (agentList[i]["type"] == "Elderly") {
                elderlyCount++;
                if (agentList[i]["preferredStrategy"] == "familiarExit") {
                    familiarExitCount++;
                }
            } else if (agentList[i]["type"] == "Disabled") {
                disabledCount++;
                if (agentList[i]["preferredStrategy"] == "familiarExit") {
                    familiarExitCount++;
                }
            } else if (agentList[i]["type"] == "Child") {
                childrenCount++;
            }
        }

        populationFitness = Math.round(fitCount / adultCount * 100);
        strategyRatio = Math.round(familiarExitCount / (populationCount - childrenCount) * 100);

        var params = {"env": currentEnv,
                      "area": currentEnvArea,
                      "time_limit": timeLimit,
                      "fire": fireEnabled,
                      "agents": populationCount,
                      "density": populationDensity,
                      "adults": adultCount,
                      "elderly": elderlyCount,
                      "disabled": disabledCount,
                      "children": childrenCount,
                      "fitness": populationFitness,
                      "strategy": strategyRatio}
        printParams(params)

        // Start the simulation
        controller.start();

    }

    // Function that stops the simulation run
    const stopSimulation = function (e) {
        // Update the GUI
        if (currentMode == "Single") {
            enableElems([batchModeBtn, agentsIndivBtn]);
        } else {
            enableElems([singleModeBtn]);
        }
        runBtn.classList.remove("hidden");
        stopBtn.classList.add("hidden");
        timer.classList.add("hidden");
        timer.classList.add("inactive");

        // Re-enable the settings
        for (var i = enabledSettings.length - 1; i >= 0; i--) {
            elem = enabledSettings.pop();
            elem.disabled = false;
        }

        // Stop the simulation
        send({"type": "interrupt"});

    }

    // Function that limits input in schedule repetition count input
    const scheduleCountKeydown = function (e) {
        if(["+", "-", "."].includes(e.key)) {
            e.preventDefault();
        }
    }

    // Function that limits input in schedule repetition count input
    const scheduleCountChange = function (e) {
        if (scheduleCount.value > 10) {
            scheduleCount.value = 10;
        } else if (scheduleCount.value == 0) {
            scheduleCount.value = 1;
        } else {
            scheduleCount.value = Math.round(scheduleCount.value);
        }
    }

    // Add the current configuration to the schedule
    const addToSchedule = function (e) {

        // Check if all the required input was provided
        if (timeLimitEnabled) {
            timeLimit = Math.round(timeLimitInput.value * 60 * 4);
            if (timeLimit == null || timeLimit == 0) {
                alert("Time limit enabled, but no value or incorrect value provided.");
                return;
            } else if (timeLimit > 60 * 60 * 4) {
                alert("Maximum time limit is 60 minutes.");
                return;
            }
        }

        if (!useDensity) {
            populationCount = populationNumberInput.value;
            if (populationCount == null || populationCount == 0) {
                alert("No value or incorrect value for number of agents provided.");
                disableElems([runBtn]);
                var trig = new Event('click');
                agentsBatchBtn.dispatchEvent(trig);
                return;
            } else if (populationCount > (currentEnvArea * 1.7)) {
                alert("Specified agent number is too high. Max. number for this environment is "
                    + Math.floor(currentEnvArea * 1.7) + "\n\n (Based on population density of 1.7 person/sqm.)");
                disableElems([runBtn]);
                return;
            } else if (populationCount > 999) {
                alert("Maximum population size is 999 agents.");
                disableElems([runBtn]);
                return;
            }
            populationDensity = Math.round(populationCount/currentEnvArea * 1000) / 1000;
        } else {
            populationDensity = Number.parseFloat(populationDensityInput.value).toPrecision(4);
            populationCount = Math.round(populationDensityInput.value * currentEnvArea);
            if (populationCount == null || populationCount == 0) {
                alert("No value or incorrect value for occupation density provided.");
                disableElems([runBtn]);
                return;
            } else if (populationDensity > 1.7) {
                alert("Specified occupation density is too high. Max. allowed density is 1.7 person/sqm.");
                disableElems([runBtn]);
                return;
            }
        }

        // Update the GUI
        enableElems([resultsBtn]);

        // Update the 'initial parameters' in results tab
        elderlyCount = Math.round(elderlyPercentage / 100 * populationCount);
        disabledCount = Math.round(disabledPercentage / 100 * populationCount);
        childrenCount = Math.round(childrenPercentage / 100 * populationCount);

        // Add a schedule entry
        var run = {"finished": false,
                   "deleted": false,
                   "env": currentEnv,
                   "area": currentEnvArea,
                   "time_limit_enabled": timeLimitEnabled,
                   "time_limit": timeLimit,
                   "fire": fireEnabled,
                   "agents": parseInt(populationCount),
                   "density": populationDensity,
                   "adults": populationCount - (elderlyCount + disabledCount + childrenCount),
                   "elderly": elderlyCount,
                   "disabled": disabledCount,
                   "children": childrenCount,
                   "fitness": populationFitness,
                   "strategy": strategyRatio,
                   "results": null}

        printParams(run);

        var runCount = parseInt(scheduleCount.value);
        var firstRunNumber = schedule.length;

        var dataRuns = []
        for (var i = 0; i < runCount; i++) {
            dataRuns.push(firstRunNumber + i)
            schedule.push({...run})
        }

        scheduleTableEntry = "<tr class='schedule-row' data-runs='" + dataRuns + "'>"
        if (runCount == 1) {
            scheduleTableEntry += "<td></td>";
        } else {
            scheduleTableEntry += "<td>▶</td>";
        }
        scheduleTableEntry += "<td>" + runCount + "</td>";
        scheduleTableEntry += "<td>" + currentEnv + "</td>";
        if (timeLimit > 0) {
            scheduleTableEntry += "<td>" + stepsToTime(timeLimit) + "</td>";
        } else {
            scheduleTableEntry += "<td>-</td>";
        }
        if (fireEnabled) {
            scheduleTableEntry += "<td>" + "✔" + "</td>";
        } else {
            scheduleTableEntry += "<td>" + "✘" + "</td>";
        }
        scheduleTableEntry += "<td>" + populationCount + "</td>";
        scheduleTableEntry += "<td>" + (populationCount - (elderlyCount + disabledCount + childrenCount)).toString() + "</td>";
        scheduleTableEntry += "<td>" + elderlyCount + "</td>";
        scheduleTableEntry += "<td>" + disabledCount + "</td>";
        scheduleTableEntry += "<td>" + childrenCount + "</td>";
        scheduleTableEntry += "<td>" + populationFitness + "%</td>";
        if (strategyRatio >= 50) {
            scheduleTableEntry += "<td>" + "Go to a familiar exit (" + strategyRatio + "%)" + "</td></tr>";
        } else {
            scheduleTableEntry += "<td>" + "Follow exit signs (" + (100 - strategyRatio).toString() + "%)" + "</td></tr>";
        }
        scheduleBody.innerHTML += scheduleTableEntry

        // Add event listeners to select schedule rows
        scheduleRows = document.getElementsByClassName("schedule-row");
            for (var i = 0; i < scheduleRows.length; i++) {
                scheduleRows[i].addEventListener('click', selectScheduleRow);
            }
        scheduleSubRows = document.getElementsByClassName("schedule-sub-row");
            for (var i = 0; i < scheduleSubRows.length; i++) {
                scheduleSubRows[i].addEventListener('click', selectScheduleRow);
            }

        // Add event listener to expand/collapse rows with multiple runs
            for (var i = 0; i < scheduleRows.length; i++) {
                scheduleRows[i].firstChild.addEventListener('click', toggleScheduleRow);
            }

        // Enable the execution btn
        enableElems([scheduleExecBtn]);
    }

    // Start executing the schedule
    const executeSchedule = function (e) {

        // Determine the number of runs and the first run to be executed
        var nextRun = null;
        totalRuns = 0;
        currentRunCount = 1;
        for (var i = 0; i < schedule.length; i++) {
            if (!schedule[i]["deleted"]) {
                totalRuns++;
                schedule[i]["finished"] = false;
                schedule[i]["results"] = null;
                if (nextRun == null) {
                    nextRun = i;
                }
            }
        }

        // Update GUI
        scheduleAddBtn.classList.add("hidden");
        scheduleCount.classList.add("hidden");
        scheduleExecBtn.classList.add("hidden");
        scheduleTimes.classList.add("hidden")
        scheduleStopBtn.classList.remove("hidden");
        timer.classList.remove("hidden");

        // Remember the enabled settings and disable the remaining GUI elements
        disableElems([singleModeBtn, deleteScheduleEntryBtn])
        for (var i = 0; i < settingElems.length; i++) {
            if (settingElems[i].disabled == false) {
                enabledSettings.push(settingElems[i]);
                settingElems[i].disabled = true;
            }
        }

        // Initiate the first run in the schedule
        scheduleRunning = true;
        scheduleFinished = false;
        currentRun = nextRun;
        if (envLabel.innerHTML == schedule[currentRun]["env"]) {
            // If the same environment is used, continue
            startScheduleRun(currentRun);
        } else {
            // Send environment update request
            send({"type": "submit_param",
                  "param": "envName",
                  "value": schedule[currentRun]["env"]});
        }
    }

    // Function that stops the run of the schedule
    const stopSchedule = function (e) {

        // Stop the simulation
        scheduleRunning = false;
        scheduleFinished = true;
        send({"type": "interrupt"});

    }


    // Add event listeners to GUI elements

    // Environment selection
    envForm.addEventListener('submit', envSelectInput);
    envDropdown.addEventListener('change', envSelectDisable);

    // Mode selection
    singleModeBtn.addEventListener('click', modeSelectSingle);
    batchModeBtn.addEventListener('click', modeSelectBatch);

    // Batch schedule
    deleteScheduleEntryBtn.addEventListener('click', deleteScheduleEntry)

    // Settings
    for (var i = 0; i < settingsBtns.length; i++) {
        settingsBtns[i].addEventListener('click', menuSwitch);
    }

    // Simulation parameters
    timeLimitCheckbox.addEventListener('change', toggleTimeLimit);
    timeLimitInput.addEventListener('keydown', timeLimitKeydown);
    timeLimitInput.addEventListener('change', setTimeLimit);
    fireCheckbox.addEventListener('change', toggleFire);
    addFireBtn.addEventListener('click', addFireMode);
    removeFireBtn.addEventListener('click', removeFire);
    randomFireRadio.addEventListener('click', toggleRandomFire);
    placeFireRadio.addEventListener('click', toggleRandomFire);
    fireList.addEventListener('click', enableRemoveFireBtn);

    // Generate agents (batch)
    populationNumberRadio.addEventListener('click', togglePopulationSize);
    populationNumberInput.addEventListener('keydown', populationNumberKey);
    populationDensityRadio.addEventListener('click', togglePopulationSize);
    populationDensityInput.addEventListener('keydown', populationDensityKey);
    populationElderlyCheckbox.addEventListener('change', toggleElderly);
    populationElderlySlider.addEventListener('change', updateElderlyRatio);
    populationDisabledCheckbox.addEventListener('change', toggleDisabled);
    populationDisabledSlider.addEventListener('change', updateDisabledRatio);
    populationChildrenCheckbox.addEventListener('change', toggleChildren);
    populationChildrenSlider.addEventListener('change', updateChildrenRatio);
    populationFitnessSlider.addEventListener('change', updateFitnessRatio);
    populationStrategySlider.addEventListener('change', updateStrategyRatio);
    generateAgentsBtn.addEventListener('click', requestEmptyCells);

    // Add individual agents
    agentsIndivTab.addEventListener('change', updatePlaceBtn);
    agentTypeDropdown.addEventListener('change', toggleAgentOptions);
    agentExitsDropdown.addEventListener('change', exitSelected);
    agentAddExitBtn.addEventListener('click', addExit);
    agentRemoveExitBtn.addEventListener('click', removeExit);
    agentExitList.addEventListener('change', enableRemoveExitBtn);
    placeAgentBtn.addEventListener('click', placeAgentMode);
    updateAgentBtn.addEventListener('click', updateAgent);
    deleteAgentBtn.addEventListener('click', deleteAgent);
    agentAddGuardianBtn.addEventListener('click', addGuardianMode);
    agentRemoveGuardianBtn.addEventListener('click', removeGuardian);
    agentGuardianList.addEventListener('change', enableRemoveGuardianBtn);

    // Add listener for ESC to exit any active mode
    window.addEventListener('keydown', function (e) {
                if (e.key == "Escape") {
                    if (!modes["addGuardianModeOn"]) {
                        clearSelection();
                    }
                    clearMode();
                }
            });

    // Results

    // Execution buttons etc.
    runBtn.addEventListener('click', startSingleRun);
    stopBtn.addEventListener('click', stopSimulation);
    scheduleAddBtn.addEventListener('click', addToSchedule);
    scheduleCount.addEventListener('keydown', scheduleCountKeydown);
    scheduleCount.addEventListener('change', scheduleCountChange);
    scheduleExecBtn.addEventListener('click', executeSchedule);
    scheduleStopBtn.addEventListener('click', stopSchedule)
});

// Backward-Compatibility aliases
const control = controller;
const elements = vizElements;
