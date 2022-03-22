function global_system_status_update(data, i){
    var content = "<span id='"+data.instruments[i].name+"_recording_status'>"+data.instruments[i].recording_status+"</span>";
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
    $('#workflow_status').replaceWith("<li class='status_"+data.das_status.workflow+"' id='workflow_status'>Workflow</li>");
}

var plotted_data = [];
var plot_timeframe = '7200';
var Plots = new Array();
var ie = ie_flag();

function ie_flag(){
	var ua = window.navigator.userAgent;
	var msie = ua.indexOf('MSIE ');
	if (msie > 0){
		// IE 10 or older
		return true;
	}
	var trident = ua.indexOf('Trident/');
	if (trident > 0){
		// IE 11 =>
		return true;
	}
	var edge = ua.indexOf('Edge/');
	if (edge > 0){
	   // IE 12 =>
		return true;
	}
	// other browser
	return false;
}
//************************************************************************80
// FUNCTION: new_monitor
//
// Desc: creates an instance of MonitorPlot onclick and stores
//       in Plots array
//
// Variables: dialog_win_generated, nid
//
//************************************************************************80
function new_monitor(element_id, option){
	var dialog_win_generated = false;   // dialog_win already exists? flag
	var nid = Plots.length;             // numeric id
	for (var i=0; i<Plots.length; i++){
		// Go through Plots
		if (Plots[i].element_id === element_id){
			dialog_win_generated = true;
			nid = i;
		}
	}
	if (dialog_win_generated === false){
		// If dialog win has not been generated already
		Plots.push(1);
		nid = Plots.length-1;
		// Create new instance of MonitorPlot
		Plots[nid] = new MonitorPlot(element_id, nid, option);
	}
	else if (dialog_win_generated === true){
		// If dialog win has been generated already get plot
		Plots[nid].option = option;
	}
	Plots[nid].pop_monitor_plot();
}

//************************************************************************80
// OBJECT: MonitorPlot
//
// Desc: handles each plot on monitor page
//
// Variables: element_id, nid, clean_name, dialog_name
//            dialog_win, plot_id, plot_content, submenu,
//            plot_options{},
//
// Methods: pop_monitor_plot, prepare_menu, local_options,
//          check_scale, close_l_opt
//
//************************************************************************80
function MonitorPlot(element_id, nid, option){

	var options_icon;
	var close_icon;
	if (ie === true){
		options_icon = "<span class='flaticon'><img src='/static/thirdparty/flaticon/icons/options.png' width='16' height='15'></span>";
		close_icon = "<span class='flaticon' style='float:right'><img src='/static/thirdparty/flaticon/icons/close.png' width='11' height='11'></span>";
	}
	else{
		options_icon = "<span class='flaticon flaticon-settings22'></span>";
		close_icon = "<span class='flaticon flaticon-close19' style='float:right'></span>";
	}
	this.element_id = element_id;
	this.nid = nid;
	this.option = option;
	this.clean_name = element_id.replace(/(:|\.)/g, '_');
	this.dialog_name = this.clean_name + "_dialog";
	this.dialog_win;
	this.plot_id = this.clean_name + "_plot";
	this.plotted_data = [];
	this.plot_content =
		"<div id='" + this.dialog_name + "' title='" + this.element_id + "' name='" + this.element_id + "'>" +
		"    <div class='live_plots'>" +
		"        <div class='options' style='float:left'>" +
		"            <a class='flaticon_link' title='Local Options' " +
		"                onclick='Plots[" + nid + "].local_options(\"" + this.dialog_name + "\")'>" + options_icon + // change onclick function to Plots.prepare_menu if adding global options capability
	"			</a>" +
		"        </div>" +
		"    </div><br><br>" +
		"    <div class='plot_timeframe'>" +
		"        <a style='outline:none;' href='javascript:void(0);' onClick='max_timeframe(\"900\");'>15m</a> | " +
		"        <a style='outline:none;' href='javascript:void(0);' onClick='max_timeframe(\"7200\");'>2h</a> | " +
		"        <a style='outline:none;' href='javascript:void(0);' onClick='max_timeframe(\"86400\");'>max</a> " +
		"    </div><br>" +
		"    <div id='" + this.clean_name + "_plot'></div>" +
		"    </div>" +
		"</div>";
	this.plot_options = {
		// plot options here!
		log_scale: false,
		psize: {width: 485, height: 250}
	}
	this.pop_monitor_plot = function(){
		// Create dialog box for plot and call poll
		if ($("#" + this.dialog_name).length === 0){
			var element_id = this.element_id;
			var dialog_name = this.dialog_name;
			var nid = this.nid;
			var plot_id = this.plot_id;
			$('#dialog_placeholder').append(this.plot_content);
			$("#" + this.dialog_name).dialog({
				width: 535,
				height: 380,
				minWidth: 265,
				minHeight: 250,
				dialogClass: "plot_class",
				resizable: true,
				closeOnEscape: true,
				resize: function(event, ui){
					dialog_resize(event, ui, nid, this);
				},
				close: function(event, ui) {
					Plots[nid].option = "0";
					Plots[nid].plot_options.psize = {width: 485, height: 250}; // restore default size
					$("#" + dialog_name).remove();
					if($("#" + dialog_name + "_submenu").length > 0){
						$("#" + dialog_name + "_submenu").remove();
					}
				},
				open: function (event, ui) {
					$("#" + this.dialog_name).css('overflow', 'hidden'); //this line does the actual hiding
				}
			});
			// Get dialog window DOM element
			this.dialog_win = $("#" + this.dialog_name).parent();
			//resize_dialog(element_id);
		}
		else{ // Move dialog box to the top if it is already open
			var hi_z = 100;
			$("#" + this.dialog_name).parent().siblings(".ui-dialog").addBack().each(function(){
				if (hi_z < $(this).css("z-index")){
					hi_z = $(this).css("z-index");
				}
			});
			hi_z = parseInt(hi_z) + 1;
			$("#" + this.dialog_name).parent().css("z-index", hi_z);
		}
		poll();
	}
	// Uncomment the following block if adding global options capability
	//this.submenu = '<div id="' + this.dialog_name +
	//               '_submenu" class="submenu"><a id="local_options_link" ' +
	//               'class="ui-button" onclick="Plots[' + nid + '].local_options(\'' +
	//               this.dialog_name + '\')" style="width:88px">Local options</a><br>' +
	//               '<a id="global_options_link" class="ui-button" ' +
	//               'onclick="global_options(\'' + this.dialog_name +
	//               '\')" style="width:88px">Global options</a></div>';
	//this.prepare_menu = function(){
	//    // Toggle submenu (for plot options)
	//    if($("#" + this.dialog_name + "_submenu").length === 0){
	//        $("#" + this.dialog_name + " .options").append(this.submenu);
	//    } else if($("#" + this.dialog_name + "_submenu").length > 0){
	//        $("#" + this.dialog_name + "_submenu").remove();
	//    }
	//}
	this.local_options = function(){
		// Uncomment the following block if adding global options capability
		//if($("#" + this.dialog_name + "_submenu").length > 0){
		//    // Remove submenu if it's open
		//    $("#" + this.dialog_name + "_submenu").remove();
		//}
		if ($("#local_options_" + this.dialog_name).length === 0){
			var cur_height = $(this.dialog_win).height();
			var new_height = cur_height + 100;
			var lin_radio;
			var log_radio;
			var html;
			if (this.plot_options.log_scale === false){
				lin_radio = "checked='checked'"; log_radio = "";
			}
			else{
				log_radio = "checked='checked'"; lin_radio = "";
			}
			html = "<div id='local_options_" + this.dialog_name + "' style='height:100px;border-top:1px solid lightgrey;padding:5px'>" +
				   "<a class='flaticon_link' onclick='Plots[" + nid + "].close_l_opt(\"local_options_" + this.dialog_name + "\")'>" + close_icon +
				   "</a>" +
				   "<h3>Local Options</h3>" +
				   "<form name='form_" + this.dialog_name + "'>" +
				   "<div id='radio_" + this.dialog_name + "'>y scale: <input type='radio' class='check_scale' " +
				   "id='scale_log_" + this.dialog_name + "' name='radio' " + log_radio + "onclick='Plots[" + nid + "].check_scale()'>" +
				   "<label for='scale_log_" + this.dialog_name + "' id='scale_log_label_" + this.clean_name + "'>log</label>" +
				   "<input type='radio' class='check_scale' id='scale_lin_" + this.dialog_name + "' name='radio' " + lin_radio +
				   "onclick='Plots[" + nid + "].check_scale()'>" +
				   "<label for='scale_lin_" + this.dialog_name + "' id='scale_lin_label_" + this.clean_name + "'>linear</label></div></form></div>";
			this.dialog_win.css("height", new_height);
			$("#" + this.dialog_name).after(html);
			$("#radio_" + this.dialog_name).buttonset();
		}
		// Remove the following block if adding global options capability
		else if ($("#local_options_" + this.dialog_name).length > 0){
			Plots[nid].close_l_opt("local_options_" + this.dialog_name)
		}
	}
	this.check_scale = function(){
		// Change scale
		if ($("#scale_log_label_" + this.clean_name).hasClass("ui-state-active")){
			this.plot_options.log_scale = true;
			poll();
		}
		else if ($("#scale_lin_label_" + this.clean_name).hasClass("ui-state-active")){
			this.plot_options.log_scale = false;
			poll();
		}
	}
	this.close_l_opt = function(){
		// Close local options bar
		var cur_height = $(this.dialog_win).height();
		var new_height = cur_height - 100;
		this.dialog_win.css("height", new_height);
		$("#local_options_" + this.dialog_name).remove();
	}
}

function dialog_resize(event, ui, nid, s){
	var adj_size = {width: $(s).width()-25, height: $(s).height()-80};
	Plots[nid].plot_options.psize = adj_size;
	plot_1d(Plots[nid].plotted_data, Plots[nid].plot_id, Plots[nid].plot_options)
}


function max_timeframe(time_period){
	plot_timeframe = time_period;
	poll();
}

function global_options(dialog_name){
	if ($("#" + dialog_name + "_submenu").length > 0){
		// Remove submenu if it's open
		$("#" + dialog_name + "_submenu").remove();
	}
	if ($("#global_options").length === 0){
		// If global options dialog box doesn't exist make one
		var g_opt_win = "<div id='global_options' title='Global options'>" +
						"<h3>Global options</h3>" +
						"Global options settings</div>";
		$("#dialog_placeholder").append(g_opt_win);
		$("#global_options").dialog({
			width: 400,
			height: 280,
			resizable: true,
			closeOnEscape: true,
			close: function( event, ui ){
				$("#global_options").remove();
			}
		});
	}
	else{ // If global options dialog box exists move to top
		$("#global_options").dialog({
			position: 'top'
		});
	}
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
