library ieee;
use ieee.std_logic_1164.all;

entity one_pulse is
    port (clk : in std_logic; rst : in std_logic; signal_in : in std_logic; pulse_out : out std_logic);
end entity one_pulse;

architecture rtl of one_pulse is
    signal delayed_signal : std_logic := '0';
begin
    delay_input : process (clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                delayed_signal <= '0';
            else
                delayed_signal <= signal_in;
            end if;
        end if;
    end process delay_input;

    pulse_out <= signal_in and not delayed_signal;
end architecture rtl;
