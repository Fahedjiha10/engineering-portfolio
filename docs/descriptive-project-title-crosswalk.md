# Descriptive Project Title Crosswalk

This crosswalk replaces generic course and Visual Studio labels with titles derived from the retained source code, state-machine models, reports, menus, functions, inputs, outputs, and assignment text. Original names remain in parentheses for traceability. They are not the public-facing project titles.

## Naming rules

- **Verified title** means the behavior is explicit in source code or on the document title page.
- **Inferred title** means the behavior is clear from implementation but the original artifact had no formal title.
- **Unrecoverable** means the retained folder is empty, contains no relevant source, or contains only a link. No function has been invented.
- Revisions and byte-for-byte copies are grouped as one project family and labeled as duplicates.
- Reference samples and supplied assignment instructions are not presented as wholly original work.

## RIMS and embedded-state-machine assignments

### Bit-Reversed Complement Port Transformer (original: `Assignment 2 - EEL4730`)

- **Purpose:** Demonstrate bit extraction, bit setting/clearing, reversal, and logical complement on an 8-bit embedded port value.
- **Inputs:** Eight-bit value read from RIMS input port A.
- **Processing:** `GetBit` isolates each source bit; `SetBit` writes the inverted bit to the mirrored destination position.
- **Outputs:** Reversed and complemented 8-bit result on port B.
- **Technologies:** C, RIMS, shifts, masks, pointers, byte-level I/O.
- **Status:** Implemented source retained; hardware/simulator verification evidence was not independently rerun.
- **Known problems:** The source assigns the full byte to `B0` rather than clearly assigning it to `B`, which may be a port-variable mistake depending on the RIMS environment.
- **Title confidence:** High; inferred directly from the loop and bit operations.

### Sensor-Gated Automatic Door Controller (original: `Assignment 3 - EEL4730`)

- **Purpose:** Open a door when the approach-sensor condition is satisfied and close it after both sensor inputs clear.
- **Inputs:** RIMS sensor bits A0 and A1.
- **Processing:** Two-state `DOOR_CLOSED`/`DOOR_OPEN` finite-state machine.
- **Outputs:** Door actuator/status on B0.
- **Technologies:** C, RIMS, finite-state machines, digital I/O.
- **Status:** Implemented in one retained C file with related report/model artifacts.
- **Duplicates/problems:** `Assignement 3- EEL4730.c` is empty; `Assignment 3 - EEL4730.c` is the meaningful implementation.
- **Title confidence:** High.

### Two-Switch Combination Lock and Collision-Aware Door Controller (original: `Assignment Z1`, `Assignment 1 examples`, and switch-sequence example)

- **Purpose:** Demonstrate state memory with two small controllers: an ordered switch sequence unlocks a lock, and front/back sensors determine whether an automatic door may open safely.
- **Inputs:** A0/A1 switch sequence; front and rear presence sensors.
- **Processing:** Sequential lock states remember prior switch events; conditional door logic prevents opening when the rear/collision condition is present.
- **Outputs:** Lock-open indication and door-open state on B0 or simulated variables.
- **Technologies:** C, RIMS-style I/O, finite-state sequencing.
- **Status:** Example implementations retained.
- **Known problems/ownership:** Some files are explicitly labeled examples and should be described as coursework exercises, not wholly original designs.
- **Title confidence:** High.

### 90-Second Infant Motion Monitor and Inactivity Alarm (original: `Assignment 4`, Exercise 1, and `Assignment 4#1` variants)

- **Purpose:** Monitor motion and activate an alarm after 90 consecutive no-motion timing cycles; provide reset/recovery behavior.
- **Inputs:** Motion sensor A0 and reset/acknowledge input A1.
- **Processing:** A counter or synchronous state machine moves through start, monitoring, no-motion, and alarm states.
- **Outputs:** Alarm bit B0.
- **Technologies:** C, RIMS, synchronous FSMs, timer/counter logic; one assembly-like draft is also retained.
- **Status:** Multiple source/model/report revisions retained; at least one direct C version expresses the complete behavior.
- **Duplicates/problems:** The generated Exercise 1 C file contains invalid identifiers, assignments inside conditions, malformed `if` syntax, and incomplete actions. The direct C versions are more credible than that generated draft.
- **Title confidence:** High.

### Mirrored Bidirectional LED Scanner (original: `Assignment 4 Exercise 2`)

- **Purpose:** Animate two lit endpoints toward one another and reverse direction as the pattern reaches its transition point.
- **Inputs:** A0 starts or resets the animation.
- **Processing:** `Start`, left-to-right, and right-to-left states shift `top` and `bot` bit patterns and combine them with bitwise OR.
- **Outputs:** Animated eight-bit LED pattern on port B.
- **Technologies:** C, RIMS state-machine generator, synchronous FSM, bit shifting.
- **Status:** C and `.sm` model retained.
- **Known problems:** The reverse-transition comparison uses `top == 0x10` in both direction states; this should be simulator-tested because it may not produce the intended full sweep.
- **Title confidence:** High.

### Asymmetric Timed LED Duty-Cycle Controller (original: `Assignment 5 Part 1`)

- **Purpose:** Alternate an LED between two timed states with different dwell durations.
- **Inputs:** Timer ticks; no external control input in the retained implementation.
- **Processing:** Two-state FSM counts approximately six ticks in one state and four in the other.
- **Outputs:** LED state on B0/port B.
- **Technologies:** C, RIMS timer interrupt, synchronous FSM.
- **Status:** Implemented C and `.sm` retained.
- **Known problems:** State names and output assignments appear inverted (`LED_ON` clears B while `LED_OFF` sets B0), so the electrical active-low assumption or naming error should be clarified.
- **Title confidence:** High for behavior; medium for intended LED polarity.

### Selectable Full-Array Flasher and Bouncing LED Scanner (original: `Assignment 5`)

- **Purpose:** Provide two LED display modes: timed all-on/all-off flashing and a single illuminated bit moving back and forth.
- **Inputs:** A0 starts the system; A1 selects the animation mode.
- **Processing:** Initialization/mode-selection states route into flasher or bidirectional shift states; counters control dwell time.
- **Outputs:** Eight-bit LED patterns on B.
- **Technologies:** C, RIMS, synchronous FSM, counters, bit shifts.
- **Status:** Implemented C, `.sm`, report, and course outline retained.
- **Known problems:** `LEFT_TO_RIGHT` shifts the `ball` variable without consistently assigning it to B, so one direction may not display correctly. Direction labels may also be reversed relative to bit order.
- **Title confidence:** High.

### Persistent-Motion Glitch Filter (original: `Assignment 6`)

- **Purpose:** Reject short motion-sensor pulses and assert motion only after the input remains active for a sustained interval.
- **Inputs:** Motion signal A0 sampled every 120 ms.
- **Processing:** `WAIT` → `FILTER_GLITCH` → `MOTION` FSM; a counter qualifies the input before accepting it.
- **Outputs:** Filtered motion indication B0.
- **Technologies:** C, RIMS, synchronous FSM, temporal filtering.
- **Status:** C, `.sm`, report, and outline retained.
- **Known problems:** `cnt` is not visibly reset when the signal returns to `WAIT`; repeated short pulses may accumulate rather than requiring one continuous interval. At 150 ticks × 120 ms, the acceptance delay is about 18 seconds, which should be checked against the assignment specification.
- **Title confidence:** High.

### Timer-Driven LED Blink Controller (original: `Assignment 7 Part 1`)

- **Purpose:** Toggle an LED between on and off states at periodic timer ticks.
- **Inputs:** Timer ticks and an internal/output bit used as a transition condition.
- **Processing:** Two-state `Blink_Off`/`Blink_On` FSM.
- **Outputs:** B0 LED state.
- **Technologies:** C, RIMS, synchronous FSM.
- **Status:** Draft implementation retained.
- **Known problems:** Conditions use assignment (`B1=1`, `B1=0`) instead of comparison, making transitions incorrect; the declared counter is unused.
- **Title confidence:** High for intended function; implementation is incomplete/incorrect.

### Sustained-Input Alarm Latch (original: `Assignment 7 Part 2`)

- **Purpose:** Require an input to remain active for a timed qualification interval before latching a stable output.
- **Inputs:** A0.
- **Processing:** `Idle` → `Tone` → `Stable` state sequence with a counter threshold.
- **Outputs:** B0 becomes active in the stable state.
- **Technologies:** C, RIMS, timer-driven FSM.
- **Status:** Draft implementation retained.
- **Known problems:** The counter is not reset when returning to idle, and `Stable` has no exit transition. The filename/report calls this a tone exercise, but the retained C only asserts a steady bit and does not generate an audible waveform.
- **Title confidence:** High for implemented behavior; “tone controller” would overstate the source.

### Concurrent LED Blinker and Three-Light Sequencer (original: `Assignment 8`)

- **Purpose:** Run two independent periodic behaviors from one scheduler: blink one LED and rotate a one-hot pattern across three other LEDs.
- **Inputs:** Shared 500 ms timer tick.
- **Processing:** Two tick functions execute round-robin: a two-state blinker and a three-state sequencer.
- **Outputs:** B0 toggles; B5, B6, and B7 cycle one at a time.
- **Technologies:** C, RIMS, concurrent synchronous state machines, shared timer scheduler.
- **Status:** C, `.sm`, and report retained.
- **Known problems:** Both machines currently use the same base period; the report contains original and updated code that should be reconciled before claiming a final verified revision.
- **Title confidence:** High.

### Multirate Embedded Task Scheduler Analysis (original: `Homework 9 - Chapter Z8`)

- **Purpose:** Analyze periodic task counts, least-common-multiple synchronization, greatest-common-divisor timer periods, and a timer-interrupt scheduler loop.
- **Inputs:** Task periods, elapsed-time values, and base timer period.
- **Processing:** Scheduler iterates through a task array, calls eligible tick functions, resets elapsed time, and advances counters.
- **Outputs:** Timing answers and C scheduler pseudocode.
- **Technologies:** C, embedded scheduling, periodic tasks, GCD/LCM timing.
- **Status:** Completed written homework retained.
- **Known problems:** The written tick sequences contain duplicated/garbled values, although the stated totals and 600 ms/100 ms timing conclusions are understandable.
- **Title confidence:** High from the document heading and code.

### Button-to-UART Queued Transmission Scheduler (original: `Homework 10 Z7`)

- **Purpose:** Convert a button event into a queued UART message using separate manager tasks.
- **Inputs:** Simulated button press and UART-ready flag.
- **Processing:** Button manager selects a string, queue manager copies characters into a circular buffer, and UART manager dequeues/transmits characters.
- **Outputs:** `Hello, UART!` emitted through simulated `printf` UART output.
- **Technologies:** C, finite-state managers, circular queue, UART scheduling.
- **Status:** Completed instructional C listing retained in a Word document.
- **Known problems:** `main` calls each manager only once, so the full string is not drained without a periodic scheduler loop; UART readiness is simulated rather than hardware-backed.
- **Title confidence:** High.

### TinyOS Task Scheduler and Low-Power Event Model Study (original: `Homework 11 - Z10`)

- **Purpose:** Compare TinyOS with Arduino and study tasks, event handlers, FIFO scheduling, non-preemption, task posting, and processor sleep behavior.
- **Inputs:** Assigned TinyOS FAQ and scheduler readings.
- **Processing:** Written technical analysis of scheduler behavior and constraints.
- **Outputs:** Completed question-and-answer document.
- **Technologies:** TinyOS, embedded operating systems, cooperative scheduling, low-power systems.
- **Status:** Completed written homework; no executable TinyOS project retained.
- **Title confidence:** High.

### Binary Company Directory Random-Access Report Generator (original: `assignmnet 10.c`)

- **Purpose:** Read fixed-size company/contact records from a binary database and produce a formatted text report.
- **Inputs:** Binary input filename and text output filename.
- **Processing:** Uses `fseek` to address each structure-sized block, `fread` to load ten company records, and a helper to format fields.
- **Outputs:** Text report containing company name, address, telephone numbers, rating, and contact.
- **Technologies:** C/C++, structs, binary files, random access, pointers.
- **Status:** Substantial implementation with pasted sample output retained.
- **Duplicates/problems:** Duplicate copy exists in standalone source. It mixes C and C++ (`using namespace std`) and appends raw output after the code, so it will not compile unchanged.
- **Title confidence:** High.

## FPGA, Zybo Z7, and computer-design assignments

### Digital Safe and Coin-Operated Vending Machine Processors (original: `Assignment 5 - Custom Single Purpose Processor`)

- **Purpose:** Design two custom single-purpose processors in VHDL: a programmable-passcode digital safe and a coin-summing soda dispenser.
- **Inputs:** Safe passcode switches/control inputs; vending price switches and nickel/dime/quarter pushbuttons.
- **Processing:** High-level state machines partition control and datapath behavior; the vending design accumulates coin value and resets after dispense.
- **Outputs:** Safe-status LEDs and soda-dispense indicator.
- **Technologies:** VHDL, Xilinx Vivado, Zybo Z7, PmodSWT, HLSM/FSM design.
- **Status:** Assignment/instruction document retained; the archive does not contain enough HDL/bitstream evidence to claim both processors were fully implemented and board-verified.
- **Known problems:** Separate supplied instructions from authored VHDL/screenshots before presenting this as completed work.
- **Title confidence:** Verified from the document.

### Zynq AXI GPIO Button-to-LED Bare-Metal System (original: `Assignment 6 - Vivado and Vitis`)

- **Purpose:** Integrate the Zynq ARM processor with AXI GPIO peripherals, then poll board buttons and drive LEDs from bare-metal C.
- **Inputs:** Zybo Z7 physical pushbuttons through AXI GPIO.
- **Processing:** Vivado block design connects the processing system and GPIO IP; exported XSA hardware is consumed by Vitis; C software polls inputs and writes outputs.
- **Outputs:** Physical LED states and serial/debug feedback.
- **Technologies:** Zybo Z7, Zynq-7000, Vivado, Vitis, AXI GPIO, C, XDC constraints.
- **Status:** Detailed instructional document retained; completed student source/bitstream evidence is incomplete in the archive.
- **Title confidence:** Verified from the document.

### Zybo AXI Timer Peripheral and Five-Second Bare-Metal Countdown (original: `Assignment 7` and `Assignment_7_Completed`)

- **Purpose:** Connect an AXI timer to the Zynq processing system and program a polled five-second delay from bare-metal software.
- **Inputs:** 100 MHz timer clock, timer reset value, and software configuration.
- **Processing:** Vivado block design connects Zynq to AXI Timer; Vitis initializes/self-tests `XTmrCtr`, configures down-count mode, loads 500,000,000 ticks, starts the timer, and polls expiration.
- **Outputs:** Serial message confirming that the five-second delay elapsed.
- **Technologies:** Zybo Z7, Zynq-7000, AXI Timer, Vivado, Vitis, C, Xilinx `XTmrCtr` driver.
- **Status:** Full assignment document and code listing retained; board execution evidence should be checked in the document screenshots before describing it as independently verified.
- **Duplicates/problems:** `Assignment_7.docx` and `Assignment_7_Completed.docx` contain the same assignment content and should be one portfolio entry.
- **Title confidence:** Verified directly from the document title and code.

### MIPS Instruction Encoding, Memory Layout, Endianness, and Arithmetic (original: `Lab 2 - EEL4709C`)

- **Purpose:** Examine MIPS instruction formats, program-counter behavior, memory alignment, byte order, address construction, and interactive arithmetic.
- **Inputs:** QtSpim programs, memory/register state, and user-entered A/B/C/D integers.
- **Processing:** Decode instructions/opcodes, trace PC and `jal`, inspect byte layout, identify little-endian storage, and compute `(A + B) - (C - D)` in assembly.
- **Outputs:** Lab answers, memory tables, traced results, and MIPS assembly program.
- **Technologies:** MIPS assembly, QtSpim, instruction encoding, computer architecture.
- **Status:** Completed report retained.
- **Known problems:** The report header says `EEL4909C`, while the filename/course grouping says EEL4709C; preserve the official course identifier only after confirmation.
- **Title confidence:** High.

### MIPS Procedures, Stack Frames, Calling Conventions, and Recursion (original: `Lab3_Report_Final`)

- **Purpose:** Study procedure calls, return addresses, caller/callee-saved registers, stack argument passing, and recursive execution.
- **Inputs:** QtSpim MIPS programs and register/memory traces.
- **Processing:** Step through `jal`/`jr`, inspect `$ra`, analyze calling conventions and recursive stack behavior.
- **Outputs:** Trace tables, written analysis, and screenshots.
- **Technologies:** MIPS assembly, QtSpim, stack frames, recursion, ABI conventions.
- **Status:** Report retained, but visible placeholders such as `[Fill from QtSpim]` indicate parts may be incomplete.
- **Title confidence:** Verified from the report title.

### IEEE-754 Arithmetic, Overflow/Underflow, and Floating-Point Factorials (original: `Lab 4 - EEL4709C`)

- **Purpose:** Analyze signed/unsigned integers and IEEE-754 single-precision data, then implement factorial calculation using MIPS floating-point operations.
- **Inputs:** Predefined register bit patterns and user-entered factorial value `n`.
- **Processing:** Decode sign/exponent/mantissa, predict overflow/underflow, convert integers with `mtc1`/`cvt.s.w`, and multiply iteratively.
- **Outputs:** Register analysis, arithmetic conclusions, MIPS/C demonstrations, and factorial results for 5, 10, 15, and 20.
- **Technologies:** MIPS assembly, C, QtSpim, IEEE-754 floating point.
- **Status:** Completed report retained.
- **Known problems:** Some theoretical wording around underflow/denormalized results should be checked against the simulator’s exact exception/rounding behavior.
- **Title confidence:** Verified from the report.

## Circuit-analysis reports

### DC Ohm's-Law and Series/Parallel Network Verification (original: `EEL3110C Circuit Lab Report #1`)

- **Purpose:** Compare calculated and Multisim voltage/current results for basic resistive circuits.
- **Inputs:** 5 V source and 1 kΩ resistor networks.
- **Processing:** Ohm's-law calculations, branch-current analysis, node-voltage comparison, and simulation.
- **Outputs:** Voltage/current tables, theoretical work, experimental analysis, and conclusions.
- **Technologies:** Circuit analysis, Multisim, Ohm's law, series/parallel networks.
- **Status:** Collaborative report retained.
- **Title confidence:** High from report content.

### Thévenin Equivalent Circuit Analysis and Simulation (original: `EEL3110C Circuit Lab Report #3`)

- **Purpose:** Reduce resistor networks to Thévenin voltage and resistance equivalents and verify them in simulation.
- **Inputs:** 5 V source and multiple 1 kΩ resistor networks.
- **Processing:** Voltage-divider, series/parallel resistance, open-circuit voltage, KCL/KVL, and Multisim comparison.
- **Outputs:** Calculated/simulated Vth and Rth values with conclusions.
- **Technologies:** Thévenin's theorem, Multisim, DC network analysis.
- **Status:** Collaborative report retained.
- **Known problems:** One result table appears to swap the Vth/Rth row labels; narrative calculations clarify the intended values.
- **Title confidence:** High.

### Series and Parallel RLC Resonance Analysis (original: `EEL3110C Circuit Lab Report #5`)

- **Purpose:** Determine resonant frequency, impedance, output response, and quality factor for series and parallel RLC circuits.
- **Inputs:** 1 mH inductor, 1 µF capacitor, 1 kΩ resistor, and 1 V peak AC source.
- **Processing:** Compute `1/(2π√LC)`, analyze reactance cancellation and impedance, calculate quality factor, and compare with simulation.
- **Outputs:** Resonance values near 1.592 kHz, voltage/impedance results, Q-factor analysis, and conclusions.
- **Technologies:** AC circuit analysis, RLC resonance, Multisim.
- **Status:** Collaborative report retained.
- **Known problems:** Some explanation wording for the parallel branch/current path is imprecise and should be edited before public quotation.
- **Title confidence:** High.

### Digital Logic in Modern Technologies - Theoretical Research Study (original: `EEL3712 Research Paper Final`)

- **Purpose:** Connect Boolean logic, combinational/sequential circuits, minimization, and state machines to CPUs, FPGAs, ASICs, embedded systems, and emerging computing technologies.
- **Inputs:** Technical literature and digital-design concepts.
- **Processing:** Comparative research covering ALUs, FPGA/ASIC implementation, power/delay scaling, fault tolerance, neuromorphic/optical/quantum computing, and future logic methods.
- **Outputs:** Formal research paper.
- **Technologies:** Digital logic, CPU architecture, FPGA, ASIC, embedded systems, emerging computing.
- **Status:** Final-labeled paper retained.
- **Title confidence:** Exact title recovered from page 1.

## Visual Studio C++ project folders

### Visual Studio Solution Shell - Function Unrecoverable (original: `Assignment 1`)

- **Purpose:** Unknown; no C/C++ source survived.
- **Inputs/processing/outputs:** Not recoverable.
- **Technologies:** Visual Studio C++ project metadata only.
- **Status:** Incomplete shell; do not present as a working project.
- **Title confidence:** Function intentionally left unrecoverable rather than invented.

### Soccer Roster, Goal Totals, and Top-Scorer Analyzer (original: `baldder`)

- **Purpose:** Load an 11-player roster, display jersey/goals data, total team goals, and identify one or more top scorers.
- **Inputs:** User-selected roster file containing player name, number, and goals.
- **Processing:** Structure array, file parsing, menu dispatch, total and maximum calculations.
- **Outputs:** Formatted roster, team-goal total, and star-player report.
- **Technologies:** C++, Visual Studio, structs, arrays, file I/O, formatted output.
- **Status:** Main source is substantial; a second unrelated grade-summary draft in the same folder is badly broken.
- **Duplicates/problems:** Main source is byte-for-byte duplicated in `Soccer`.

### Grade File Loader Prototype (original: `COURSE SUMMARY`)

- **Purpose:** Provide a menu that opens a course-grade data file as the first stage of a grade-report program.
- **Inputs:** Menu choice and filename.
- **Processing:** Validate choice and attempt file open.
- **Outputs:** File-open success/failure or goodbye message.
- **Technologies:** C++, Visual Studio, file streams, switch statements.
- **Status:** Early prototype, not a complete analytics report.
- **Duplicates:** Predecessor to `coursesummary_THISONE` and `Project1`.

### Course Grade Summary Report Generator (original: `coursesummary_THISONE`)

- **Purpose:** Read course metadata and student scores from a file and display a structured grade summary.
- **Inputs:** User-selected grade file.
- **Processing:** Parse course/professor/term and student records; intended summary calculations include extrema and average.
- **Outputs:** Course header, student list, and grade summary.
- **Technologies:** C++, file I/O, strings, loops, menu validation.
- **Status:** More developed authored revision, though control-flow and summary completeness should be compiler-tested.
- **Duplicates:** Same project family as `COURSE SUMMARY` and `Project1`.

### Four-Score Console Formatting Exercise (original: `dummy`)

- **Purpose:** Practice newline placement and chained console output.
- **Inputs:** None.
- **Processing:** Literal string output only.
- **Outputs:** A fragmented “Four score and seven years ago” phrase.
- **Technologies:** Beginner C++ console I/O.
- **Status/problems:** Missing braces/namespace qualification in the retained file; scratch exercise, not a portfolio project.

### Basic Variable and Console-Output Scratchpad (original: `DUMMY PRACTICE`)

- **Purpose:** Very early variable/string/output experimentation.
- **Status:** Excluded from employer-facing material.
- **Known problems:** Contains an unprofessional/vulgar string and no meaningful completed function.

### Lost in the Everglades Ranger Rescue Game - Alternate Build (original: `Everglades`)

- **Purpose:** Guide a ranger across a 5×5 grid to rescue tourists before a 12-gong timer expires while resolving random hazards.
- **Inputs:** Menu choices, row/column moves, fight/wait decisions.
- **Processing:** Random hazard placement, map management, validation, combat, and time-cost rules.
- **Outputs:** Console map, warnings, remaining time, and win/loss result.
- **Technologies:** C++, arrays, functions, randomization, stateful game logic.
- **Status/problems:** Substantial alternate revision; movement writes `map[row - 1][col]`, which can index outside the array and does not correctly track the previous ranger position.
- **Duplicates:** Same project family as `EVERGLASED REVISED`, `Project2`, and `Project5`.

### Lost in the Everglades Rescue Strategy Game - Featured Revision (original: `EVERGLASED REVISED`)

- **Purpose:** Featured group revision of the ranger-rescue grid game.
- **Inputs/processing/outputs:** Same core game model as above, with improved menu, movement, danger, and timing structure.
- **Technologies:** C++, Visual Studio, matrices, randomization, validation, modular functions.
- **Status:** Selected public revision; collaborative work must remain labeled.
- **Duplicates:** Consolidates the other Everglades folders rather than representing a separate concept.

### Hello-World and Syntax Scratchpad Collection (original: `HW3`)

- **Purpose:** Introductory compiler/project testing.
- **Status:** Scratch folder; not portfolio-worthy.
- **Known problems:** Contains a tiny Hello World, an unprofessional duplicate scratch file, and an empty source.

### Mobile Data Plan Billing and Overage Calculator (original: `iMOBILEcalculator`)

- **Purpose:** Calculate a cellular customer’s monthly charge for package A, B, or C.
- **Inputs:** Package selection and gigabytes used.
- **Processing:** Validate inputs, apply included-data allowance and package-specific overage rate.
- **Outputs:** Calculated amount due and validation messages.
- **Technologies:** C++, conditional logic, numeric input validation.
- **Status:** Implemented coursework program.
- **Duplicates:** Standalone `iMobile.cpp` is the same project family.

### Loan Amortization Summary Calculator - Early Revisions (original: `loanCalculator`)

- **Purpose:** Produce a borrower/lender loan-payment report.
- **Inputs:** Borrower, lender, principal, annual rate, loan term, and report date.
- **Processing:** Convert annual to monthly interest, calculate payment count, amortized monthly payment, total repayment, and total interest.
- **Outputs:** Loan-payment summary.
- **Technologies:** C++, financial formulas, formatted console output.
- **Status:** Two early revisions retained.
- **Duplicates:** Same family as `loanCalculator.cpp`, `retry`, `LOANPAYMENT.CPP`, and standalone copies.

### Formatted Loan Payment Summary Calculator (original: `loanCalculator.cpp`)

- **Purpose:** Most developed formatted revision of the loan-amortization report.
- **Status:** Logic is present but audit compilation failed.
- **Known problems:** Calls `pow()` without including `<cmath>`; input and financial assumptions should be validated before reuse.

### Empty C++ Source Placeholder (original: `m6uta`)

- **Purpose:** Unrecoverable; retained source file is empty.
- **Status:** Exclude as a project.

### Interior Paint and Labor Cost Estimator (original: `paintEstimator`)

- **Purpose:** Estimate materials, labor, and total price for painting multiple rooms.
- **Inputs:** Price per gallon, room count, and wall area per room.
- **Processing:** Validate values, derive required gallons and labor hours, then calculate paint and labor costs.
- **Outputs:** Gallons, hours, paint cost, labor cost, and total project cost.
- **Technologies:** C++, functions, numeric validation, estimation formulas.
- **Status:** Implemented and modularized coursework program.

### Visual Studio Hello-World Setup Test (original: `Project 1`)

- **Purpose:** Verify solution/project creation and basic console compilation.
- **Inputs:** None.
- **Outputs:** Hello World text.
- **Status:** Minimal setup exercise, not a substantive project.

### Course Grade Analytics and Summary Report (original: `Project1`)

- **Purpose:** Read a grade file, present course/student data, and identify highest and lowest grades.
- **Inputs:** Grade-data filename and records.
- **Processing:** Parse metadata/student pairs and track extrema.
- **Outputs:** Formatted course report and grade statistics.
- **Technologies:** C++, file I/O, strings, loops, formatted output.
- **Status:** Developed alternate revision.
- **Duplicates:** Same family as `COURSE SUMMARY` and `coursesummary_THISONE`.

### Everglades Ranger Rescue Game - Alternate Matrix Build (original: `Project2`)

- **Purpose:** Full alternate implementation of the 5×5 rescue game.
- **Status:** Substantial but duplicate concept.
- **Duplicates:** Consolidate with the featured Everglades revision.

### Lo Shu Magic-Square Validator - Basic Version (original: `Project3`)

- **Purpose:** Determine whether nine entered numbers form a 3×3 Lo Shu magic square.
- **Inputs:** Nine integer values and retry choice.
- **Processing:** Arrange a matrix and compare row, column, and diagonal sums.
- **Outputs:** Displayed square and valid/invalid result.
- **Technologies:** C++, arrays, loops, validation logic.
- **Status/problems:** Working concept; weaker input-range and duplicate checking than `Project4`.

### Lo Shu Magic-Square Validator with Range and Duplicate Protection (original: `Project4`)

- **Purpose:** Robust revision of the 3×3 Lo Shu validator.
- **Inputs:** Nine unique integers from 1 through 9.
- **Processing:** Reject out-of-range/duplicate input, then verify every row, column, and diagonal.
- **Outputs:** Matrix and validity result.
- **Technologies:** C++, arrays, nested loops, defensive input validation.
- **Status:** Preferred magic-square revision.
- **Duplicates:** Supersedes `Project3`.

### Everglades Rescue Game - Adjacent-Movement Revision (original: `Project5`)

- **Purpose:** Alternate game revision emphasizing adjacent-cell validation, randomized danger, gong tracking, and danger resolution.
- **Status:** Substantial duplicate revision.
- **Duplicates:** Consolidate with featured Everglades project.

### Microsoft Word Service-Report Print Automation Prototype (original: `Project6`)

- **Purpose:** Launch Microsoft Word through COM, open a service-report document, print it, close Word, and release automation objects.
- **Inputs:** Hard-coded/local Word document path and installed Word COM server.
- **Processing:** COM initialization, Word application/document automation, print command, cleanup.
- **Outputs:** Printed service report.
- **Technologies:** Windows C++, COM automation, Microsoft Word.
- **Status:** Experimental prototype; not working production software.
- **Known problems:** Incomplete/incorrect COM declarations and error handling; path portability and Office dependency remain unresolved.

### Rectangular-Solid Volume and Surface-Area Calculator (original: `recSolid`)

- **Purpose:** Calculate rectangular-prism geometry.
- **Inputs:** Height, length, and width.
- **Processing:** Volume `l×w×h`; surface area `2(lw+lh+wh)`.
- **Outputs:** Volume and surface area.
- **Technologies:** Beginner C++, arithmetic, console input/output.
- **Status:** Implemented; two near-identical source revisions.
- **Duplicates:** `RecSolid.cpp` and `Recsolid (1).cpp` are the same project family.

### Rectangular-Solid Geometry Calculator - Alternate Revision (original: `RecSolid.cpp`)

- **Purpose:** Alternate beginner implementation of the same geometry formulas.
- **Status:** Duplicate revision; group under the project above.

### Loan Payment Calculator Recovery Revision (original: `retry`)

- **Purpose:** Reconstruct/repair the formatted loan-payment calculation.
- **Outputs:** Annual/monthly rate, payment count, monthly payment, total repayment, and interest.
- **Status:** Partial alternate revision, not a separate project.
- **Duplicates:** Group with the loan calculator family.

### Soccer Roster and Top-Scorer Analyzer - Duplicate Copy (original: `Soccer`)

- **Purpose:** Same roster/statistics behavior as `baldder`.
- **Status:** Duplicate folder.
- **Known fact:** Principal source is byte-for-byte identical to `baldder/Source.cpp`.

### Stock Investment Gain/Loss Calculator - Early Version (original: `Stock Trade`)

- **Purpose:** Measure realized performance of a stock purchase and sale.
- **Inputs:** Company/symbol, share count, purchase price, selling price, and commission assumptions.
- **Processing:** Calculate acquisition cost, sale proceeds, buying/selling commissions, and net gain/loss.
- **Outputs:** Investment performance summary.
- **Technologies:** C++, financial arithmetic, formatted output.
- **Status:** Early revision.
- **Duplicates:** Superseded by `StockTrade`; standalone copies also exist.

### Commission-Aware Stock Trade Profit/Loss Report (original: `StockTrade`)

- **Purpose:** Preferred revision of the stock-investment calculator with a formatted realized gain/loss report.
- **Inputs/processing/outputs:** Same project family as above, with clearer commission-aware reporting.
- **Status:** More developed revision; use this title publicly.

## Software-design and experimental artifacts

### Window and Door Quote Calculator - Java Design Proposal (original: `COP2210 Project Proposal`)

- **Purpose:** Design a Java estimating application for window/door openings, products, glass, installation, tax, and total quote value.
- **Inputs:** Opening number, width, height, quantity, product type, glass type, and installation selection.
- **Processing:** Object-oriented opening records, square-footage calculation, product/installation pricing, tax, and project aggregation.
- **Outputs:** Organized opening summary and total estimate.
- **Technologies:** Proposed Java classes/objects, arrays, loops, methods, and user input.
- **Status:** Proposal/design artifact; no completed Java application was found in the archive.
- **Title confidence:** Exact proposal title recovered.

### Unreal First-Person Environment and Interaction Prototype (original: `MyProject2` / Unreal prototype)

- **Purpose:** Explore an Unreal Engine first-person character, projectile/rifle interaction, level layout, and world-partition content.
- **Inputs:** Keyboard/mouse first-person controls and template interaction inputs.
- **Processing:** Unreal Blueprint/template gameplay and level assets.
- **Outputs:** Playable first-person prototype environment.
- **Technologies:** Unreal Engine 5, Blueprint assets, world partition.
- **Status:** Experimental; personal modifications have not been fully separated from Epic/template and Storage House pack content.
- **Known problems/ownership:** Do not claim third-party assets as original work; two near-duplicate project folders were found.

## Recommended public project-family names

Use these as the portfolio-level titles, while the detailed crosswalk above preserves individual assignments and revisions:

1. ESP8266 IoT Telemetry and Remote Device Control
2. RIMS Embedded Control and Concurrent State-Machine Portfolio
3. Zybo Z7 Hardware/Software Co-Design Portfolio
4. MIPS Computer Architecture and Arithmetic Laboratory Portfolio
5. Circuit Simulation and Network Analysis Laboratory Portfolio
6. C++ Financial and Engineering Calculator Collection
7. C++ File Processing and Analytics Collection
8. Lost in the Everglades Rescue Strategy Game
9. Floorplan Reader - Construction Drawing Classification and QA
10. Window and Door Quote Calculator - Software Design Proposal


