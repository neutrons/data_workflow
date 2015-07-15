function appfunctions(i){
    var anchor = plots[i].anchor;
    console.log(anchor);
    var plot = plots[i]; // This plot object

    // Change mustache.js tags
    Mustache.tags = ['[[', ']]'];
    // Create and append css menu for this plot object
    $("." + anchor + ".cssmenu").append(Mustache.render(plots[i].tplt_menu, plots[i].data_menu));


    // If log scale is true onload, apply checkbox icon
    if (plots[i].plot_options.log_scale == true) {
      var log_flag = Plot_2d.menu_flag_check_true;
      $("." + anchor + " .log_scale").children("i").attr("class", log_flag);
    }
    // If grid is true onload, apply checkbox icon
    if (plots[i].plot_options.grid == true) {
      var grid_flag = Plot_2d.menu_flag_check_true;
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
      this.data_objs.top = h / 3;
      this.data_objs.left = w / 4;
      this.data_objs.width = w / 2;
      this.data_objs.height = h / 3 + 10;
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
      else if (change_id == "see_values") {
        // this.add_region();
        alert("see data values");
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
      console.log(this.anchor)
      saveSvgAsPng(document.getElementById(this.anchor + "_svg"), "diagram.png", {
        scale: 2
      });
    }

    //
    // Function to export svg as svg file
    //
    plots[i].export_svg = function() {
      var svg_link = "";
      svgAsDataUri(document.getElementById(this.anchor + "_svg"), {}, function(uri){
        svg_link = uri;
      });
      // Make an invisible link to the svg and click on it to download
      var a = document.createElement('a');
      $(a).attr("id", "svg_file_link");
      $("body").append(a);
      $(a).attr("href", svg_link);
      $(a).attr("download", "diagram.svg");
      document.getElementById("svg_file_link").click();
      // Remove invisible link
      $(a).remove();
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
  Plot_2d.menu_flag_check_true = "menu-icon fa fa-check-square-o";
  Plot_2d.menu_flag_check_false = "menu-icon fa fa-square-o";
  Plot_2d.menu_flag_radio_true = "menu-icon fa fa-circle";
  Plot_2d.menu_flag_radio_false = "menu-icon fa fa-circle-thin";

  var i;
  //
  // Loop through plots
  //
  for (i = 0; i < plots.length; i++) {
    appfunctions(i);
    // Initialize event handlers/listeners
    event_handlers(plots[i], i);
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

  // When user presses the Log Scale item in the Options submenu
  $(document).on("click", "." + anchor + " .log_scale", function(){
    // Toggle log scale flag
    var log_flag = $(this).children("i").attr("class");
    if (log_flag == Plot_2d.menu_flag_check_false) {
      console.log("is false, will change to true");
      log_flag = Plot_2d.menu_flag_check_true;
      plots[i].plot_options.log_scale = true;
    }
    else {
      console.log("is true, will change to false");
      log_flag = Plot_2d.menu_flag_check_false;
      plots[i].plot_options.log_scale = false;
    }
    // Refresh plot
    $("." + anchor + ".cssmenu").empty();
    $("#" + anchor).empty();
    $("." + anchor + ".user-console").empty();
    var temp_options = plots[i].plot_options;
    plots[i] = new Plot_2d(anchor, plots[i].raw_data, qx, qy, max_iq, temp_options);
    mustachetemplates(i);
    appfunctions(i);
    // Change Log Scale checkbox icon in submenu
    $(this).children("i").attr("class", log_flag);
    // Add zoom console item
    $("." + anchor + " .console-input.zoom").html(parseInt(100) + "%");


  })


  // When user clicks on Pan and Zoom mode,
  $(document).on("click", "." + anchor + " .pan_and_zoom", function(){
    var flag = true;
    var pan_flag = $(this).children("i").attr("class");
    // Change Pan and Zoom checkbox icon in menu
    if (pan_flag == Plot_2d.menu_flag_radio_true) {}
    else {
      flag = true;
      pan_flag = Plot_2d.menu_flag_radio_true;
      $("." + anchor + " .modes-list > li > span > a").not(this)
        .children("i")
        .attr("class", Plot_2d.menu_flag_radio_false);
    }
    $(this).children("i").attr("class", pan_flag);
    plots[i].toggle_pan_and_zoom(flag);
    // Add zoom console item
    self.add_console_item("zoom");
    // Set zoom console item to 100%
    $("." + anchor + " .console-input.zoom").html(parseInt(plots[i].scale_val * 100) + "%");
  });

  $(document).on("click", "." + anchor + " .zoom_100", function(){
    // There's a better way to do this...
    // alert("implement this asap");
    plots[i].zoom_reset();
  })

  // When user clicks on Select Region mode,
  $(document).on("click", "." + anchor + " .see_values", function(){
    var flag = true;
    var select_flag = $(this).children("i").attr("class");
    // Change Select Region checkbox icon in menu
    if (select_flag == Plot_2d.menu_flag_radio_true) {}
    else {
      flag = true;
      select_flag = Plot_2d.menu_flag_radio_true;
      $("." + anchor + " .modes-list > li > span > a").not(this)
        .children("i")
        .attr("class", Plot_2d.menu_flag_radio_false);
    }
    $(this).children("i").attr("class", select_flag);
    // If See Values mode is not already active, make it active
    console.log("length: " + $("." + anchor + " .pan").length);
    if ($("." + anchor + " .pan").length == 0) {}
    else {
      // $("#" + anchor + " .pan").remove();
      plots[i].toggle_pan_and_zoom(false);
    }
  });

  // When user clicks on Help > Topics, open Topics modal,
  // $(document).on("click", "." + anchor + " .topics", function(){
  //   // var flag = true; // why do I need this again??
  //   var offset = $("#" + anchor).offset();
  //   var w = $("#" + anchor).width();
  //   var h = $("#" + anchor).height();
  //   self.graph_modal(offset, w, h, "topics");
  // })

  // When user clicks on Help > About, open About modal,
  // $(document).on("click", "." + anchor + " .about", function(){
  //   // var flag = true; // why do I need this again??
  //   var offset = $("#" + anchor).offset();
  //   var w = $("#" + anchor).width();
  //   var h = $("#" + anchor).height();
  //   self.graph_modal(offset, w, h, "about");
  // })

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
  // Still working on this
  // $("." + anchor + " .export_png").click(function() {
  //   test666();
  // });
  // $("." + anchor + " .export_svg").click(function() {
  //   test777();
  // });
  // $("." + anchor + " .export_pdf").click(function() {
  //   test888();
  // });



}
