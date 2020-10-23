/**
COMP702 - Evacuation simulation
Lukasz Przybyla
JS Script that handles the creation, placement and sizing
 of the HTML canvas elements.
A modified version of the default Mesa's CanvasModule.js.
 */
var CanvasModule = function(canvas_width, canvas_height, grid_width, grid_height) {
	// Create the element
	// ------------------

	// Get the cell size
	cellSize = canvas_width / grid_width;

	// Create the tag with absolute positioning :
	var background_canvas_tag = `<canvas width="${canvas_width}" height="${canvas_height}" 
						class="single-mode-el world-grid" id="background-canvas"/>`

	var canvas_tag = `<canvas width="${canvas_width}" height="${canvas_height}" 
						class="single-mode-el world-grid" id="canvas"/>`

	var interaction_handler_tag = `<canvas width="${canvas_width}" height="${canvas_height}" 
									class="single-mode-el world-grid" id="interaction-handler"/>`

	var loading_bckgrnd_tag = `<div class="single-mode-el" id="loading-bckgrnd"></div>`

	var loading_tag = `<div class="single-mode-el" id="loading-info">
							<p>PREPARING THE ENVIRONMENT</p>
							<p id="loading-percents"></p>
						<div class="single-mode-el loader"></div></div>`

	var parent_div_tag = '<div style="height:' + canvas_height + 'px; width:'
							+ canvas_width + 'px;" class="single-mode-el world-grid-parent" '
							+ 'id="canvas-parent" ' + 'oncontextmenu="return false;"></div>'

	// Append it to body:
	var background_canvas = $(background_canvas_tag)[0];
	var canvas = $(canvas_tag)[0];
	var interaction_canvas = $(interaction_handler_tag)[0];
	var parent = $(parent_div_tag)[0];
	var loading_bckgrnd = $(loading_bckgrnd_tag)[0];
	var loading_info = $(loading_tag)[0];

	$("#sim-visuals").append(parent);
	parent.append(background_canvas);
	parent.append(canvas);
	parent.append(interaction_canvas);
	parent.append(loading_bckgrnd);
	$("#sim-visuals").append(loading_info);

	// Create the context and a GridVisualization instance for the background
	var background_context = background_canvas.getContext("2d");
	var backgroundDraw = new GridVisualization(canvas_width, canvas_height, grid_width, grid_height, background_context, null);

	// Create the context for the active canvas layer
	var context = canvas.getContext("2d");

	// Create an interaction handler
	var interactionHandler = new InteractionHandler(canvas_width, canvas_height, grid_width, grid_height, interaction_canvas.getContext("2d"));

	// Create a GridVisualization instance for the active canvas layer
	var canvasDraw = new GridVisualization(canvas_width, canvas_height, grid_width, grid_height, context, interactionHandler);

	var backgroundDrawn = false;

	this.init = function(data, final) {
		canvasDraw.resetCanvas();
		for (var layer in data) {
			if (layer > 1) {
				canvasDraw.drawLayer(data[layer], final);
			} else {
				if (!backgroundDrawn) {
					backgroundDraw.drawLayer(data[layer], final);
				}
			}
		};
		if (!backgroundDrawn) {
			backgroundDraw.drawGridLines("#eee");
		}
		backgroundDrawn = true;
	};

	this.render = function(data, final) {
		canvasDraw.resetCanvas();
		for (var layer in data) {
			if (layer > 1) {
				canvasDraw.drawLayer(data[layer], final);
			}
		};
	};

	this.reset = function(canvas_width = 0, canvas_height = 0, grid_width = 0, grid_height = 0) {
		if (canvas_height + canvas_width + grid_height + grid_width == 0) {
			canvasDraw.resetCanvas();
			backgroundDraw.resetCanvas();
		} else {
			var newInteractionHandler = new InteractionHandler(canvas_width, canvas_height, grid_width, grid_height, interaction_canvas.getContext("2d"));
      		backgroundDraw = new GridVisualization(canvas_width, canvas_height, grid_width, grid_height, background_context, null);
			backgroundDraw.resetCanvas();
      		canvasDraw = new GridVisualization(canvas_width, canvas_height, grid_width, grid_height, context, newInteractionHandler);
			canvasDraw.resetCanvas();
		}
		backgroundDrawn = false;
	};
};
