from . import platform
from .yml_util import get_num_in_range, get_one_of


class Clocks:
    def __init__(self, config, part, ddr):
        self.parse_ps_clk(config)
        print("Generating Zynq clocks:")
        self.parse_cpu_clk(config, part)
        self.gen_io_pll(config, part)
        if ddr.enabled:
            self.parse_ddr_clk(ddr, part)

    def tcl_parameters(self):
        return {
            # Osc in
            "PCW_CRYSTAL_PERIPHERAL_FREQMHZ": self.ps_in_freq_mhz,
            # CPU
            "PCW_APU_CLK_RATIO_ENABLE": self.cpu_ratio_mode,
            "PCW_APU_PERIPHERAL_FREQMHZ": self.cpu_freq_mhz,
            "PCW_ARMPLL_CTRL_FBDIV": self.cpu_pll_mul,
            "PCW_CPU_CPU_PLL_FREQMHZ": self.cpu_pll_freq_mhz,
            "PCW_CPU_PERIPHERAL_DIVISOR0": self.cpu_pll_div,
            # DDR
            "PCW_DDRPLL_CTRL_FBDIV": self.ddr_pll_mul,
            "PCW_DDR_DDR_PLL_FREQMHZ": self.ddr_pll_freq_mhz,
            "PCW_DDR_PERIPHERAL_DIVISOR0": self.ddr_pll_div,
            "PCW_UIPARAM_DDR_FREQ_MHZ": self.ddr_freq_mhz,
            # IO
            "PCW_IOPLL_CTRL_FBDIV": self.io_pll_mul,
            "PCW_IO_IO_PLL_FREQMHZ": self.io_pll_freq_mhz,
        }

    def calculate_io_div_and_freq(self, peripheral, target_freq_mhz,
                                  min_freq, max_freq):
        # Brute-force exhaustive search ;)
        best_option = None, None, None

        pll_div_candidates = range(
            platform["io_divisor"]["min"], platform["io_divisor"]["max"] + 1)

        for div in pll_div_candidates:
            freq = self.io_pll_freq_mhz / float(div)
            error = abs(freq - target_freq_mhz)
            if (freq >= min_freq and freq <= max_freq):
                if best_option[0] is None or error < best_option[2]:
                    best_option = (div, freq , error)

        div, freq, _ = best_option
        if div is None:
            raise RuntimeError(
                f"Could not find clk divisor for target {peripheral}"
                f" frequency of: { target_freq_mhz } MHz")

        print(f"\tPeripheral clk source: IO PLL")
        print(f"\tPeripheral clk divisor: {div}")
        print(f"\tActual peripheral frequency: {freq} MHz")
        return div, freq

    def parse_ps_clk(self, config):
        self.ps_in_freq_mhz = get_num_in_range(
            config, "ps_in_freq_mhz", None, float, 
            platform["ps_in_freq_mhz"]["min"],
            platform["ps_in_freq_mhz"]["max"]
        )
        print(f"PS input clk frequency: {self.ps_in_freq_mhz} MHz")

    def parse_cpu_clk(self, config, part):
        print("CPU clock:")
        if "cpu" not in config:
            raise RuntimeError("cpu config section must be specified")
        cpu_config = config["cpu"]

        self.cpu_ratio_mode = get_one_of(
            cpu_config, "ratio_mode", "cpu", str,
            platform["cpu_ratio_modes"]
        )
        
        cpu_min_freq = float(platform["cpu_freq_mhz"]["min"])
        cpu_max_freq = float(
            platform["cpu_freq_mhz"]["max"][self.cpu_ratio_mode][part.speed_grade]
        )

        if "freq_mhz" in cpu_config:
            print("\tcpu freq_mhz specified, auto-calculating CPU PLL values...")
            self.calculate_cpu_pll(cpu_config, part, cpu_min_freq, cpu_max_freq)
        else:
            print("\tcpu freq_mhz not specified, looking for CPU PLL parameters...")
            self.parse_cpu_pll(cpu_config)

        print(f"\tCPU PLL multiplier: {self.cpu_pll_mul}")
        print(f"\tCPU PLL frequency: {self.cpu_pll_freq_mhz}")
        print(f"\tCPU PLL divisor: {self.cpu_pll_div}")


        pll_min_freq = float(platform["pll_freq_mhz"]["min"])
        pll_max_freq = float(platform["pll_freq_mhz"]["max"][part.speed_grade])
        if (self.cpu_pll_freq_mhz < pll_min_freq
            or self.cpu_pll_freq_mhz > pll_max_freq
        ):
            raise RuntimeError(
                "CPU PLL frequency must be in range: {} to {}".format(
                    pll_min_freq, pll_max_freq
                )
            )

        if self.cpu_freq_mhz < cpu_min_freq or self.cpu_freq_mhz > cpu_max_freq:
            raise RuntimeError(
                "CPU frequency must be in range: {} to {}".format(
                    cpu_min_freq, cpu_max_freq
                )
            )

    def calculate_cpu_pll(self, cpu_config, part, cpu_min_freq, cpu_max_freq):
        target_cpu_freq = float(cpu_config["freq_mhz"])
        if target_cpu_freq < cpu_min_freq or target_cpu_freq > cpu_max_freq:
            raise RuntimeError(
                "cpu freq_mhz must be in range: {} to {} MHz".format(
                    cpu_min_freq, cpu_max_freq
                )
            )
        best_option = calculate_pll_params(
                self.ps_in_freq_mhz,
                target_cpu_freq,
                cpu_min_freq,
                cpu_max_freq,
                part.speed_grade,
            )
        if best_option is None:
            raise RuntimeError(
                f"Could not find PLL parameters for target CPU"
                f" frequency of: { target_cpu_freq } MHz")

        self.cpu_pll_mul, self.cpu_pll_div, _ = best_option
        self.cpu_pll_freq_mhz = self.ps_in_freq_mhz * self.cpu_pll_mul

        self.cpu_freq_mhz = self.cpu_pll_freq_mhz / self.cpu_pll_div
        error_percent = (
            100.0 * abs(target_cpu_freq - self.cpu_freq_mhz) / target_cpu_freq
        )
        print(
            f"\tActual CPU frequency: {self.cpu_freq_mhz} MHz"
            f" (target: {target_cpu_freq} MHz, error: {error_percent:.1f}%)"
        )

    def parse_cpu_pll(self, cpu_config):
        self.cpu_pll_mul = get_num_in_range(
            cpu_config, "pll_mul", "cpu", int,
            platform["pll_mul"]["min"],
            platform["pll_mul"]["max"]
        )
        self.cpu_pll_div = get_num_in_range(
            cpu_config, "pll_div", "cpu", int,
            platform["pll_div"]["min"],
            platform["pll_div"]["max"]
        )
        self.cpu_pll_freq_mhz = self.ps_in_freq_mhz * self.cpu_pll_mul
        self.cpu_freq_mhz = self.cpu_pll_freq_mhz / self.cpu_pll_div
        print(f"\tCPU frequency: {self.cpu_freq_mhz} MHz")

    def gen_io_pll(self, config, part):
        print("IO PLL:")
        pll_min_freq = float(platform["pll_freq_mhz"]["min"])
        pll_max_freq = float(platform["pll_freq_mhz"]["max"][part.speed_grade])
        if "io_pll" in config:
            io_pll_config = config["io_pll"]
            if "freq_mhz" in io_pll_config:
                self.target_io_pll_freq = get_num_in_range(
                    io_pll_config, "freq_mhz", "io_pll", float,
                    pll_min_freq, pll_max_freq
                )
                print("\tTarget IO PLL target frequency: "
                      f"{self.target_io_pll_freq} MHz")
                self.calculate_io_pll(self.target_io_pll_freq, part)
            else:
                self.parse_io_pll(io_pll_config)
                
        else:
            self.target_io_pll_freq = platform["io_pll_freq_mhz_default"]
            print("\tTarget IO PLL frequency not specified")
            print(f"\t\tUsing default of: {self.target_io_pll_freq} MHz")
            self.calculate_io_pll(self.target_io_pll_freq, part)

        if (self.io_pll_freq_mhz < pll_min_freq
            or self.io_pll_freq_mhz > pll_max_freq
        ):
            raise RuntimeError(
                "IO PLL frequency must be in range: {} to {}".format(
                    pll_min_freq, pll_max_freq
                )
            )

    def calculate_io_pll(self, target_freq_mhz, part):
        pll_min_freq = float(platform["pll_freq_mhz"]["min"])
        pll_max_freq = float(platform["pll_freq_mhz"]["max"][part.speed_grade])
        if (target_freq_mhz < pll_min_freq
            or target_freq_mhz > pll_max_freq
        ):
            raise RuntimeError(
                "IO PLL frequency must be in range: {} to {}".format(
                    pll_min_freq, pll_max_freq
                )
            )
        best_option = calculate_pll_mul(
            self.ps_in_freq_mhz,
            target_freq_mhz,
            part.speed_grade
        )
        if best_option is None:
            raise RuntimeError(
                f"Could not find PLL parameters for target IO PLL"
                f" frequency of: { target_freq_mhz } MHz")

        self.io_pll_mul, _ = best_option
        self.io_pll_freq_mhz = self.ps_in_freq_mhz * self.io_pll_mul

        error_percent = (
            100.0 * abs(target_freq_mhz - self.io_pll_freq_mhz)
            / target_freq_mhz
        )
        print(f"\tIO PLL multiplier: {self.io_pll_mul}")
        print(
            f"\tActual IO PLL frequency: {self.io_pll_freq_mhz} MHz"
            f" (target: {target_freq_mhz} MHz, error: {error_percent:.1f}%)"
        )

    def parse_io_pll(self, io_pll_config):
        self.io_pll_mul = get_num_in_range(
            io_pll_config, "pll_mul", "io_pll", int,
            platform["pll_mul"]["min"],
            platform["pll_mul"]["max"]
        )
        self.io_pll_freq_mhz = self.ps_in_freq_mhz * self.io_pll_mul
        print(f"\tIO PLL multiplier: {self.io_pll_mul}")
        print(f"\tActual IO PLL frequency: {self.io_pll_freq_mhz}")

    def parse_ddr_clk(self, ddr, part):
        print("DDR clock:")
        self.target_ddr_freq = ddr.data_rate_mbps / 2.0
        max_ddr_freq = (platform["ddr_data_max_rate"]
            [ddr.type][part.speed_grade] / 2.0)
        best_option = calculate_pll_params(
            self.ps_in_freq_mhz,
            self.target_ddr_freq,
            platform["ddr_min_feq"],
            max_ddr_freq,
            part.speed_grade,
        )
        if best_option is None:
            raise RuntimeError(
                f"Could not find PLL parameters for target DDR"
                f" frequency of: { self.target_ddr_freq } MHz")

        self.ddr_pll_mul, self.ddr_pll_div, _ = best_option
        self.ddr_pll_freq_mhz = self.ps_in_freq_mhz * self.ddr_pll_mul
        self.ddr_freq_mhz = self.ddr_pll_freq_mhz / self.ddr_pll_div
        error_percent = (
            100.0 * abs(self.target_ddr_freq - self.ddr_freq_mhz)
            / self.target_ddr_freq
        )
        print(
            f"\tActual DDR frequency: {self.ddr_freq_mhz} MHz"
            f" (target: {self.target_ddr_freq} MHz, error: {error_percent:.1f}%)"
        )
        print(f"\tDDR PLL multiplier: {self.ddr_pll_mul}")
        print(f"\tDDR PLL frequency: {self.ddr_pll_freq_mhz}")
        print(f"\tDDR PLL divisor: {self.ddr_pll_div}")
        print(f"\tActual DDR data rate: {self.ddr_freq_mhz * 2.0} Mbps")


def calculate_pll_params(input_freq_mhz, target_freq_mhz,
                         min_freq, max_freq, speed_grade):
    # Brute-force exhaustive search ;)
    best_option = None
    pll_min_freq = float(platform["pll_freq_mhz"]["min"])
    pll_max_freq = float(platform["pll_freq_mhz"]["max"][speed_grade])

    pll_mul_candidates = range(
        platform["pll_mul"]["min"], platform["pll_mul"]["max"] + 1)
    pll_div_candidates = range(
        platform["pll_div"]["min"], platform["pll_div"]["max"] + 1)

    for mul in pll_mul_candidates:
        for div in pll_div_candidates:
            pll_freq = input_freq_mhz * float(mul)
            freq = pll_freq / float(div)
            error = abs(freq - target_freq_mhz)
            if (
                pll_freq >= pll_min_freq
                and pll_freq <= pll_max_freq
                and freq >= min_freq
                and freq <= max_freq
            ):
                if best_option is None or error < best_option[2]:
                    best_option = (mul, div, error)
    return best_option


def calculate_pll_mul(input_freq_mhz, target_pll_freq_mhz, speed_grade):
    # Brute-force exhaustive search ;)
    best_option = None
    pll_min_freq = float(platform["pll_freq_mhz"]["min"])
    pll_max_freq = float(platform["pll_freq_mhz"]["max"][speed_grade])

    pll_mul_candidates = range(
        platform["pll_mul"]["min"], platform["pll_mul"]["max"] + 1)

    for mul in pll_mul_candidates:
        pll_freq = input_freq_mhz * float(mul)
        error = abs(pll_freq - target_pll_freq_mhz)
        if (
            pll_freq >= pll_min_freq
            and pll_freq <= pll_max_freq
        ):
            if best_option is None or error < best_option[1]:
                best_option = (mul , error)
    return best_option
