function global_system_status_update(data, i){
    var content = "<li class='status_"+data.instruments[i].dasmon_status+"' id='"+data.instruments[i].name+"_dasmon_status'>DASMON</li>";
    $('#'+data.instruments[i].name+'_dasmon_status').replaceWith(content);
    
    content = "<li class='status_"+data.instruments[i].pvstreamer_status+"' id='"+data.instruments[i].name+"_pvstreamer_status'>PVStreamer</li>";
    $('#'+data.instruments[i].name+'_pvstreamer_status').replaceWith(content);
    
    content = "<span id='"+data.instruments[i].name+"_recording_status'>"+data.instruments[i].recording_status+"</span>";
    $('#'+data.instruments[i].name+'_recording_status').replaceWith(content);
    return content
}

function update_from_ajax_data(data){
    for (var i=0; i<data.variables.length; i++)
    { 
        if (data.variables[i].key=='count_rate')
            $('#count_rate_top').replaceWith("<span id='count_rate_top'>"+data.variables[i].value+"</span>");
        
        $('#'+data.variables[i].key).replaceWith("<span id='"+data.variables[i].key+"'>"+data.variables[i].value+"</span>");
        $('#'+data.variables[i].key+'_timestamp').replaceWith("<span id='"+data.variables[i].key+"_timestamp'>"+data.variables[i].timestamp+"</span>");
    }

    $('#dasmon_status').replaceWith("<li class='status_"+data.das_status.dasmon+"' id='dasmon_status'>DASMON</li>");
    $('#pvstreamer_status').replaceWith("<li class='status_"+data.das_status.pvstreamer+"' id='pvstreamer_status'>PVStreamer</li>");
    $('#workflow_status').replaceWith("<li class='status_"+data.das_status.workflow+"' id='workflow_status'>Workflow</li>");
    $('#catalog_status').replaceWith("<li class='status_"+data.das_status.catalog+"' id='catalog_status'>Catalog</li>");
    $('#reduction_status').replaceWith("<li class='status_"+data.das_status.reduction+"' id='reduction_status'>Reduction</li>");
}

function plot_combined_rates(run_data, error_data, anchor, parameters){
	type = (typeof parameters === "undefined") ? "detailed" : parameters;
	anchor = (typeof anchor === "undefined") ? "runs_per_hour" : anchor;

	$(".tooltip").each(function(){
		if ($(this).css("visibility") === "hidden"){
			//console.log("this is hidden");
			$(this).remove();
		}
		else if ($(this).css("visibility") === "visible"){
			throw new Error("");
		}
	});
	BarGraph(run_data, error_data, anchor, type);
}

function plot_monitor(monitor_data, element_id, label_text){
	var options = {
			xaxis: {
				minTickSize:0.01,
				show: true,
				tickFormatter: function (val, axis) { 
					if (val==0) {
						return "now";
					} else {
						return val.toFixed(1);
					}
				},
			},
			yaxis: { 
				minTickSize:0.0001,
				tickFormatter: function (val, axis) { 
					if (val>10000 || (val<0.0001&&val>0)) {
						return val.toExponential(4); 
					} else {
						return val.toPrecision(4);
					}
				},
			},
			shadowSize: 0,
			lines: {
				show: true,
				steps: true
			},
			grid: { 
				color: "#5e5e5e",
				borderWidth: 1
			},
			legend: {
				show: true,
				position: 'nw'
			}
	};
	
	if (window.plotted_monitor_vars == null)
		window.plotted_monitor_vars = [];
	
	if ($.inArray(element_id, window.plotted_monitor_vars)>=0) { 
		options.yaxis.transform = function (v) { return Math.log(v); };
		options.yaxis.inverseTransform = function (v) { return Math.exp(v); };
		
		var ymin = -1.0;
		for (i=0; i<monitor_data.length; i++) {
			val = +monitor_data[i][1];
			if (val>0.0 && val<ymin) ymin = val;
			if (ymin<0.0 && val>0.0) ymin = val;
		}
		options.yaxis.min = ymin;
	};
	
	var plot = $.plot($(element_id), [ {label:label_text, data:monitor_data} ],
	                              options);
	$.each(plot.getAxes(), function (i, axis) {
		if (!axis.show)
			return;
		
		if (axis.direction != "y")
			return;

		var box = axis.box;

		$("<div class='axisTarget' style='position:absolute; left:" + box.left + "px; top:" + box.top + "px; width:" + box.width +  "px; height:" + box.height + "px'></div>")
			.data("axis.direction", axis.direction)
			.data("axis.n", axis.n)
			.css({ backgroundColor: "#f00", opacity: 0, cursor: "pointer" })
			.appendTo(plot.getPlaceholder())
			.hover(
				function () { $(this).css({ opacity: 0.10 }) },
				function () { $(this).css({ opacity: 0 }) }
			)
			.click(function () {
				if ($.inArray(element_id, window.plotted_monitor_vars)>=0) { 
					var var_index = window.plotted_monitor_vars.indexOf(element_id);
					window.plotted_monitor_vars.splice(var_index, 1);
				} else {
					window.plotted_monitor_vars.push(element_id); 
				};
				plot_monitor(monitor_data, element_id, label_text);
			});
	});
}

