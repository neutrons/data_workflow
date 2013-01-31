function plot_rates(run_data, error_data){
	var options = {
			xaxis: {
				show: true,
				ticks:[[1, "-24 hrs"], [25, "last hour"]] 	
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
	$.plot($("#runs_per_hour"), [ {label:"Number of runs [#/hr]", data:run_data} ], options);
	$.plot($("#errors_per_hour"), [ {label:"Number of errors [#/hr]",
										data:error_data,
										color:"#ED5B4B"} ], options);
}
