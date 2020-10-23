/**
COMP702 - Evacuation simulation
Lukasz Przybyla
JS Script that controls the dragging of the environment
 representation and placing / selecting objects on click
 */
var dragCanvas = function (e) {
    const env = document.getElementById('interaction-handler');

    let currPos = {top: 0, left: 0};
    let currMouse = {x: 0, y: 0};

    const mouseDownHandler = function(e) {
        env.style.cursor = 'grab';

        currPos = {
            left: env.parentElement.parentElement.scrollLeft,
            top: env.parentElement.parentElement.scrollTop
        }
        currMouse = {
            x: e.clientX,
            y: e.clientY
        }

        document.addEventListener('mousemove', mouseMoveHandler);
        document.addEventListener('mouseup', mouseUpHandler);
    }

    const mouseMoveHandler = function(e) {
        env.style.cursor = 'grab';

        env.style.cursor = 'grabbing';
        env.style.userSelect = 'none';

        const dx = e.clientX - currMouse.x;
        const dy = e.clientY - currMouse.y;

        env.parentElement.parentElement.scrollLeft = currPos.left - dx;
        env.parentElement.parentElement.scrollTop = currPos.top - dy;
    };

    const mouseUpHandler = function(e) {
        env.style.cursor = 'auto';
        if (Math.abs(e.clientX - currMouse.x) < 15 && Math.abs(e.clientY - currMouse.y) < 15) {
            canvasParams = env.getBoundingClientRect();
            gridX = Math.floor((e.clientX - canvasParams["x"]) / cellSize);
            gridY = Math.floor((canvasParams["bottom"] - e.clientY) / cellSize);
            if (modes["placeFireModeOn"]) {
                // Send a message to check if a fire can be added in indicated cell
                send({"type": "place_obj",
                      "object": "Fire",
                      "x": gridX.toString(),
                      "y": gridY.toString()});
            } else if (modes["placeAgentModeOn"]) {
                // Send a message to check if an agent can be added in indicated cell
                send({"type": "place_obj",
                      "object": "Agent",
                      "x": gridX.toString(),
                      "y": gridY.toString()});
            } else if (modes["addGuardianModeOn"]) {
                // Check if an Adult-type agent is present in the indicated cell
                send({"type": "check_for_obj",
                      "object": "Adult",
                      "x": gridX.toString(),
                      "y": gridY.toString()});
            } else if (currentEnv != "None") {
                // Check if an agent is present in the indicated cell to select them
                send({"type": "check_for_obj",
                      "object": "Agent",
                      "x": gridX.toString(),
                      "y": gridY.toString()});
            }
        }

        document.removeEventListener('mousemove', mouseMoveHandler);
        document.removeEventListener('mouseup', mouseUpHandler);
    };

    env.addEventListener('mousedown', mouseDownHandler);
};


document.addEventListener('DOMContentLoaded', dragCanvas(this));