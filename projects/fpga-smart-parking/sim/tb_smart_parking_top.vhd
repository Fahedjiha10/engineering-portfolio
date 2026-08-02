library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use std.env.all;

entity tb_smart_parking_top is
end entity tb_smart_parking_top;

architecture simulation of tb_smart_parking_top is
    constant CLK_PERIOD : time := 1 us;
    signal clk          : std_logic := '0';
    signal rst_btn      : std_logic := '0';
    signal entry_btn    : std_logic := '0';
    signal exit_btn     : std_logic := '0';
    signal capacity_sw  : std_logic_vector(3 downto 0) := std_logic_vector(to_unsigned(4, 4));
    signal count_led    : std_logic_vector(3 downto 0);
    signal status_red   : std_logic;
    signal status_green : std_logic;
    signal status_blue  : std_logic;
begin
    clk <= not clk after CLK_PERIOD / 2;

    dut : entity work.smart_parking_top
        generic map (CLK_FREQ_HZ => 1_000_000, DEBOUNCE_MS => 1, PWM_BIT => 3)
        port map (
            clk => clk, rst_btn => rst_btn, entry_btn => entry_btn, exit_btn => exit_btn,
            capacity_sw => capacity_sw, count_led => count_led, status_red => status_red,
            status_green => status_green, status_blue => status_blue
        );

    stimulus : process
        variable error_count : natural := 0;

        procedure check_count(constant expected : natural) is
        begin
            if unsigned(count_led) /= to_unsigned(expected, count_led'length) then
                report "ERROR at " & time'image(now) & ": expected " & integer'image(expected) &
                    ", got " & integer'image(to_integer(unsigned(count_led))) severity error;
                error_count := error_count + 1;
            else
                report "PASS at " & time'image(now) & ": count = " &
                    integer'image(to_integer(unsigned(count_led))) severity note;
            end if;
        end procedure check_count;

        procedure apply_reset is
        begin
            rst_btn <= '1'; wait for 5 ms; rst_btn <= '0'; wait for 2 ms;
        end procedure apply_reset;

        procedure press_entry is
        begin
            entry_btn <= '1'; wait for 2 ms; entry_btn <= '0'; wait for 2 ms;
        end procedure press_entry;

        procedure press_exit is
        begin
            exit_btn <= '1'; wait for 2 ms; exit_btn <= '0'; wait for 2 ms;
        end procedure press_exit;

        procedure press_both is
        begin
            entry_btn <= '1'; exit_btn <= '1'; wait for 2 ms;
            entry_btn <= '0'; exit_btn <= '0'; wait for 2 ms;
        end procedure press_both;
    begin
        apply_reset; check_count(4);
        press_entry; check_count(3);
        press_entry; check_count(2);
        press_entry; check_count(1);
        press_entry; check_count(0);
        press_entry; check_count(0);
        press_exit; check_count(1);
        press_exit; check_count(2);
        press_exit; check_count(3);
        press_exit; check_count(4);
        press_exit; check_count(4);
        press_both; check_count(4);

        capacity_sw <= std_logic_vector(to_unsigned(7, 4));
        wait for 2 ms; check_count(4);
        apply_reset; check_count(7);

        entry_btn <= '1';
        wait for 2 ms; check_count(6);
        wait for 3 ms; check_count(6);
        entry_btn <= '0'; wait for 2 ms;

        if status_blue /= '0' then
            report "ERROR: blue RGB channel must remain off" severity error;
            error_count := error_count + 1;
        end if;

        if error_count = 0 then
            report "SMART PARKING VHDL TESTBENCH PASSED" severity note;
            finish;
        else
            report "SMART PARKING VHDL TESTBENCH FAILED WITH " &
                integer'image(error_count) & " ERRORS" severity failure;
        end if;
        wait;
    end process stimulus;
end architecture simulation;
