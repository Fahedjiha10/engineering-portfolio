# What Every Project Does

This guide explains the function of each identifiable project or project revision in the portfolio. Descriptions are based on actual source code, menus, functions, reports, project metadata, and filenames—not memory. Revisions and duplicates are called out so they are not mistaken for separate accomplishments.

## Featured software projects

### Floorplan Reader

Reads architectural/construction PDF plan sets and helps organize their pages. The code searches title blocks and sheet indexes, classifies pages into categories such as floor plans, door schedules, storefront/window schedules, structural wind information, kitchen/vendor details, and MEP details, then exports selected pages and a JSON manifest. It can prepare a review package and store manual corrections so later runs classify similar sheets more accurately. A Windows executable and automated tests are included.

### Everglades Rescue Game — revised version

A C++ console adventure on a 5×5 Everglades map. The player controls a ranger trying to reach stranded tourists before a 12-gong time limit expires. Cells may contain alligators, mosquitoes, spiders, or pythons. The player chooses adjacent moves and decides whether to fight or wait when encountering danger; those decisions consume different amounts of time and can reset the ranger's position. The program provides rules, a game menu, randomized hazards, map display, movement validation, and win/loss logic. This is a group project.

### Al Tallow Website

A two-page front-end website prototype. `index.html` provides the main landing experience, `product.html` provides a product-focused page, `style.css` defines the site presentation, and `app.js` provides client-side interactions. A mockup image and short README are included. It demonstrates basic static-site structure and separation of HTML, CSS, JavaScript, and assets.

### Python Hangman

A console word-guessing game. It selects a secret word from `words.txt`, displays blanks and correctly guessed letters, validates that the user enters a single letter, prevents repeated guesses, counts mistakes, and ends with a win or loss after the permitted number of incorrect guesses. Screenshots show the source and sample output. The required `words.txt` was not found, so the game needs that file before it runs normally.

### Deal Scout

A local web dashboard for browsing deal data. The HTML file contains the interface and client-side behavior; the PowerShell scripts provide a lightweight local server and retrieve/serve deal information. It was designed to make deal listings easier to review in a browser. This was produced in an AI-assisted Codex task and should be described that way.

## ESP8266, Arduino, MQTT, and sensor projects

### MQTT Project 1 / MQTT_1 / sketch_mar12a / Alternate Copy

These are near-duplicate versions of the same NodeMCU ESP8266 exercise. They configure the onboard LED as an output and the Flash button as an input with a pull-up resistor. When the button is not pressed, the LED blinks slowly; pressing the button changes it to a faster blink. The exercise demonstrates digital input, digital output, active-low LEDs, functions, and timing with `delay()`.

### MQTT_2 — Losant button and remote LED

Connects an ESP8266 to Wi-Fi and the Losant IoT platform. It reports device state when a physical button is pressed and listens for a Losant `toggle` command that turns the LED on or off remotely. It includes connection/reconnection handling, command parsing, button debouncing/state detection, and device-state transmission. Credentials in the portfolio copy are redacted.

### MQTT_3 — local DHT22 reader

Reads temperature and humidity from a DHT22 sensor connected to the ESP8266 and prints measurements through the serial interface. This stage focuses on sensor initialization, periodic sampling, validation, and local telemetry before cloud transmission is added.

### MQTT4 — Losant temperature and humidity telemetry

Combines the ESP8266, DHT22, Wi-Fi, and Losant. It connects the board to the network/cloud service, reads temperature and humidity, builds a device-state payload, and reports those measurements to the Losant dashboard. The associated reports and dashboard screenshot provide evidence of the telemetry workflow. Credentials in the portfolio copy are redacted.

## RIMS and embedded state-machine coursework

### Bit-Reversed Complement Port Transformer (original: Assignment 2)

Demonstrates reading and writing individual bits in an eight-bit value. `GetBit` extracts a selected bit with shifting and masking; `SetBit` sets or clears a selected bit. The main routine applies those helpers to simulated RIMS input/output ports.

### Sensor-Gated Automatic Door Controller (original: Assignment 3)

Implements a two-state automatic-door controller with `DOOR_CLOSED` and `DOOR_OPEN` states. Sensor inputs determine when the door opens and when it returns to closed, while an output bit represents the door actuator. One C copy is empty, but the other contains the implemented state logic and matching RIMS/report files.

### Two-Switch Combination Lock and Collision-Aware Door Controller (original: Assignment Z1 / Assignment 1 examples)

Contains small finite-state examples for controlling a lock/door from two switches and recognizing an ordered input sequence. They demonstrate how a controller remembers prior inputs instead of treating each switch independently. Some files are labeled as examples and should not be claimed as original project work without checking the assignment instructions.

### 90-Second Infant Motion Monitor and Inactivity Alarm (original: Assignment 4)

Implements a motion-monitoring alarm. Motion resets an inactivity counter; if no motion is detected for the configured interval, the alarm output activates. A reset input silences or resets the alarm. The folder contains several implementations: direct C, RIMS-generated state-machine C, `.sm` models, an assembly-like draft, and reports.

### Mirrored Bidirectional LED Scanner (original: Assignment 4 Exercise 2)

Uses `Start`, left-to-right, and right-to-left states to move an illuminated pattern across output LEDs and then reverse its direction. It demonstrates timed state transitions and output-pattern manipulation.

### Asymmetric Timed LED Duty-Cycle Controller (original: Assignment 5 Part 1)

A simple two-state timed machine that alternates an LED between `LED_ON` and `LED_OFF`. It is an introductory example of using the RIMS timer interrupt and state-machine clock.

### Selectable Full-Array Flasher and Bouncing LED Scanner (original: Assignment 5)

A larger LED-pattern controller with initialization, mode selection, all-on/all-off states, and left-to-right or right-to-left motion. It uses counters and timed ticks to generate animated output patterns.

### Persistent-Motion Glitch Filter (original: Assignment 6)

Implements `WAIT`, `FILTER_GLITCH`, and `MOTION` states. A sensor change must remain stable long enough to pass through the filter state before it is accepted as real motion. The purpose is to reject brief electrical or mechanical glitches rather than immediately changing the output.

### Timer-Driven LED Blink Controller (original: Assignment 7 Part 1)

A two-state `Blink_Off`/`Blink_On` timed controller. A counter and timer tick determine when the output toggles, illustrating periodic behavior in a synchronous state machine.

### Sustained-Input Alarm Latch (original: Assignment 7 Part 2)

Uses `Idle`, `Tone`, and `Stable` states to generate or control a timed tone in response to input. The intermediate/stable states prevent uncontrolled retriggering and demonstrate timed output sequencing.

### Concurrent LED Blinker and Three-Light Sequencer (original: Assignment 8)

Runs at least two timed machines: one toggles an LED, while another cycles through states `T0`, `T1`, and `T2`. It demonstrates sharing one timer scheduler across multiple synchronous state machines with different behaviors.

### Multirate Scheduler, Queued UART, and TinyOS Studies (original: EEL4730 Homeworks 9–11 / Z7 / Z10)

These reports, `.sm` files, and supporting documents continue the state-machine progression into later course zones/homework. The available filenames establish the course sequence, but several documents must be opened manually to distinguish supplied instructions from completed answers. They are retained as supporting evidence rather than described as independent finished products.

### RIMS Parking Lot sample

A reference example showing how a state machine can count or control parking-lot occupancy/entry behavior. It is stored under `Reference_Samples`, meaning it should be treated as course/reference material rather than an authored portfolio project.

### RIMS Latch sample

A reference implementation of a digital latch: an input event sets or changes an output that remains in its state until another event changes it.

### RIMS PWM sample

A minimal reference stub associated with pulse-width modulation. The file is only 47 bytes and is not a developed implementation.

### RIMS Frequency Reader sample

A reference program that measures or derives an input signal's frequency using RIMS timing/counter behavior.

### Binary Company Directory Random-Access Report Generator (original: `assignmnet 10.c`)

This file is not an EEL4730 state-machine project even though the original filename caused it to be copied into that section. It defines a fixed-size company/contact record, asks for input and output filenames, uses `fseek` and `fread` to retrieve selected binary records by block number, and writes formatted company information to an output file. Another copy appears in the standalone C/C++ folder.

## FPGA, Zybo Z7, and bare-metal coursework

### FPGA Smart Parking Garage Counter

A completed VHDL-2008 system that tracks available garage spaces on a Zybo Z7-20. Four switches set capacity; reset loads that capacity; debounced entry and exit buttons generate one-clock events for a three-state finite-state machine. The four-bit count remains between zero and the loaded maximum, drives LD0-LD3 in binary, and changes RGB LD5 from green to red when the garage is full. The project includes synthesizable modules, a self-checking testbench, Zybo constraints, repeatable Tcl flows, selected Vivado evidence, and the generated bitstream. Behavioral simulation passed, all timing constraints were met with +3.967 ns WNS and 0.000 ns TNS, and Vivado Hardware Manager detected and programmed the `xc7z020` device.

### Digital Safe and Coin-Operated Vending Machine Processors (original: Assignment 5)

An EEL4740 assignment centered on designing dedicated digital processors in VHDL for a digital safe and a vending machine. The objective is to translate control behavior into datapath/controller logic and target the design to the Zybo Z7 in Vivado. The retained document may include both supplied instructions and student work, so review it before publication.

### Zynq AXI GPIO Button-to-LED Bare-Metal System (original: Assignment 6)

Builds a Zynq hardware design with the ARM processing system and AXI GPIO peripherals connected to physical buttons and LEDs, then develops a bare-metal C program in Vitis that polls buttons and writes LED outputs. It demonstrates the hardware/software boundary in an FPGA SoC workflow.

### Zybo AXI Timer Peripheral and Five-Second Bare-Metal Countdown (original: Assignment 7)

Creates a Zynq/Vivado block design with an AXI Timer connected to the ARM processing system, exports the hardware platform to Vitis, and configures the timer from bare-metal C. The supplied code initializes and self-tests the `XTmrCtr` driver, loads a 500,000,000-count reset value for a 100 MHz clock, selects down-count mode, polls for expiration, and prints confirmation after a five-second delay. `Assignment_7.docx` and `Assignment_7_Completed.docx` contain the same project content and should be treated as duplicates, not separate accomplishments.

### Zybo Z7 master constraints

An XDC pin-constraint reference for mapping design ports to the Zybo Z7 board's switches, buttons, LEDs, clocks, and peripheral pins. It supports FPGA projects but is a Digilent/reference board file, not a standalone authored project.

### Vivado board-setup utilities

Tcl scripts used to detect the installed Zybo Z7-20 board definition, select it for a Vivado project, add the master XDC constraints file, and verify the resulting project configuration. Logs and journal files document the runs. These scripts were created during an AI-assisted troubleshooting task.

## Electrical and computer-engineering reports

### DC Networks, Thévenin Equivalents, and RLC Resonance (original: EEL3110C Labs 1, 3, and 5)

Three collaborative circuit-analysis reports. Lab 1 verifies Ohm's law and series/parallel resistive networks with Multisim. Lab 3 calculates and simulates Thévenin equivalent voltage and resistance. Lab 5 analyzes series and parallel RLC resonance, impedance, output response, and quality factor near 1.592 kHz.

### MIPS Encoding, Procedures, Stack/Recursion, and IEEE-754 Arithmetic (original: EEL4709C Labs 2–4)

Lab 2 studies MIPS instruction formats, program-counter behavior, memory alignment, little-endian byte order, address construction, and an assembly arithmetic program. Lab 3 covers procedures, calling conventions, `$ra`, stack-based arguments, and recursion in QtSpim. Lab 4 analyzes integer and IEEE-754 representation, overflow/underflow, and a floating-point factorial program. The Lab 3 report still contains visible trace placeholders and should be labeled incomplete.

### Digital Logic in Modern Technologies — A Theoretical Research Study (original: EEL3712 research paper)

A final-labeled research paper connecting Boolean algebra, combinational and sequential logic, minimization, ALUs, FPGAs, ASICs, and embedded systems to neuromorphic, optical, quantum, reversible, approximate, and low-power computing. The title above is taken directly from page 1.

## Visual Studio C++ project folders

### Visual Studio Solution Shell — Function Unrecoverable (original: Assignment 1)

Contains a Visual Studio solution/project structure but no retained C or C++ source file. Its function cannot be recovered from the available contents. Treat it as an incomplete shell, not a portfolio project.

### Soccer Roster, Goal Totals, and Top-Scorer Analyzer (original: baldder)

A soccer-team statistics program. It loads player names, jersey numbers, and goals from a file; displays the roster; totals the team's goals; and identifies the highest-scoring player or tied top scorers. It is effectively a duplicate/revision of the `Soccer` project and contains two source revisions.

### Grade File Loader Prototype (original: COURSE SUMMARY)

An early Course Summary App. It presents a menu, asks for a grade-data filename, opens the file, and produces a grade summary. Two source copies are present, both earlier than the more developed `coursesummary_THISONE`/`Project1` versions.

### Course Grade Summary Report Generator (original: coursesummary_THISONE)

A later course-grade reporting program. It opens a user-selected data file, prints course/professor/term information and a student list, and calculates summary results such as highest and lowest grades. This is one of the clearer authored revisions.

### Four-Score Console Formatting Exercise (original: dummy)

A five-line beginner output-formatting exercise intended to print a version of “Four score and seven years ago.” It is practice code, not a meaningful project.

### Basic Variable and Console-Output Scratchpad — Excluded (original: DUMMY PRACTICE)

A short beginner variable/input practice file. It contains an unprofessional/vulgar output string and should never be published or shown to an employer.

### Lost in the Everglades Ranger Rescue Game — Alternate Build (original: Everglades)

One implementation of the Everglades rescue game. It includes separate functions for rules, menus, map display, danger randomization, movement, and combat. It is closely related to `Project2`, `Project5`, and `EVERGLASED REVISED`.

### Lost in the Everglades Rescue Strategy Game — Featured Revision (original: EVERGLASED REVISED)

The selected featured version of the Everglades group game. It is described above and should be used instead of presenting every revision separately.

### Hello-World and Syntax Scratchpad Collection (original: HW3)

Contains a six-line “Hello, World!” program, a duplicate of the unprofessional dummy-practice file, and an empty source file. It is a scratch/homework folder and should be excluded from public presentation.

### Mobile Data Plan Billing and Overage Calculator (original: iMOBILEcalculator)

A mobile-data billing calculator. The user selects Package A, B, or C and enters gigabytes used. The program validates the package/data input, applies the package's base allowance and overage rate, and prints the amount due.

### Loan Amortization Summary Calculator — Early Revisions (original: loanCalculator)

Contains two early loan-payment report implementations. They collect borrower, lender, principal, annual rate, term, and report date, then calculate monthly interest, number of payments, monthly payment, total repayment, and total interest.

### Formatted Loan Payment Summary Calculator (original: loanCalculator.cpp)

The most developed loan calculator revision, with a formatted “Loan Payment Summary Report.” Its current source does not compile under the audit compiler because it calls `pow()` without including `<cmath>`.

### Empty C++ Source Placeholder — Function Unrecoverable (original: m6uta)

Contains an empty C++ source file. No function can be recovered; it is not a usable project.

### Interior Paint and Labor Cost Estimator (original: paintEstimator)

Estimates a professional interior paint job. It validates price per gallon, number of rooms, and wall area; calculates gallons of paint and labor hours; then reports paint cost, labor cost, and total job cost. The logic is divided into dedicated input and calculation functions.

### Visual Studio Hello-World Setup Test (original: Project 1)

A minimal eight-line “Hello World” Visual Studio test project. It demonstrates only project setup and console output.

### Course Grade Analytics and Summary Report (original: Project1)

A more developed Course Summary App. It reads a grade file, displays course metadata and student scores, and reports highest and lowest grades. This project appears to be a later/alternate revision of `COURSE SUMMARY`.

### Everglades Ranger Rescue Game — Alternate Matrix Build (original: Project2)

Another full Everglades Rescue Game implementation. It initializes the 5×5 matrix, places tourists and hazards, moves the ranger, handles fight/wait decisions, and enforces the gong time limit. It is a substantial alternate revision, not a separate concept.

### Lo Shu Magic-Square Validator — Basic Version (original: Project3)

Prompts the user for nine values, displays them as a 3×3 square, and checks whether they form a Lo Shu magic square—each row, column, and diagonal must sum correctly. It permits retrying, but this earlier version has less duplicate-input validation.

### Lo Shu Magic-Square Validator with Range and Duplicate Protection (original: Project4)

An improved Lo Shu magic-square validator. In addition to checking the 3×3 sums, it rejects values outside 1–9 and prevents the user from entering duplicate numbers.

### Everglades Rescue Game — Adjacent-Movement Revision (original: Project5)

Another large Everglades game revision with menu, rules, randomized dangers, map display, adjacent-cell validation, gong tracking, and danger resolution. It overlaps heavily with the featured revised version.

### Microsoft Word Service-Report Print Automation Prototype (original: Project6)

An experimental Windows C++ program intended to automate Microsoft Word through COM: launch Word invisibly, open a service-report document, print it, close it, and release COM objects. The implementation is incomplete/incorrect and should be treated as a prototype rather than working software.

### Rectangular-Solid Volume and Surface-Area Calculator (original: recSolid)

A rectangular-solid geometry calculator. It accepts height, length, and width and calculates the solid's volume and surface area. Two nearly identical source revisions are included.

### Rectangular-Solid Geometry Calculator — Alternate Revision (original: RecSolid.cpp)

Another beginner version of the rectangular-solid calculator, using separate prompts for width, height, and length before printing volume and surface area.

### Loan Payment Calculator Recovery Revision (original: retry)

An alternate/partial loan-payment calculator. It formats a loan summary containing annual and monthly interest rates, payment count, monthly payment, total repayment, and total interest. It appears to be a revision or recovery attempt rather than a distinct project.

### Soccer Roster and Top-Scorer Analyzer — Duplicate Copy (original: Soccer)

The soccer roster/statistics program described under `baldder`. The principal source is byte-for-byte identical to `baldder/Source.cpp`, so these should be treated as duplicate project folders.

### Stock Investment Gain/Loss Calculator — Early Version (original: Stock Trade)

An early stock-investment performance calculator. It asks for company/symbol, shares, purchase cost, and selling price, then reports total cost, sale proceeds, commissions, and realized gain or loss.

### Commission-Aware Stock Trade Profit/Loss Report (original: StockTrade)

The more developed stock calculator revision. It produces a formatted realized gain/loss report and accounts for buying and selling commissions. Use this revision if promoting the project publicly.

## Standalone C/C++ copies

### Mobile Data Plan Billing and Overage Calculator — Standalone Copy (original: iMobile.cpp)

Standalone copy of the iMobile billing calculator; it is not a separate project.

### Loan Amortization Summary Calculator — Standalone Revisions (original: loanCalculator.cpp / LOANPAYMENT.CPP)

Standalone revisions of the loan-payment calculator. They perform the same core amortized-payment/report calculation with different prompts and formatting.

### Rectangular-Solid Geometry Calculator — Standalone Copy (original: Recsolid (1).cpp)

Standalone copy of the rectangular-solid surface-area/volume exercise.

### Commission-Aware Stock Trade Profit/Loss Calculator — Standalone Revisions (original: stockTrade.cpp / stocktrade_REVISION.cpp)

Standalone copies/revisions of the stock investment gain/loss calculator.

### Binary Company Directory Random-Access Report Generator — Standalone Copy (original: assignmnet 10.c)

The random-access company-record reader described in the embedded section. The standalone location is the better classification for this file.

## Design/documentation artifacts

### Window and Door Quote Calculator — Object Model (original: Window Quote class diagram)

An editable PowerPoint class diagram for a window-quotation application. It documents proposed software classes and relationships rather than containing the application itself.

### Window and Door Quote Calculator — Java Design Proposal (original: COP2210 project proposal)

A proposal for a Java application that stores window and door openings and calculates square footage, product cost, installation cost, tax, and final quote totals. Planned inputs include opening number, width, height, quantity, product type, glass type, and installation selection. The artifact is a design proposal; no completed Java application was found.

### Zybo AXI Timer Peripheral and Five-Second Bare-Metal Countdown — Duplicate Document (original: Assignment 7 completed document)

A duplicate copy of the EEL4740 Zybo AXI Timer assignment. It documents the Vivado Zynq-plus-AXI-Timer design and Vitis `XTmrCtr` code for a polled five-second countdown. Group it with the FPGA/Zybo entry rather than presenting it as separate software-design work.

## Prototype and experimental work

### Unreal First-Person Environment and Interaction Prototype (original: MyProject2)

An Unreal Engine 5 first-person project based on Epic starter/template content and a Storage House asset pack. The curated portfolio copy retains the project configuration, first-person character/game mode/projectile/rifle assets, weapon and arm assets, level-prototyping content, and world-partition actor data. Most of the original project's 2.9 GB is third-party/template content, and two almost identical project folders were found. Personal modifications have not yet been isolated, so do not claim the supplied assets as original work.

### Microsoft Word Service-Report Print Automation Prototype — Experimental Copy (original: Word COM Automation / Project6)

Duplicate curated copy of Visual Studio `Project6`, stored in the experimental section because that is its correct maturity level. Its intended function is to automate printing a Microsoft Word service-report document from C++.

## Recommended public portfolio grouping

To avoid presenting revisions as separate projects, group the material into these real project families:

1. Floorplan Reader
2. ESP8266 MQTT/Losant IoT progression
3. Everglades Rescue Game
4. FPGA Smart Parking Garage
5. RIMS Embedded State-Machine Portfolio
6. Zybo Z7 FPGA/Bare-Metal Coursework
7. Circuit and Computer-Architecture Labs
8. Al Tallow Website
9. Python Hangman
10. Deal Scout
11. Course Summary App
12. iMobile Billing Calculator
13. Loan Payment Calculator
14. Paint Job Estimator
15. Lo Shu Magic Square Validator
16. Soccer Roster Analyzer
17. Stock Investment Performance Calculator
18. Rectangular Solid Calculator
19. Company Record Random-Access Reader
20. Unreal First-Person Prototype
21. Word COM Automation Experiment

Folders labeled dummy, practice, empty, example, reference sample, or duplicate revision should remain archival and should not be presented as separate finished projects.

