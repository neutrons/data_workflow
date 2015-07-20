//
// Plot object that handles all SVG (d3) elements
//
function Plot_1d(raw_data, anchor, plot_options) {
  var self = this; // Assign scope
  self.raw_data = raw_data;
  self.anchor = anchor;
  self.plot_options = plot_options;
  self.translate_val = [0, 0];
  self.scale_val = 1;
  var plot_size = {
    height: 244,
    width: 360
  };
  var margin = {
    top: 30,
    right: 15,
    bottom: 50,
    left: 65
  };
  var color = this.plot_options.color; // color of points and line in plot
  var log_scale_x = this.plot_options.log_scale_x; // x-axis log scale flag
  var log_scale_y = this.plot_options.log_scale_y; // y-axis log scale flag
  var grid = this.plot_options.grid; // display grid in plot flag
  var x_label = this.plot_options.x_label;
  var y_label = this.plot_options.y_label;
  var title_label = this.plot_options.title;
  var x_label_align = this.plot_options.x_label_align;
  var y_label_align = this.plot_options.y_label_align;
  var title_label_align = this.plot_options.title_label_align;
  var marker_size = 1;
  var marker_size_focus = 6;
  var path_stroke_width = 1.5;
  var data_error_bars = false;
  var pan_bool = true;
  var append_grid;
  var w;
  var h;
  var x;
  var y;
  var y_min;
  var y_max;
  var xAxis;
  var xAxisMinor;
  var xAxisItems;
  var yAxis;
  var yAxisMinor;
  var yAxisItems;
  var svg;
  var clip;
  var interp_line; // interpolation line object
  var points; // points object
  var tooltip;
  var little_pt;
  var circle_ar;
  var mouseY;
  var mouseX;
  var formatter;
  var data = [];

  for (var i = 0; i < raw_data.length; i++) {
    if (log_scale_y == false || raw_data[i][1] > 0) data.push(raw_data[i]);
  }

  //
  // Check to see if raw_data has 3 columns; if it does, an error is provided
  // and data_error_bars flags for error bars to be drawn
  //
  this.need_error_bars = function() {
    if (raw_data[0].length == 3) data_error_bars = true;
  }

  //
  // Get log scale flags from plot_options and draw plot scale
  //
  this.get_scale = function(log_scale_x, log_scale_y) {
    x = log_scale_x ? d3.scale
      .log()
      .range([0, plot_size.width])
      .nice() :
      d3.scale
      .linear()
      .range([0, plot_size.width]);
    y = log_scale_y ? d3.scale
      .log()
      .range([plot_size.height, 0])
      .nice() :
      d3.scale
      .linear()
      .range([plot_size.height, 0]);
  }

  //
  // Get domain of raw_data
  //
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
    } else {
      y.domain([y_min, y_max]);
    }
  }

  //
  // Format values on axes
  //
  formatter = function(d) {
    if (d < 1000000.0 && d > 1.0e-3) {
      // console.log(d3.format("5.3g")(d));
      return d3.format("5.3g")(d);
    } else {
      return d3.format("1.2g")(d);
    }
  };

  //
  // Draw x-axis and y-axis
  //
  this.get_axes = function() {
    xAxis = d3.svg
      .axis()
      .scale(x)
      .orient("bottom")
      .ticks(4, formatter)
      .tickSize(-plot_size.height);
    if (log_scale_y == false) {
      yAxis = d3.svg
        .axis()
        .scale(y)
        .orient("left")
        .ticks(4)
        .tickSize(-plot_size.width)
        .tickFormat(formatter);
    } else {
      yAxis = d3.svg
        .axis()
        .scale(y)
        .orient("left")
        .ticks(4, formatter)
        .tickSize(-plot_size.width);
    }
  }

  //
  // Create axis values and tick marks
  //
  this.axis_items = function(){
    xAxisItems = svg.append("g")
                          .attr("class", "x axis")
                          .attr("transform", "translate(0," + plot_size.height + ")")
                          .call(xAxis);
    yAxisItems = svg.append("g")
                          .attr("class", "y axis")
                          .call(yAxis);
  }

  //
  // On zoom action, scale data points and line such that the paths
  // don't become too thick or too thin
  //
  this.scale_objects = function() {
    scale_factor = parseFloat(d3.transform(d3.select("#" + self.anchor + " path")
        .attr("transform"))
      .scale[0]);
    d3.select("#" + self.anchor + " path")
      .attr("stroke-width", path_stroke_width / scale_factor);
    d3.selectAll("#" + self.anchor + " .error_bar")
      .attr("stroke-width", path_stroke_width / scale_factor);
    d3.selectAll("#" + self.anchor + " .datapt")
      .attr("r", (path_stroke_width / scale_factor) * (parseFloat(2) / parseFloat(3)));
    d3.selectAll("#" + self.anchor + " .focus")
      .attr("r", (path_stroke_width / scale_factor) * (parseFloat(2) / parseFloat(3)) * 5);
  }

  //
  // Zoom and pan function for data path, point, error bar (if applicable),
  // and grid (if applicable). Then scales objects
  //
  this.zm = function() {
    self.translate_val = d3.event.translate;
    self.scale_val = d3.event.scale;
    d3.select("#" + self.anchor + " path")
      .attr("transform", "translate(" + self.translate_val + ")scale(" + self.scale_val + ")");
    d3.selectAll("#" + self.anchor + " .datapt")
      .attr("transform", "translate(" + self.translate_val + ")scale(" + self.scale_val + ")");
    d3.selectAll("#" + self.anchor + " .focus")
      .attr("transform", "translate(" + self.translate_val + ")scale(" + self.scale_val + ")");
    d3.selectAll("#" + self.anchor + " .error_bar")
      .attr("transform", "translate(" + self.translate_val + ")scale(" + self.scale_val + ")");
    d3.selectAll("#" + self.anchor + " .extent")
      .attr("transform", "translate(" + self.translate_val[0] + ",0)scale(" + self.scale_val + ")");
    d3.selectAll("#" + self.anchor + " .brush-label")
      .attr("transform", "translate(" + self.translate_val[0] + ",0)scale(1)");
    svg.select("#" + self.anchor + " g.x.axis")
      .call(xAxis);
    svg.select("#" + self.anchor + " g.y.axis")
      .call(yAxis);
    self.toggle_grid();
    self.scale_objects();
    d3.select("." + self.anchor + " .console-input.zoom").html(parseInt(self.scale_val * 100) + "%");
  }

  //
  // Applies listener on user scroll and calls zm() the zoom function
  //
  this.apply_zooms = function(){
    self.zoom_setup = d3.behavior.zoom()
      .x(x)
      .y(y);
    self.zoom = self.zoom_setup
      .on("zoom", self.zm);
  }

  //
	// Resets zoom to 100% and translates back to origin
	//
  this.zoom_reset = function(){
    // console.log("in zoom reset");
    self.translate_val = [0,0];
    self.zoom.translate(self.translate_val);
    self.scale_val = 1;
    self.zoom.scale(self.scale_val);
    d3.select("#" + self.anchor + " path")
      .attr("transform", "translate(" + self.translate_val + ")scale(" + self.scale_val + ")");
    d3.selectAll("#" + self.anchor + " .datapt")
      .attr("transform", "translate(" + self.translate_val + ")scale(" + self.scale_val + ")");
    d3.selectAll("#" + self.anchor + " .focus")
      .attr("transform", "translate(" + self.translate_val + ")scale(" + self.scale_val + ")");
    d3.selectAll("#" + self.anchor + " .error_bar")
      .attr("transform", "translate(" + self.translate_val + ")scale(" + self.scale_val + ")");
    d3.selectAll("#" + self.anchor + " .extent")
      .attr("transform", "translate(" + self.translate_val[0] + ",0)scale(" + self.scale_val + ")");
    d3.selectAll("#" + self.anchor + " .brush-label")
      .attr("transform", "translate(" + self.translate_val[0] + ",0)scale(1)");
    svg.select("#" + self.anchor + " g.x.axis")
      .call(xAxis);
    svg.select("#" + self.anchor + " g.y.axis")
      .call(yAxis);
    self.toggle_grid();
    self.scale_objects();
    d3.select("." + self.anchor + " .console-input.zoom").html(parseInt(self.scale_val * 100) + "%");
  }

  //
  // Toggles display of grid
  //
  this.toggle_grid = function() {
    grid = self.plot_options.grid;
    if (grid === true) {
      svg.select("#" + self.anchor + " g.x.axis").remove();
      svg.select("#" + self.anchor + " g.y.axis").remove();
      self.axis_items();
    } else if (grid === false) {
      d3.select("#" + self.anchor + " .y.axis").selectAll(".tick line").remove();
      d3.select("#" + self.anchor + " .x.axis").selectAll(".tick line").remove();
    }
  }

  //
  // Create svg element and add axis items
  //
  this.create_svg = function(){
    // Remove old plot (if any) to redraw
    d3.select("#" + anchor).select("svg").remove();
    // Draw svg element
    svg = d3.select("#" + self.anchor).append("svg")
      .attr("class", "default_1d")
      .attr("id", self.anchor + "_svg")
      .attr("width", plot_size.width + margin.left + margin.right)
      .attr("height", plot_size.height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
    self.main_plot = svg.append("g").attr("class", "main_plot");
    self.axis_items();
  }

  //
  // Initialize brush variables for region mode
  //
  this.init_brush = function(){
    // Brush element
    self.d0 = null; // brush value left
    self.d1 = null; // brush value right
    self.last_brush = 0;
  }

  //
  // Handles drawing of region
  //   brushstart: activate region
  //   brush: get and show boundaries in user console, show region
  //   brushend: snap to nearest data point and show in user console,
  //             add region in region object called data_region
  //
  function brush() {
    var num_of_brushes = $("." + self.anchor + " g.brush").length;
    var this_index;
    var this_id; // id of current brush
    var this_name; // name of current brush
    var this_shortname; // shorter name of current brush
    var brushend;
    var brush_action = d3.svg.brush()
      .x(x)
      .extent([self.d0, self.d1])
      .on("brushstart", function(d) {
        self.d0 = brush_action.extent()[0];
        self.d1 = brush_action.extent()[1];
        num_of_brushes = $("." + self.anchor + " g.brush").length;
      })
      .on("brush", function(d) {
        self.d0 = brush_action.extent()[0];
        self.d1 = brush_action.extent()[1];
        $("." + self.anchor + " .console-input.left").text(formatter(self.d0));
        $("." + self.anchor + " .console-input.right").text(formatter(self.d1));
        $(this).children(".brush-label").attr("visibility", "visible")
          .attr("x", x(self.d0) + 3)
          .attr("y", 12);
        num_of_brushes = $("." + self.anchor + " g.brush").length;
      })
      .on("brushend", function(d) {
        brushend(this);
      });

    brushend = function(s) {
      // Snap region to nearest data points
      var bisect_data = d3.bisector(function(d) {
        return d[0];
      }).left;
      var i = bisect_data(data, self.d0);
      // console.log("i : " + i);
      if (i != 0 && i < data.length) {
        if (Math.abs(data[i - 1][0] - self.d0) < Math.abs(data[i][0] - self.d0)) {
          self.d0 = data[i - 1][0]
        } else {
          self.d0 = data[i][0]
        }
      } else if (i <= 0) {
        self.d0 = data[i][0]
      } else if (i >= data.length) {
        self.d0 = data[i - 1][0]
      }
      i = bisect_data(data, self.d1);
      if (i != 0 && i < data.length) {
        if (Math.abs(data[i - 1][0] - self.d1) < Math.abs(data[i][0] - self.d1)) {
          self.d1 = data[i - 1][0]
        } else {
          self.d1 = data[i][0]
        }
      } else if (i <= 0) {
        self.d1 = data[i][0];
      } else if (i >= data.length) {
        self.d1 = data[i - 1][0]
      }

      d3.select(s).transition()
        .call(brush_action.extent([self.d0, self.d1]))
        .call(brush_action);
      $("." + self.anchor + " .console-input.left").text(formatter(self.d0));
      $("." + self.anchor + " .console-input.right").text(formatter(self.d1));
      $(s).attr("left", formatter(self.d0));
      $(s).attr("right", formatter(self.d1));
      num_of_brushes = $("." + self.anchor + " g.brush").length;
      for (this_index = 0; this_index < parseInt(self.data_region.info_table.length); this_index++) {
        if (self.data_region.info_table[this_index].region_id == this_id) {
          break;
        }
      }
      self.data_region.info_table[this_index].left = formatter(self.d0);
      self.data_region.info_table[this_index].right = formatter(self.d1);
      $(s).children(".brush-label").attr("x", x(self.d0) + 3).attr("y", 12);
      self.d0 = null;
      self.d1 = null;
    }
    d3.select("." + self.anchor + " .default_1d")
      .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")")
      .datum(function() {
        return self.last_brush;
      })
      // .attr("class", "brush")
      .attr("class", function(d) {
        return this_id = "brush brush_" + String.fromCharCode(65 + d);
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
    self.last_brush++; // ?????? this needs to be here for some reason
    this_shortname = this_id.split(" ")[1];
    // Add data about new region
    self.data_region.info_table.push({
      "graph_id": self.anchor,
      "region_id": this_id,
      "region_name": this_name,
      "region_shortname": this_shortname,
      "active": true,
      "left": 0,
      "right": 0,
      "delete": false
    });
    $("." + self.anchor + " .console-input.id").text(self.data_region.info_table[num_of_brushes].region_name);
    $("." + self.anchor + " .console-input.left").text(self.data_region.info_table[num_of_brushes].left);
    $("." + self.anchor + " .console-input.right").text(self.data_region.info_table[num_of_brushes].right);
  }

  //
  // Create clipping reference for zoom element
  //
  this.create_clipping = function(){
    clip = svg.append("defs")
      .append("clipPath")
      .attr("id", "clip")
      .append("rect")
      .attr("id", "clip-rect")
      .attr("x", 0)
      .attr("y", 0)
      .attr("width", plot_size.width)
      .attr("height", plot_size.height);
    // Reference to clip object
    self.main_plot.attr("clip-path", "url(#clip)");
  }

  //
  // Create text objects (x-axis, y-axis, title labels)
  //
  this.create_labels = function() {
    d3.selectAll("." + this.anchor + " .label").remove();
    var text_anchor;
    var pos;
    // Create X axis label
    if (self.plot_options.x_label_align == "left") {
      text_anchor = "start";
      pos = 0;
    } else if (self.plot_options.x_label_align == "center") {
      text_anchor = "middle";
      pos = plot_size.width / 2.0;
    } else if (self.plot_options.x_label_align == "right") {
      text_anchor = "end";
      pos = plot_size.width;
    }
    svg.append("text")
      .attr("x", pos)
      .attr("y", plot_size.height + 40)
      .attr("class", "label x_label")
      .attr("font-size", "11px")
      .style("text-anchor", text_anchor)
      .text(self.plot_options.x_label);
    // Create Y axis label
    if (self.plot_options.y_label_align == "left") {
      text_anchor = "start";
      pos = plot_size.height;
    } else if (self.plot_options.y_label_align == "center") {
      text_anchor = "middle";
      pos = plot_size.height / 2.0;
    } else if (self.plot_options.y_label_align == "right") {
      text_anchor = "end";
      pos = 0;
    }
    svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 4 - margin.left)
      .attr("x", 10 - pos)
      .attr("class", "label y_label")
      .attr("dy", "1.5em")
      .attr("dx", "-1em")
      .style("text-anchor", text_anchor)
      .text(self.plot_options.y_label);
    // Create title
    if (self.plot_options.title_label_align == "left") {
      text_anchor = "start";
      pos = 0;
    } else if (self.plot_options.title_label_align == "center") {
      text_anchor = "middle";
      pos = plot_size.width / 2.0;
    } else if (self.plot_options.title_label_align == "right") {
      text_anchor = "end";
      pos = plot_size.width;
    }
    svg.append("text")
      .attr("x", pos)
      .attr("y", -10)
      .attr("class", "label title")
      .attr("font-size", "16px")
      .style("text-anchor", text_anchor)
      .text(self.plot_options.title);
  }

  //
  // Interpolate data points to draw line graph
  //
  this.create_data_line = function(){
    self.main_plot.select("#" + self.anchor + " path").remove();
    interp_line = d3.svg.line()
      .interpolate("linear")
      .x(function(d) {
        return x(d[0]);
      })
      .y(function(d) {
        return y(d[1]);
      });
    self.main_plot.append("path")
      .attr("d", interp_line(data))
      .attr("fill", "none")
      .attr("stroke", color)
      .attr("stroke-width", path_stroke_width)
      .style("opacity", 0.5);
  }

  //
  // Create data points in graph
  //
  this.create_data_points = function(){
    self.data_points = d3.select("#" + self.anchor + " .main_plot").insert("g", ".focus")
      .attr("class", "data_points")
      .attr("clip-path", "url(#clip)");
    // Points obj with data
    points = self.data_points.selectAll("#" + anchor + " circle")
      .data(data)
      .enter();
  }

  //
  // Make data points interactive by adding a hidden larger circle to
  // detect mouse movements, showing a colored outline on mouseover
  //
  this.interactive_points = function(points) {
    tooltip = d3.select("body")
      .append("text")
      .attr("class", "tooltip")
      .style("position", "absolute")
      .style("z-index", "2010")
      .style("visibility", "hidden")
      .style("color", "black");
    // Circle obj with colored outline
    self.circle_ol = self.data_points.append("circle")
      .attr("class", "circle_ol")
      .attr("cx", "0")
      .attr("cy", "0")
      .attr("r", marker_size_focus)
      .style("z-index", "500")
      .style("visibility", "hidden")
      .style("fill", "white")
      .style("fill-opacity", "0")
      .style("stroke", color)
      .style("stroke-width", 1 / self.scale_val)

    // Little points
    little_pt = points.append('circle')
      .attr("class", "datapt")
      .attr("cx", function(d) {
        return x(d[0]);
      })
      .attr("cy", function(d) {
        return y(d[1]);
      })
      .attr("r", marker_size / self.scale_val)
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


    if (data_error_bars == true) {
      // Append vertical dotted line
      points.append("line").attr("class", "error_bar")
        .attr("x1", function(d) {
          return (x(d[0]));
        })
        .attr("y1", function(d) {
          return (y(d[1] - d[2]));
        })
        .attr("x2", function(d) {
          return (x(d[0]));
        })
        .attr("y2", function(d) {
          return (y(d[1] + d[2]));
        })
        .attr("stroke-width", path_stroke_width / 2)
        .attr("stroke", color)
        //.attr("stroke-dasharray", "2,2")
        .attr("opacity", 0.7);
      // Append horizontal top line
      points.append("line").attr("class", "error_bar")
        .attr("x1", function(d) {
          return (x(d[0]) - parseFloat(marker_size));
        })
        .attr("y1", function(d) {
          return (y(d[1] + d[2]));
        })
        .attr("x2", function(d) {
          return (x(d[0]) + parseFloat(marker_size));
        })
        .attr("y2", function(d) {
          return (y(d[1] + d[2]));
        })
        .attr("stroke-width", path_stroke_width / 2)
        .attr("stroke", color);
      // Append horizontal bottom line
      points.append("line").attr("class", "error_bar")
        .attr("x1", function(d) {
          return (x(d[0]) - parseFloat(marker_size));
        })
        .attr("y1", function(d) {
          return (y(d[1] - d[2]));
        })
        .attr("x2", function(d) {
          return (x(d[0]) + parseFloat(marker_size));
        })
        .attr("y2", function(d) {
          return (y(d[1] - d[2]));
        })
        .attr("stroke-width", path_stroke_width / 2)
        .attr("stroke", color);
    }
  }

  //
  // When Pan and Zoom mode is selected, call the zoom function and
  // make sure data values are visible on mouseover
  //
  this.toggle_pan_and_zoom = function(pan_bool) {
    if (pan_bool == true) {
      // Remove any previous pan rect element
      d3.select("#" + self.anchor + " .pan").remove();
      // Points obj with data
      points = 0;
      points = this.main_plot.selectAll("#" + self.anchor + " circle")
        .data(data)
        .enter();
      self.interactive_points(points);
      little_pt.attr("transform", "translate(" + self.translate_val + ")scale(" + self.scale_val + ")");
      d3.select("#" + self.anchor + " path")
        .attr("transform", "translate(" + self.translate_val + ")scale(" + self.scale_val + ")");
      pan = d3.select("#" + self.anchor + " .main_plot").insert("rect", ".datapt")
        .attr("class", "pan")
        .attr("width", plot_size.width)
        .attr("height", plot_size.height)
        .call(self.zoom);
    }
  }

  //
  // Enable d3 brush for regions mode
  //
  this.enable_brush = function() {
    d3.select("#" + self.anchor + "_svg")
      //.attr("class", "brushes")
      .call(brush)
      .selectAll("rect")
      .attr("height", plot_size.height);
  }

  //
  // Check if regions are predetermined and Region Mode is allowed
  //
  this.check_predetermined_regions = function(){
    self.predetermined_regions_flag = false;
    if (self.plot_options.predetermined_region.length > 0 && self.plot_options.allow_region_mode == true) {
      self.predetermined_regions_flag = true;
    }
  }

  //
  // Remove region
  //
  this.clear_brush = function() {
    d3.selectAll("." + this.anchor + " .brush").remove();
  }

  //
  // Assign color
  //
  this.change_color = function() {
    d3.select("#" + self.anchor + " path").attr("stroke", self.plot_options.color)
    self.circle_ol.style("fill-opacity", "0").style("stroke", self.plot_options.color);
    d3.select("#" + self.anchor + " .circle_ol").style("stroke", self.plot_options.color);
    d3.selectAll("#" + self.anchor + " .datapt").style("fill", self.plot_options.color);
    d3.selectAll("#" + self.anchor + " .error_bar").style("stroke", self.plot_options.color);
    little_pt.style("fill", self.plot_options.color);
  }

  //
  // Get data values on hover event
  //
  this.get_data_values = function(d) {
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

  //
  // Show data values and outline when mouse neters data point
  //
  function mouseover(d) {
    mouseY = 0;
    mouseX = 0;
    self.circle_ol.attr("cx", x(d[0]))
      .attr("cy", y(d[1]))
      .style("visibility", "visible");
    tooltip.style("visibility", "visible");
    if (window.Event && document.captureEvents)
      document.captureEvents(Event.MOUSEOVER);
    document.onmouseover = getMousePos;
    tooltip.text(d3.format("6.3g")(d[0]) + ", " + d3.format("6.3g")(d[1]));
    tooltip.style("top", (mouseY - 10) + "px")
      .style("left", (mouseX + 10) + "px");
  }

  //
  // Follow mouse near data point
  //
  function mousemove(d) {
    self.circle_ol.attr("cx", x(d[0]))
      .attr("cy", y(d[1]))
      .style("visibility", "visible");
    tooltip.style("visibility", "visible");
    if (window.Event && document.captureEvents)
      document.captureEvents(Event.MOUSEMOVE);
    document.onmousemove = getMousePos;
    tooltip.text(d3.format("6.3g")(d[0]) + ", " + d3.format("6.3g")(d[1]));
    tooltip.style("top", (mouseY - 10) + "px")
      .style("left", (mouseX + 10) + "px");
  }

  //
  // Hide data values and outline when mouse leaves data point
  //
  function mouseout(d) {
    self.circle_ol.style("visibility", "hidden");
    return tooltip.style("visibility", "hidden");
  }

  //
  // Manually get mouse position for Chrome and Firefox
  //
  function getMousePos(e) {
    if (!e) var e = window.event || window.Event;
    if ('undefined' != typeof e.pageX) {
      mouseX = e.pageX;
      mouseY = e.pageY;
    } else {
      mouseX = e.clientX + document.body.scrollLeft;
      mouseY = e.clientY + document.body.scrollTop;
    }
  }

  self.need_error_bars();
  self.get_scale(log_scale_x, log_scale_y);
  self.get_domain();
  self.get_axes();
  self.apply_zooms();
  self.create_svg();
  self.init_brush();
  self.create_clipping();
  self.create_labels();
  self.create_data_line();
  self.create_data_points();
  self.toggle_pan_and_zoom(pan_bool);
  self.toggle_grid();
  self.check_predetermined_regions();
  self.get_data_values(data);

}
