set script_dir [file dirname [file normalize [info script]]]
source "$script_dir/ensure_project_vhdl.tcl"
set_property xsim.simulate.runtime all [get_filesets sim_1]
launch_simulation -simset sim_1 -mode behavioral
puts "VHDL_SIMULATION_RUN_COMPLETED"
close_sim
close_project
