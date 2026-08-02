set script_dir  [file dirname [file normalize [info script]]]
set root_dir    [file normalize "$script_dir/.."]
set project_dir [file normalize "$root_dir/vivado_project_vhdl"]
set project_name "smart_parking_garage_vhdl"
set project_file "$project_dir/$project_name.xpr"

if {[llength [get_projects -quiet]] > 0} { close_project }

if {[file exists $project_file]} {
    open_project $project_file
} else {
    create_project $project_name $project_dir -part xc7z020clg400-1 -force
    set_property target_language VHDL [current_project]
    set_property simulator_language VHDL [current_project]
    set design_files [glob "$root_dir/src/*.vhd"]
    add_files -norecurse $design_files
    foreach design_file $design_files {
        set_property file_type {VHDL 2008} [get_files [file tail $design_file]]
    }
    add_files -fileset constrs_1 -norecurse "$root_dir/constraints/zybo_z7_20_smart_parking.xdc"
    set testbench_file "$root_dir/sim/tb_smart_parking_top.vhd"
    add_files -fileset sim_1 -norecurse $testbench_file
    set_property file_type {VHDL 2008} [get_files [file tail $testbench_file]]
}

set_property top smart_parking_top [get_filesets sources_1]
set_property top tb_smart_parking_top [get_filesets sim_1]
update_compile_order -fileset sources_1
update_compile_order -fileset sim_1
puts "VHDL_PROJECT_READY: $project_file"
