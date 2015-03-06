// Bar graph 

function BarGraph(run_data, error_data, anchor, type){
	
	
    // Remove old plot
    d3.select("#" + anchor).select("svg").remove();
    
    var svg_w;
	var svg_h;
	var w;
	var h;
	var padding;
	var trans;
	var barPadding = 1;
	var max_val;
	var barHeightFactor;
	var barWidth;
	var x;
	var y;
	var x_ticks;
	var y_ticks_div;
	var xAxis;
	var yAxis;
	var yAxisMinor;
	var chartContainer;
	var borderPath;
	var barsContainer;
	var right_label_text;
	var left_label_text;
	var xts; // x tick size
	var yts; // y tick size
	var font_size;

	var formatted_runs_data = Array.apply(null, new Array(24)).map(Number.prototype.valueOf,0);
	var formatted_error_data = Array.apply(null, new Array(24)).map(Number.prototype.valueOf,0);

	// Format data
	function formatData(){
		for (var i=0; i<run_data.length; i++){
			var loc = run_data[i][0] * (-1); 	// location
			var val = run_data[i][1]; 		// value
			formatted_runs_data[loc] = val;
		}
		for (var i=0; i<error_data.length; i++){
			var loc = error_data[i][0] * (-1);	// location
			var val = error_data[i][1];		// value
			formatted_error_data[loc] = val;
		}
	}					
	// Check for type of graph to generate
	function getTypeParameters(type){
		if (type === "detailed"){
			svg_w = 510;
			svg_h = 150;
			w = svg_w - 40;
			h = svg_h - 30;
			padding = {left: 15, right: 0, top: 10, bottom: 0};
			trans = {w: 25, h: 5}
			x_ticks = 12;
			y_ticks_div = 2;
			xts = 3;
			yts = 3;
			right_label_text = "last hour";
			left_label_text = "hrs";
			font_size = "10px";
		}
		else if (type === "summary"){
			svg_w = 200;
			svg_h = 50;
			w = svg_w - 25;
			h = svg_h - 10;
			padding = {left: 0, right: 2, top: 4, bottom: 0};
			trans = {w: 25, h: 5}
			x_ticks = 0;
			y_ticks_div;
			xts = 1;
			yts = 2;
			right_label_text = "";
			left_label_text = "";
			font_size = "9px";
		}
	}		
	// Calculate bar height factor
	function calcBarHeightFactor(){
		var max_run = Math.max.apply(Math, formatted_runs_data);
		var max_error = Math.max.apply(Math, formatted_error_data);
		max_val = Math.max(max_run, max_error);
		if (max_val === 0) max_val = 1;
		max_val = max_val * 1.1;		// buffer for nice look
		barHeightFactor = (h) / max_val;
	}
	// Calculate num y ticks
	function calcYticks(type){
		if (type === "summary"){
			var y_ticks_div_n = [1, 2, 5];
			y_ticks_div = y_ticks_div_n[i];
			do {
				for (var i=0; i<y_ticks_div_n.length; i++){
					y_ticks_div = y_ticks_div_n[i];
					if (max_val/y_ticks_div > 5){
						y_ticks_div_n[i] = y_ticks_div_n[i] * 10;
					}
					else break;
				}
			}
			while (max_val/y_ticks_div > 5);
		}
		else if (type === "detailed"){
			var y_ticks_div_n = [1, 2, 5];
			y_ticks_div = y_ticks_div_n[i];
			do {
				for (var i=0; i<y_ticks_div_n.length; i++){
					y_ticks_div = y_ticks_div_n[i];
					if (max_val/y_ticks_div > 10){
						y_ticks_div_n[i] = y_ticks_div_n[i] * 10;
					}
					else break;
				}
			}
			while (max_val/y_ticks_div > 10);
		}
	}
	// Calculate bar width
	function calcBarWidth(){
		barWidth = (w / formatted_runs_data.length);
	}

	formatData();
	getTypeParameters(type);
	calcBarHeightFactor();
	calcYticks(type);
	calcBarWidth();
    
	chart = d3.select("#" + anchor).append("svg")
			.attr("id", anchor + "_svg")
			.attr("width", svg_w)
			.attr("height", svg_h)
			.style("padding-left", padding.left + "px")
			.style("padding-right", padding.right + "px")
			.style("padding-top", padding.top + "px")
			.style("padding-bottom", padding.bottom + "px");
			
	chartContainer = chart.append("g") // because svg won't take transform attribute
			.attr("transform", "translate(" + trans.w + "," + trans.h + ")");
			
	barsContainer = chartContainer.append("g")
			.attr("class", anchor + "_bar_group");
			

	x = d3.scale.linear().range([w - barPadding, 0]);
	y = d3.scale.linear().range([h, 0]);
	x.domain([0, formatted_runs_data.length*(-1)]);
	y.domain([0, max_val]);
	xAxis = d3.svg.axis().scale(x).orient("bottom").ticks(x_ticks).tickSize(xts,xts);
	yAxis = d3.svg.axis().scale(y).orient("left").ticks(max_val/y_ticks_div).tickSize(yts,yts);
	yAxisMinor = d3.svg.axis().scale(y).orient("left").ticks(max_val/y_ticks_div);
	
			
	yGrid = chartContainer.append("g")
		.attr("class", "grid")
		.call(yAxisMinor
			.tickSize(-w + barPadding, 0, 0)
			.tickFormat("")
		)

	// Create error bars
	var errors = barsContainer.append("g")
			.attr("class", anchor + "_error_bars")
			.selectAll(".bars")
			.data(formatted_error_data)
			.enter()
			.append("rect")
			.attr("class", anchor + "_error_rect")
			.attr("x", function(d, i){
				return w - ((i+1) * barWidth); // start from the right
			})
			.attr("y", function(d){
				return h - (d * barHeightFactor);
			})
			.attr("width", barWidth - barPadding)
			.attr("height", function(d){
				return d * barHeightFactor;
			})
			.style("stroke", "#d62815")
			.style("stroke-width", "none")
			.style("shape-rendering", "crispEdges")
			.attr("fill", "#ED5B4B")
			.attr("opacity", "0.6");
		 
	// Create run bars 
	var runs = barsContainer.append("g")
			.attr("class", anchor + "_run_bars")
			.selectAll(".bars")
			.data(formatted_runs_data)
			.enter()
			.append("rect")
			.attr("class", anchor + "_runs_rect")
			.attr("x", function(d, i){
				return w - ((i+1) * barWidth); // start from the right
			})
			.attr("y", function(d){
				return h - (d * barHeightFactor)
			})
			.attr("width", barWidth - barPadding)
			.attr("height", function(d){
				return d * barHeightFactor;
			})
			.style("stroke", "#2f859b")
			.style("stroke-width", "none")
			.style("shape-rendering", "crispEdges")
			.attr("fill", "#4dafc9")
			.attr("opacity", "0.6");
			
	// Create bars that cover the 		 
	var placeholders = barsContainer.append("g")
			.attr("class", anchor + "_placeholder_bars")
			.selectAll(".bars")
			.data(formatted_runs_data)
			.enter()
			.append("rect")
			.attr("class", anchor + "_focus_rect")
			.attr("x", function(d, i){
				return  w - ((i+1) * barWidth); // start from the right
			})
			.attr("y", 1)
			.attr("width", barWidth - barPadding)
			.attr("height", h)
			.attr("fill", "#888")
			.attr("opacity", "0");

	d3.select("#" + anchor + "_svg g").append("g")
			.attr("class", "x axis")
			.attr("transform", "translate(0," + h + ")")
			.call(xAxis);
	d3.select("#" + anchor + "_svg g").append("g")
			.attr("class", "y axis")
			.call(yAxis);
			
						
	borderPath = chartContainer.append("g")
			.attr("class", "chart_border")
			.append("rect")
			.attr("x", 0)
			.attr("y", 0)
			.attr("height", h)
			.attr("width", w - barPadding)
			.style("stroke", "#000")
			.style("fill", "none")
			.style("stroke-width", "none")
			.style("shape-rendering", "crispEdges");
						
	rightLabel = chartContainer.append("text")
			.attr("class", "label")
			.attr("transform", "translate(" + (w-30) + ", " + (svg_h-5) + ")")
			.style("color", "black")
			.text(right_label_text);
	leftLabel = chartContainer.append("text")
			.attr("class", "label")
			.attr("transform", "translate(-5, " + (svg_h-5) + ")")
			.style("color", "black")
			.text(left_label_text);
			 
	d3.selectAll("text")
		.style("font-size", font_size);
		
	
	// Tooltip obj
	tooltip = d3.select("body")
					.append("text")
					.attr("class", "tooltip")
					.style("position", "absolute")
					.style("z-index", "2010")
					.style("visibility", "hidden")
					.style("color", "black")
					.style("font-size", font_size);

	d3.selectAll("." + anchor + "_focus_rect")
		.on("mouseover", function(d, i){
			mouseover(d, i, this); 
		})
		.on("mousemove", function(d, i){
			mousemove(d, i, this); 
		})
		.on("mouseout", function(d, i){ 
			mouseout(d, i, this); 
		});
		
	function mouseover(d, i, t){
		ith_child = parseInt(i+1); // iterator to start at 1 for css-type selector
		d3.select("." + anchor + "_runs_rect:nth-child(" + ith_child + ")").attr("opacity", "0.9");
		d3.select("." + anchor + "_error_rect:nth-child(" + ith_child + ")").attr("opacity", "0.7");
		return tooltip.style("visibility", "visible");
	}
	function mousemove(d, i, t){
		if (formatted_runs_data[i] == 0 && formatted_error_data[i] == 0){
			tooltip.style("visibility", "hidden");
		}
		else{
			tooltip.html("# of runs: " + formatted_runs_data[i] + 
				"<br># of errors: " + formatted_error_data[i]);
		}
		d3.event.stopPropagation();
		return tooltip.style("top", (d3.event.pageY-10)+"px")
						.style("left",(d3.event.pageX+10)+"px");
	}
	function mouseout(d, i, t){
		console.log("this is mouseout from bar");
		ith_child = parseInt(i+1); // iterator to start at 1 for css-type selector
		d3.select("." + anchor + "_runs_rect:nth-child(" + ith_child + ")").attr("opacity", "0.6");
		d3.select("." + anchor + "_error_rect:nth-child(" + ith_child + ")").attr("opacity", "0.6");
		return tooltip.style("visibility", "hidden");
	}
}
