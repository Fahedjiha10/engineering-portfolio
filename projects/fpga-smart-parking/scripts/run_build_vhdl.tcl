set script_dir  [file dirname [file normalize [info script]]]
set root_dir    [file normalize "$script_dir/.."]
set results_dir [file normalize "$root_dir/vivado_results_vhdl"]
file mkdir $results_dir
source "$script_dir/ensure_project_vhdl.tcl"

reset_run synth_1
launch_runs synth_1 -jobs 4
wait_on_run synth_1
set synth_progress [get_property PROGRESS [get_runs synth_1]]
if {$synth_progress ne "100%"} { error "VHDL synthesis did not complete successfully." }

reset_run impl_1
launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1
set impl_progress [get_property PROGRESS [get_runs impl_1]]
if {$impl_progress ne "100%"} { error "VHDL implementation did not complete successfully." }

open_run impl_1
report_timing_summary -delay_type max -max_paths 10 -file "$results_dir/timing_summary.rpt"
report_utilization -file "$results_dir/utilization.rpt"
report_drc -file "$results_dir/drc.rpt"
report_io -file "$results_dir/io_report.rpt"

set bit_candidates [glob -nocomplain "$root_dir/vivado_project_vhdl/*.runs/impl_1/*.bit"]
if {[llength $bit_candidates] == 0} { error "No VHDL bitstream was found after implementation." }
foreach bit_file $bit_candidates {
    file copy -force $bit_file "$results_dir/[file tail $bit_file]"
}
puts "VHDL_BUILD_RUN_COMPLETED"
close_project
