

function Plot_1d(raw_data, anchor) {

		//this.user_options = user_options;
    var self = this;

    self.user_options = user_options;

    //console.log(this.user_options.marker_size_focus);

    var color = this.user_options.color;
    var marker_size = this.user_options.marker_size;
    var marker_size_focus = this.user_options.marker_size_focus;
    var path_stroke_width = this.user_options.path_stroke_width;
    var w;
    var h;
    var mod_psize = {
        height: 244,
        width: 360
    };
    var margin = {
        top: 30,
        right: 15,
        bottom: 50,
        left: 65
    };
    var log_scale = this.user_options.log_scale;
    var grid = this.user_options.grid;
		var append_grid;
    var translate_val = [0, 0];
    var scale_val = 1;
    var x_label = "Energy transfer (meV)";
    var y_label = "Intensity";
    var title_label = "";
    var x_label_align = "right";
    var y_label_align = "right";
    var title_label_align = "center";
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

    for (var i = 0; i < raw_data.length; i++) {
        if (log_scale == false || raw_data[i][1] > 0) data.push(raw_data[i]);
    }

    this.get_scale = function(log_scale) {
        x = d3.scale
            .linear()
            .range([0, mod_psize.width]);
        y = log_scale ? d3.scale
            .log()
            .range([mod_psize.height, 0])
            .nice() :
            d3.scale
            .linear()
            .range([mod_psize.height, 0]);
    }
    self.get_scale(log_scale);

    this.get_domain = function() {
        y_min = d3.min(data, function(d) {
                return d[1];
            }) // for a better display of a constant function
        y_max = d3.max(data, function(d) {
            return d[1];
        })
        x.domain(d3.extent(data, function(d) {
            return d[0];
        }));
        if (y_min === y_max) {
            y.domain([y_min - 1, y_max + 1]);
        }
        else {
            y.domain([y_min, y_max]);
        }
    }
    self.get_domain();

    formatter = function(d) {
        if (d < 1000000.0 && d > 1e-3) {
            return d3.format("5.3g")(d);
        }
        else {
            return d3.format("5.3g")(d);
            //return d3.format("5.1e")(d);
        }
    };
		this.get_axes= function(){
		    xAxis = d3.svg
		        .axis()
		        .scale(x)
		        .orient("bottom")
		        .ticks(5)
		        .tickSize(-mod_psize.height)
		        .tickFormat(d3.format("6d"));

		    if (log_scale == false) {
		        yAxis = d3.svg
		            .axis()
		            .scale(y)
		            .orient("left")
		            .ticks(4)
		            .tickSize(-mod_psize.width)
		            .tickFormat(formatter);
		    }
		    else {
		        yAxis = d3.svg
		            .axis()
		            .scale(y)
		            .orient("left")
		            .ticks(4, formatter)
		            .tickSize(-mod_psize.width);
		    }
		}
		self.get_axes();



		this.scale_objects = function() {
				scale_factor = parseFloat(d3.transform(d3.select("path")
								.attr("transform"))
						.scale[0]);
				d3.select("path")
						.attr("stroke-width", path_stroke_width / scale_factor);
				d3.selectAll(".datapt")
						.attr("r", (path_stroke_width / scale_factor) * (parseFloat(2) / parseFloat(3)));
				d3.selectAll(".focus")
						.attr("r", (path_stroke_width / scale_factor) * (parseFloat(2) / parseFloat(3)) * 5);
		}

    this.zm = function() {
        translate_val = d3.event.translate; // CLEAN THIS UP
        scale_val = d3.event.scale;
				self.translate_val = translate_val;
				self.scale_val = scale_val;
        // console.log("translate_val: " + translate_val);
        // console.log("scale_val: " + scale_val);
        d3.select("path")
            .attr("transform", "translate(" + translate_val + ")scale(" + scale_val + ")");
        d3.selectAll(".datapt")
            .attr("transform", "translate(" + translate_val + ")scale(" + scale_val + ")");
        d3.selectAll(".focus")
            .attr("transform", "translate(" + translate_val + ")scale(" + scale_val + ")");
        d3.selectAll(".extent")
            .attr("transform", "translate(" + translate_val[0] + ",0)scale(" + scale_val + ")");
        d3.selectAll(".brush-label")
            .attr("transform", "translate(" + translate_val[0] + ",0)scale(1)");
        svg.select("g.x.axis")
            .call(xAxis);
        svg.select("g.y.axis")
            .call(yAxis);
        self.toggle_grid();
        self.scale_objects();
				d3.select(".console-input.zoom").attr("value", parseInt(scale_val*100) + "%");
    }

    var zoom = d3.behavior.zoom()
        .x(x)
        .y(y)
        .on("zoom", self.zm);

    this.toggle_grid = function() {
        grid = self.user_options.grid;
        if (grid === true) {
            //console.log("grid is true");
            append_grid = d3.selectAll(".tick").select("line").style("opacity", "0.7");
        }
        else if (grid === false) {
            // console.log("grid is false");
            append_grid = d3.selectAll(".tick").select("line").style("opacity", "0");
        }
    }



    // Remove old plot
    d3.select("#" + anchor).select("svg").remove();


    // Create svg element
    var svg = d3.select("." + anchor).append("svg")
        .attr("class", "default_1d")
        .attr("id", anchor + "_svg")
        .attr("width", mod_psize.width + margin.left + margin.right)
        .attr("height", mod_psize.height + margin.top + margin.bottom)
        .append("g")
        .attr("id", anchor + "_g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    // Brush element
    var x0; // brush value -left
    var x1; // brush value -right
    var d0;
    var d1;
    self.last_brush = 0;

    function brush(){
        var num_of_brushes = $(".brush").length;
				//var this_key = num_of_brushes;
        var this_index;
        var this_id; // id of current brush
        var this_name; // name of current brush
        var brush_action = d3.svg.brush()
            .x(x)
            .on("brushstart", function(d) {})
            .on("brush", function(d) {
                d0 = brush_action.extent()[0];
                d1 = brush_action.extent()[1];
                resize = d3.select(".resize .n");
								console.log("num_of_brushes: " + num_of_brushes)
                // $(".console-input.id").text(data_region.info_table[num_of_brushes].region_name);
                $(".console-input.left").attr("value", formatter(d0));
                $(".console-input.right").attr("value", formatter(d1));
                $(this).children(".brush-label").attr("visibility", "visible")
                    .attr("x", x(d0) + 3)
                    .attr("y", 12);
            })
            .on("brushend", function(d) {
							  // Snap region to nearest data points
                var bisect_data = d3.bisector(function(d) {
                    return d[0];
                }).left;
                var i = bisect_data(data, d0);
                console.log("i : " + i);
                if (i != 0 && i < data.length) {
                    if (Math.abs(data[i - 1][0] - d0) < Math.abs(data[i][0] - d0)) {
                        d0 = data[i - 1][0]
                    }
                    else {
                        d0 = data[i][0]
                    }
                }
                else if (i <= 0) {
                    d0 = data[i][0]
                }
                else if (i >= data.length) {
                    d0 = data[i - 1][0]
                }
                i = bisect_data(data, d1);
                if (i != 0 && i < data.length) {
                    if (Math.abs(data[i - 1][0] - d1) < Math.abs(data[i][0] - d1)) {
                        d1 = data[i - 1][0]
                    }
                    else {
                        d1 = data[i][0]
                    }
                }
                else if (i <= 0) {
                    d1 = data[i][0];
                }
                else if (i >= data.length) {
                    d1 = data[i - 1][0]
                }

                d3.select(this).transition()
                    .call(brush_action.extent([d0, d1]))
                    .call(brush_action);
                $(".console-input.left").attr("value", formatter(d0));
                $(".console-input.right").attr("value", formatter(d1));
                $(this).attr("left", formatter(d0));
                $(this).attr("right", formatter(d1));
                console.log("region_id: " + this_id);
                // data_region.info_table[num_of_brushes].left = formatter(d0);
                // data_region.info_table[num_of_brushes].right = formatter(d1);
                // console.log(data_region.info_table.length);
                // console.log(data_region.info_table[parseInt(data_region.info_table.length) - 1]);
                for (this_index = 0; this_index < parseInt(data_region.info_table.length); this_index++) {
                    if (data_region.info_table[this_index].region_id == this_id) {
                        console.log(data_region.info_table[this_index].region_id);
                        break;
                    }
                }
                data_region.info_table[this_index].left = formatter(d0);
                data_region.info_table[this_index].right = formatter(d1);
				        console.log(data_region.info_table[this_index].left);
				        console.log(data_region.info_table[this_index].right);
                $(this).children(".brush-label").attr("x", x(d0) + 3).attr("y", 12);
            });

        d3.select("#graph_g")
            .append("g")
            .attr("class", "brush")
            .datum(function() {
                return self.last_brush;
            })
            .attr("id", function(d) {
                return this_id = "brush_" + String.fromCharCode(65 + d);
            })
            .attr("name", function(d) {
                return this_name = String.fromCharCode(65 + d);
            })
            .attr("clip-path", "url(#clip)")
            .call(brush_action)
            .append("text")
            .attr("class", "brush-label")
            .text(function(d) {
                return String.fromCharCode(65 + d);
            })
            .attr("visibility", "hidden");
        self.last_brush++;
        // Add data about new region
        data_region.info_table.push({
            "region_id": this_id,
            "region_name": this_name,
            "active": true,
            "left": 0,
            "right": 0,
            "delete": false
        });
        d0 = brush_action.extent()[0];
        d1 = brush_action.extent()[1];
        resize = d3.select(".resize .n");
				$(".console-input.id").text(data_region.info_table[num_of_brushes].region_name);
        $(".console-input.left").attr("value", data_region.info_table[num_of_brushes].left);
        $(".console-input.right").attr("value", data_region.info_table[num_of_brushes].right);
    }


    // Create clipping reference for zoom element
    clip = svg.append("defs")
        .append("clipPath")
        .attr("id", "clip")
        .append("rect")
        .attr("id", "clip-rect")
        .attr("x", 0)
        .attr("y", 0)
        .attr("width", mod_psize.width)
        .attr("height", mod_psize.height);


    this.main_plot = svg.append("g").attr("class", "main_plot");

		test1 = svg.append("g");
		test2 = svg.append("g");
    test1.attr("class", "x axis")
        .attr("transform", "translate(0," + mod_psize.height + ")")
        .call(xAxis);
    test2.attr("class", "y axis").call(yAxis);


    // Refer to clip reference
    self.main_plot.attr("clip-path", "url(#clip)");

    // Create X axis label
    svg.append("text")
        .attr("x", mod_psize.width)
        .attr("y", mod_psize.height + 40)
        .attr("id", "x_label")
        .attr("font-size", "11px")
        .style("text-anchor", "end")
        .text(x_label);


    // Create Y axis label
    svg.append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", 4 - margin.left)
        .attr("x", 0)
        .attr("id", "y_label")
        .attr("dy", "1.5em")
        .attr("dx", "-1em")
        .style("text-anchor", "end")
        .text(y_label);


    // Create title
    svg.append("text")
        .attr("x", mod_psize.width / 2.0)
        .attr("y", -10)
        .attr("id", "title")
        .attr("font-size", "16px")
        .style("text-anchor", "middle")
        .text(title_label);


    // Interpolate
    this.main_plot.select("path").remove();
    var interp_line = d3.svg.line()
        .interpolate("linear")
        .x(function(d) {
            return x(d[0]);
        })
        .y(function(d) {
            return y(d[1]);
        });
    this.main_plot.append("path")
        .attr("d", interp_line(data))
        .attr("fill", "none")
        .attr("stroke", color)
        .attr("stroke-width", path_stroke_width)
        .style("opacity", 0.5);

    this.data_points = d3.select(".main_plot").insert("g", ".focus")
        .attr("class", "data_points")
        .attr("clip-path", "url(#clip)");

    // Tooltip obj
    var tooltip = d3.select("body")
        .append("text")
        .attr("class", "tooltip")
        .style("position", "absolute")
        .style("z-index", "2010")
        .style("visibility", "hidden")
        .style("color", "black");


    // Points obj with data
    var points = self.data_points.selectAll("circle")
        .data(data)
        .enter();
    var pan;
    var circle_ol;
    var little_pt;
    var circle_ar;
    //interactive_points(points);
    this.interactive_points = function(points) {
        // Circle obj with colored outline
        circle_ol = self.data_points.append("circle")
				    .attr("class", "circle_ol")
            .attr("cx", "0")
            .attr("cy", "0")
						.attr("r", marker_size_focus)
            .style("z-index", "500")
            .style("visibility", "hidden")
            .style("fill", "white")
            .style("fill-opacity", "0")
            .style("stroke", color)
            .style("stroke-width", 1 / scale_val)

        // Little points
        little_pt = points.append('circle')
            .attr("class", "datapt")
            .attr("cx", function(d) {
                return x(d[0]);
            })
            .attr("cy", function(d) {
                return y(d[1]);
            })
            .attr("r", marker_size / scale_val)
            .style('fill', color);

        // This is used to get coordinates on mouseover
        circle_ar = points.append("circle")
            .attr("class", "focus")
            .attr("cx", function(d) {
                return x(d[0]);
            })
            .attr("cy", function(d) {
                return y(d[1]);
            })
            .attr("r", marker_size_focus)
            .style("fill", "white")
            .style("fill-opacity", "0");
    }

    pan_flag = true;
    this.toggle_pan_and_zoom = function(pan_flag) {
        //console.log(pan_flag);
        if (pan_flag == true) {
					  // remove any previous pan rect element
            d3.select(".pan").remove();
            // Points obj with data
            //svg.selectAll("circle").remove();
            points = 0;
            points = this.main_plot.selectAll("circle")
                .data(data)
                .enter();
            self.interactive_points(points);
            little_pt.attr("transform", "translate(" + translate_val + ")scale(" + scale_val + ")");
            //translate_val = d3.event.translate;
            //scale_val = d3.event.scale;
            d3.select("path")
                .attr("transform", "translate(" + translate_val + ")scale(" + scale_val + ")");
            // d3.selectAll(".data_pt")
            //     .attr("transform", "translate(" + translate_val + ")scale(" + scale_val + ")");
            // d3.selectAll(".focus")
            //     .attr("transform", "translate(" + translate_val + ")scale(" + scale_val + ")");

            //svg.select("g.x.axis")
            //.call(xAxis);
            //svg.select("g.y.axis")
            //.call(yAxis);
            // Add pan rect
            pan = d3.select(".main_plot").insert("rect", ".datapt")
                .attr("class", "pan")
                .attr("width", mod_psize.width)
                .attr("height", mod_psize.height)
                .call(zoom);
        }
        else {
            // Remove pan rect
            //d3.select(".pan").remove();
            // Points obj with data
            //svg.selectAll("circle").remove();
            //points = 0;
            //points = data_points.selectAll("circle")
            //.data(data)
            //.enter();
            //interactive_points(points);
            //get_data_values();
            //little_pt.attr("transform", "translate(" + translate_val + ")scale(" + scale_val + ")");
        }
    }
    this.toggle_pan_and_zoom(pan_flag);


    self.toggle_grid();



    this.enable_brush = function() {
        d3.select("#graph_g")
            //.attr("class", "brushes")
            .call(brush)
            .selectAll("rect")
            .attr("height", mod_psize.height);
    }

    this.clear_brush = function() {
        console.log("in clear brush");
        d3.selectAll(".brush").remove();
        // get_domain();
    }

		this.change_color = function() {
				d3.select("path").attr("stroke", self.user_options.color)
				circle_ol.style("fill-opacity", "0").style("stroke", self.user_options.color);
        d3.selectAll(".datapt").style("fill", self.user_options.color);
				little_pt.style("fill", self.user_options.color);
		}

    function get_data_values(d) {
        svg.selectAll(".focus")
            .on("mouseover", function(d) {
                mouseover(d);
            })
            .on("mousemove", function(d) {
                mousemove(d);
            })
            .on("mouseout", function(d) {
                mouseout(d);
            });
    }
    // Get data values on hover event
    get_data_values(data);

    function mouseover(d) {
        mouseY = 0;
        mouseX = 0;
        circle_ol.attr("cx", x(d[0]))
            .attr("cy", y(d[1]))
            .style("visibility", "visible");
        tooltip.style("visibility", "visible");
        if (window.Event && document.captureEvents)
            document.captureEvents(Event.MOUSEOVER);
        document.onmouseover = getMousePos;
        tooltip.text(d3.round(d[0], 1) + ", " + d3.format("6.3g")(d[1]));
        tooltip.style("top", (mouseY - 10) + "px")
            .style("left", (mouseX + 10) + "px");
    }

    function mousemove(d) {
        circle_ol.attr("cx", x(d[0]))
            .attr("cy", y(d[1]))
            .style("visibility", "visible");
        tooltip.style("visibility", "visible");
        if (window.Event && document.captureEvents)
            document.captureEvents(Event.MOUSEMOVE);
        document.onmousemove = getMousePos;
        tooltip.text(d3.round(d[0], 1) + ", " + d3.format("6.3g")(d[1]));
        tooltip.style("top", (mouseY - 10) + "px")
            .style("left", (mouseX + 10) + "px");
    }

    function mouseout(d) {
        circle_ol.style("visibility", "hidden");
        return tooltip.style("visibility", "hidden");
    }

    function getMousePos(e) {
        if (!e) var e = window.event || window.Event;

        if ('undefined' != typeof e.pageX) {
            mouseX = e.pageX;
            mouseY = e.pageY;
        }
        else {
            mouseX = e.clientX + document.body.scrollLeft;
            mouseY = e.clientY + document.body.scrollTop;
        }
    }

}
