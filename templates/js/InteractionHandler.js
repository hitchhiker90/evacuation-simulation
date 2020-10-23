/**
COMP702 - Evacuation simulation
Lukasz Przybyla
Handles the creation of an interaction layer that displays
 the tooltips with the parameters of agents / environment components.
A modified version of the default Mesa's InteractionHandler.js.
 */

/**
Mesa Visualization InteractionHandler
====================================================================

This uses the context of an additional canvas laid overtop of another canvas
visualization and maps mouse movements to agent position, displaying any agent
attributes included in the portrayal that are not listed in the ignoredFeatures.

**/


var InteractionHandler = function(width, height, gridWidth, gridHeight, ctx){

    // Find cell size:
    cellWidth = Math.floor(width / gridWidth);
    cellHeight = Math.floor(height / gridHeight);

    const lineHeight = 12;

        // list of standard rendering features to ignore (and key-values in the portrayal will be added )
        const ignoredFeatures = [
            'Shape',
            'Filled',
            'Color',
            'r',
            'x',
            'y',
            'w',
            'h',
            'width',
            'height',
            'heading_x',
            'heading_y',
            'stroke_color',
            'text_color',
            'Layer',
            'scale'
        ];

    // Set a variable to hold the lookup table and make it accessible to draw scripts
    var mouseoverLookupTable = this.mouseoverLookupTable = buildLookupTable(gridWidth, gridHeight);
    function buildLookupTable(gridWidth, gridHeight){
        var lookupTable;
        this.init = function(){
            lookupTable = [...Array(gridHeight).keys()].map(i => Array(this.gridWidth));
        }

        this.set = function(x, y, value){
            if(lookupTable[y][x])
                lookupTable[y][x].push(value);
            else
                lookupTable[y][x] = [value];
        }

        this.get = function(x, y){
            if(lookupTable[y])
                return lookupTable[y][x] || []
                return [];
        }

        return this;
    }

    var coordinateMapper;
    this.setCoordinateMapper = function(mapperName){
        if(mapperName === "hex"){
            coordinateMapper = function(event){
            const x = Math.floor(event.offsetX/this.cellWidth);
            const y = (x % 2 === 0)
                ? Math.floor(event.offsetY/this.cellHeight)
                : Math.floor((event.offsetY - this.cellHeight/2 )/this.cellHeight)
            return {x: x, y: y};
        }
        return;
        }

        // default coordinate mapper for grids
        coordinateMapper = function(event){
            return {
                x: Math.floor(event.offsetX/this.cellWidth),
                y: Math.floor(event.offsetY/this.cellHeight)
            };
        };
    };

    this.setCoordinateMapper('grid');


    // wrap the rect styling in a function
    function drawTooltipBox(ctx, x, y, width, height){
        ctx.fillStyle = "#F0F0F0";
        ctx.beginPath();
        ctx.shadowOffsetX = -3;
        ctx.shadowOffsetY = 2;
        ctx.shadowBlur = 6;
        ctx.shadowColor = "#33333377";
        ctx.rect(x, y, width, height);
        ctx.fill();
        ctx.shadowColor = "transparent";
    }

    var listener; var tmp
    this.updateMouseListeners = function(portrayalLayer, final){

        tmp = portrayalLayer

        // Remove the prior event listener to avoid creating a new one every step
        ctx.canvas.removeEventListener("mousemove", listener);

        if (final) {
            return this;
        }

        // define the event listener for this step
        listener = function(event){
            // clear the previous interaction
            ctx.clearRect(0, 0, width, height);

            // map the event to x,y coordinates
            const position = coordinateMapper(event);
            const yPosition = Math.floor(event.offsetY/this.cellHeight);
            const xPosition = Math.floor(event.offsetX/this.cellWidth);

            // look up the portrayal items the coordinates refer to and draw a tooltip
            var count = 0;
            mouseoverLookupTable.get(position.x, position.y).forEach((portrayalIndex, nthAgent) => {

                const agent = portrayalLayer[portrayalIndex];
                    const features = Object.keys(agent).filter(k => ignoredFeatures.indexOf(k) < 0);
                const textWidth = Math.max.apply(null, features.map(k => ctx.measureText(`${k}: ${agent[k]}`).width));
                    const textHeight = features.length * lineHeight;
                    const y = Math.max(lineHeight * 2, Math.min(height - textHeight, event.offsetY - textHeight/2));
                const rectMargin = 2 * lineHeight;
                var x = 0;
                var rectX = 0;

                if(event.offsetX < width/2){
                    x = event.offsetX + rectMargin + nthAgent * (textWidth + rectMargin);
                    ctx.textAlign = "left";
                    rectX = x - rectMargin/2;
                } else {
                    x = event.offsetX - rectMargin - nthAgent * (textWidth + rectMargin + lineHeight );
                    ctx.textAlign = "right";
                    rectX = x - textWidth - rectMargin/2;
                }

                // draw a background box
                drawTooltipBox(ctx, rectX, y - rectMargin, textWidth + rectMargin, textHeight + rectMargin);

                // set the color and draw the text
                ctx.fillStyle = "black";
                    features.forEach((k,i) => {
                    ctx.fillText(`${k}: ${agent[k]}`, x, y + i * lineHeight)
                    })
            })

        };
        ctx.canvas.addEventListener("mousemove", listener);
    };

    return this;
}
