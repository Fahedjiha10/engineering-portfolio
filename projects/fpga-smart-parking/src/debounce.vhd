library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity debounce is
    generic (CLK_FREQ_HZ : positive := 125_000_000; DEBOUNCE_MS : positive := 20);
    port (clk : in std_logic; rst : in std_logic; noisy : in std_logic; clean : out std_logic);
end entity debounce;

architecture rtl of debounce is
    function clog2(value : positive) return positive is
        variable result : natural := 0;
        variable temp   : natural := value - 1;
    begin
        while temp > 0 loop
            result := result + 1;
            temp := temp / 2;
        end loop;
        if result = 0 then return 1; end if;
        return result;
    end function;

    constant COUNT_MAX   : positive := (CLK_FREQ_HZ / 1000) * DEBOUNCE_MS;
    constant COUNT_WIDTH : positive := clog2(COUNT_MAX + 1);
    signal sync_0      : std_logic := '0';
    signal sync_1      : std_logic := '0';
    signal clean_value : std_logic := '0';
    signal count       : unsigned(COUNT_WIDTH - 1 downto 0) := (others => '0');
begin
    clean <= clean_value;

    synchronize_input : process (clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                sync_0 <= '0';
                sync_1 <= '0';
            else
                sync_0 <= noisy;
                sync_1 <= sync_0;
            end if;
        end if;
    end process synchronize_input;

    debounce_input : process (clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                clean_value <= '0';
                count <= (others => '0');
            elsif sync_1 = clean_value then
                count <= (others => '0');
            elsif count = to_unsigned(COUNT_MAX - 1, COUNT_WIDTH) then
                clean_value <= sync_1;
                count <= (others => '0');
            else
                count <= count + 1;
            end if;
        end if;
    end process debounce_input;
end architecture rtl;
