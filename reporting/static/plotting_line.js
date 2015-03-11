// ********************************************** //
// ********* code for line plots **************** //
// ********************************************** //

function plot_1d(raw_data, anchor, options) {
    // Raw_data is fed in,
    // anchor is the dialog box, and options
    // are plot options.

    var color = '#0077cc';
    var marker_size = 2;
    var w;
    var h;
    var mod_psize;
    var margin = {top: 30, right: 15, bottom: 50, left: 45};
    var log_scale = options.log_scale;
    var grid = true;
    var x_label = "time elapsed [minutes]";
    var y_label = "";
    var title = "";
    var x;
    var y;
    var y_min;
    var y_max;
    var xAxis;
    var xAxisMinor;
    var yAxis;
    var yAxisMinor;
    var mouseY;
    var mouseX;

    var data = [];
    for (var i=0; i<raw_data.length; i++){
        if (log_scale == false || raw_data[i][1]>0 ) data.push(raw_data[i]);
    }
    
    var tid = $(".live_plots").parent().attr("id");

    w = options.psize.width;
    h = options.psize.height;
    w = w - margin.left - margin.right;
    h = h - margin.top - margin.bottom;
    mod_psize = {height: h, width: w};
    x = d3.scale.linear().range([0, mod_psize.width]);
    y = log_scale ? d3.scale.log().range([mod_psize.height, 0]).nice() : d3.scale.linear().range([mod_psize.height, 0]);
    
    y_min = d3.min(data, function(d) { return d[1]; }) // for a better display of a constant function
    y_max = d3.max(data, function(d) { return d[1]; })
    
    x.domain(d3.extent(data, function(d) { return d[0]; }));
    if ( y_min === y_max ){
        y.domain([y_min-1, y_max+1]);
    }
    else{
        y.domain([y_min, y_max]);
    }
    xAxis = d3.svg.axis().scale(x).orient("bottom").ticks(5).tickFormat(d3.format("6d"));
    xAxisMinor = d3.svg.axis().scale(x).orient("bottom").ticks(5).tickSize(3,3).tickSubdivide(0).tickFormat('');
    
    formatter = function(d) { if(d<1000000.0 && d>1e-3) {return d3.format("5.3g")(d);} else {return d3.format("5.1e")(d);}};
    if (log_scale == false) {
        yAxis = d3.svg.axis().scale(y).orient("left").ticks(4).tickFormat(formatter);
    } else {
        yAxis = d3.svg.axis().scale(y).orient("left").ticks(4, formatter);
    }
    // Remove old plot
    d3.select("#" + anchor).select("svg").remove();
    
    console.log("DEFAULT 1D: mod_psize.width: " + mod_psize.width + ", mod_psize.height: " + mod_psize.height);
    // Create svg element
    var svg = d3.select("#" + anchor).append("svg")
        .attr("class", "default_1d")
        .attr("id", anchor + "_svg")
        .attr("width", mod_psize.width + margin.left + margin.right)
        .attr("height", mod_psize.height + margin.top + margin.bottom)
        .append("g")
        .attr("id", anchor + "_g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
        
    svg.append("g").attr("class", "x axis")
                   .attr("transform", "translate(0," + mod_psize.height + ")")
                   .call(xAxis);
    svg.append("g").attr("class", "x axis")
                   .attr("transform", "translate(0," + mod_psize.height + ")")
                   .call(xAxisMinor);
    svg.append("g").attr("class", "y axis").call(yAxis)
    
    // Create X axis label
    svg.append("text")
       .attr("x", mod_psize.width)
       .attr("y",  mod_psize.height+40)
       .attr("font-size", "11px")
       .style("text-anchor", "end")
       .text(x_label);

    // Create Y axis label
    svg.append("text")
       .attr("transform", "rotate(-90)")
       .attr("y", 10-margin.left)
       .attr("x", 40-margin.top)
       .attr("dy", "1em")
       .style("text-anchor", "end")
       .text(y_label);

    // Create title
    svg.append("text")
       .attr("x", mod_psize.width/2.0 )
       .attr("y",  -10)
       .attr("font-size", "16px")
       .style("text-anchor", "middle")
       .text(title);

    // Make or remove grid
    if (grid == true){
        // If grid checkbox is checked, add grid
        xGrid = svg.append("g")
            .attr("class", "grid")
            .attr("transform", "translate(0," + mod_psize.height + ")")
            .call(xAxis
                .tickSize(-mod_psize.height, 0, 0)
                .tickFormat("")
            )
        yGrid = svg.append("g")
            .attr("class", "grid")
            .call(yAxis
                .tickSize(-mod_psize.width, 0, 0)
                .tickFormat("")
            )
    }
    else if (grid == false && typeof xGrid !== 'undefined' && typeof yGrid !== 'undefined'){
        // If grid checkbox is unchecked and a grid already exists, remove grid
        svg.select("xGrid").remove();
        svg.select("yGrid").remove();
    }

    // Interpolate
    svg.select("path").remove();
    var interp_line = d3.svg.line()
                        .interpolate("step-before")
                        .x(function(d) { return x(d[0]); })
                        .y(function(d) { return y(d[1]); });
    svg.append("path")
       .attr("d", interp_line(data))
       .attr("fill", "none")
       .attr("stroke", "#0077cc")
       .attr("stroke-width", 2.5)
       .style("opacity", 0.5);

    // Tooltip obj
    var tooltip = d3.select("body")
                    .append("text")
                    .attr("class", "tooltip")
                    .style("position", "absolute")
                    .style("z-index", "2010")
                    .style("visibility", "hidden")
                    .style("color", "black");

    // Circle obj with colored outline
    var circle_ol = d3.select("#" + anchor + "_g")
                        .append("circle")
                        .attr("cx", "0")
                        .attr("cy", "0")
                        .attr("r", marker_size+5)
                        .style("z-index", "2020")
                        .style("visibility", "hidden")
                        .style("fill", "white")
                        .style("fill-opacity", "0")
                        .style("stroke", color);

    // Points obj with data
    var points = svg.selectAll("circle")
                    .data(data)
                    .enter();

    // Little points
    var little_pt = points.append('circle')
                          .attr("class", "datapt")
                          .attr("cx", function(d) { return x(d[0]); })
                          .attr("cy", function(d) { return y(d[1]); })
                          .attr("r", marker_size)
                          .style('fill', color);

    // This is used to get coordinates on mouseover
    var circle_ar = points.append("circle")
                          .attr("class", anchor + "_focus")
                          .attr("cx", function(d) { return x(d[0]); })
                          .attr("cy", function(d) { return y(d[1]); })
                          .attr("r", marker_size+5)
                          .style("fill", "white")
                          .style("fill-opacity", "0");

    // Get data values on hover event
    svg.selectAll("." + anchor + "_focus")
       .on("mouseover", function(d){ mouseover(d); })
       .on("mousemove", function(d){ mousemove(d); })
       .on("mouseout", function(d){ mouseout(d); });
    
    function mouseover(d){
        mouseY = 0;
        mouseX = 0;
        circle_ol.attr("cx", x(d[0]))
                 .attr("cy", y(d[1]))
                 .style("visibility", "visible");
        tooltip.style("visibility", "visible");
        if(window.Event && document.captureEvents)
        document.captureEvents(Event.MOUSEOVER);
        document.onmouseover = getMousePos;
        tooltip.text(d3.round(d[0],1) + ", " + d3.format("6.3g")(d[1]));
        tooltip.style("top", (mouseY-10)+"px")
               .style("left",(mouseX+10)+"px");
    }
    function mousemove(d){
        circle_ol.attr("cx", x(d[0]))
                 .attr("cy", y(d[1]))
                 .style("visibility", "visible");
        tooltip.style("visibility", "visible");
        if(window.Event && document.captureEvents)
        document.captureEvents(Event.MOUSEMOVE);
        document.onmousemove = getMousePos;
        tooltip.text(d3.round(d[0],1) + ", " + d3.format("6.3g")(d[1]));
        tooltip.style("top", (mouseY-10)+"px")
               .style("left",(mouseX+10)+"px");
    }
    function mouseout(d){
        circle_ol.style("visibility", "hidden");
        return tooltip.style("visibility", "hidden");
    }
    
    function getMousePos(e){
        if (!e) var e = window.event||window.Event;

        if('undefined'!=typeof e.pageX){
            mouseX = e.pageX;
            mouseY = e.pageY;
        }
        else {
            mouseX = e.clientX + document.body.scrollLeft;
            mouseY = e.clientY + document.body.scrollTop;
        }
    }
    
}
