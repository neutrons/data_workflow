function mustachetemplates(i){

    var anchor = plots[i].anchor;
    //
    // Main menu template
    //
    plots[i].data_menu = {
      "options":
      {
        "name": "Options",
        "class": "options-menu",
        "list": "options-list",
        "buttons": [
        {
          "class": "log_scale",
          "icon": "menu-icon fa fa-line-chart",
          "name": "Log Scale",
          "sub_menu": true,
          "sub_buttons": [
          {
            "class": "log_scale_x",
            "icon": "menu-icon fa fa-square-o",
            "name": "x-axis Log Scale",
            "sub_menu": false
          },
          {
            "class": "log_scale_y",
            "icon": "menu-icon fa fa-square-o",
            "name": "y-axis Log Scale",
            "sub_menu": false
          }]
        },
        {
          "class": "view_grid",
          "icon": "menu-icon fa fa-square-o",
          "name": "View Grid",
          "sub_menu": false
        },
        {
          "class": "color_picker",
          "icon": "menu-icon fa fa-pencil-square-o",
          "name": "Color",
          "sub_menu": false
        },
        {
          "class": "",
          "icon": "menu-icon fa fa-font",
          "name": "Axis Labels",
          "sub_menu": true,
          "sub_buttons": [
          {
            "class": "title_label",
            "icon": "menu-icon fa fa-font",
            "name": "Title",
            "sub_menu": false
          },
          {
            "class": "x_axis_label",
            "icon": "menu-icon fa fa-font",
            "name": "x-axis Label",
            "sub_menu": false
          },
          {
            "class": "y_axis_label",
            "icon": "menu-icon fa fa-font rotate-left",
            "name": "y-axis Label",
            "sub_menu": false
          }]
        }]
      },
      "modes":
      {
        "name": "Modes",
        "class": "modes-menu",
        "list": "modes-list",
        "buttons": [
        {
          "class": "pan_and_zoom",
          "icon": "menu-icon fa fa-circle",
          "name": "Pan and Zoom",
          "sub_menu": true,
          "sub_buttons": [
          {
            "class": "zoom_100",
            "icon": "menu-icon fa fa-search",
            "name": "Zoom 100%",
            "sub_menu": false
          }
          ]
        },
        {
          "class": "select_region",
          "icon": "menu-icon fa fa-circle-thin",
          "name": "Select Region",
          "sub_menu": false
        }]
      },
      "export":
      {
        "name": "Export",
        "class": "export-menu",
        "list": "export-list",
        "buttons": [
        // {
        //   "class": "export_pdf",
        //   "icon": "menu-icon fa fa-file-pdf-o",
        //   "name": "PDF",
        //   "sub_menu": false
        // },
        {
          "class": "export_png",
          "icon": "menu-icon fa fa-file-image-o",
          "name": "PNG",
          "sub_menu": false
        },
        {
          "class": "export_svg",
          "icon": "menu-icon fa fa-file-image-o",
          "name": "SVG",
          "sub_menu": false
        }
        ]
      }
      // Uncomment to add Help menu
      // "help":
      // {
      //   "name": "Help",
      //   "class": "help-menu",
      //   "list": "help-list",
      //   "buttons": [
      //   {
      //     "class": "topics",
      //     "icon": "menu-icon fa fa-book",
      //     "name": "Topics",
      //     "sub_menu": false
      //   },
      //   {
      //     "class": "about",
      //     "icon": "menu-icon fa fa-info-circle",
      //     "name": "About",
      //     "sub_menu": false
      //   }]
      // }
    }
    plots[i].tplt_menu = '<ul>' +
      '<li class="has-sub"><a href="#/" class="[[options.class]]">[[options.name]]</a>' +
        '<ul class="[[options.list]]">' +
        '[[#options.buttons]]' +
          '<li[[#sub_menu]] class="has-sub"[[/sub_menu]]><span>' +
            '<a class="[[class]]" href="#/"><i class="[[icon]]"></i>[[name]]</a></span>' +
            '[[#sub_menu]]<ul>[[#sub_buttons]]' +
            '<li><span><a class="[[class]]" href="#/"><i class="[[icon]]"></i>[[name]]</a></span></li>' +
            '[[/sub_buttons]]</ul>[[/sub_menu]]' +
            '</li>' +
        '[[/options.buttons]]' +
      '</ul></li>' +
      '<li class="has-sub"><a href="#/" class="[[modes.class]]">[[modes.name]]</a>' +
        '<ul class="[[modes.list]]">' +
        '[[#modes.buttons]]' +
          '<li[[#sub_menu]] class="has-sub"[[/sub_menu]]><span>' +
            '<a class="[[class]]" href="#/"><i class="[[icon]]"></i>[[name]]</a></span>' +
            '[[#sub_menu]]<ul>[[#sub_buttons]]' +
            '<li><span><a class="[[class]]" href="#/"><i class="[[icon]]"></i>[[name]]</a></span></li>' +
            '[[/sub_buttons]]</ul>[[/sub_menu]]' +
            '</li>' +
        '[[/modes.buttons]]' +
      '</ul></li>' +
      '<li class="has-sub"><a href="#/" class="[[export.class]]">[[export.name]]</a>' +
        '<ul class="[[export.list]]">' +
        '[[#export.buttons]]' +
          '<li[[#sub_menu]] class="has-sub"[[/sub_menu]]><span>' +
            '<a class="[[class]]" href="#/"><i class="[[icon]]"></i>[[name]]</a></span>' +
            '[[#sub_menu]]<ul>[[#sub_buttons]]' +
            '<li><span><a class="[[class]]" href="#/"><i class="[[icon]]"></i>[[name]]</a></span></li>' +
            '[[/sub_buttons]]</ul>[[/sub_menu]]' +
            '</li>' +
        '[[/export.buttons]]' +
      '</ul></li>' +
      // Uncomment to add Help menu
      // '<li class="has-sub"><a href="#/" class="[[help.class]]">[[help.name]]</a>' +
      //   '<ul class="[[help.list]]">' +
      //   '[[#help.buttons]]' +
      //     '<li[[#sub_menu]] class="has-sub"[[/sub_menu]]><span>' +
      //       '<a class="[[class]]" href="#/"><i class="[[icon]]"></i>[[name]]</a></span>' +
      //       '[[#sub_menu]]<ul>[[#sub_buttons]]' +
      //       '<li><span><a class="[[class]]" href="#/"><i class="[[icon]]"></i>[[name]]</a></span></li>' +
      //       '[[/sub_buttons]]</ul>[[/sub_menu]]' +
      //       '</li>' +
      //   '[[/help.buttons]]' +
      // '</ul></li>' +
      '</ul>';

    //
    // Console items for boundary and zoom
    //
    plots[i].data_console_item = {
      snap_bounds: [
      {
        name: "Left",
        class: "left"
      },
      {
        name: "Right",
        class: "right"
      }],
      zoom: [
      {
        name: "Zoom",
        class: "zoom"
      }]
    };
    plots[i].tplt_console_region = '<span class="console-item" class="snap_bounds">' +
      '<b><span class="console-input id"></span></b> - ' +
      '[[#snap_bounds]]' +
      '[[name]]: <span class="console-input [[class]]">0</span> - ' +
      '[[/snap_bounds]]' +
      '</span>';
    plots[i].tplt_console_zoom = '<span class="console-item" class="zoom">' +
      '[[#zoom]]' +
      '[[name]]: <span class="console-input [[class]]">100%</span>' +
      '[[/zoom]]' +
      '</span>';

    //
    // Buttons for modal object
    //
    plots[i].modal_buttons = "<div class='modal-buttons'><a href='#/' class='modal-cancel button'>Cancel</a>" +
      "<a href='#/' class='modal-submit button'>Submit</a></div>";
    plots[i].close_button = "<div class='modal-buttons'><a href='#/' class='modal-close button'>Close</a></div>";

    //
    // Dimensions data for backdrop, modal, and sidebar objects
    //
    plots[i].data_objs = {
      "name": "",
      "top": 0,
      "left": 0,
      "width": 0,
      "height": 0
    }
    plots[i].tplt_backdrop = "<div class='backdrop' style='top:[[top]]; left:[[left]];" +
      "width:[[width]]px; height:[[height]]px;'></div>";
    plots[i].tplt_modal = "<div class='modal-window [[name]]_modal' name='[[name]]'" +
      " style='top:[[top]]px; left:[[left]]px; width:[[width]]px;" +
      " height:[[height]]px;'></div>";
    plots[i].tplt_sidebar = "<div class='sidebar' class='[[name]]_sidebar' name='[[name]]'" +
      " style='top:[[top]]px; left:[[left]]px; width:[[width]]px;" +
      " height:[[height]]px;'></div>";

    //
    // x Label
    //
    plots[i].data_x_label = {
      heading: "Change x-axis label",
      val: "",
      align: ""
    };
    plots[i].tplt_x_label = "<div class='modal-heading'>[[heading]]<span>×</span></div>" +
      "<div class='modal-content'>Text: <input type='text' value='[[val]]'></input>" +
      // "<br /><br />Align: <span><a href='#/'><i class='fa fa-align-left' style='border: 1px solid black'></i></a> " +
      // "<a href='#/'><i class='fa fa-align-center'></i></a> " +
      // "<a href='#/'><i class='fa fa-align-right'></i></a></span>" +
      "</div>" + plots[i].modal_buttons;

    //
    // y Label
    //
    plots[i].data_y_label = {
      heading: "Change y-axis label",
      val: "",
      align: ""
    };
    plots[i].tplt_y_label = "<div class='modal-heading'>[[heading]]<span>×</span></div>" +
      "<div class='modal-content'>Text: <input type='text' value='[[val]]'></input>" +
      // "<br /><br />Align: <span><a href='#/'><i class='fa fa-align-left'></i></a> " +
      // "<a href='#/'><i class='fa fa-align-center'></i></a> " +
      // "<a href='#/'><i class='fa fa-align-right'></i></a></span>" +
      "</div>" + plots[i].modal_buttons;

    //
    // Title
    //
    plots[i].data_title_label = {
      heading: "Change Title label",
      val: "",
      align: ""
    };
    plots[i].tplt_title_label = "<div class='modal-heading'>[[heading]]<span>×</span></div>" +
      "<div class='modal-content'>Text: <input type='text' value='[[val]]'></input>" +
      // "<br /><br />Align: <span><a href='#/'><i class='fa fa-align-left'></i> " +
      // "<a href='#/'><i class='fa fa-align-center'></i></a> " +
      // "<a href='#/'><i class='fa fa-align-right'></i></a></span>" +
      "</div>" + plots[i].modal_buttons;

    //
    // Color Picker
    //
    plots[i].data_color_picker = {
      heading: "Choose color"
    };
    plots[i].tplt_color_picker = "<div class='modal-heading'>[[heading]]<span>×</span></div>" +
      "<div class='modal-content'><input type='text' class='color_val' value='1'></input>" +
      "</div>" + plots[i].modal_buttons;

    //
    // Select Region
    //
    plots[i].data_region = {
      "heading": "Regions",
      "info_table": [
        //{
        //"graph_id": "graph",
        //"region_id": "brush brush_A",
        //"region_name": "A",
        //"region_shortname": "brush_A",
        //"active": false,
        //"left": 2.71,
        //"right": 3.14,
        //"delete": false
        //}
      ]
    };
    plots[i].tplt_region = "<div class='sidebar-heading'>[[heading]]</div>" +
      "<div class='sidebar-content'><table class='info_table'>Visible regions:<thead>" +
        "<tr><th>ID</th>" +
        "<th>Active</th>" +
        "<th>Remove</th></tr>" +
      "</thead>" +
      "<tbody>" +
        "[[#info_table]]" +
        "<tr class='[[region_id]]_info'><td name='[[region_id]]'>[[region_name]]</td>" +
        "<td><input type='radio' name='[[graph_id]]_regions' [[#active]] checked [[/active]]></input></td>" +
        "<td><a href='#/' class='link_remove_region'><i class='fa fa-times'></i></a></td></tr>" +
        "[[/info_table]]" +
        "<tr class='new_row'><td><a href='#/' class='link_add_region'>Add</a></td><td></td>" +
        "<td><a href='#/' class='link_remove_all_regions'>Remove All</a></td></tr>" +
      "</tbody>" +
      "</table></div>"; // + buttons;

    //
    // Topics (uncomment if added Help menu above)
    //
    // plots[i].data_topics = {
    //   heading: "Help Topics"
    // };
    // plots[i].tplt_topics = "<div class='modal-heading'>[[heading]]<span>×</span></div>" +
    //   "<div class='modal-content'>under construction" +
    //   "</div>" + plots[i].close_button;

    //
    // About (uncomment if added Help menu above)
    //
    // plots[i].data_about = {
    //   heading: "About"
    // };
    // plots[i].tplt_about = "<div class='modal-heading'>[[heading]]<span>×</span></div>" +
    //   "<div class='modal-content'><img src='/static/sns_logo_111x75.png' height='50%'><br>" +
    //   "ORNL Spallation Neutron Source" +
    //   "</div>" + plots[i].close_button;

    //
    // Dummy row for regions table
    //
    plots[i].data_add_region;
    plots[i].tplt_add_region = "<td>";

}

$(function(){
  var i;
  for (i = 0; i < plots.length; i++) {
	  mustachetemplates(i);
  }

})
