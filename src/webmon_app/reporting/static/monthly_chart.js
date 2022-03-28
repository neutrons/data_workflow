// Bar graph

function MonthlyGraph(run_data, anchor, type){

    // Remove old plot
    d3.select("#" + anchor).select("svg").remove();

    var svg_w;
    var svg_h;
    var w;
    var h;
    var padding;
    var trans;
    var barPadding = 0;
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

    var formatted_runs_data = Array.apply(null, new Array(30)).map(Number.prototype.valueOf,0);
    run_data.shift();

    // Format data
    function formatData(){
        for (var i=0; i<run_data.length; i++){
            var loc = new Date(run_data[i][0]); // date
            var val = run_data[i][1];        // value
            formatted_runs_data[i] = [loc, val];
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
            x_ticks = 10;
            y_ticks_div = 2;
            xts = 2;
            yts = 3;
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
        max_val = d3.max(formatted_runs_data, function(d){return d[1]});
        if (max_val === 0) max_val = 1;
        max_val = max_val * 1.1; // buffer for nice look
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
                          .attr("transform", "translate(" +
                                  trans.w + "," +
                                  trans.h + ")");

    barsContainer = chartContainer.append("g")
                                  .attr("class", anchor + "_bar_group");


    x = d3.time.scale().range([w - barPadding, 0]);
    y = d3.scale.linear().range([h, 0]);
    x.domain([d3.time.month.offset(formatted_runs_data[0][0], 1),
              d3.time.month.offset(formatted_runs_data[formatted_runs_data.length-1][0], 0)]);
    y.domain([0, max_val]);
    xAxis = d3.svg.axis().scale(x).orient("bottom").ticks(d3.time.months, 3).tickSize(xts,xts);
    yAxis = d3.svg.axis().scale(y).orient("left").ticks(max_val/y_ticks_div).tickSize(yts,yts);
    yAxisMinor = d3.svg.axis().scale(y).orient("left").ticks(max_val/y_ticks_div);

    yGrid = chartContainer.append("g")
                          .attr("class", "grid")
                          .call(yAxisMinor
                            .tickSize(-w + barPadding, 0, 0)
                            .tickFormat("")
                          )

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
            .attr("y", function(d, i){
                return h - (d[1] * barHeightFactor)
            })
            .attr("width", barWidth - barPadding)
            .attr("height", function(d, i){
                return d[1] * barHeightFactor;
            })
            .style("stroke", "#777777")
            .style("stroke-width", "none")
            .style("shape-rendering", "crispEdges")
            .attr("fill", "#eeeeee")
            .attr("opacity", "0.6");

    // Create transparent bars that cover the error and run bars
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

    var tooltip_date_format = d3.time.format("%b %Y");
    function mouseover(d, i, t){
        ith_child = parseInt(i+1); // iterator to start at 1 for css-type selector
        d3.select("." + anchor + "_runs_rect:nth-child(" + ith_child + ")").attr("opacity", "0.95");
        return tooltip.style("visibility", "visible");
    }
    function mousemove(d, i, t){
        if (formatted_runs_data[i] == 0){
            tooltip.style("visibility", "hidden");
        }
        else{
            tooltip.html(tooltip_date_format(formatted_runs_data[i][0]) +
				"<br># of runs: " + formatted_runs_data[i][1]);
        }
        d3.event.stopPropagation();
        return tooltip.style("top", (d3.event.pageY-10)+"px")
                        .style("left",(d3.event.pageX+10)+"px");
    }
    function mouseout(d, i, t){
        ith_child = parseInt(i+1); // iterator to start at 1 for css-type selector
        d3.select("." + anchor + "_runs_rect:nth-child(" + ith_child + ")").attr("opacity", "0.6");
                return tooltip.style("visibility", "hidden");
    }
}
