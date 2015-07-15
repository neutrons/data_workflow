


function Plot_2d(anchor, raw_data, qx, qy, max_iq, plot_options) {
	var self = this;
	self.anchor = anchor;
	self.raw_data = raw_data;
	self.qx = qx;
	self.qy = qy;
	self.max_iq = max_iq;
	self.plot_options = plot_options;
	var log_scale = this.plot_options.log_scale;
	var x_label = this.plot_options.x_label;
	var y_label = this.plot_options.y_label;
	var title = this.plot_options.title;
  var x_label_align = this.plot_options.x_label_align;
  var y_label_align = this.plot_options.y_label_align;
  var title_label_align = this.plot_options.title_label_align;
	var drag_init = false;
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
  plot_size.width = plot_size.width - margin.left - margin.right,
  plot_size.height = plot_size.height - margin.top - margin.bottom;


    var x = d3.scale.linear().range([0, plot_size.width]);
    var y = d3.scale.linear().range([plot_size.height, 0]);
    //x.domain(d3.extent(qx, function(d) { return d; })).nice();
    //y.domain(d3.extent(qy, function(d) { return d; })).nice();
    //x.domain([-1,1]);
    //y.domain([-1,1]);
		var x_min = d3.min(qx, function(d) {return d;});
		var x_max = d3.max(qx, function(d) {return d;})*1.1;
		var y_min = d3.min(qy, function(d) {return d;});
		var y_max = d3.max(qy, function(d) {return d;})*1.1;
    // x.domain([d3.min(qx, function(d) {return d;}), d3.max(qx, function(d) {return d;})*1.1]);
    // y.domain([d3.min(qy, function(d) {return d;}), d3.max(qy, function(d) {return d;})*1.1]);
		x.domain([x_min, x_max]);
		y.domain([y_min, y_max]);



	var xAxis = d3.svg.axis()
	                  .scale(x)
										.orient("bottom");
	var yAxis = d3.svg.axis()
	                  .scale(y)
										.orient("left");


  //
  // On zoom action, scale data points and line such that the paths
  // don't become too thick or too thin
  //
  this.scale_objects = function() {
		console.log("in scale_objects");
    // scale_factor = parseFloat(d3.transform(d3.select("#" + self.anchor + " path")
    //     .attr("transform"))
    //   .scale[0]);
	}

  //
  // Zoom and pan function for data path, point, error bar (if applicable),
  // and grid (if applicable). Then scales objects
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
		self.scale_objects();
	}

		var zoom_setup = d3.behavior.zoom()
		  .x(x)
			.y(y);
	  var zoom = zoom_setup
	    .on("zoom", self.zm);
		this.zoom_reset = function(){
			// console.log(self.zm);
			zoom_element = d3.select("." + anchor + " .pan");
			zoom_element.call(zoom);
			zoom.scale(1);
			zoom.translate([0,0]);
			zoom.event(zoom_element);

			// svg.call(zoom_setup.event().translate([0,0]).scale(1));
			// svg.call(self.zm.event.translate([0,0]).scale(1));
			//  .x()
			// 	.y()
			// 	.event);
		}

		var brush = d3.svg.brush()
						.x(x)
						.y(y)
						.on("brushstart", function(d){
						})
						.on("brush", function(d){
							// width = parseInt(d3.select(".extent").attr("width"));
							// height = parseInt(d3.select(".extent").attr("height"));
							// make square
							//if (height > width){
								////console.log("height: " + height)
								//d3.select(".extent").attr("width", height);
							//}
							//else if (width >= height){
								////console.log("width: " + width);
								//d3.select(".extent").attr("height", width);
							//}
							resize = d3.select(".resize .n");
						})
						.on("brushend", function(d){
							// pixel values
							// ul_x = parseInt(d3.select(".extent").attr("x"))
							// ul_y = parseInt(d3.select(".extent").attr("y"))
							// bl_x = ul_x
							// bl_y = ul_y + height
							// ur_x = ul_x + width
							// ur_y = ul_y
							// br_x = ul_x + width
							// br_y = ul_y + height
							//
							// // data values
							// ul_x = x.invert(ul_x)
							// ul_y = y.invert(ul_y)
							// console.log(ul_x)
							// console.log(ul_y)
							// bl_x = x.invert(bl_x)
							// bl_y = y.invert(bl_y)
							// ur_x = x.invert(ur_x)
							// ur_y = y.invert(ur_y)
							// br_x = x.invert(br_x)
							// br_y = y.invert(br_y)
						});

	// console.log(qx);

    // Remove old plot
    //d3.select("div").select("svg").remove();
    var svg = d3.select("#" + self.anchor).append("svg")
      .attr("class", "Spectral")
			.attr("id", self.anchor + "_svg")
      .attr("width", plot_size.width + margin.left + margin.right)
      .attr("height", plot_size.height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")")
      // .attr("class", self.anchor + "_main");

      var trans_scale = parseInt(plot_size.width) + parseInt(margin.left);
      d3.select(".Spectral")
      .append("g")
      .attr("transform", "translate(" + trans_scale + "," + margin.top + ")")
      .attr("class", "scale");

  //
  // Create clipping reference for zoom element
  //
  clip = svg.append("defs")
    .append("clipPath")
    .attr("id", "clip")
    .append("rect")
    .attr("id", "clip-rect")
    .attr("x", 0)
    .attr("y", 0)
    .attr("width", plot_size.width)
    .attr("height", plot_size.height);


    // Scale up the calculated pixel width so that we don't produce visual artifacts
    var adj_pixel_h = 0.9*(y(qy[0])-y(qy[1]));
    var adj_pixel_w = 0.9*(x(qx[1])-x(qx[0]));
		var adj_pixel_stroke = Math.max(0.1*(x(qx[1])-x(qx[0])), 0.1*(y(qy[0])-y(qy[1])));
		console.log(adj_pixel_h);
		console.log(adj_pixel_stroke);

    var n_colors = 64;
    var quantize;
    if (log_scale) {
      var bins = [];
      var step = Math.log(max_iq+1.0)/(n_colors-1);
      for (i=0; i<n_colors-1; i++) {
        bins.push(Math.exp(step*i)-1.0);
      }
      quantize = d3.scale.threshold()
      .domain(bins)
      .range(d3.range(n_colors).map(function(i) { return get_color(i, n_colors); }));
    } else {
        var quantize = d3.scale.quantize()
        .domain([0, max_iq])
        .range(d3.range(n_colors).map(function(i) {
					//console.log(get_color(i, n_colors));
					return get_color(i, n_colors);
				}));

    };

  svg.append('g')
	  .attr('class', 'main_plot')
		.append('g')
		.attr('class', 'data_block')
	  .selectAll('g')
    .data(raw_data)
    .enter()
    .append('g')
    .attr("transform", function(d,i) {
			var trans = y(qy[i])-adj_pixel_h;
			return "translate(0,"+ trans + ")";
	  })
    .selectAll('rect')
    .data(function(d) { return d; })
    .enter()
    .append('rect')
		.attr('class', 'pixel')
    .attr('x', function(d,i) { return x(qx[i]); })
    .attr('y', function(d,i) { return 0; })
    .attr('width', function(d,i) { return adj_pixel_w; })
    .attr('height', function(d,i) { return adj_pixel_h; })
    .attr('fill', function(d) { return quantize(d); })
		.attr('stroke', function(d) { return quantize(d); })
		.attr('stroke-width', adj_pixel_stroke);
    svg.append("g").attr("class", "x axis")
				   .attr("transform", "translate(0," + plot_size.height + ")").call(xAxis);
    svg.append("g").attr("class", "y axis").call(yAxis);


  // Reference to clip object
  d3.select("." + self.anchor + " .main_plot").attr("clip-path", "url(#clip)");

    // d3.select(".scale")
    //   .append('rect')
    //   .attr('x', 10)
    //   .attr('y', 2)
    //   .attr('width', 50)
    //   .attr('height', plot_size.height)
		// .data(data)
		// .enter()
    // .attr('fill', function(d) { return quantize(d); })

this.create_labels = function(){
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
	.attr("y", plot_size.height+margin.top+15)
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
	.attr("y", 4-margin.left)
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
self.create_labels();



  var pan_flag = true;
	this.toggle_pan_and_zoom = function(pan_flag){
      // pan = d3.select("#" + self.anchor + " .main_plot").insert("rect", "g")
		var pan
		if (pan_flag == true){
      console.log("wanna pan and zoom?");
      pan = d3.select("#" + self.anchor + " .main_plot").append("rect")
        .attr("class", "pan")
        .attr("width", plot_size.width)
        .attr("height", plot_size.height)
        .call(zoom);
		}
		else{
			// console.log("want to see values?");
			d3.select("rect.pan").remove();
		}
	}
  self.toggle_pan_and_zoom(pan_flag);



  //
  // Enable d3 brush for regions mode
  //
  // this.enable_brush = function() {
  //   d3.select("#" + self.anchor + " .main_plot")
	// 	  .call(brush);
  // }

function get_color(i, n_max) {
    var n_divs = 4.0;
    var phase = 1.0*i/n_max;
    var max_i = 210;
    if (phase<1.0/n_divs) {
        b = max_i;
        r = 0;
        g = Math.round(max_i*Math.abs(Math.sin(Math.PI/2.0*i/n_max*n_divs)));
    } else if (phase<2.0/n_divs) {
        b = Math.round(max_i*Math.abs(Math.cos(Math.PI/2.0*i/n_max*n_divs)));
        r = 0;
        g = max_i;
    } else if (phase<3.0/n_divs) {
        b = 0;
        r = Math.round(max_i*Math.abs(Math.sin(Math.PI/2.0*i/n_max*n_divs)));
        g = max_i;
    } else if (phase<4.0/n_divs) {
        b = 0;
        r = max_i;
        g = Math.round(max_i*Math.abs(Math.cos(Math.PI/2.0*i/n_max*n_divs)));
    }
    r = r + 30;
    g = g + 30;
    return 'rgb('+r+','+g+','+b+')';
}

  //
  // Tooltip obj
  //
  var tooltip = d3.select("body")
    .append("text")
    .attr("class", "tooltip")
    .style("position", "absolute")
    .style("z-index", "2010")
    .style("visibility", "hidden")
    .style("color", "black");


  //
  // Get data values on hover event
  //
  function get_data_values(d) {
    svg.selectAll(".pixel")
      .on("mouseover", function(d, i) {
				// console.log(i);
				// console.log(d3.select(this).attr("width"));
				// console.log(this);
				// var copy = this;
				// d3.select(".data_block").append(this)
				d3.select(this)
				  .attr("stroke", "#000")
					.attr("stroke-alignment", "inner")
				  .attr("stroke-width", adj_pixel_stroke)
        mouseover(d);
      })
      .on("mousemove", function(d, i) {
				// console.log(i);
        mousemove(d);
      })
      .on("mouseout", function(d) {
				var color = d3.select(this).attr("fill");
				d3.select(this).attr("stroke", color)
				  .attr("stroke-width", adj_pixel_stroke)
        mouseout(d);
      });
  }
  get_data_values(raw_data);

  //
  // Show data values and outline when mouse enters data point
  //
  function mouseover(d) {
    mouseY = 0;
    mouseX = 0;
    tooltip.style("visibility", "visible");
    if (window.Event && document.captureEvents)
      document.captureEvents(Event.MOUSEOVER);
    document.onmouseover = getMousePos;
    tooltip.text(d3.round(d, 3));
    tooltip.style("top", (mouseY - 10) + "px")
      .style("left", (mouseX + 10) + "px");
  }

  //
  // Follow mouse near data point
  //
  function mousemove(d) {
    tooltip.style("visibility", "visible");
    if (window.Event && document.captureEvents)
      document.captureEvents(Event.MOUSEMOVE);
    document.onmousemove = getMousePos;
    tooltip.text(d3.round(d, 3));
    tooltip.style("top", (mouseY - 10) + "px")
      .style("left", (mouseX + 10) + "px");
  }

  //
  // Hide data values and outline when mouse leaves data point
  //
  function mouseout(d) {
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

}
