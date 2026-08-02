# FPGA Smart Parking Garage Controller

A completed VHDL-2008 controller for the Digilent Zybo Z7-20. Four switches set the garage capacity, push buttons simulate vehicle entry and exit, four LEDs show the remaining spaces in binary, and the RGB status LED changes from green to red when the garage becomes full.

## How it works

- **Inputs:** 125 MHz board clock, reset/load button, entry button, exit button, and four capacity switches.
- **Processing:** two-stage input synchronization, 20 ms push-button debouncing, one-clock event pulses, and an `IDLE` / `PROCESS_ENTRY` / `PROCESS_EXIT` finite-state machine.
- **Safety behavior:** the counter cannot fall below zero or rise above the loaded capacity. Simultaneous entry and exit events are ignored.
- **Outputs:** LD0-LD3 display the number of available spaces in binary. RGB LD5 is green when spaces remain and red when the count reaches zero; PWM reduces its brightness.

## Verification

The included self-checking testbench covers reset, entry and exit events, lower and upper bounds, simultaneous button presses, capacity reload behavior, held-button behavior, and the unused blue LED channel.

| Check | Result |
|---|---|
| Behavioral simulation | Passed with no reported errors |
| Synthesis | Completed successfully |
| Implementation and bitstream | Completed successfully |
| Timing | Met; WNS +3.967 ns, TNS 0.000 ns |
| Utilization | 50 LUTs and 80 registers |
| Hardware connection | Zybo Z7-20 `xc7z020` detected and programmed |

The design-rule report contains one expected `ZPS7-1` warning because the project uses only programmable logic and does not instantiate the Zynq processing system.

## Repository layout

```text
src/          Synthesizable VHDL modules
sim/          Self-checking VHDL testbench
constraints/  Zybo Z7-20 pin and clock constraints
scripts/      Reproducible Vivado simulation, build, and programming flows
results/      Concise verification record
release/      Generated FPGA bitstream
```

## Reproduce in Vivado

Run these commands from the project root in Vivado batch mode:

```powershell
vivado -mode batch -source scripts/run_simulation_vhdl.tcl
vivado -mode batch -source scripts/run_build_vhdl.tcl
vivado -mode batch -source scripts/program_board_vhdl.tcl
```

The project targets `xc7z020clg400-1`. Programming requires a connected, powered Zybo Z7-20 configured for JTAG.

## Completion status

Completed and verified in Summer 2026. Source, testbench, constraints, automation scripts, verification results, and the generated bitstream are included. Screenshots, generated Vivado caches, and machine-specific logs are intentionally excluded because they expose local paths and add little beyond the reproducible source and results.
