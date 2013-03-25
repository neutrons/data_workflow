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
	$.plot($(element_id), [ {label:label_text, data:monitor_data} ],
	                              options);
}

