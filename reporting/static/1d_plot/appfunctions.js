function appfunctions(i){
    var anchor = plots[i].anchor;
    var plot = plots[i]; // This plot object

    // Change mustache.js tags
    Mustache.tags = ['[[', ']]'];
    // Create and append css menu for this plot object
    $("." + anchor + ".cssmenu").append(Mustache.render(plots[i].tplt_menu, plots[i].data_menu));


    // If log scale for x-axis is true onload, apply checkbox icon
    if (plots[i].plot_options.log_scale_x == true) {
      var log_flag = Plot_1d.menu_flag_check_true;
      $("." + anchor + " .log_scale_x").children("i").attr("class", log_flag);
    }
    // If log scale for y-axis is true onload, apply checkbox icon
    if (plots[i].plot_options.log_scale_y == true) {
      var log_flag = Plot_1d.menu_flag_check_true;
      $("." + anchor + " .log_scale_y").children("i").attr("class", log_flag);
    }
    // If grid is true onload, apply checkbox icon
    if (plots[i].plot_options.grid == true) {
      var grid_flag = Plot_1d.menu_flag_check_true;
      $("." + anchor + " .view_grid").children("i").attr("class", grid_flag);
    }
    // If region mode is not needed, remove Modes menu and reduce width
    if (plots[i].plot_options.allow_region_mode == false) {
      $("." + anchor + " .modes-menu").parent().remove();
      $("." + anchor + ".main").css("width", 500);
    }

    //
    // Function to change labels (x-axis, y-axis, title) of plot object
    //
    plots[i].add_change_label = function(label) {
      var offset = $("#" + this.anchor).offset();
      var w = $("#" + this.anchor).width();
      var h = $("#" + this.anchor).height();
      this.graph_modal(offset, w, h, label);
    }

    //
    // Function to add console item (zoom % or region bounds)
    //
    plots[i].add_console_item = function(id) {
      var self = this; // Assign scope
      var html;
      $("." + this.anchor + " .console-item").each(function() {
          $(this).remove(); // Remove previous console item
        })
        // If user chooses Select Region mode, change console item
      if (id == "snap_bounds" && $("." + this.anchor + " ." + id).length == 0) {
        html = Mustache.render(this.tplt_console_region, this.data_console_item);
      }
      // If user chooses Pan and Zoom mode, change console item
      if (id == "zoom" && $("." + this.anchor + " ." + id).length == 0) {
        html = Mustache.render(this.tplt_console_zoom, this.data_console_item);
      }
      // Append console item to console bar
      $("." + self.anchor + ".user-console").append(html);
    }
    // Page loads with zoom console item by default
    plots[i].add_console_item("zoom");

    //
    // Function when user adds a new region in Select Region mode
    //
    plots[i].add_region = function() {
      // Deactivate other regions if there are any
      $("." + this.anchor + " .brush").each(function() {
        $(this).css("pointer-events", "none");
      });
      // Add another region
      this.enable_brush();
      // Refresh side panel
      $("." + this.anchor + " .sidebar").remove();
      var offset = $("#" + this.anchor).offset();
      var w = $("#" + this.anchor).width();
      var h = $("#" + this.anchor).height();
      this.graph_sidebar(offset, w, h, "select_region");
      // Make new region active
      this.change_region(null);
    }

    //
    // Function to change region (either when user
    // adds a new region or toggles a different region)
    //
    plots[i].change_region = function(region_id) {
      var self = this; // Assign scope
      var region_shortname; // brush_X (brush_A, brush_B, etc)

      // Change active region when user clicks on radio button in side panel
      // or when user adds new region
      $("." + this.anchor + " .info_table input").change(function() {
        // Get region id of selected region and change in table and graph
        region_id = $(this).parent().prev().attr("name");
        region_shortname = change_region_in_table(region_id);
        activate_region_in_graph(region_shortname);
      });

      // Change active region when user removes current active region
      if (region_id != null) {
        region_shortname = change_region_in_table(region_id);
        activate_region_in_graph(region_shortname);
      }
      // Make the selected region active in side panel table
      function change_region_in_table(region_id) {
        var region_shortname;
        var i; // Index

        // Loop through regions to get index and region shortname of
        // the newly selected region
        for (var c = 0; c < parseInt(self.data_region.info_table.length); c++) {
          self.data_region.info_table[c].active = false;
          if (self.data_region.info_table[c].region_id == region_id) {
            self.data_region.info_table[c].active = true;
            region_shortname = self.data_region.info_table[c].region_shortname;
            i = c;
          }
        }
        // Uncheck all other regions in side panel table
        $("." + self.anchor + " .info_table input").each(function() {
          $(this).attr('checked', false);
        });

        // Check radio button in side panel
        $("." + self.anchor + " ." + self.data_region.info_table[i].region_shortname + "_info input").attr('checked', true);
        $("." + self.anchor + " ." + self.data_region.info_table[i].region_shortname + "_info input").prop('checked', true);
        // Change console data (for console item in Select Region mode)
        $("." + self.anchor + " .console-input.id").text(self.data_region.info_table[i].region_name);
        $("." + self.anchor + " .console-input.left").text(self.data_region.info_table[i].left);
        $("." + self.anchor + " .console-input.right").text(self.data_region.info_table[i].right);
        return region_shortname;
      }

      // Make the selected region active in graph
      function activate_region_in_graph(region_shortname) {
        $("." + self.anchor + " ." + region_shortname).css("pointer-events", "all");
        $("." + self.anchor + " ." + region_shortname).appendTo("#" + self.anchor + "_svg");
      }
    }

    //
    // Function to remove region
    //
    plots[i].remove_region = function(region_id) {
      var self = this; // Assign scope
      var i; // Index
      var active_flag = false;

      // Get region shortname from region_id
      var region_shortname = region_id.split(" ")[1];
      // Loop through regions to get index of region to be deleted. Check
      // to see if this region is currently active.
      for (i = 0; i < parseInt(self.data_region.info_table.length); i++) {
        if (self.data_region.info_table[i].region_id == region_id) {
          if (self.data_region.info_table[i].active == true) {
            active_flag = true;
          }
          break;
        }
      }

      // Remove the region in the graph
      $("." + this.anchor + " ." + region_shortname).remove();
      // Remove the region in the regions data object
      self.data_region.info_table.splice(i, 1);
      // Remove the region in the side panel table
      $("." + this.anchor + " ." + region_shortname + "_info").remove();

      // If other regions exist
      if (self.data_region.info_table.length > 0) {
        // If the active region was removed
        if (active_flag == true) {
          // If any other region was active and removed, select the next region
          if (i !== self.data_region.info_table.length) {
            $("." + this.anchor + " ." + self.data_region.info_table[i].region_shortname + "_info input").attr('checked', true);
            $("." + this.anchor + " ." + self.data_region.info_table[i].region_shortname + "_info input").prop('checked', true);
            self.data_region.info_table[i].active = true;
            self.change_region(self.data_region.info_table[i].region_id);
          }
          // Else if the last region was active and removed, select the previous region
          else {
            $("." + this.anchor + " ." + self.data_region.info_table[i - 1].region_shortname + "_info input").attr('checked', true);
            $("." + this.anchor + " ." + self.data_region.info_table[i - 1].region_shortname + "_info input").prop('checked', true);
            self.data_region.info_table[i - 1].active = true;
            self.change_region(self.data_region.info_table[i - 1].region_id);
          }
        }
      }
      // If no other regions exist, remove side panel, clear regions table,
      // and activate Pan and Zoom mode
      else if (self.data_region.info_table.length === 0) {
        $("." + this.anchor + " .sidebar").remove();
        $("#snap_bounds").remove();
        this.last_brush = 0;
        this.data_region.info_table = [];
        $("." + this.anchor + " .pan_and_zoom").trigger("click");
      }
    }

    //
    // Function to remove all regions and go back to Pan and Zoom mode
    //
    plots[i].remove_all_regions = function() {
      // Loop through all regions and remove them
      for (var i = 0; i < parseInt(this.data_region.info_table.length); i++) {
        $("." + this.anchor + " ." + this.data_region.info_table[i].region_shortname).remove();
      }
      // Remove side panel
      $("." + this.anchor + " .sidebar").remove();
      $("#snap_bounds").remove();
      this.last_brush = 0;
      // Clear regions data object
      this.data_region.info_table = [];
      // Turn on Pan and Zoom mode
      $("." + this.anchor + " .pan_and_zoom").trigger("click");
    }

    //
    // Function to create modal objects
    //
    plots[i].graph_modal = function(offset, w, h, type) {
      var html;
      var sect_html;
      var change_id = type;
      var modal_id = change_id + "_modal";
      var spectrum_flag = false;
      // If user wants to change x-axis label
      if (change_id == "x_label") {
        this.data_x_label.val = $("." + this.anchor + " .x_label").text();
        sect_html = Mustache.render(this.tplt_x_label, this.data_x_label);
      }
      // If user wants to change y-axis label
      else if (change_id == "y_label") {
        this.data_y_label.val = $("." + this.anchor + " .y_label").text();
        sect_html = Mustache.render(this.tplt_y_label, this.data_y_label);
      }
      // If user wants to change title
      else if (change_id == "title") {
        this.data_title_label.val = $("." + this.anchor + " .title").text();
        sect_html = Mustache.render(this.tplt_title_label, this.data_title_label);
      }
      // If user wants to change color of graph
      else if (change_id == "color_picker") {
        sect_html = Mustache.render(this.tplt_color_picker, this.data_color_picker);
      }

      // If user selects Help > About
      else if (change_id == "about") {
        sect_html = Mustache.render(plots[i].tplt_about, plots[i].data_about);
      }
      // If user selects Help > Topics
      else if (change_id == "topics") {
        sect_html = Mustache.render(plots[i].tplt_topics, plots[i].data_topics);
      }
      // Add darker backdrop to code
      html = this.create_backdrop(offset, w, h, type);
      // Add modal to code
      html = html + this.create_modal(offset, w, h, type);
      // Append modal and backdrop
      $("." + this.anchor + ".main").prepend(html);
      // Append modal contents
      $("." + this.anchor + " .modal-window").html(sect_html);
      // Make color picker interactive
      this.activate_spectrum();
    }

    //
    // Function to create sidebar
    //
    plots[i].graph_sidebar = function(offset, w, h, type) {
      var html;
      var sect_html;
      var change_id = type;
      var sidebar_id = change_id + "_sidebar";
      // If user chooses Select Region mode
      if (change_id == "select_region") {
        sect_html = Mustache.render(this.tplt_region, this.data_region);
      }
      // Add sidebar to code
      html = this.create_sidebar(offset, w, h, type);
      // Append sidebar
      $("." + this.anchor + ".main").prepend(html);
      // Append sidebar contents
      $("." + this.anchor + " .sidebar").html(sect_html);
      // Make color picker interactive
      // this.activate_spectrum();
    }

    //
    // Function to create backdrop (for modal)
    //
    plots[i].create_backdrop = function(offset, w, h, type) {
      h = h + 64;
      this.data_objs.top = offset.top - 32;
      this.data_objs.left = offset.left;
      this.data_objs.width = w;
      this.data_objs.height = h;
      return Mustache.render(this.tplt_backdrop, this.data_objs);
    }

    //
    // Function to create modal
    //
    plots[i].create_modal = function(offset, w, h, type) {
      h = h + 64;
      this.data_objs.name = type;
      this.data_objs.top = h / 4;
      this.data_objs.left = w / 4;
      this.data_objs.width = w / 2;
      this.data_objs.height = h / 2 + 10;
      return Mustache.render(this.tplt_modal, this.data_objs);
    }

    //
    // Function to create sidebar
    //
    plots[i].create_sidebar = function(offset, w, h, type) {
      this.data_objs.name = type;
      this.data_objs.top = 32;
      this.data_objs.left = w - w / 4 - 1;
      this.data_objs.width = w / 4;
      this.data_objs.height = h - 1;
      return Mustache.render(this.tplt_sidebar, this.data_objs);
    }

    //
    // Function to add functionality to buttons in modal
    //
    plots[i].modal_actions = function(change_id, modal_id) {
      if (change_id == "color_picker") {
        var color = $("." + this.anchor + " .color_val").val();
        this.plot_options.color = color;
        this.change_color();
      }
      else if (change_id == "select_region") {
        this.add_region();
      }
      else { // change label (x_label, y_label, title)
        this.change_label(change_id, modal_id);
      }
    }

    //
    // Function to change labels (x-axis, y-axis, title labels)
    //
    plots[i].change_label = function(change_id, modal_id) {
      // Get user input from textbox
      var val = $("." + this.anchor + " ." + modal_id).children(".modal-content").children("input").val();
      if (change_id == "x_label") {
        this.plot_options.x_label = val
      }
      else if (change_id == "y_label") {
        this.plot_options.y_label = val
      }
      else if (change_id == "title") {
        this.plot_options.title = val
      }
      // Change label text
      $("." + this.anchor + " ." + change_id).text(val);
    }

    //
    // Function to make the color picker interactive
    //
    plots[i].activate_spectrum = function() {
      var self = this;
      $("." + self.anchor + " .color_val").attr("value", this.plot_options.color);
      $("." + this.anchor + " .color_val").spectrum({
        flat: true,
        color: self.plot_options.color,
        clickoutFiresChange: true,
        showButtons: false,
        move: function(color) {
          $("." + self.anchor + " .color_val").attr("value", color.toHexString());
        }
      });
    }

    // function encode_as_img_and_link(){
    //  // Add some critical information
    //   $("#default_1d").attr({ version: '1.1' , xmlns:"http://w.w3.org/2000/svg"});
    //
    //  var svg = $("#default_1d").html();
    //  // var b64 = Base64.encode(svg); // or use btoa if supported
    //  var b64 = btoa(svg);
    //
    //  // Works in recent Webkit(Chrome)
    //  $("body").append($("<img src='data:image/svg+xml;utf8,"+b64+"' alt='file.svg'/>"));
    //
    //  // Works in Firefox 3.6 and Webit and possibly any browser which supports the data-uri
    //  $("body").append($("<a href-lang='image/svg+xml' href='data:image/svg+xml;utf8,"+b64+"' title='file.svg'>Download</a>"));
    // }

    //
    // Function to export svg as png file
    //
    plots[i].export_png = function() {
      saveSvgAsPng(document.getElementById(this.anchor + "_svg"), "diagram.png", {
        scale: 2
      });
    }

    function saveAs(uri, filename) {
        var link = document.createElement('a');
        if (typeof link.download === 'string') {
            link.href = uri;
            link.download = filename;

            // Firefox requires the link to be in the body
            document.body.appendChild(link);

            // simulate click
            link.click();

            // remove the link when done
            document.body.removeChild(link);
        } else {
            window.open(uri);
        }
    }

    //
    // Function to export svg as svg file
    //
    plots[i].export_svg = function() {
      var svg_link = "";
      svgAsDataUri(document.getElementById(this.anchor + "_svg"), {}, function(uri){
        svg_link = uri;
      });
      saveAs(svg_link, "data.svg");
    }

    //
    // Function to export data as text file
    //
    plots[i].export_txt = function() {       
      // Get and format data
      var txt_link = "data:text/plain;charset=utf-8;,";
      for (var j=0; j<plots[i].raw_data.length; j++){
        var line = "";
        for (var k=0; k<plots[i].raw_data[j].length; k++){
          line = line + plots[i].raw_data[j][k] + "%20"; // add space character
        }
        txt_link = txt_link + line + '%0A'; // add newline character
      }
      saveAs(txt_link, "data.txt");
    }

    // plots[i].export_pdf = function() {
    //   var svg_link = "";
    //   var doc = new jsPDF();
    //   svgAsDataUri(document.getElementById("graph_svg"), {}, function(uri){
    //     svg_link = uri;
    //     return uri;
    //   });
    //   var svg = $("#graph_svg").get(0);
    //   // console.log(svg);
    //
    //   // doc.addImage(svg_link, 'svg', 15, 40, 180, 180);
    //   svgElementToPdf(svg, doc, {
    //     scale: 72/96,
    //     removeInvalid: false
    //   });
    //   doc.addSVG(svg);
    //   // doc.output("datauri");
    //   doc.save('Test.pdf');
    // }



}

$(function(){
  // Icons for menu items (checkbox or radio button)
  Plot_1d.menu_flag_check_true = "menu-icon fa fa-check-square-o";
  Plot_1d.menu_flag_check_false = "menu-icon fa fa-square-o";
  Plot_1d.menu_flag_radio_true = "menu-icon fa fa-circle";
  Plot_1d.menu_flag_radio_false = "menu-icon fa fa-circle-thin";

  var i;
  //
  // Loop through plots
  //
  for (i = 0; i < plots.length; i++) {
    appfunctions(i);
    // Initialize event handlers/listeners
    event_handlers(plots[i], i);
    // If there are predetermined regions in the graph, display them
    if (plots[i].predetermined_regions_flag == true) {
      // For first predetermined region
      // Get region bounds
      plots[i].d0 = plots[i].plot_options.predetermined_region[0][0];
      plots[i].d1 = plots[i].plot_options.predetermined_region[0][1];
      // Trigger Select Region mode and add region
      $("." + plots[i].anchor + " .select_region").trigger("click");

      // Add region bounds to region data object
      plots[i].data_region.info_table[0].left = formatter(plots[i].d0);
      plots[i].data_region.info_table[0].right = formatter(plots[i].d1);

      var this_region_shortname = plots[i].data_region.info_table[0].region_shortname;
      // Add label to region near left bound
      var x = parseInt($("." + plots[i].anchor + " ." + this_region_shortname + " .extent").attr("x"));
      $("." + plots[i].anchor + " ." + this_region_shortname).children(".brush-label").attr("visibility", "visible")
        .attr("x", x + 3)
        .attr("y", 12);

      // Get region name, left bound, right bound, insert in console item
      $("." + plots[i].anchor + " .console-input.id").text(plots[i].data_region.info_table[0].region_name);
      $("." + plots[i].anchor + " .console-input.left").text(plots[i].data_region.info_table[0].left);
      $("." + plots[i].anchor + " .console-input.right").text(plots[i].data_region.info_table[0].right);

      // For subsequent predetermined regions
      for (var count = 1; count < plots[i].plot_options.predetermined_region.length; count++) {
        // Get region bounds
        plots[i].d0 = plots[i].plot_options.predetermined_region[count][0];
        plots[i].d1 = plots[i].plot_options.predetermined_region[count][1];
        // Trigger Add Region button and add region
        $("." + plots[i].anchor + " .link_add_region").trigger("click");

        // Add region bounds to region data object
        plots[i].data_region.info_table[count].left = formatter(plots[i].d0);
        plots[i].data_region.info_table[count].right = formatter(plots[i].d1);

        var this_region_shortname = plots[i].data_region.info_table[count].region_shortname;
        // Add label to region near left bound
        var x = parseInt($("." + plots[i].anchor + " ." + this_region_shortname + " .extent").attr("x"));
        $("." + plots[i].anchor + " ." + this_region_shortname).children(".brush-label").attr("visibility", "visible")
          .attr("x", x + 3)
          .attr("y", 12);

        // Get region name, left bound, right bound, insert in console item
        $("." + plots[i].anchor + " .console-input.id").text(plots[i].data_region.info_table[count].region_name);
        $("." + plots[i].anchor + " .console-input.left").text(plots[i].data_region.info_table[count].left);
        $("." + plots[i].anchor + " .console-input.right").text(plots[i].data_region.info_table[count].right);
      }
      // Reset region bounds
      plots[i].d0 = null;
      plots[i].d1 = null;
    }
  }

  i--; // For some reason this needs to be here...
})

function event_handlers(self, i) {
  var anchor = plots[i].anchor;
  this.iter = i;

  // When user clicks on a Cancel button, Close button, or the close X button
  // in a modal, remove the backdrop and modal item
  $(document).on('click', "." + self.anchor + " .modal-heading span, " +
    "." + self.anchor + " .modal-cancel, " +
    "." + self.anchor + " .modal-close",
    function() {
      $("." + self.anchor + " .backdrop").remove();
      $("." + self.anchor + " .modal-window").remove();
    });

  // When user clicks on a Submit button, take the appropriate action
  // (determined by the modal_actions function) and remove the backdrop
  // and modal item
  $(document).on('click', "." + self.anchor + " .modal-submit", function() {
    var change_id = $(this).parent().parent().attr("name");
    var modal_id = $(this).parent().parent().attr("class").split(" ")[1];
    plots[i].modal_actions(change_id, modal_id);
    $("." + self.anchor + " .backdrop").remove();
    $("." + self.anchor + " .modal-window").remove();
  });

  // When user clicks on the Add [region] button, call add_region function
  $(document).on('click', "." + self.anchor + " .link_add_region", function() {
    plots[i].add_region();
  })

  // When user clicks on the X button to remove region, call remove_region
  // function
  $(document).on('click', "." + self.anchor + " .link_remove_region", function() {
    var region_id = $(this).parent().prev().prev().attr("name");
    plots[i].remove_region(region_id);
  })

  // When user clicks on Remove All button to remove all regions, call
  // remove_all_regions
  $(document).on('click', "." + self.anchor + " .link_remove_all_regions", function() {
    plots[i].remove_all_regions();
  })

  // When user presses the Enter key on the keyboard to change the
  // x-axis, y-axis, or title labels, trigger the Submit button
  $(document).on('keydown', "." + anchor + " .x_label_modal input, " +
    "." + anchor + " .y_label_modal input, " +
    "." + anchor + " .title_modal input",
    function(e) {
      if (e.keyCode == 13) {
        $("." + anchor + " .modal-submit").trigger("click");
      }
  });

  // When user clicks on x-axis Log Scale option in submenu,
  $(document).on("click", "." + anchor + " .log_scale_x", function(){
    // Toggle log scale flag for x-axis
    var log_flag = $(this).children("i").attr("class");
    if (log_flag == Plot_1d.menu_flag_check_false) {
      log_flag = Plot_1d.menu_flag_check_true;
      plots[i].plot_options.log_scale_x = true;
    }
    else {
      log_flag = Plot_1d.menu_flag_check_false;
      plots[i].plot_options.log_scale_x = false;
    }
    // Refresh plot
    $("." + anchor + " .sidebar").remove();
    $("." + anchor + ".cssmenu").empty();
    $("#" + anchor).empty();
    $("." + anchor + ".user-console").empty();
    var temp_options = plots[i].plot_options;
    // plots[i] = null;
    plots[i] = new Plot_1d(plots[i].raw_data, anchor, temp_options);
    mustachetemplates(i);
    appfunctions(i);
    // Change x-axis Log Scale checkbox icon in submenu
    $(this).children("i").attr("class", log_flag);
    // Change to Pan and Zoom mode
    $("." + anchor + " .pan_and_zoom").trigger("click");
    // Add zoom console item
    $("." + anchor + " .console-input.zoom").html(parseInt(100) + "%");
  });

  // When user clicks on y-axis Log Scale option in submenu,
  $(document).on("click", "." + anchor + " .log_scale_y", function(){
    // Toggle log scale flag for y-axis
    var log_flag = $(this).children("i").attr("class");
    if (log_flag == Plot_1d.menu_flag_check_false) {
      log_flag = Plot_1d.menu_flag_check_true;
      plots[i].plot_options.log_scale_y = true;
    }
    else {
      log_flag = Plot_1d.menu_flag_check_false;
      plots[i].plot_options.log_scale_y = false;
    }
    // Refresh plot
    $("." + anchor + " .sidebar").remove();
    $("." + anchor + ".cssmenu").empty();
    $("#" + anchor).empty();
    $("." + anchor + ".user-console").empty();
    var temp_options = plots[i].plot_options;
    // plots[i] = null;
    plots[i] = new Plot_1d(plots[i].raw_data, anchor, temp_options);
    mustachetemplates(i);
    appfunctions(i);
    // Change y-axis Log Scale checkbox icon in submenu
    $(this).children("i").attr("class", log_flag);
    // Change to Pan and Zoom mode
    $("." + anchor + " .pan_and_zoom").trigger("click");
    // Add zoom console item
    $("." + anchor + " .console-input.zoom").html(parseInt(100) + "%");
  });

  // When user clicks on View Grid option in menu,
  $(document).on("click", "." + anchor + " .view_grid", function(){
    // Toggle grid flag
    var grid_flag = $(this).children("i").attr("class");
    if (grid_flag == Plot_1d.menu_flag_check_false) {
      grid_flag = Plot_1d.menu_flag_check_true;
      plots[i].plot_options.grid = true;
    }
    else {
      grid_flag = Plot_1d.menu_flag_check_false;
      plots[i].plot_options.grid = false;
    }
    // Call toggle_grid function
    plots[i].toggle_grid();
    // Change View Grid checkbox icon in menu
    $(this).children("i").attr("class", grid_flag);
  });

  // When user clicks on Color option in menu, open color picker,
  $(document).on("click", "." + anchor + " .color_picker", function(){
    var offset = $("#" + anchor).offset();
    var w = $("#" + anchor).width();
    var h = $("#" + anchor).height();
    self.graph_modal(offset, w, h, "color_picker");
  });

  // When user clicks on Pan and Zoom mode,
  $(document).on("click", "." + anchor + " .pan_and_zoom", function(){
    var pan_bool = true;
    var pan_flag = $(this).children("i").attr("class");
    // Change Pan and Zoom checkbox icon in menu
    if (pan_flag == Plot_1d.menu_flag_radio_true) {}
    else {
      flag = true;
      pan_flag = Plot_1d.menu_flag_radio_true;
      $("." + anchor + " .modes-list > li > span > a").not(this)
        .children("i")
        .attr("class", Plot_1d.menu_flag_radio_false);
    }
    $(this).children("i").attr("class", pan_flag);
    // If there are any regions on the graph, remove them
    if (self.data_region.info_table.length > 0) {
      self.data_region.info_table.length = 0;
      self.remove_all_regions();
    }
    plots[i].toggle_pan_and_zoom(pan_bool)
    plots[i].clear_brush();
    $("." + anchor + " .sidebar").remove();
    // Reset regions data
    plots[i].data_region = {
      "heading": "Regions",
      "info_table": []
    };
    // Add zoom console item
    self.add_console_item("zoom");
    // Set zoom console item to 100%
    $("." + anchor + " .console-input.zoom").html(parseInt(plots[i].scale_val * 100) + "%");
  });

  $(document).on("click", "." + anchor + " .zoom_100", function(){
    plots[i].zoom_reset();
  })

  // When user clicks on Select Region mode,
  $(document).on("click", "." + anchor + " .select_region", function(){
    var flag = true;
    var select_flag = $(this).children("i").attr("class");
    // Change Select Region checkbox icon in menu
    if (select_flag == Plot_1d.menu_flag_radio_true) {}
    else {
      flag = true;
      select_flag = Plot_1d.menu_flag_radio_true;
      $("." + anchor + " .modes-list > li > span > a").not(this)
        .children("i")
        .attr("class", Plot_1d.menu_flag_radio_false);
    }
    $(this).children("i").attr("class", select_flag);
    // If Select Region mode is not already active, make it active
    if ($("." + anchor + " .brush").length != 0) {}
    else {
      // Initialize the first region
      plots[i].enable_brush();
      var offset = $("#" + anchor).offset();
      var w = $("#" + anchor).width();
      var h = $("#" + anchor).height();
      // Append side panel
      plots[i].graph_sidebar(offset, w, h, "select_region");
      // Add Region console item
      plots[i].add_console_item("snap_bounds");
      $("." + anchor + " .console-input.id").text(plots[i].data_region.info_table[0].region_name);
    }
  });

  // When user clicks on Help > Topics, open Topics modal,
  $(document).on("click", "." + anchor + " .topics", function(){
    var offset = $("#" + anchor).offset();
    var w = $("#" + anchor).width();
    var h = $("#" + anchor).height();
    self.graph_modal(offset, w, h, "topics");
  })

  // When user clicks on Help > About, open About modal,
  $(document).on("click", "." + anchor + " .about", function(){
    var offset = $("#" + anchor).offset();
    var w = $("#" + anchor).width();
    var h = $("#" + anchor).height();
    self.graph_modal(offset, w, h, "about");
  })

  // When user clicks on x-Axis label in submenu, open modal,
  $(document).on("click", "." + anchor + " .x_axis_label", function(){
    var label = "x_label";
    self.add_change_label(label);
  });

  // When user clicks on y-Axis label in submenu, open modal,
  $(document).on("click", "." + anchor + " .y_axis_label", function(){
    var label = "y_label";
    self.add_change_label(label);
  });

  // When user clicks on title label in submenu, open modal,
  $(document).on("click", "." + anchor + " .title_label", function(){
    var label = "title";
    self.add_change_label(label);
  });

  // Export as PNG file
  $(document).on("click", "." + anchor + " .export_png", function() {
    plots[i].export_png();
  });

  // Export as SVG file
  $(document).on("click", "." + anchor + " .export_svg", function() {
    plots[i].export_svg();
  });

  // Export as ASCII file
  $(document).on("click", "." + anchor + " .export_txt", function(){
    plots[i].export_txt();
  });

  // $(document).on("click", "." + anchor + " .export_pdf", function() {
  //   plots[i].export_pdf();
  // });

  // $(document).on("click", ".test", function(){
  //   var output = "";
  //   for (var key in plots[i].plot_options){
  //     if (plots[i].plot_options.hasOwnProperty(key)){
  //       output = output + key + ": " + plots[i].plot_options[key] + "\n";
  //     }
  //   }
  // });



}
