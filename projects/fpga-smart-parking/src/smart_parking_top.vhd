library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity smart_parking_top is
    generic (
        CLK_FREQ_HZ : positive := 125_000_000;
        DEBOUNCE_MS : positive := 20;
        PWM_BIT     : natural  := 17
    );
    port (
        clk          : in  std_logic;
        rst_btn      : in  std_logic;
        entry_btn    : in  std_logic;
        exit_btn     : in  std_logic;
        capacity_sw  : in  std_logic_vector(3 downto 0);
        count_led    : out std_logic_vector(3 downto 0);
        status_red   : out std_logic;
        status_green : out std_logic;
        status_blue  : out std_logic
    );
end entity smart_parking_top;

architecture rtl of smart_parking_top is
    type state_type is (IDLE, PROCESS_ENTRY, PROCESS_EXIT);

    signal state             : state_type := IDLE;
    signal next_state        : state_type := IDLE;
    signal spaces_available  : unsigned(3 downto 0) := (others => '0');
    signal maximum_capacity  : unsigned(3 downto 0) := (others => '0');
    signal pwm_counter       : unsigned(PWM_BIT downto 0) := (others => '0');
    signal entry_clean       : std_logic;
    signal exit_clean        : std_logic;
    signal entry_pulse       : std_logic;
    signal exit_pulse        : std_logic;
    signal pwm_gate          : std_logic;
begin
    entry_debounce : entity work.debounce
        generic map (CLK_FREQ_HZ => CLK_FREQ_HZ, DEBOUNCE_MS => DEBOUNCE_MS)
        port map (clk => clk, rst => rst_btn, noisy => entry_btn, clean => entry_clean);

    exit_debounce : entity work.debounce
        generic map (CLK_FREQ_HZ => CLK_FREQ_HZ, DEBOUNCE_MS => DEBOUNCE_MS)
        port map (clk => clk, rst => rst_btn, noisy => exit_btn, clean => exit_clean);

    entry_one_pulse : entity work.one_pulse
        port map (clk => clk, rst => rst_btn, signal_in => entry_clean, pulse_out => entry_pulse);

    exit_one_pulse : entity work.one_pulse
        port map (clk => clk, rst => rst_btn, signal_in => exit_clean, pulse_out => exit_pulse);

    choose_next_state : process (state, entry_pulse, exit_pulse)
    begin
        next_state <= state;
        case state is
            when IDLE =>
                if entry_pulse = '1' and exit_pulse = '0' then
                    next_state <= PROCESS_ENTRY;
                elsif exit_pulse = '1' and entry_pulse = '0' then
                    next_state <= PROCESS_EXIT;
                end if;
            when PROCESS_ENTRY | PROCESS_EXIT =>
                next_state <= IDLE;
        end case;
    end process choose_next_state;

    update_counter : process (clk)
    begin
        if rising_edge(clk) then
            if rst_btn = '1' then
                state <= IDLE;
                maximum_capacity <= unsigned(capacity_sw);
                spaces_available <= unsigned(capacity_sw);
            else
                state <= next_state;
                case state is
                    when PROCESS_ENTRY =>
                        if spaces_available > 0 then
                            spaces_available <= spaces_available - 1;
                        end if;
                    when PROCESS_EXIT =>
                        if spaces_available < maximum_capacity then
                            spaces_available <= spaces_available + 1;
                        end if;
                    when IDLE => null;
                end case;
            end if;
        end if;
    end process update_counter;

    generate_pwm : process (clk)
    begin
        if rising_edge(clk) then
            if rst_btn = '1' then
                pwm_counter <= (others => '0');
            else
                pwm_counter <= pwm_counter + 1;
            end if;
        end if;
    end process generate_pwm;

    pwm_gate <= pwm_counter(PWM_BIT);
    count_led <= std_logic_vector(spaces_available);
    status_green <= pwm_gate when spaces_available > 0 else '0';
    status_red <= pwm_gate when spaces_available = 0 else '0';
    status_blue <= '0';
end architecture rtl;
