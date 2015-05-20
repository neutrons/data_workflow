//
// Main menu template
//
var data_menu = {
	  "options": {
			  "name": "Options",
				"class": "options-menu",
				"list": "options-list",
				"buttons": [
					  {
					    "id": "log_scale",
							"icon": "menu-icon fa fa-square-o",
							"name": "Log Scale",
							"sub_menu": false
				    },
						{
					    "id": "view_grid",
							"icon": "menu-icon fa fa-square-o",
							"name": "View Grid",
							"sub_menu": false
				    },
						{
					    "id": "color_picker",
							"icon": "menu-icon fa fa-pencil-square-o",
							"name": "Color",
							"sub_menu": false
				    },
						{
					    "id": "",
							"icon": "menu-icon fa fa-font",
							"name": "Axis Labels",
							"sub_menu": true,
							"sub_buttons": [
								{
									"id": "title_label",
									"icon": "menu-icon fa fa-font",
									"name": "Title",
									"sub_menu": false
								},
								{
									"id": "x_axis_label",
									"icon": "menu-icon fa fa-font",
									"name": "x-axis Label",
									"sub_menu": false
								},
								{
									"id": "y_axis_label",
									"icon": "menu-icon fa fa-font rotate-left",
									"name": "y-axis Label",
									"sub_menu": false
								}
							]
				    }
				]
		},
		"modes": {
			  "name": "Modes",
				"class": "modes-menu",
				"list": "modes-list",
				"buttons": [
					  {
					    "id": "pan_and_zoom",
							"icon": "menu-icon fa fa-circle",
							"name": "Pan and Zoom",
							"sub_menu": false
				    },
						{
					    "id": "select_region",
							"icon": "menu-icon fa fa-circle-thin",
							"name": "Select Region",
							"sub_menu": false
				    }
				]
		},
		"export": {
		    "name": "Export",
				"class": "export-menu",
				"list": "export-list",
				"buttons": [
					  {
					    "id": "export_pdf",
							"icon": "menu-icon fa fa-file-pdf-o",
							"name": "PDF",
							"sub_menu": false
				    },
						{
					    "id": "export_png",
							"icon": "menu-icon fa fa-file-image-o",
							"name": "PNG",
							"sub_menu": false
				    },
						{
					    "id": "export_svg",
							"icon": "menu-icon fa fa-file-image-o",
							"name": "SVG",
							"sub_menu": false
				    }
				]
		},
		"help": {
			  "name": "Help",
				"class": "help-menu",
				"list": "help-list",
				"buttons": [
					  {
							"id": "topics",
							"icon": "menu-icon fa fa-book",
							"name": "Topics",
							"sub_menu": false
						},
					  {
							"id": "about",
							"icon": "menu-icon fa fa-info-circle",
							"name": "About",
							"sub_menu": false
						}
				]
		}
}
var tplt_menu = '<ul>' +
		'<li class="has-sub"><a href="#" class="[[options.class]]">[[options.name]]</a>' +
			'<ul class="[[options.list]]">' +
			'[[#options.buttons]]' +
				'<li[[#sub_menu]] class="has-sub"[[/sub_menu]]><span>' +
				  '<a id="[[id]]" href="#"><i class="[[icon]]"></i>[[name]]</a></span>' +
					'[[#sub_menu]]<ul>[[#sub_buttons]]' +
					'<li><span><a id="[[id]]" href="#"><i class="[[icon]]"></i>[[name]]</a></span></li>' +
					'[[/sub_buttons]]</ul>[[/sub_menu]]' +
					'</li>' +
			'[[/options.buttons]]' +
		'</ul></li>' +
		'<li class="has-sub"><a href="#" class="[[modes.class]]">[[modes.name]]</a>' +
			'<ul class="[[modes.list]]">' +
			'[[#modes.buttons]]' +
				'<li[[#sub_menu]] class="has-sub"[[/sub_menu]]><span>' +
				  '<a id="[[id]]" href="#"><i class="[[icon]]"></i>[[name]]</a></span>' +
					'[[#sub_menu]]<ul>[[#sub_buttons]]' +
					'<li><span><a id="[[id]]" href="#"><i class="[[icon]]"></i>[[name]]</a></span></li>' +
					'[[/sub_buttons]]</ul>[[/sub_menu]]' +
					'</li>' +
			'[[/modes.buttons]]' +
		'</ul></li>' +
		'<li class="has-sub"><a href="#" class="[[export.class]]">[[export.name]]</a>' +
			'<ul class="[[export.list]]">' +
			'[[#export.buttons]]' +
				'<li[[#sub_menu]] class="has-sub"[[/sub_menu]]><span>' +
				  '<a id="[[id]]" href="#"><i class="[[icon]]"></i>[[name]]</a></span>' +
					'[[#sub_menu]]<ul>[[#sub_buttons]]' +
					'<li><span><a id="[[id]]" href="#"><i class="[[icon]]"></i>[[name]]</a></span></li>' +
					'[[/sub_buttons]]</ul>[[/sub_menu]]' +
					'</li>' +
			'[[/export.buttons]]' +
		'</ul></li>' +
		'<li class="has-sub"><a href="#" class="[[help.class]]">[[help.name]]</a>' +
			'<ul class="[[help.list]]">' +
			'[[#help.buttons]]' +
				'<li[[#sub_menu]] class="has-sub"[[/sub_menu]]><span>' +
				  '<a id="[[id]]" href="#"><i class="[[icon]]"></i>[[name]]</a></span>' +
					'[[#sub_menu]]<ul>[[#sub_buttons]]' +
					'<li><span><a id="[[id]]" href="#"><i class="[[icon]]"></i>[[name]]</a></span></li>' +
					'[[/sub_buttons]]</ul>[[/sub_menu]]' +
					'</li>' +
			'[[/help.buttons]]' +
		'</ul></li>' +
    '</ul>';

//
// Console items for boundary and zoom
//
var data_console_item = {
    snap_bounds: [{
            name: "Left",
            class: "left"
        },
        {
            name: "Right",
            class: "right"
        }
    ],
		zoom: [{
		        name: "Zoom",
						class: "zoom"
				}
		]
};
var tplt_console_region = '<span class="console-item" id="snap_bounds">' +
    '<b><span class="console-input id"></span></b> - ' +
    '[[#snap_bounds]]' +
    '[[name]]: <input class="console-input [[class]]" disabled value="0"> ' +
    '[[/snap_bounds]]' +
    '</span>';
var tplt_console_zoom = '<span class="console-item" id="zoom">' +
    '[[#zoom]]' +
		'[[name]]: <input class="console-input [[class]]" disabled value="100%">' +
		'[[/zoom]]' +
		'</span>';

//
// Buttons for modal object
//
var modal_buttons = "<div class='modal-buttons'><a href='#' class='modal-cancel button'>Cancel</a>" +
    "<a href='#' class='modal-submit button'>Submit</a></div>";
var close_button = "<div class='modal-buttons'><a href='#' class='modal-close button'>Close</a></div>";

//
// Dimensions data for backdrop, modal, and sidebar objects
//
var data_objs = {
    "name": "",
    "top": 0,
    "left": 0,
    "width": 0,
    "height": 0
}
var tplt_backdrop = "<div class='backdrop' style='top:[[top]]; left:[[left]];" +
    "width:[[width]]px; height:[[height]]px;'></div>";
var tplt_modal = "<div class='modal-window' id='[[name]]_modal' name='[[name]]'" +
    " style='top:[[top]]px; left:[[left]]px; width:[[width]]px;" +
    " height:[[height]]px;'></div>";
var tplt_sidebar = "<div class='sidebar' id='[[name]]_sidebar' name='[[name]]'" +
    " style='top:[[top]]px; left:[[left]]px; width:[[width]]px;" +
    " height:[[height]]px;'></div>";

//
// x Label
//
var data_x_label = {
    heading: "Change x-axis label",
    val: "test this first"
};
var tplt_x_label = "<div class='modal-heading'>[[heading]]<span>×</span></div>" +
    "<div class='modal-content'>Text: <input type='text' value='[[val]]'></input>" +
    "<br /><br />Align: <span><i class='fa fa-align-left'></i> " +
    "<i class='fa fa-align-center'></i> " +
    "<i class='fa fa-align-right'></i></span>" +
    "</div>" + modal_buttons;

//
// y Label
//
var data_y_label = {
    heading: "Change y-axis label",
    val: "test this first..."
};
var tplt_y_label = "<div class='modal-heading'>[[heading]]<span>×</span></div>" +
    "<div class='modal-content'>Text: <input type='text' value='[[val]]'></input>" +
    "<br /><br />Align: <span><i class='fa fa-align-left'></i> " +
    "<i class='fa fa-align-center'></i> " +
    "<i class='fa fa-align-right'></i></span>" +
    "</div>" + modal_buttons;

//
// Title
//
var data_title_label = {
    heading: "Change Title label",
    val: "test this first"
};
var tplt_title_label = "<div class='modal-heading'>[[heading]]<span>×</span></div>" +
    "<div class='modal-content'>Text: <input type='text' value='[[val]]'></input>" +
    "<br /><br />Align: <span><i class='fa fa-align-left'></i> " +
    "<i class='fa fa-align-center'></i> " +
    "<i class='fa fa-align-right'></i></span>" +
    "</div>" + modal_buttons;

//
// Color Picker
//
var data_color_picker = {
    heading: "Choose color"
};
var tplt_color_picker = "<div class='modal-heading'>[[heading]]<span>×</span></div>" +
    "<div class='modal-content'><input type='text' id='color_test' value='test'></input>" +
    "</div>" + modal_buttons;

//
// Select Region
//
var data_region = {
    "heading": "Regions",
    "info_table": [
        //{
        //"region_id": "test",
        //"region_name": "test",
        //"active": false,
        //"left": 2.71,
        //"right": 3.14,
        //"delete": false
        //}
    ]
};
var tplt_region = "<div class='sidebar-heading'>[[heading]]</div>" +
    "<div class='sidebar-content'><table id='info_table'>Visible regions:<thead>" +
    "<tr><th>ID</th>" +
    "<th>Active</th>" +
    "<th>Remove</th></tr>" +
    "</thead>" +
    "<tbody>" +
    "[[#info_table]]" +
    "<tr id='[[region_id]]_info'><td name='[[region_id]]'>[[region_name]]</td>" +
    "<td><input type='radio' name='regions' [[#active]] checked [[/active]]></input></td>" +
    "<td><a href='#' onclick='remove_region(\"[[region_id]]\")'><i class='fa fa-times'></i></a></td></tr>" +
    "[[/info_table]]" +
    "<tr id='new_row'><td><a href='#' id='link_add_region' onclick='add_region()'>Add</a></td><td></td>" +
		"<td><a href='#' onclick='remove_all_regions()'>Remove All</a></td></tr>" +
    "</tbody>" +
    "</table></div>"; // + buttons;

//
// Topics
//
var data_topics = {
	  heading: "Help Topics"
};
var tplt_topics = "<div class='modal-heading'>[[heading]]<span>×</span></div>" +
    "<div class='modal-content'>..." +
    "</div>" + close_button;

//
// About
//
var data_about = {
	  heading: "About"
};
var tplt_about = "<div class='modal-heading'>[[heading]]<span>×</span></div>" +
    "<div class='modal-content'><img src='/static/sns_logo_111x75.png' height='50%'><br>" +
		"ORNL Spallation Neutron Source" +
    "</div>" + close_button;

//
// Dummy row for regions table
//
var data_add_region;
var tplt_add_region = "<td>";
