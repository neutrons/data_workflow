function global_system_status_update(data, i){
    var content = "<li class='status_"+data.instruments[i].dasmon_status+"' id='"+data.instruments[i].name+"_dasmon_status'>DASMON</li>";
    $('#'+data.instruments[i].name+'_dasmon_status').replaceWith(content);
    
    content = "<li class='status_"+data.instruments[i].pvstreamer_status+"' id='"+data.instruments[i].name+"_pvstreamer_status'>PVStreamer</li>";
    $('#'+data.instruments[i].name+'_pvstreamer_status').replaceWith(content);
    
    content = "<li class='status_"+data.postprocess_status.workflow+"' id='"+data.instruments[i].name+"_workflow_status'>Workflow</li>";
    $('#'+data.instruments[i].name+'_workflow_status').replaceWith(content);
    
    content = "<li class='status_"+data.postprocess_status.catalog+"' id='"+data.instruments[i].name+"_catalog_status'>Catalog</li>";
    $('#'+data.instruments[i].name+'_catalog_status').replaceWith(content);
    
    content = "<li class='status_"+data.postprocess_status.reduction+"' id='"+data.instruments[i].name+"_reduction_status'>Reduction</li>";
    $('#'+data.instruments[i].name+'_reduction_status').replaceWith(content);
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

function plot_combined_rates(run_data, error_data){
	var options = {
			xaxis: {
				show: true,
				min: -24,
				max: 1,
				ticks:[[-24, "-24 hrs"], [1, "last hour"]] 	
			},
			yaxis: { minTickSize:1 },
			shadowSize: 0,
			bars: {
				show: true,
				lineWidth: 1
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
	$.plot($("#runs_per_hour"), [ {label:"Number of runs [#/hr]", data:run_data},
	                              {label:"Number of errors [#/hr]", data:error_data, color:"#ED5B4B"} ],
	                              options);
}

function plot_monitor(monitor_data, element_id, label_text){
	var options = {
			xaxis: {
				show: true,
				tickFormatter: function (val, axis) { 
					if (val==0) {
						return "now";
					} else {
						return val;
					}
				},
			},
			yaxis: { 
				minTickSize:1,
				tickFormatter: function (val, axis) { 
					if (val>10000 || (val<0.0001&&val>0)) {
						return val.toExponential(); 
					} else {
						return val;
					}
				},
			},
			shadowSize: 0,
			bars: {
				show: false,
				lineWidth: 1
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
	$.plot($(element_id), [ {label:label_text, data:monitor_data} ],
	                              options);
}

