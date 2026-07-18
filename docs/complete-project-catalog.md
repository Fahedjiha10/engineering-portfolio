# What Every Project Does

This guide explains the function of each identifiable project or project revision in the portfolio. Descriptions are based on actual source code, menus, functions, reports, project metadata, and filenamesâ€”not memory. Revisions and duplicates are called out so they are not mistaken for separate accomplishments.

## Featured software projects

### Floorplan Reader

Reads architectural/construction PDF plan sets and helps organize their pages. The code searches title blocks and sheet indexes, classifies pages into categories such as floor plans, door schedules, storefront/window schedules, structural wind information, kitchen/vendor details, and MEP details, then exports selected pages and a JSON manifest. It can prepare a review package and store manual corrections so later runs classify similar sheets more accurately. A Windows executable and automated tests are included.

### Everglades Rescue Game â€” revised version

A C++ console adventure on a 5Ã—5 Everglades map. The player controls a ranger trying to reach stranded tourists before a 12-gong time limit expires. Cells may contain alligators, mosquitoes, spiders, or pythons. The player chooses adjacent moves and decides whether to fight or wait when encountering danger; those decisions consume different amounts of time and can reset the ranger's position. The program provides rules, a game menu, randomized hazards, map display, movement validation, and win/loss logic. This is a group project.

### Al Tallow Website

A two-page front-end website prototype. `index.html` provides the main landing experience, `product.html` provides a product-focused page, `style.css` defines the site presentation, and `app.js` provides client-side interactions. A mockup image and short README are included. It demonstrates basic static-site structure and separation of HTML, CSS, JavaScript, and assets.

### Python Hangman

A console word-guessing game. It selects a secret word from `words.txt`, displays blanks and correctly guessed letters, validates that the user enters a single letter, prevents repeated guesses, counts mistakes, and ends with a win or loss after the permitted number of incorrect guesses. Screenshots show the source and sample output. The required `words.txt` was not found, so the game needs that file before it runs normally.

### Deal Scout

A local web dashboard for browsing deal data. The HTML file contains the interface and client-side behavior; the PowerShell scripts provide a lightweight local server and retrieve/serve deal information. It was designed to make deal listings easier to review in a browser. This was produced in an AI-assisted Codex task and should be described that way.

## ESP8266, Arduino, MQTT, and sensor projects

### MQTT Project 1 / MQTT_1 / sketch_mar12a / Alternate Copy

These are near-duplicate versions of the same NodeMCU ESP8266 exercise. They configure the onboard LED as an output and the Flash button as an input with a pull-up resistor. When the button is not pressed, the LED blinks slowly; pressing the button changes it to a faster blink. The exercise demonstrates digital input, digital output, active-low LEDs, functions, and timing with `delay()`.

### MQTT_2 â€” Losant button and remote LED

Connects an ESP8266 to Wi-Fi and the Losant IoT platform. It reports device state when a physical button is pressed and listens for a Losant `toggle` command that turns the LED on or off remotely. It includes connection/reconnection handling, command parsing, button debouncing/state detection, and device-state transmission. Credentials in the portfolio copy are redacted.

### MQTT_3 â€” local DHT22 reader

Reads temperature and humidity from a DHT22 sensor connected to the ESP8266 and prints measurements through the serial interface. This stage focuses on sensor initialization, periodic sampling, validation, and local telemetry before cloud transmission is added.

### MQTT4 â€” Losant temperature and humidity telemetry

Combines the ESP8266, DHT22, Wi-Fi, and Losant. It connects the board to the network/cloud service, reads temperature and humidity, builds a device-state payload, and reports those measurements to the Losant dashboard. The associated reports and dashboard screenshot provide evidence of the telemetry workflow. Credentials in the portfolio copy are redacted.

## RIMS and embedded state-machine coursework

### Assignment 2 â€” bit manipulation

Demonstrates reading and writing individual bits in an eight-bit value. `GetBit` extracts a selected bit with shifting and masking; `SetBit` sets or clears a selected bit. The main routine applies those helpers to simulated RIMS input/output ports.

### Assignment 3 â€” automatic door state machine

Implements a two-state automatic-door controller with `DOOR_CLOSED` and `DOOR_OPEN` states. Sensor inputs determine when the door opens and when it returns to closed, while an output bit represents the door actuator. One C copy is empty, but the other contains the implemented state logic and matching RIMS/report files.

### Assignment Z1 / Assignment 1 examples â€” door and switch sequencing

Contains small finite-state examples for controlling a lock/door from two switches and recognizing an ordered input sequence. They demonstrate how a controller remembers prior inputs instead of treating each switch independently. Some files are labeled as examples and should not be claimed as original project work without checking the assignment instructions.

### Assignment 4 â€” baby monitor / inactivity alarm

Implements a motion-monitoring alarm. Motion resets an inactivity counter; if no motion is detected for the configured interval, the alarm output activates. A reset input silences or resets the alarm. The folder contains several implementations: direct C, RIMS-generated state-machine C, `.sm` models, an assembly-like draft, and reports.

### Assignment 4 Exercise 2 â€” bidirectional LED sequence

Uses `Start`, left-to-right, and right-to-left states to move an illuminated pattern across output LEDs and then reverse its direction. It demonstrates timed state transitions and output-pattern manipulation.

### Assignment 5 Part 1 â€” timed LED on/off controller

A simple two-state timed machine that alternates an LED between `LED_ON` and `LED_OFF`. It is an introductory example of using the RIMS timer interrupt and state-machine clock.

### Assignment 5 â€” selectable LED animation

A larger LED-pattern controller with initialization, mode selection, all-on/all-off states, and left-to-right or right-to-left motion. It uses counters and timed ticks to generate animated output patterns.

### Assignment 6 â€” motion glitch filter

Implements `WAIT`, `FILTER_GLITCH`, and `MOTION` states. A sensor change must remain stable long enough to pass through the filter state before it is accepted as real motion. The purpose is to reject brief electrical or mechanical glitches rather than immediately changing the output.

### Assignment 7 Part 1 â€” blinking output

A two-state `Blink_Off`/`Blink_On` timed controller. A counter and timer tick determine when the output toggles, illustrating periodic behavior in a synchronous state machine.

### Assignment 7 Part 2 â€” tone controller

Uses `Idle`, `Tone`, and `Stable` states to generate or control a timed tone in response to input. The intermediate/stable states prevent uncontrolled retriggering and demonstrate timed output sequencing.

### Assignment 8 â€” concurrent state machines

Runs at least two timed machines: one toggles an LED, while another cycles through states `T0`, `T1`, and `T2`. It demonstrates sharing one timer scheduler across multiple synchronous state machines with different behaviors.

### EEL4730 Homework 9â€“11 and Z7/Z10 artifacts

These reports, `.sm` files, and supporting documents continue the state-machine progression into later course zones/homework. The available filenames establish the course sequence, but several documents must be opened manually to distinguish supplied instructions from completed answers. They are retained as supporting evidence rather than described as independent finished products.

### RIMS Parking Lot sample

A reference example showing how a state machine can count or control parking-lot occupancy/entry behavior. It is stored under `Reference_Samples`, meaning it should be treated as course/reference material rather than an authored portfolio project.

### RIMS Latch sample

A reference implementation of a digital latch: an input event sets or changes an output that remains in its state until another event changes it.

### RIMS PWM sample

A minimal reference stub associated with pulse-width modulation. The file is only 47 bytes and is not a developed implementation.

### RIMS Frequency Reader sample

A reference program that measures or derives an input signal's frequency using RIMS timing/counter behavior.

### `assignmnet 10.c` â€” random-access company-record reader

This file is not an EEL4730 state-machine project even though the original filename caused it to be copied into that section. It defines a fixed-size company/contact record, asks for input and output filenames, uses `fseek` and `fread` to retrieve selected binary records by block number, and writes formatted company information to an output file. Another copy appears in the standalone C/C++ folder.

## FPGA, Zybo Z7, and bare-metal coursework

### FPGA Smart Parking Garage Counter

A proposed FPGA system that tracks cars entering and leaving a garage. Push buttons simulate entry/exit sensors; the available-space count decreases or increases while remaining between zero and the configured capacity. A green LED indicates availability, a red LED indicates a full garage, and LEDs or a seven-segment display show the remaining count. The intended design uses a finite-state machine, counters, input debouncing, and real-time outputs. Only the proposal was foundâ€”no completed HDL or bitstream.

### Assignment 5 â€” custom single-purpose processors

An EEL4740 assignment centered on designing dedicated digital processors in VHDL for a digital safe and a vending machine. The objective is to translate control behavior into datapath/controller logic and target the design to the Zybo Z7 in Vivado. The retained document may include both supplied instructions and student work, so review it before publication.

### Assignment 6 â€” Vivado/Vitis bare-metal GPIO system

Builds a Zynq hardware design with the ARM processing system and AXI GPIO peripherals connected to physical buttons and LEDs, then develops a bare-metal C program in Vitis that polls buttons and writes LED outputs. It demonstrates the hardware/software boundary in an FPGA SoC workflow.

### Assignment 7

The available document is retained as later EEL4740 coursework, but its project-specific function could not be established reliably from the text extracted during this audit. Treat it as an unidentified course artifact until it is opened and reviewed manually.

### Zybo Z7 master constraints

An XDC pin-constraint reference for mapping design ports to the Zybo Z7 board's switches, buttons, LEDs, clocks, and peripheral pins. It supports FPGA projects but is a Digilent/reference board file, not a standalone authored project.

### Vivado board-setup utilities

Tcl scripts used to detect the installed Zybo Z7-20 board definition, select it for a Vivado project, add the master XDC constraints file, and verify the resulting project configuration. Logs and journal files document the runs. These scripts were created during an AI-assisted troubleshooting task.

## Electrical and computer-engineering reports

### EEL3110C circuit lab reports

Three reports from circuit-analysis laboratory work. They document experimental procedures, circuit calculations or simulation, measurements, results, and conclusions for Labs 1/3/5 as indicated by the filenames. Exact circuit topics should be taken from the report titles before creating public rÃ©sumÃ© bullets.

### EEL4709C Labs 2 and 4 / final Lab 3 report

Computer-architecture or computer-engineering laboratory reports retained as evidence of hardware-focused coursework. They likely document implementation and measured results, but their exact functions require page-level review before making a more specific claim.

### EEL3712 digital-design research paper

The latest final-labeled research paper from the digital-design course. It demonstrates technical research and writing; the exact subject should be taken from the paper's title page before publication.

## Visual Studio C++ project folders

### Assignment 1

Contains a Visual Studio solution/project structure but no retained C or C++ source file. Its function cannot be recovered from the available contents. Treat it as an incomplete shell, not a portfolio project.

### baldder

A soccer-team statistics program. It loads player names, jersey numbers, and goals from a file; displays the roster; totals the team's goals; and identifies the highest-scoring player or tied top scorers. It is effectively a duplicate/revision of the `Soccer` project and contains two source revisions.

### COURSE SUMMARY

An early Course Summary App. It presents a menu, asks for a grade-data filename, opens the file, and produces a grade summary. Two source copies are present, both earlier than the more developed `coursesummary_THISONE`/`Project1` versions.

### coursesummary_THISONE

A later course-grade reporting program. It opens a user-selected data file, prints course/professor/term information and a student list, and calculates summary results such as highest and lowest grades. This is one of the clearer authored revisions.

### dummy

A five-line beginner output-formatting exercise intended to print a version of â€œFour score and seven years ago.â€ It is practice code, not a meaningful project.

### DUMMY PRACTICE

A short beginner variable/input practice file. It contains an unprofessional/vulgar output string and should never be published or shown to an employer.

### Everglades

One implementation of the Everglades rescue game. It includes separate functions for rules, menus, map display, danger randomization, movement, and combat. It is closely related to `Project2`, `Project5`, and `EVERGLASED REVISED`.

### EVERGLASED REVISED

The selected featured version of the Everglades group game. It is described above and should be used instead of presenting every revision separately.

### HW3

Contains a six-line â€œHello, World!â€ program, a duplicate of the unprofessional dummy-practice file, and an empty source file. It is a scratch/homework folder and should be excluded from public presentation.

### iMOBILEcalculator

A mobile-data billing calculator. The user selects Package A, B, or C and enters gigabytes used. The program validates the package/data input, applies the package's base allowance and overage rate, and prints the amount due.

### loanCalculator

Contains two early loan-payment report implementations. They collect borrower, lender, principal, annual rate, term, and report date, then calculate monthly interest, number of payments, monthly payment, total repayment, and total interest.

### loanCalculator.cpp

The most developed loan calculator revision, with a formatted â€œLoan Payment Summary Report.â€ Its current source does not compile under the audit compiler because it calls `pow()` without including `<cmath>`.

### m6uta

Contains an empty C++ source file. No function can be recovered; it is not a usable project.

### paintEstimator

Estimates a professional interior paint job. It validates price per gallon, number of rooms, and wall area; calculates gallons of paint and labor hours; then reports paint cost, labor cost, and total job cost. The logic is divided into dedicated input and calculation functions.

### Project 1

A minimal eight-line â€œHello Worldâ€ Visual Studio test project. It demonstrates only project setup and console output.

### Project1

A more developed Course Summary App. It reads a grade file, displays course metadata and student scores, and reports highest and lowest grades. This project appears to be a later/alternate revision of `COURSE SUMMARY`.

### Project2

Another full Everglades Rescue Game implementation. It initializes the 5Ã—5 matrix, places tourists and hazards, moves the ranger, handles fight/wait decisions, and enforces the gong time limit. It is a substantial alternate revision, not a separate concept.

### Project3

Prompts the user for nine values, displays them as a 3Ã—3 square, and checks whether they form a Lo Shu magic squareâ€”each row, column, and diagonal must sum correctly. It permits retrying, but this earlier version has less duplicate-input validation.

### Project4

An improved Lo Shu magic-square validator. In addition to checking the 3Ã—3 sums, it rejects values outside 1â€“9 and prevents the user from entering duplicate numbers.

### Project5

Another large Everglades game revision with menu, rules, randomized dangers, map display, adjacent-cell validation, gong tracking, and danger resolution. It overlaps heavily with the featured revised version.

### Project6

An experimental Windows C++ program intended to automate Microsoft Word through COM: launch Word invisibly, open a service-report document, print it, close it, and release COM objects. The implementation is incomplete/incorrect and should be treated as a prototype rather than working software.

### recSolid

A rectangular-solid geometry calculator. It accepts height, length, and width and calculates the solid's volume and surface area. Two nearly identical source revisions are included.

### RecSolid.cpp

Another beginner version of the rectangular-solid calculator, using separate prompts for width, height, and length before printing volume and surface area.

### retry

An alternate/partial loan-payment calculator. It formats a loan summary containing annual and monthly interest rates, payment count, monthly payment, total repayment, and total interest. It appears to be a revision or recovery attempt rather than a distinct project.

### Soccer

The soccer roster/statistics program described under `baldder`. The principal source is byte-for-byte identical to `baldder/Source.cpp`, so these should be treated as duplicate project folders.

### Stock Trade

An early stock-investment performance calculator. It asks for company/symbol, shares, purchase cost, and selling price, then reports total cost, sale proceeds, commissions, and realized gain or loss.

### StockTrade

The more developed stock calculator revision. It produces a formatted realized gain/loss report and accounts for buying and selling commissions. Use this revision if promoting the project publicly.

## Standalone C/C++ copies

### iMobile.cpp

Standalone copy of the iMobile billing calculator; it is not a separate project.

### loanCalculator.cpp / LOANPAYMENT.CPP

Standalone revisions of the loan-payment calculator. They perform the same core amortized-payment/report calculation with different prompts and formatting.

### Recsolid (1).cpp

Standalone copy of the rectangular-solid surface-area/volume exercise.

### stockTrade.cpp / stocktrade_REVISION.cpp

Standalone copies/revisions of the stock investment gain/loss calculator.

### assignmnet 10.c

The random-access company-record reader described in the embedded section. The standalone location is the better classification for this file.

## Design/documentation artifacts

### Window Quote class diagram

An editable PowerPoint class diagram for a window-quotation application. It documents proposed software classes and relationships rather than containing the application itself.

### COP2210 project proposal

A proposal document for an introductory programming project. The exact proposed application should be confirmed from the PDF before writing a public description.

### Assignment 7 completed document

A completed recent assignment document produced from the supplied Assignment 7 materials. Review its title/content to determine whether it belongs with FPGA work, software design, or another course before publishing.

## Prototype and experimental work

### Unreal First-Person Prototype

An Unreal Engine 5 first-person project based on Epic starter/template content and a Storage House asset pack. The curated portfolio copy retains the project configuration, first-person character/game mode/projectile/rifle assets, weapon and arm assets, level-prototyping content, and world-partition actor data. Most of the original project's 2.9 GB is third-party/template content, and two almost identical project folders were found. Personal modifications have not yet been isolated, so do not claim the supplied assets as original work.

### Word COM Automation Prototype

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
