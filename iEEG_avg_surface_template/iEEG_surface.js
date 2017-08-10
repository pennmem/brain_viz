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
       
   
    resize_options = function() {
        document.getElementById('options_panel').style.maxHeight = ($(window).height() - document.getElementById('display_panel').style.height) +"px";
    };

    var options_hidden = true;
    document.getElementById("show_options").onmousedown = function () {
        if (options_hidden) {
            document.getElementById("main_canvas_container").style.width="65%";
            document.getElementById("options_panel").style.width="35%";
            document.getElementById("show_options").style.right = "35.6%";
            resize_options();
            }
        else {
            document.getElementById("main_canvas_container").style.width="100%"
            document.getElementById("options_panel").style.width="0%";
            document.getElementById("show_options").style.right = "0.6%";
        }
        options_hidden = !options_hidden;
    }
    
   
   //Highlight contacts or regions on hover over and display name
    function mouse_move(e) {
        var x = m_mouse.get_coords_x(e);
        var y = m_mouse.get_coords_y(e);
        picked = m_scenes.pick_object(x, y);
        picked_name = m_scenes.get_object_name(picked);
        document.getElementById('ecog_container').innerHTML = picked_name;
        }
    
    canvas_elem.addEventListener("mousemove", mouse_move, false);
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
   
    // Button functions to show or hide hemispheres, cortex labels, transparency, monopolars, bipolars
    var left_hidden = false;
    var right_hidden = false;

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
            for (var i = 0; i < all_objs.length; i++) {
                if (lh_test.test(m_scenes.get_object_name(all_objs[i])) || rh_test.test(m_scenes.get_object_name(all_objs[i]))) {
                    m_mat.set_diffuse_color(all_objs[i], "White", [Math.random(),Math.random(),Math.random()]);
                }
            }
        }
        else {
            for (var i = 0; i < all_objs.length; i++) {
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
        for (var i = 0; i < all_objs.length; i++) {
            if (lh_test.test(m_scenes.get_object_name(all_objs[i])) || rh_test.test(m_scenes.get_object_name(all_objs[i]))) {
                cortex_color = m_mat.get_diffuse_color(all_objs[i], "White");
                cortex_color[3] = opacity
                m_mat.set_diffuse_color(all_objs[i], "White", cortex_color);
            }
        }
    };
   
      
    // Allows the righthand option panel to scroll properly.
    $(window).resize(function() {
        resize_fusion();
        resize_options();
    });
}

});

// import the app module and start the app by calling the init method
b4w.require("iEEG_surface").init();
