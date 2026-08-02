## Smart Parking Garage Counter - Digilent Zybo Z7-20 Rev. B
## Top module: smart_parking_top

## 125 MHz PL clock
set_property -dict { PACKAGE_PIN K17 IOSTANDARD LVCMOS33 } [get_ports { clk }]
create_clock -add -name sys_clk_pin -period 8.00 -waveform {0 4} [get_ports { clk }]

## Capacity setting switches SW0-SW3
set_property -dict { PACKAGE_PIN G15 IOSTANDARD LVCMOS33 } [get_ports { capacity_sw[0] }]
set_property -dict { PACKAGE_PIN P15 IOSTANDARD LVCMOS33 } [get_ports { capacity_sw[1] }]
set_property -dict { PACKAGE_PIN W13 IOSTANDARD LVCMOS33 } [get_ports { capacity_sw[2] }]
set_property -dict { PACKAGE_PIN T16 IOSTANDARD LVCMOS33 } [get_ports { capacity_sw[3] }]

## Push-buttons: BTN0 reset, BTN1 entry, BTN2 exit
set_property -dict { PACKAGE_PIN K18 IOSTANDARD LVCMOS33 } [get_ports { rst_btn }]
set_property -dict { PACKAGE_PIN P16 IOSTANDARD LVCMOS33 } [get_ports { entry_btn }]
set_property -dict { PACKAGE_PIN K19 IOSTANDARD LVCMOS33 } [get_ports { exit_btn }]

## Available-space count on LD0-LD3
set_property -dict { PACKAGE_PIN M14 IOSTANDARD LVCMOS33 } [get_ports { count_led[0] }]
set_property -dict { PACKAGE_PIN M15 IOSTANDARD LVCMOS33 } [get_ports { count_led[1] }]
set_property -dict { PACKAGE_PIN G14 IOSTANDARD LVCMOS33 } [get_ports { count_led[2] }]
set_property -dict { PACKAGE_PIN D18 IOSTANDARD LVCMOS33 } [get_ports { count_led[3] }]

## RGB LED LD5: red, green, and blue channels
set_property -dict { PACKAGE_PIN Y11 IOSTANDARD LVCMOS33 } [get_ports { status_red }]
set_property -dict { PACKAGE_PIN T5  IOSTANDARD LVCMOS33 } [get_ports { status_green }]
set_property -dict { PACKAGE_PIN Y12 IOSTANDARD LVCMOS33 } [get_ports { status_blue }]
