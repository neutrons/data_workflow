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
        if ($(this).css("visibility") === "visible"){
            $(this).css("visibility", "hidden");
        }
    });
    if ($(".tooltip").length > 5){
        $("text.tooltip:lt(-5)").remove();
    }
    BarGraph(run_data, error_data, anchor, type);
}
