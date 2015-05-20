$(function() {
    Mustache.tags = ['[[', ']]'];
    $(".cssmenu").append(Mustache.render(tplt_menu, data_menu));
    add_console_item("zoom");

    //////////////
    // FOR MENU //
    //////////////

    // put this in an object!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    var menu_flag_check_true = "menu-icon fa fa-check-square-o";
    var menu_flag_check_false = "menu-icon fa fa-square-o";
    var menu_flag_radio_true = "menu-icon fa fa-circle";
    var menu_flag_radio_false = "menu-icon fa fa-circle-thin";

    $("#log_scale").click(function() {
        var log_flag = $(this).children("i").attr("class");
        // alert(log_flag)
        // alert(First_plot.user_options.log_scale);
        if (log_flag == menu_flag_check_false) {
            log_flag = menu_flag_check_true;
            First_plot.user_options.log_scale = true;
        }
        else {
            log_flag = menu_flag_check_false;
            First_plot.user_options.log_scale = false;
        }
        First_plot = new Plot_1d(raw_data, anchor);
        $("#pan_and_zoom").trigger("click");
        $(this).children("i").attr("class", log_flag);
        $(".console-input.zoom").attr("value", parseInt(100) + "%");
    });
    $("#view_grid").click(function() {
        var grid_flag = $(this).children("i").attr("class");
        if (grid_flag == menu_flag_check_false) {
            grid_flag = menu_flag_check_true;
            First_plot.user_options.grid = true;
        }
        else {
            grid_flag = menu_flag_check_false;
            First_plot.user_options.grid = false;
        }
        First_plot.toggle_grid();
        $(this).children("i").attr("class", grid_flag);
    });
    $("#color_picker").click(function() {
        var offset = $(".graph").offset();
        var www = $(".graph").width();
        var hhh = $(".graph").height();
        graph_modal(offset, www, hhh, "color_picker");
    });
    $("#pan_and_zoom").click(function() {
        var flag = true;
        var pan_flag = $(this).children("i").attr("class");
        if (pan_flag == menu_flag_radio_true) {
        }
        else {
            flag = true;
            pan_flag = menu_flag_radio_true;
            $(".modes-list > li > span > a").not(this)
                .children("i")
                .attr("class", menu_flag_radio_false);
        }
        $(this).children("i").attr("class", pan_flag);
        if (data_region.info_table.length > 0) {
            data_region.info_table.length = 0;
            remove_region();
        }
        First_plot.toggle_pan_and_zoom(flag)
        First_plot.clear_brush();
        add_console_item("zoom");
        $(".console-input.zoom").attr("value", parseInt(First_plot.scale_val*100) + "%");
    });
    $("#select_region").click(function() {
        var flag = true;
        var select_flag = $(this).children("i").attr("class");
        if (select_flag == menu_flag_radio_true) {
        }
        else {
            flag = true;
            select_flag = menu_flag_radio_true;
            $(".modes-list > li > span > a").not(this)
                .children("i")
                .attr("class", menu_flag_radio_false);
        }
        $(this).children("i").attr("class", select_flag);
        if ($(".brush").length != 0) {
        }
        else {
            First_plot.enable_brush();
            var offset = $(".graph").offset();
            var www = $(".graph").width();
            var hhh = $(".graph").height();
            graph_sidebar(offset, www, hhh, "select_region");
            add_console_item("snap_bounds");
            console.log(data_region.info_table[0].region_name)
            $(".console-input.id").text(data_region.info_table[0].region_name);
        }
    });

    // Help menu
    $("#topics").click(function() {
        var flag = true; // why do I need this again??
        var offset = $(".graph").offset();
        var www = $(".graph").width();
        var hhh = $(".graph").height();
        graph_modal(offset, www, hhh, "topics");
    })
    $("#about").click(function() {
        var flag = true; // why do I need this again??
        var offset = $(".graph").offset();
        var www = $(".graph").width();
        var hhh = $(".graph").height();
        graph_modal(offset, www, hhh, "about");
    })

    // Axis labels
    $("#x_label").dblclick(function() {
        var label = "x_label";
        add_change_label(label);
    });
    $("#y_label").dblclick(function() {
        var label = "y_label";
        add_change_label(label);
    });
    $("#x_axis_label").click(function() {
        var label = "x_label";
        add_change_label(label);
    });
    $("#y_axis_label").click(function() {
        var label = "y_label";
        add_change_label(label);
    });
    $("#title_label").click(function() {
        var label = "title";
        add_change_label(label);
    });

});

    function add_change_label(label) {
        var offset = $(".graph").offset();
        var www = $(".graph").width();
        var hhh = $(".graph").height();
        graph_modal(offset, www, hhh, label);
    }

    function add_console_item(id) {
        var html;
        $(".console-item").each(function(){
          $(this).remove(); // Remove previous console item
        })
        if (id == "snap_bounds" && $("#" + id).length == 0) {
            html = Mustache.render(tplt_console_region, data_console_item);
        }
        if (id == "zoom" && $("#" + id).length == 0) {
            html = Mustache.render(tplt_console_zoom, data_console_item);
        }
        $(".user-console").append(html);
        // console.log(data_region.info_table[0].region_id)
    }

    function region_info() {
        $("#select_region").trigger("click");
    }

    function add_region() {
        // alert("in add_region()");
        var i;
        for (i = 0; i < parseInt(data_region.info_table.length); i++) {
            // console.log(data_region.info_table[i].active = false);
        }
        $(".brush").each(function() {
            $(this).css("pointer-events", "none");
        });

        First_plot.enable_brush();
        $(".sidebar").remove();
        var offset = $(".graph").offset();
        var www = $(".graph").width();
        var hhh = $(".graph").height();
        graph_sidebar(offset, www, hhh, "select_region");
        // console.log(data_region);
        change_region(null);
    }

    function change_region(region_id) {
        $("#info_table input").change(function() {
            region_id = $(this).parent().prev().attr("name");
            change_region_in_table(region_id);
            activate_region_in_graph(region_id);
        });
        if (region_id != null) {
            change_region_in_table(region_id);
            activate_region_in_graph(region_id);
        }
        function change_region_in_table(region_id) {
            var i;
            for (i = 0; i < parseInt(data_region.info_table.length); i++) {
                data_region.info_table[i].active = false;
                if (data_region.info_table[i].region_id == region_id) {
                    // console.log(data_region.info_table[i].region_id);
                    data_region.info_table[i].active = true;
                    break;
                }
            }
            $("#info_table input").each(function() {
                $(this).attr('checked', false);
            });
            $("#" + region_id + "_info input").attr('checked', true);
            $("#" + region_id + "_info input").prop('checked', true);
            $(".brush").each(function() {
                $(this).css("pointer-events", "none");
            });
            console.log(data_region.info_table[i].region_name)
            $(".console-input.id").text(data_region.info_table[i].region_name);
            $(".console-input.left").attr("value", data_region.info_table[i].left);
            $(".console-input.right").attr("value", data_region.info_table[i].right);
        }
        function activate_region_in_graph(region_id) {
            $("#" + region_id).css("pointer-events", "all");
            $("#" + region_id).appendTo("#graph_g");
        }
    }

    function remove_region(region_id) {
        var i;
        var active_flag = false;
        for (i = 0; i < parseInt(data_region.info_table.length); i++) {
            if (data_region.info_table[i].region_id == region_id) {
                console.log(data_region.info_table[i].region_id);
                if (data_region.info_table[i].active == true) {
                    active_flag = true;
                    // console.log("the " + i + "th brush was active");
                }
                break;
            }
        }
        $("#" + region_id).remove();
        data_region.info_table.splice(i, 1);
        $("#" + region_id + "_info").remove();
        if (data_region.info_table.length > 0) { // if other regions exist
            if (active_flag == true) {
                if (i !== data_region.info_table.length) {
                    $("#" + data_region.info_table[i].region_id + "_info input").attr('checked', true);
                    $("#" + data_region.info_table[i].region_id + "_info input").prop('checked', true);
                    data_region.info_table[i].active = true;
                    change_region(data_region.info_table[i].region_id);
                }
                else {
                    $("#" + data_region.info_table[i - 1].region_id + "_info input").attr('checked', true);
                    $("#" + data_region.info_table[i - 1].region_id + "_info input").prop('checked', true);
                    data_region.info_table[i - 1].active = true;
                    change_region(data_region.info_table[i - 1].region_id);
                }
            }
        }
        else if (data_region.info_table.length === 0) { // if no regions exist
            $(".sidebar").remove();
            $("#snap_bounds").remove();
            First_plot.last_brush = 0;
            data_region.info_table = [];
            $("#pan_and_zoom").trigger("click");
        }
    }

    function remove_all_regions() {
        for (var i = 0; i < parseInt(data_region.info_table.length); i++) {
            $("#" + data_region.info_table[i].region_id).remove();
        }
        $(".sidebar").remove();
        $("#snap_bounds").remove();
        First_plot.last_brush = 0;
        data_region.info_table = [];
        $("#pan_and_zoom").trigger("click");
    }

    function rem_console_item(id) {
        $("#" + id).remove();
    }


    function graph_modal(offset, www, hhh, type) {
        var html;
        var sect_html;
        var change_id = type;
        var modal_id = change_id + "_modal";
        var spectrum_flag = false;
        if (change_id == "x_label") {
            data_x_label.val = $("#x_label").text();
            sect_html = Mustache.render(tplt_x_label, data_x_label);
        }
        else if (change_id == "y_label") {
            data_y_label.val = $("#y_label").text();
            sect_html = Mustache.render(tplt_y_label, data_y_label);
        }
        else if (change_id == "title") {
            data_title_label.val = $("#title").text();
            sect_html = Mustache.render(tplt_title_label, data_title_label);
        }
        else if (change_id == "color_picker") {
            sect_html = Mustache.render(tplt_color_picker, data_color_picker);
        }
        else if (change_id == "select_region") {
            var num_of_brushes = $(".brush").length;
            sect_html = Mustache.render(tplt_region, data_region);
        }
        else if (change_id == "about") {
            sect_html = Mustache.render(tplt_about, data_about);
        }
        else if (change_id == "topics") {
            sect_html = Mustache.render(tplt_topics, data_topics);
        }
        html = create_backdrop(offset, www, hhh, type);
        html = html + create_modal(offset, www, hhh, type);
        $("#main").prepend(html);
        $('.modal-window').html(sect_html);
        activate_spectrum(); // if change color
        activate_buttons(change_id, modal_id);
    }

    function graph_sidebar(offset, www, hhh, type) {
        var html;
        var sect_html;
        var change_id = type;
        var sidebar_id = change_id + "_sidebar";
        if (change_id == "select_region") {
            sect_html = Mustache.render(tplt_region, data_region);
        }
        html = create_sidebar(offset, www, hhh, type);
        $("#main").prepend(html);
        $('.sidebar').html(sect_html);
        activate_spectrum();
        activate_buttons(change_id, sidebar_id);
    }

    function create_backdrop(offset, www, hhh, type) {
        hhh = hhh + 64;
        data_objs.top = offset.top - 32;
        data_objs.left = offset.left;
        data_objs.width = www;
        data_objs.height = hhh;
        return Mustache.render(tplt_backdrop, data_objs);
    }

    function create_modal(offset, www, hhh, type) {
        hhh = hhh + 64;
        data_objs.name = type;
        data_objs.top = offset.top + hhh / 6;
        data_objs.left = offset.left + www / 4;
        data_objs.width = www / 2;
        data_objs.height = hhh / 2 + 10;
        return Mustache.render(tplt_modal, data_objs);
    }

    function create_sidebar(offset, www, hhh, type) {
        data_objs.name = type;
        // data_objs.top = offset.top;
        console.log("widht: " + www);
        console.log("height: " + hhh);
        data_objs.top = 32;
        data_objs.left = www - www / 4 - 1;
        // data_objs.left = 450;
        data_objs.width = www / 4;
        data_objs.height = hhh - 1;
        return Mustache.render(tplt_sidebar, data_objs);
    }

    function activate_buttons(change_id, modal_id) {
        $(".modal-heading span, " + // close button
          ".modal-cancel, " +
          ".modal-close").click(function() {
            $(".backdrop").remove();
            $(".modal-window").remove();
        });

        $(".modal-submit").click(function(){
            modal_actions(change_id, modal_id);
            $(".backdrop").remove();
            $(".modal-window").remove();
        });

        $("#x_label_modal input, " +
          "#y_label_modal input, " +
          "#title_modal input").keydown(function(e) {
            if (e.keyCode == 13) {
                $(".modal-submit").trigger("click");
            }
        });
    };

    function modal_actions(change_id, modal_id) {
        var val = $("#" + modal_id).children(".modal-content").children("input").val();
        if (change_id == "color_picker") {
            var color = $("#color_test").val();
            First_plot.user_options.color = color;
            First_plot.change_color();
        }
        else if (change_id == "select_region") {
            add_region();
        }
        else {
            console.log(val);
            $("#" + change_id).text(val);
        }
    }

    function activate_spectrum() {
        $("#color_test").spectrum({
            flat: true,
            color: First_plot.user_options.color,
            clickoutFiresChange: true,
            showButtons: false,
            move: function(color) {
                $("#color_test").attr("value", color.toHexString());
            }
        });
    }

    $("#export_svg").click(function() {
      // encode_as_img_and_link();
      test666();
    })

    // function encode_as_img_and_link(){
    //  // Add some critical information
    //   $("#default_1d").attr({ version: '1.1' , xmlns:"http://www.w3.org/2000/svg"});
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

    function test666(){
      var html = d3.select("svg")
              .attr("title", "test2")
              .attr("version", 1.1)
              .attr("xmlns", "http://www.w3.org/2000/svg")
              .node().parentNode.innerHTML;
      d3.select("body").append("div")
              .attr("id", "download")
              .html("Right-click on this preview and choose Save as<br />Left-Click to dismiss<br />")
              .append("img")
              .attr("src", "data:image/svg+xml;base64,"+ btoa(html));
    }
