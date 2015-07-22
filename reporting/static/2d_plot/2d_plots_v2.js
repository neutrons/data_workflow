//
// Plot object that handles all SVG (d3) elements
//
function Plot_2d(anchor, raw_data, qx, qy, max_iq, plot_options) {
  var self = this;
  self.anchor = anchor;
  self.raw_data = raw_data;
  self.qx = qx;
  self.qy = qy;
  self.max_iq = max_iq;
  self.plot_options = plot_options;
  var plot_size = {
    height: 500,
    width: 500
  }
  var margin = {
    top: 40,
    right: 40,
    bottom: 60,
    left: 60
  };
  var log_scale = this.plot_options.log_scale;
  var x_label = this.plot_options.x_label;
  var y_label = this.plot_options.y_label;
  var title = this.plot_options.title;
  var x_label_align = this.plot_options.x_label_align;
  var y_label_align = this.plot_options.y_label_align;
  var title_label_align = this.plot_options.title_label_align;
  var drag_init = false;
  var pan_bool = true;
  var n_colors = 64;
  var x;
  var y;
  var x_domain;
  var y_domain;
  var xAxis;
  var yAxis;
  var xAxisItems;
  var yAxisItems;
  var svg;
  var adj_pixel_h;
  var adj_pixel_w;
  var adj_pixel_stroke;
  var quantize;
  var tooltip;
  plot_size.width = plot_size.width - margin.left - margin.right,
    plot_size.height = plot_size.height - margin.top - margin.bottom;

  //
  // Draw plot scale
  //
  this.get_scale = function() {
    x = d3.scale.linear()
      .range([0, plot_size.width]);
    y = d3.scale.linear()
      .range([plot_size.height, 0]);
  }

  //
  // Get domain of raw_data
  //
  this.get_domain = function() {
    var x_min = d3.min(qx, function(d) {
      return d;
    });
    var x_max = d3.max(qx, function(d) {
      return d;
    }) * 1.1;
    var y_min = d3.min(qy, function(d) {
      return d;
    });
    var y_max = d3.max(qy, function(d) {
      return d;
    }) * 1.1;
    x_domain = x.domain([x_min, x_max]);
    y_domain = y.domain([y_min, y_max]);
  }

  //
  // Draw x-axis and y-axis
  //
  this.get_axes = function() {
    xAxis = d3.svg.axis()
      .scale(x)
      .orient("bottom");
    yAxis = d3.svg.axis()
      .scale(y)
      .orient("left");
  }

  //
  // Create axis values and tick marks
  //
  this.axis_items = function() {
    xAxisItems = svg.append("g")
      .attr("class", "x axis")
      .attr("transform", "translate(0," + plot_size.height + ")")
      .call(xAxis);
    yAxisItems = svg.append("g")
      .attr("class", "y axis")
      .call(yAxis);
  }

  //
  // Create svg element and add axis items
  //
  this.create_svg = function() {
    // Remove old plot
    d3.select("#" + anchor).select("svg").remove();
    // Draw svg element
    svg = d3.select("#" + self.anchor).append("svg")
      .attr("class", "Spectral")
      .attr("id", self.anchor + "_svg")
      .attr("width", plot_size.width + margin.left + margin.right)
      .attr("height", plot_size.height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
    self.main_plot = svg.append("g").attr("class", "main_plot");
    self.axis_items();
  }

  //
  // Zoom and pan function for data pixels
  //
  this.zm = function() {
    self.translate_val = d3.event.translate;
    self.scale_val = d3.event.scale;
    d3.selectAll("#" + self.anchor + " .data_block")
      .attr("transform", "translate(" + self.translate_val + ")scale(" + self.scale_val + ")");
    svg.select("#" + self.anchor + " g.x.axis")
      .call(xAxis);
    svg.select("#" + self.anchor + " g.y.axis")
      .call(yAxis);
    d3.select("." + self.anchor + " .console-input.zoom").html(parseInt(self.scale_val * 100) + "%");
  }

  //
  // Applies listener on user scroll and calls zm() the zoom function
  //
  this.apply_zooms = function() {
    self.zoom_setup = d3.behavior.zoom()
      .x(x)
      .y(y);
    self.zoom = self.zoom_setup
      .on("zoom", self.zm);
  }

  //
  // Resets zoom to 100% and translates back to origin
  //
  this.zoom_reset = function() {
    self.translate_val = [0, 0];
    self.zoom.translate(self.translate_val);
    self.scale_val = 1;
    self.zoom.scale(self.scale_val);
    d3.selectAll("#" + self.anchor + " .data_block")
      .attr("transform", "translate(" + self.translate_val + ")scale(" + self.scale_val + ")");
    svg.select("#" + self.anchor + " g.x.axis")
      .call(xAxis);
    svg.select("#" + self.anchor + " g.y.axis")
      .call(yAxis);
    d3.select("." + self.anchor + " .console-input.zoom").html(parseInt(self.scale_val * 100) + "%");
  }

  //
  // Create clipping reference for zoom element
  //
  this.create_clipping = function() {
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
    d3.select("." + self.anchor + " .main_plot").attr("clip-path", "url(#clip)");
  }

  //
  // Scale up the calculated pixel width so that we don't produce visual artifacts
  //
  this.create_pixels = function() {
    adj_pixel_h = 0.9 * (y(qy[0]) - y(qy[1]));
    adj_pixel_w = 0.9 * (x(qx[1]) - x(qx[0]));
    adj_pixel_stroke = Math.max(0.1 * (x(qx[1]) - x(qx[0])), 0.1 * (y(qy[0]) - y(qy[1])));
    if (log_scale) {
      var bins = [];
      var step = Math.log(max_iq + 1.0) / (n_colors - 1);
      for (i = 0; i < n_colors - 1; i++) {
        bins.push(Math.exp(step * i) - 1.0);
      }
      quantize = d3.scale.threshold()
        .domain(bins)
        .range(d3.range(n_colors).map(function(i) {
          return get_color(i, n_colors);
        }));
    } else {
      quantize = d3.scale.quantize()
        .domain([0, max_iq])
        .range(d3.range(n_colors).map(function(i) {
          return get_color(i, n_colors);
        }));
    };
  }

  //
  // Input data in the pixels and create the entire block of data
  //
  this.data_block = function() {
    console.log("start data_block");
    self.main_plot.append('g')
      .attr('class', 'data_block')
      .selectAll('g')
      .data(raw_data)
      .enter()
      .append('g')
      .attr("transform", function(d, i) {
        var trans = y(qy[i]) - adj_pixel_h;
        return "translate(0," + trans + ")";
      })
      .selectAll('rect')
      .data(function(d) {
        return d;
      })
      .enter()
      .append('rect')
      .attr('class', 'pixel')
      .attr('x', function(d, i) {
        return x(qx[i]);
      })
      .attr('y', function(d, i) {
        return 0;
      })
      .attr('width', function(d, i) {
        return adj_pixel_w;
      })
      .attr('height', function(d, i) {
        return adj_pixel_h;
      })
      .attr('fill', function(d) {
        return quantize(d);
      })
      .attr('stroke', function(d) {
        return quantize(d);
      })
      .attr('stroke-width', adj_pixel_stroke);
    console.log("end data_block");
  }

  //
  // Create text objects (x-axis, y-axis, title labels)
  //
  this.create_labels = function() {
    d3.selectAll("." + this.anchor + " .label").remove();
    var text_anchor;
    var pos;
    //
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
      .attr("y", plot_size.height + margin.top + 15)
      .attr("class", "label x_label")
      .attr("font-size", "12px")
      .style("text-anchor", text_anchor)
      .text(x_label);

    //
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
      .attr("x", 0 - pos)
      .attr("class", "label y_label")
      .attr("dy", "1em")
      .attr("font-size", "12px")
      .style("text-anchor", text_anchor)
      .text(y_label);

    //
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
      .attr("y", -20)
      .attr("class", "label title")
      .attr("font-size", "16px")
      .style("text-anchor", text_anchor)
      .text(title);
  }


  //
  // When Pan and Zoom mode is selected, call the zoom function and
  // make sure data values are visible on mouseover
  //
  this.toggle_pan_and_zoom = function(pan_bool) {
    var pan
    if (pan_bool == true) {
      pan = d3.select("#" + self.anchor + " .main_plot").append("rect")
        .attr("class", "pan")
        .attr("width", plot_size.width)
        .attr("height", plot_size.height)
        .call(self.zoom);
    } else {
      d3.select("rect.pan").remove();
    }
  }

  //
  // Get color for each pixel
  //
  function get_color(i, n_max) {
    var n_divs = 4.0;
    var phase = 1.0 * i / n_max;
    var max_i = 210;
    if (phase < 1.0 / n_divs) {
      b = max_i;
      r = 0;
      g = Math.round(max_i * Math.abs(Math.sin(Math.PI / 2.0 * i / n_max * n_divs)));
    } else if (phase < 2.0 / n_divs) {
      b = Math.round(max_i * Math.abs(Math.cos(Math.PI / 2.0 * i / n_max * n_divs)));
      r = 0;
      g = max_i;
    } else if (phase < 3.0 / n_divs) {
      b = 0;
      r = Math.round(max_i * Math.abs(Math.sin(Math.PI / 2.0 * i / n_max * n_divs)));
      g = max_i;
    } else if (phase < 4.0 / n_divs) {
      b = 0;
      r = max_i;
      g = Math.round(max_i * Math.abs(Math.cos(Math.PI / 2.0 * i / n_max * n_divs)));
    }
    r = r + 30;
    g = g + 30;
    return 'rgb(' + r + ',' + g + ',' + b + ')';
  }

  //
  // Tooltip obj
  //
  this.create_tooltip = function() {
    tooltip = d3.select("body")
      .append("text")
      .attr("class", "tooltip")
      .style("position", "absolute")
      .style("z-index", "2010")
      .style("visibility", "hidden")
      .style("color", "black");
  }

  //
  // Get data values on hover event
  //
  this.get_data_values = function(d) {
    svg.selectAll(".pixel")
      .on("mouseover", function(d, i) {
        mouseover(d, this);
      })
      .on("mousemove", function(d, i) {
        mousemove(d);
      })
      .on("mouseout", function(d) {
        mouseout(d, this);
      });
  }

  //
  // Show data values and outline when mouse enters data point
  //
  function mouseover(d, s) {
    d3.select(s)
      .attr("stroke", "#000")
      .attr("stroke-alignment", "inner")
      .attr("stroke-width", adj_pixel_stroke);
    mouseY = 0;
    mouseX = 0;
    var text = "";
    tooltip.style("visibility", "visible");
    if (window.Event && document.captureEvents)
      document.captureEvents(Event.MOUSEOVER);
    document.onmouseover = getMousePos;
    text = d3.round(d, 3);
    tooltip.text(text);
    tooltip.style("top", (mouseY - 10) + "px")
      .style("left", (mouseX + 10) + "px");
  }

  //
  // Follow mouse near data point
  //
  function mousemove(d) {
    var text = "";
    tooltip.style("visibility", "visible");
    if (window.Event && document.captureEvents)
      document.captureEvents(Event.MOUSEMOVE);
    document.onmousemove = getMousePos;
    text = d3.round(d, 3)
    tooltip.text(text);
    tooltip.style("top", (mouseY - 10) + "px")
      .style("left", (mouseX + 10) + "px");
  }

  //
  // Hide data values and outline when mouse leaves data point
  //
  function mouseout(d, s) {
    var color = d3.select(s).attr("fill");
    d3.select(s).attr("stroke", color)
      .attr("stroke-width", adj_pixel_stroke)
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

  self.get_scale();
  self.get_domain();
  self.get_axes();
  self.create_svg();
  self.apply_zooms();
  self.create_clipping();
  self.create_pixels();
  self.data_block();
  self.create_labels();
  self.toggle_pan_and_zoom(pan_bool);
  self.create_tooltip();
  self.get_data_values(raw_data);

}
