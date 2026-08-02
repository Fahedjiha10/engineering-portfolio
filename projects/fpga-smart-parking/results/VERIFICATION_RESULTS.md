# Verification Results

Results recorded from the completed Vivado VHDL flow:

- Self-checking behavioral testbench: passed.
- Synthesis: completed with zero errors and zero critical warnings.
- Implementation: placement, routing, physical optimization, and bitstream generation completed.
- Timing: all user-specified constraints met; worst negative slack was +3.967 ns and total negative slack was 0.000 ns.
- Utilization: 50 slice LUTs (0.09%) and 80 slice registers (0.08%).
- I/O: 15 bonded I/O pins (12%).
- DRC: one `ZPS7-1` warning because this programmable-logic-only design intentionally does not instantiate the Zynq processing system.
- Hardware manager: detected and programmed the `xc7z020` device successfully.

The full machine-generated Vivado reports and logs were reviewed but are not committed because they contain machine-specific paths and build metadata.
