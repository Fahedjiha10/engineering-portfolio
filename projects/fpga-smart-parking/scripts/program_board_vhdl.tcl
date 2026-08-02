set script_dir  [file dirname [file normalize [info script]]]
set root_dir    [file normalize "$script_dir/.."]
set bit_file    [file normalize "$root_dir/release/smart_parking_top.bit"]
if {![file exists $bit_file]} { error "VHDL bitstream not found: $bit_file" }

open_hw_manager
connect_hw_server -allow_non_jtag
open_hw_target
set devices [get_hw_devices]
if {[llength $devices] == 0} { error "No JTAG FPGA device was detected." }

set device ""
foreach candidate $devices {
    if {[string match "*xc7z020*" $candidate]} { set device $candidate; break }
}
if {$device eq ""} { error "No xc7z020 FPGA was found. Detected devices: $devices" }

current_hw_device $device
refresh_hw_device -update_hw_probes false $device
set_property PROGRAM.FILE $bit_file $device
program_hw_devices $device
refresh_hw_device -update_hw_probes false $device
puts "VHDL_HARDWARE_PROGRAMMING_PASSED: $device"
close_hw_target
disconnect_hw_server
close_hw_manager
