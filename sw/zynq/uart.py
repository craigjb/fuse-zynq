from . import platform
from .yml_util import get_num_in_range, get_one_of
from .mio import MioDirection, MioSlew


class Uarts:
    def __init__(self, config, mio, clocks):
        if "uarts" not in config:
            print("No UARTs configured")
        else:
            print("UART configuration:")
            self.parse_config(config["uarts"])
            self.uarts = []
            for index in platform["uarts"].keys():
                config_name = f"uart{index}"
                if config_name in config["uarts"]:
                    uart_config = config["uarts"][config_name]
                    self.uarts.append(Uart(index, uart_config, mio))
            self.gen_clock(clocks)

    def tcl_parameters(self):
        if len(self.uarts) > 0:
            params = {
                "PCW_UART_PERIPHERAL_VALID": 1,
                "PCW_UART_PERIPHERAL_DIVISOR0": self.clk_divisor,
                "PCW_UART_PERIPHERAL_CLKSRC": self.clk_source,
                "PCW_UART_PERIPHERAL_FREQMHZ": self.freq_mhz,
            }
            for uart in self.uarts:
                params.update(uart.tcl_parameters())
            return params
        else:
            return {}

    def parse_config(self, uarts_config):
        if "freq_mhz" in uarts_config:
            self.target_freq_mhz = get_num_in_range(
                uarts_config, "freq_mhz", "uarts", float,
                platform["uart_freq_mhz"]["min"],
                platform["uart_freq_mhz"]["max"]
            )
            print(f"\tTarget peripheral frequency: {self.target_freq_mhz} MHz")
        else:
            self.target_freq_mhz = platform["uart_freq_mhz"]["default"]
            print("\tTarget peripheral frequency not specified")
            print(f"\t\tUsing default of: {self.target_freq_mhz} MHz")

    def gen_clock(self, clocks):
        self.clk_source = "IO PLL"
        self.clk_divisor, self.freq_mhz = clocks.calculate_io_div_and_freq(
            "UART",
            self.target_freq_mhz,
            platform["uart_freq_mhz"]["min"],
            platform["uart_freq_mhz"]["max"]
        )
        

class Uart:
    def __init__(self, index, uart_config, mio):
        self.index = index
        print(f"\tUART{index}:")
        self.rx_pin = get_one_of(
            uart_config, "rx_pin", f"uart{index}", str,
            [g["rx"] for g in platform["uarts"][index]["pin_groups"]]
        )
        rx_pin_group = [g for g in platform["uarts"][index]["pin_groups"]
                     if g["rx"] == self.rx_pin][0]

        self.tx_pin = get_one_of(
            uart_config, "tx_pin", f"uart{index}", str,
            [g["tx"] for g in platform["uarts"][index]["pin_groups"]]
        )
        tx_pin_group = [g for g in platform["uarts"][index]["pin_groups"]
                     if g["tx"] == self.tx_pin][0]

        if self.tx_pin != rx_pin_group["tx"]:
            print(f"Error: uart{index} pins must be in the same group")
            print("\tConfigured pins:")
            print(f"\t\tRX: {self.rx_pin}\n\t\tTX: {self.tx_pin}")
            print("\tPossible configurations (see Xilinx manual for full list):")
            print(f"\t\tRX: {rx_pin_group['rx']}\n\t\tTX: {rx_pin_group['tx']}")
            print("\t\t   or")
            print(f"\t\tRX: {tx_pin_group['rx']}\n\t\tTX: {tx_pin_group['tx']}")
            raise RuntimeError(f"uart{index} pins must be in the same group")

        self.pin_group = rx_pin_group
        print(f"\t\tRX: {self.rx_pin}\n\t\tTX: {self.tx_pin}")
        mio.assign_pin(
            self.rx_pin, f"UART{index}",
            MioDirection.IN, MioSlew.SLOW, pullup=True
        )
        mio.assign_pin(
            self.tx_pin, f"UART{index}",
            MioDirection.OUT, MioSlew.SLOW, pullup=True
        )

        self.baud_rate = get_one_of(
            uart_config, "baud_rate", f"uart{index}", int,
            platform["uart_baud_rates"]
        )
        print(f"\t\tBAUD rate: {self.baud_rate}")

    def tcl_parameters(self):
        return {
            f"PCW_UART{self.index}_PERIPHERAL_ENABLE": 1,
            f"PCW_EN_UART{self.index}": 1,
            f"PCW_UART{self.index}_UART{self.index}_IO":
                self.pin_group["name"],
            f"PCW_UART{self.index}_BAUD_RATE": self.baud_rate
        }
