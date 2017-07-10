"use strict"

// register the application module
b4w.register("iEEG_surface", function(exports, require) {

// import modules used by the app
var m_app       = require("app");
var m_data      = require("data");
// Joel added this
var m_scenes    = require("scenes");
var m_mouse     = require("mouse");
var m_constraints = require("constraints");
var m_transform = require("transform");
var m_mat       = require("material");
var m_textures = require("textures");

    var subject = "291";
    var picked;
    var picked_before = "empty";
    var contacts_CT;
    var slicenum;
    var cor_slicenum;
    var newslice = 'axial/axial0200.png';
    var cor_newslice = 'coronal/sagittal0300.png';
    var picked_name;
    var annotating = false;
    var annotate = [];
    var annotate_name;
    var annotate_color = [1,1,1];
    var annotate_show = true;
    var annotate_contact;
    var cortex_white = true;
    var cortex_color = [];
    var cortex_opaque = true;
    var opacity = 1;
    var zoom = 1;
    var canvas;
    var cor_canvas;
    var resize_fusion;
    var resize_options;
    var add_annotate = '';
    var first_slice = 94;
    var last_slice = 238;
    var cor_first_slice = 76;
    var cor_last_slice = 418;

/**
 * export the method to initialize the app (called at the bottom of this file)
 */
exports.init = function() {
    m_app.init({
        canvas_container_id: "main_canvas_container",
        callback: init_cb,
        show_fps: false,
        console_verbose: true,
        autoresize: true
    });
}

/**
 * callback executed when the app is initialized 
 */
function init_cb(canvas_elem, success) {

    if (!success) {
        console.log("b4w init failure");
        return;
    }

    load();
    
    //Joel added this
    
    $( '#item-1').hide();
    $( '#item-2').hide();
    $( '#item-3').hide();
    $( '#item-4').hide();
    $( '#item-5').hide();
    $( '#item-6').hide();
    
    resize_fusion = function() {
        var options_width = $( "#options_panel" )[0].offsetWidth;
        if (options_width < 532) {zoom = (options_width-20)/512;} else {zoom = 1;}
        canvas.width = 512*zoom;
        canvas.height = 512*zoom;
        canvas.style.marginTop = '-' + 512*zoom + 'px';
        document.getElementById("slice").style.width = 512*zoom + 'px';
        document.getElementById("slice").style.height = 512*zoom + 'px';
        cor_canvas.width = 514*zoom;
        cor_canvas.height = 511*zoom;
        cor_canvas.style.marginTop = '-' + 512*zoom + 'px';
        document.getElementById("cor_slice").style.width = 514*zoom + 'px';
        document.getElementById("cor_slice").style.height = 511*zoom + 'px';
    };
    
    resize_options = function() {
        document.getElementById('options_panel').style.maxHeight = ($(window).height() - document.getElementById('display_panel').style.height - document.getElementById('fusion_panel').style.height) +"px";
    };

    var options_hidden = true;
    document.getElementById("show_options").onmousedown = function () {
        if (options_hidden) {
            document.getElementById("main_canvas_container").style.width="65%";
            document.getElementById("options_panel").style.width="35%";
            document.getElementById("show_options").style.right = "35.6%";
            resize_fusion();
            resize_options();
            }
        else {
            document.getElementById("main_canvas_container").style.width="100%"
            document.getElementById("options_panel").style.width="0%";
            document.getElementById("show_options").style.right = "0.6%";
        }
        options_hidden = !options_hidden;
    }
    
    // Load the monopolar and bipolar names and CT coordinates
    // Nested jQuery AJAX calls to make sure data is loaded
    var monopolars_CT = [];
    var bipolars_CT = [];
    var contacts_CT = [];
    $.ajax({
        type: 'GET',
        url: 'VOX_coords_mother_dykstra.txt',
        success: function(data) {
            var data1 = data.split(/\r?\n/);
            for(var i = 0; i < data1.length; i++){
                monopolars_CT.push(data1[i].split(/\s/));
            }
            $.ajax({
                type: 'GET',
                url: 'VOX_coords_mother_dykstra_bipolar.txt',
                success: function(data) {
                    var data1 = data.split(/\r?\n/);
                    for(var i = 0; i < data1.length; i++){
                        bipolars_CT.push(data1[i].split(/\s/));
                    }
                    contacts_CT = monopolars_CT.concat(bipolars_CT);
                }
            });
        }
    });
    
    canvas = document.getElementById("depth_coords");
    cor_canvas = document.getElementById("cor_depth_coords");
    //Highlight contacts or regions on hover over and display name
    function mouse_move(e) {
        var x = m_mouse.get_coords_x(e);
        var y = m_mouse.get_coords_y(e);
        picked = m_scenes.pick_object(x, y);
        if (picked != null) {
            if (picked != picked_before) {
                if (picked_before != "empty") {
                    if (picked_before.annotated) {
                        m_mat.set_diffuse_color(picked_before, "Red", picked_before.annotate_color);
                        m_mat.set_diffuse_color(picked_before, "Blue", picked_before.annotate_color);
                        m_mat.set_diffuse_color(picked_before, "Green", picked_before.annotate_color);
                    }
                    else {
                        //Sets previously hovered over contact back to original color
                        m_mat.set_diffuse_color(picked_before, "Red", [1,0,0]);
                        m_mat.set_diffuse_color(picked_before, "Blue", [0,0,1]);
                        m_mat.set_diffuse_color(picked_before, "Green", [0,1,0]);
                    }
                }
            }
            //Highlights newly hovered over contacts
            if (picked.annotate_name) {add_annotate = " - " + picked.annotate_name;} else {add_annotate = "";}
            picked_name = m_scenes.get_object_name(picked);
            m_mat.set_diffuse_color(picked, "Red", [1,0.8,0]);
            m_mat.set_diffuse_color(picked, "Blue", [1,0.8,0]);
            m_mat.set_diffuse_color(picked, "Green", [1,0.8,0]);
            document.getElementById('ecog_container').innerHTML = picked_name + add_annotate;
            picked_before = picked;
        }
        //Highlight depth if depth_viewer loaded
        if (!options_hidden) {
            for(var i = 0; i < contacts_CT.length; i++) {
                if(contacts_CT[i][0] == picked_name || "o" + contacts_CT[i][0] == picked_name) {
                        slicenum = "00" + contacts_CT[i][3];
                        slicenum = slicenum.substring(slicenum.length-4, slicenum.length);
                        newslice = "axial/axial" + slicenum + ".png";
                        document.getElementById("slice").src=newslice;
                        document.getElementById("slice").style.width = 512*zoom + 'px';
                        document.getElementById("slice").style.height = 512*zoom + 'px';
                        var ctx = canvas.getContext("2d");
                        ctx.clearRect(0, 0, canvas.width, canvas.height);
                        ctx.beginPath();
                        console.log(contacts_CT[i][1]*zoom,(contacts_CT[i][2]*zoom)-18,5*zoom,0,2*Math.PI);
                        ctx.arc(contacts_CT[i][1]*zoom,(contacts_CT[i][2]*zoom)-18,5*zoom,0,2*Math.PI);
                        ctx.strokeStyle = '#FFFE9A';
                        ctx.stroke();
                        
                        cor_slicenum = "00" + contacts_CT[i][2];
                        cor_slicenum = cor_slicenum.substring(cor_slicenum.length-4, cor_slicenum.length);
                        cor_newslice = "coronal/sagittal" + cor_slicenum + ".png";
                        document.getElementById("cor_slice").src=cor_newslice;
                        document.getElementById("cor_slice").style.width = 514*zoom + 'px';
                        document.getElementById("cor_slice").style.height = 511*zoom + 'px';
                        var cor_ctx = cor_canvas.getContext("2d");
                        cor_ctx.clearRect(0, 0, cor_canvas.width, cor_canvas.height);
                        cor_ctx.beginPath();
                        console.log(contacts_CT[i][1]*zoom,((cor_canvas.height-44*zoom-(contacts_CT[i][3])*1.436*zoom))-21, 5*zoom,0,2*Math.PI);
                        cor_ctx.arc(contacts_CT[i][1]*zoom,((cor_canvas.height-44*zoom-(contacts_CT[i][3])*1.436*zoom))-21, 5*zoom,0,2*Math.PI);
                        console.log(zoom);
                        cor_ctx.strokeStyle = '#FFFE9A';
                        cor_ctx.stroke();
                }
            }
        }
        
    }
    
    annotate_contact = function(a, b, c, d) {
        m_mat.set_diffuse_color(a, "Red", c);
        m_mat.set_diffuse_color(a, "Blue", c);
        a.annotated = true;
        a.annotate_name = b;
        a.annotate_color = c;
        a.annotate_show = true;
        a.annotate_onoff = d;
    };
    
    function mouse_down() {
        if (annotating) {
            if(picked) {
                if(picked.annotated) {
                    m_mat.set_diffuse_color(picked_before, "Red", [1,0,0]);
                    m_mat.set_diffuse_color(picked_before, "Blue", [0,0,1]);
                    picked.annotated = false;
                }
                else {
                    annotate_contact(picked, annotate_name, annotate_color, 0);
                }
            }
        }
    }
    canvas_elem.addEventListener("mousedown", mouse_down, false);
    canvas_elem.addEventListener("mousemove", mouse_move, false);
    
    var y1 = 0;
    function mousemoveslice(e) {
        var y = m_mouse.get_coords_y(e);
        slicenum = slicenum.replace(/^0+/, '');
        if (y - y1 > 0) {
            slicenum = Number(slicenum) + 1;
            if (slicenum == last_slice) {slicenum = first_slice + 1;}
        }
        if (y - y1 < 0) {
            slicenum = Number(slicenum) - 1;
            if (slicenum == first_slice) {slicenum = last_slice - 1;}
        }
        slicenum = "000" + slicenum;
        slicenum = slicenum.substring(slicenum.length-4, slicenum.length);
        newslice = "axial/axial" + slicenum + ".png";
        document.getElementById("slice").src=newslice;
    }
    
    function cor_mousemoveslice(e) {
        var y = m_mouse.get_coords_y(e);
        cor_slicenum = cor_slicenum.replace(/^0+/, '');
        if (y - y1 > 0) {
            cor_slicenum = Number(cor_slicenum) + 1;
            if (cor_slicenum == cor_last_slice) {cor_slicenum = cor_first_slice + 1;}
        }
        if (y - y1 < 0) {
            cor_slicenum = Number(cor_slicenum) - 1;
            if (cor_slicenum == cor_first_slice) {cor_slicenum = cor_last_slice - 1;}
        }
        cor_slicenum = "000" + cor_slicenum;
        cor_slicenum = cor_slicenum.substring(cor_slicenum.length-4, cor_slicenum.length);
        cor_newslice = "coronal/sagittal" + cor_slicenum + ".png";
        document.getElementById("cor_slice").src=cor_newslice;
    }
    
    
    function mouseup(e) {
        canvas.removeEventListener("mousemove", mousemoveslice, false);
        cor_canvas.removeEventListener("mousemove", cor_mousemoveslice, false);
    }
    
    canvas.addEventListener("mousedown", getPosition, false);
    function getPosition(event) {
          y1 = event.y;
          console.log(y1);
          canvas.getContext("2d").clearRect(0, 0, canvas.width, canvas.height);
          canvas.addEventListener("mousemove", mousemoveslice, false);
          canvas.addEventListener("mouseup", mouseup, false);
    }
    
    cor_canvas.addEventListener("mousedown", cor_getPosition, false);
    function cor_getPosition(event) {
          y1 = event.y;
          console.log(y1);
          cor_canvas.getContext("2d").clearRect(0, 0, cor_canvas.width, cor_canvas.height);
          cor_canvas.addEventListener("mousemove", cor_mousemoveslice, false);
          cor_canvas.addEventListener("mouseup", mouseup, false);
    }
    
}



/**
 * load the scene data
 */
function load() {
    m_data.load("iEEG_surface.json", load_cb);
}

/**
 * callback executed when the scene is loaded
 */
function load_cb(data_id) {
    m_app.enable_camera_controls();

    // Joel added this
    m_mouse.enable_mouse_hover_outline();
    // Joel added below this
    var monopolars;
    var monopolars_start;
    var bipolars;
    var contacts;
    var i;
    // Load the monopolar and bipolar names and orient contacts to center
    // Also load contacts at the original coordinates before Dykstra method
    // Nested jQuery AJAX calls to make sure data is loaded
    $.ajax({
        type: 'GET',
        url: 'monopolar_names.txt',
        success: function(data) {
            monopolars = data.replace(/\"/g, '');
            monopolars = monopolars.replace(/,\s*$/, "");
            monopolars = monopolars.split(",");
            $.ajax({
                type: 'GET',
                url: 'monopolar_start_names.txt',
                success: function(data) {
                    monopolars_start = data.replace(/\"/g, '');
                    monopolars_start = monopolars_start.replace(/,\s*$/, "");
                    monopolars_start = monopolars_start.split(",");
                    contacts = monopolars.concat(monopolars_start);
                    $.ajax({
                        type: 'GET',
                        url: 'bipolar_names.txt',
                        success: function(data) {
                            bipolars = data.replace(/\"/g, '');
                            bipolars = bipolars.replace(/,\s*$/, "");
                            bipolars = bipolars.split(",");
                            contacts = contacts.concat(bipolars);
                            for (i = 0; i < contacts.length; i++) {
                                m_constraints.append_track(m_scenes.get_object_by_name(contacts[i]), m_scenes.get_object_by_name('Empty'), 'Z','X');
                            }
                            // Hide the contacts at the original starting coordinates
                            for (i = 0; i < monopolars_start.length; i++) {
                                m_scenes.hide_object(m_scenes.get_object_by_name(monopolars_start[i]), false);
                            }
                        }
                    });
                }
            }); 
        }
    });   
    
    // Button functions to show or hide hemispheres, cortex labels, transparency, monopolars, bipolars
    var left_hidden = false;
    var right_hidden = false;
    var bipolars_hidden = false;
    var monopolars_hidden = false;
    var monopolars_start_hidden = true;
    document.getElementById("cortex_left").onclick = function () {
        if (left_hidden == false) {
            m_scenes.hide_object(m_scenes.get_object_by_name('lh'), false);
        }
        else {
            m_scenes.show_object(m_scenes.get_object_by_name('lh'), false);
        }
        left_hidden = !left_hidden;
    };
    document.getElementById("cortex_right").onclick = function () {
        if (right_hidden == false) {
            m_scenes.hide_object(m_scenes.get_object_by_name('rh'), false);
        }
        else {
            m_scenes.show_object(m_scenes.get_object_by_name('rh'), false);
        }
        right_hidden = !right_hidden;
    };
    var lh_test = new RegExp("lh.");
    var rh_test = new RegExp("rh.");
    document.getElementById("cortex_color").onclick = function () {
        var all_objs = m_scenes.get_all_objects("ALL", data_id)
        if (cortex_white) {
            for (i = 0; i < all_objs.length; i++) {
                if (lh_test.test(m_scenes.get_object_name(all_objs[i])) || rh_test.test(m_scenes.get_object_name(all_objs[i]))) {
                    m_mat.set_diffuse_color(all_objs[i], "White", [Math.random(),Math.random(),Math.random()]);
                }
            }
        }
        else {
            for (i = 0; i < all_objs.length; i++) {
                if (lh_test.test(m_scenes.get_object_name(all_objs[i])) || rh_test.test(m_scenes.get_object_name(all_objs[i]))) {
                    m_mat.set_diffuse_color(all_objs[i], "White", [1,1,1]);
                }
            }
        }
        cortex_white = !cortex_white;
    };
    document.getElementById("cortex_transparent").onclick = function () {
        var all_objs = m_scenes.get_all_objects("ALL", data_id)
        if (cortex_opaque) { opacity = 0.5; } else { opacity = 1; }
        cortex_opaque = !cortex_opaque
        for (i = 0; i < all_objs.length; i++) {
            if (lh_test.test(m_scenes.get_object_name(all_objs[i])) || rh_test.test(m_scenes.get_object_name(all_objs[i]))) {
                cortex_color = m_mat.get_diffuse_color(all_objs[i], "White");
                cortex_color[3] = opacity
                m_mat.set_diffuse_color(all_objs[i], "White", cortex_color);
            }
        }
    };
    document.getElementById("monopolars").onclick = function () {
        for (i = 0; i < monopolars.length; i++) {
            if (monopolars_hidden === false) {
                m_scenes.hide_object(m_scenes.get_object_by_name(monopolars[i]), false);
            }
            else{
                m_scenes.show_object(m_scenes.get_object_by_name(monopolars[i]), false);
            }   
        }
        monopolars_hidden = !monopolars_hidden;
    };
    document.getElementById("bipolars").onclick = function () {
        for (i = 0; i < bipolars.length; i++) {
            if (bipolars_hidden === false) {
                m_scenes.hide_object(m_scenes.get_object_by_name(bipolars[i]), false);
            }
            else{
                m_scenes.show_object(m_scenes.get_object_by_name(bipolars[i]), false);
            }   
        }
        bipolars_hidden = !bipolars_hidden;
    };
     document.getElementById("monopolars_start").onclick = function () {
        for (i = 0; i < monopolars_start.length; i++) {
            if (monopolars_start_hidden === false) {
                m_scenes.hide_object(m_scenes.get_object_by_name(monopolars_start[i]), false);
            }
            else{
                m_scenes.show_object(m_scenes.get_object_by_name(monopolars_start[i]), false);
            }   
        }
        monopolars_start_hidden = !monopolars_start_hidden;
    };
    document.getElementById("slice_up").onclick = function () {
        canvas.getContext("2d").clearRect(0, 0, canvas.width, canvas.height);
        slicenum = slicenum.replace(/^0+/, '');
        slicenum = Number(slicenum) + 1;
        if (slicenum == last_slice) {slicenum = first_slice + 1;}
        slicenum = "000" + slicenum;
        slicenum = slicenum.substring(slicenum.length-4, slicenum.length);
        newslice = "axial/axial" + slicenum + ".png";
        document.getElementById("slice").src=newslice;
    };
    document.getElementById("slice_down").onclick = function () {
        canvas.getContext("2d").clearRect(0, 0, canvas.width, canvas.height);
        slicenum = slicenum.replace(/^0+/, '');
        slicenum = Number(slicenum) - 1;
        if (slicenum == first_slice) {slicenum = last_slice - 1;}
        slicenum = "000" + slicenum;
        slicenum = slicenum.substring(slicenum.length-4, slicenum.length);
        newslice = "axial/axial" + slicenum + ".png";
        document.getElementById("slice").src=newslice;
    };
    document.getElementById("slice_back").onclick = function () {
        cor_canvas.getContext("2d").clearRect(0, 0, canvas.width, canvas.height);
        cor_slicenum = cor_slicenum.replace(/^0+/, '');
        cor_slicenum = Number(cor_slicenum) + 1;
        if (cor_slicenum == cor_last_slice) {cor_slicenum = cor_first_slice + 1;}
        cor_slicenum = "000" + cor_slicenum;
        cor_slicenum = cor_slicenum.substring(cor_slicenum.length-4, cor_slicenum.length);
        cor_newslice = "coronal/sagittal" + cor_slicenum + ".png";
        document.getElementById("cor_slice").src=cor_newslice;
    };
    document.getElementById("slice_front").onclick = function () {
        cor_canvas.getContext("2d").clearRect(0, 0, canvas.width, canvas.height);
        cor_slicenum = cor_slicenum.replace(/^0+/, '');
        cor_slicenum = Number(cor_slicenum) - 1;
        if (cor_slicenum == cor_first_slice) {cor_slicenum = cor_last_slice - 1;}
        cor_slicenum = "000" + cor_slicenum;
        cor_slicenum = cor_slicenum.substring(cor_slicenum.length-4, cor_slicenum.length);
        cor_newslice = "coronal/sagittal" + cor_slicenum + ".png";
        document.getElementById("cor_slice").src=cor_newslice;
    };
    // Change contact colors for a given label
    function changeColor(label, color) {
        var parts = color.match(/^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/);
        color = [parts[1]/255, parts[2]/255, parts[3]/255];
        console.log(color);
        var all_objs = m_scenes.get_all_objects("ALL", data_id);
            for (i = 0; i < all_objs.length; i++) {
                if (all_objs[i].annotate_name == label) {
                        all_objs[i].annotate_color = color;
                        m_mat.set_diffuse_color(all_objs[i], "Red", color);
                        m_mat.set_diffuse_color(all_objs[i], "Blue", color);
                }
                all_objs[i].annotate_show = true;
            }      
    }
    
    // Detect changes in jscolor background to propogate to contacts
    var target = document.querySelectorAll(".jscolor");
    for (var i = 0; i < target.length; i++) {
            // create an observer instance
        var observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                changeColor(mutation.target.previousSibling.previousSibling.textContent, mutation.target.style.backgroundColor);
            });
        });
        observer.observe(target[i], { attributes : true, attributeFilter : ['style'] });
    }

    // Turn contact label color on or off by passing contact object
    var toggleLabel = function (contact) {
        if (contact.annotate_show) {
            m_mat.set_diffuse_color(contact, "Red", [1,0,0]);
            m_mat.set_diffuse_color(contact, "Blue", [0,0,1]);
        }
        else {
             m_mat.set_diffuse_color(contact, "Red", contact.annotate_color);
             m_mat.set_diffuse_color(contact, "Blue", contact.annotate_color);
        }
        contact.annotate_show = !contact.annotate_show;
    };
    
    // Provide click functions for eye and edit buttons in annotate list items
    $('#annotation_panel ul li fieldset div div label').bind('touchstart mousedown', function(e) {
        console.log($(this));
        if ($(this).next().attr('name') == 'eye') {
            annotate_name = $(this).parent().parent().parent().prev().prev().text();
            var all_objs = m_scenes.get_all_objects("ALL", data_id);
            for (i = 0; i < all_objs.length; i++) {
                if (all_objs[i].annotate_name == annotate_name) {
                    toggleLabel(all_objs[i]);
                }
            }
        }
        if ($(this).next().attr('name') == 'edit') {
            annotating = !annotating;
            annotate_name = $(this).parent().parent().parent().prev().prev().text();
            var parts = $(this).parent().parent().parent().prev().css('backgroundColor').match(/^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/);
            annotate_color = [parts[1]/255, parts[2]/255, parts[3]/255];
        }
        //console.log('Selected Name=' + $(this).next().attr('name'));
        //console.log(annotate_name);
        //console.log(annotate_color);
    });
    
    // Send annotations to google doc via form
    document.getElementById("save_annotate").onmousedown = function () {
        var all_objs = m_scenes.get_all_objects("ALL", data_id);
        for (i = 0; i < all_objs.length; i++) {
            if (all_objs[i].annotated === true) {
                annotate.push([subject, m_scenes.get_object_name(all_objs[i]), all_objs[i].annotate_name, all_objs[i].annotate_color]);
                $.ajax({
                    url: "https://docs.google.com/forms/d/e/1FAIpQLSdgX10ACmilLovcMTUi0G_24Zr_32H11EO2h9WvlHVqnjRc3g/formResponse",
                    data: {"entry.525775213" : subject, "entry.1690210053" : m_scenes.get_object_name(all_objs[i]), "entry.2036554337": all_objs[i].annotate_name, "entry.1765014722": all_objs[i].annotate_color[0], "entry.85863895": all_objs[i].annotate_color[1], "entry.736496415": all_objs[i].annotate_color[2], "entry.1193438455": all_objs[i].onoff},
                    type: "POST",
                    dataType: "xml"
                });
            }
        }
        console.log(annotate);
    };
    
    // Show a new annotate list item
    var new_annotate = function(label, color) {
        var new_list_item = $( ".list_annotate li:hidden:first" );
        new_list_item.show();
        $( ".list_annotate li:visible:last h2" )[0].textContent = label;
        $( ".list_annotate li:visible:last .jscolor" )[0].style.backgroundColor = "rgb(" + Math.round(color[0]*255) +", " + Math.round(color[1]*255) + ", " +  Math.round(color[2]*255) + ")";
        console.log("rgb(" + color[0]*255 +", " + color[1]*255 + ", " +  color[2]*255 + ")");
    };
    
    // Add a new annotate list item based on name chosen by user
    document.getElementById("new_annotate").onmousedown = function () {
        new_annotate(document.getElementById('text-basic').value, [0.5, 0.5, 0.5]);
    };
    
    // Add unique annotations in to the annotation list
    var add_uniques = function(annotate) {
        var d = [];
        var unique = [];
        for (i=0; i < annotate.length; i++) {
            var item = [annotate[i][2]].concat(annotate[i][3]);
            console.log(item);
            var rep = item.toString();
            if (!d[rep]) {
                d[rep] = true;
                unique.push(item);
            }
        }
        for (i=0; i < unique.length; i++) {
            new_annotate(unique[i][0], [unique[i][1], unique[i][2], unique[i][3]]);
        }
    };
    
    // Load annotations from google doc
    document.getElementById("load_annotate").onmousedown = function () {
        var annotate = [];
        var spreadsheetID = "1Gqal9jyo21nRIk2GUSpoj9s8jXEx4EJGf76k-Vd3aEQ";
        var url = "https://spreadsheets.google.com/feeds/list/" + spreadsheetID + "/1/public/values?alt=json";
        $.getJSON(url, function(data) {
            var entry = data.feed.entry;
            $(entry).each(function(){
                if (this.gsx$subject.$t == subject) {
                    annotate_color = [+this.gsx$colorr.$t, +this.gsx$colorg.$t, +this.gsx$colorb.$t];
                    annotate.push([this.gsx$subject.$t, this.gsx$contact.$t, this.gsx$label.$t, annotate_color, +this.gsx$onoff.$t]);
                    annotate_contact(m_scenes.get_object_by_name(this.gsx$contact.$t), this.gsx$label.$t, annotate_color, +this.gsx$onoff.$t);
                }
            });
            add_uniques(annotate);
        });
    };
    
    document.getElementById("play_annotate").onmousedown = function () {
        var playlist = [];
        var all_objs = m_scenes.get_all_objects("ALL", data_id);
        for (i = 0; i < all_objs.length; i++) {
            if (all_objs[i].annotate_onoff && all_objs[i].annotate_onoff > 0) {
                playlist.push(all_objs[i]);
            }
        }
        for (i = 0; i < playlist.length; i++) {
            setTimeout(toggleLabel, playlist[i].annotate_onoff, playlist[i]);
        }
    };
    
    // Load annotations from local file
    $('#load_local').on('click', function() {$('#files').trigger('click');});
    
    // Parse locally loaded file and then load
    function handleFileSelect(evt) {
        var annotate = [];
        var file = evt.target.files[0];
        Papa.parse(file, {
          header: false,
          dynamicTyping: true,
          complete: function(results) {
            for (i=0; i < results.data.length; i++) {
                annotate_color = [results.data[i][2], results.data[i][3], results.data[i][4]];
                annotate.push([subject, results.data[i][0], results.data[i][1], annotate_color]);
                annotate_contact(m_scenes.get_object_by_name(results.data[i][0]), results.data[i][1], annotate_color);
                add_uniques(annotate);
            }
          }
        });
    }
    $(document).ready(function(){$("#files").change(handleFileSelect);});
        
    // Allows the righthand option panel to scroll properly.
    $(window).resize(function() {
        resize_fusion();
        resize_options();
    });
}

});

// import the app module and start the app by calling the init method
b4w.require("iEEG_surface").init();
