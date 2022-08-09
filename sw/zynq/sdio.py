from . import platform
from .yml_util import get_num_in_range, get_one_of
from .mio import MioDirection, MioSlew

class Sdios:
    def __init__(self, config, mio, clocks):
        self.sdios = []
        if "sdio" not in config:
            print("No SDIOs configured")
        else:
            print("SDIO configuration:")
            self.parse_config(config["sdio"])
            for index in platform["sdio"]["peripherals"].keys():
                config_name = f"sdio{index}"
                if config_name in config["sdio"]:
                    sdio_config = config["sdio"][config_name]
                    self.sdios.append(Sdio(index, sdio_config, mio))
            self.gen_clock(clocks)

    def tcl_parameters(self):
        if len(self.sdios) > 0:
            params = {
                "PCW_SDIO_PERIPHERAL_VALID": 1,
                "PCW_SDIO_PERIPHERAL_CLKSRC": self.clk_source,
                "PCW_SDIO_PERIPHERAL_DIVISOR0": self.clk_divisor,
                "PCW_SDIO_PERIPHERAL_FREQMHZ": self.freq_mhz,
            }
            for sdio in self.sdios:
                params.update(sdio.tcl_parameters())
            return params
        else:
            return {}


    def parse_config(self, sdios_config):
        if "freq_mhz" in sdios_config:
            self.target_freq_mhz = get_num_in_range(
                sdios_config, "freq_mhz", "sdio", float,
                platform["uart_freq_mhz"]["min"],
                platform["uart_freq_mhz"]["max"]
            )
            print(f"\tTarget peripheral frequency: {self.target_freq_mhz} MHz")
        else:
            self.target_freq_mhz = platform["sdio"]["freq_mhz"]["default"]
            print("\tTarget peripheral frequency not specified")
            print(f"\t\tUsing default of: {self.target_freq_mhz} MHz")

    def gen_clock(self, clocks):
        self.clk_source = "IO PLL"
        self.clk_divisor, self.freq_mhz = clocks.calculate_io_div_and_freq(
            "QSPI",
            self.target_freq_mhz,
            platform["sdio"]["freq_mhz"]["min"],
            platform["sdio"]["freq_mhz"]["max"]
        )


class Sdio:
    def __init__(self, index, sdio_config, mio):
        self.index = index
        print(f"\tSDIO{index}:")
        pin_groups = platform["sdio"]["peripherals"][index]["pin_groups"]

        self.ck_pin = get_one_of(
            sdio_config, "ck_pin", f"sdio{index}", str,
            [g["ck"] for g in pin_groups]
        )
        self.cmd_pin = get_one_of(
            sdio_config, "cmd_pin", f"sdio{index}", str,
            [g["cmd"] for g in pin_groups]
        )
        self.io0_pin = get_one_of(
            sdio_config, "io0_pin", f"sdio{index}", str,
            [g["io0"] for g in pin_groups]
        )
        self.io1_pin = get_one_of(
            sdio_config, "io1_pin", f"sdio{index}", str,
            [g["io1"] for g in pin_groups]
        )
        self.io2_pin = get_one_of(
            sdio_config, "io2_pin", f"sdio{index}", str,
            [g["io2"] for g in pin_groups]
        )
        self.io3_pin = get_one_of(
            sdio_config, "io3_pin", f"sdio{index}", str,
            [g["io3"] for g in pin_groups]
        )

        pin_group = [g for g in pin_groups if g["ck"] == self.ck_pin][0]
        if (pin_group["cmd"] != self.cmd_pin
                or pin_group["io0"] != self.io0_pin
                or pin_group["io1"] != self.io1_pin
                or pin_group["io2"] != self.io2_pin
                or pin_group["io3"] != self.io3_pin):
            print(f"Error: sdio{index} pins must be in the same group")
            print("\tConfigured pins:")
            print(f"\t\tck: {self.ck_pin}")
            print(f"\t\tcmd: {self.cmd_pin}")
            print(f"\t\tio0: {self.io0_pin}")
            print(f"\t\tio1: {self.io1_pin}")
            print(f"\t\tio2: {self.io2_pin}")
            print(f"\t\tio3: {self.io3_pin}")
            print("\tPossible configurations:")
            for i, grp in enumerate(pin_groups):
                print(f"\t\tck: {grp['ck']}")
                print(f"\t\tcmd: {grp['cmd']}")
                print(f"\t\tio0: {grp['io0']}")
                print(f"\t\tio1: {grp['io1']}")
                print(f"\t\tio2: {grp['io2']}")
                print(f"\t\tio3: {grp['io3']}")
                if i < len(pin_groups) - 1:
                    print("\t\t   or")
            raise RuntimeError(f"uart{index} pins must be in the same group")
        self.pin_group = pin_group

        mio.assign_pin(
            self.ck_pin, f"SDIO{index}",
            MioDirection.INOUT, MioSlew.SLOW, pullup=True
        )
        print(f"\t\tck: {self.ck_pin}")
        mio.assign_pin(
            self.cmd_pin, f"SDIO{index}",
            MioDirection.INOUT, MioSlew.SLOW, pullup=True
        )
        print(f"\t\tcmd: {self.cmd_pin}")
        mio.assign_pin(
            self.io0_pin, f"SDIO{index}",
            MioDirection.INOUT, MioSlew.SLOW, pullup=True
        )
        print(f"\t\tio0: {self.io0_pin}")
        mio.assign_pin(
            self.io1_pin, f"SDIO{index}",
            MioDirection.INOUT, MioSlew.SLOW, pullup=True
        )
        print(f"\t\tio1: {self.io1_pin}")
        mio.assign_pin(
            self.io2_pin, f"SDIO{index}",
            MioDirection.INOUT, MioSlew.SLOW, pullup=True
        )
        print(f"\t\tio2: {self.io2_pin}")
        mio.assign_pin(
            self.io3_pin, f"SDIO{index}",
            MioDirection.INOUT, MioSlew.SLOW, pullup=True
        )
        print(f"\t\tio3: {self.io3_pin}")

        allowable_detect_pins = [
            f"MIO {i}" for i in range(0, platform["mio_count"])
            if i not in platform["sdio"]["invalid_detect_pins"]
        ] + ["EMIO"]
        self.detect_pin = None
        if "detect_pin" in sdio_config:
            self.detect_pin = get_one_of(
                sdio_config, "detect_pin", f"sdio{index}", str,
                allowable_detect_pins
            )
            mio.assign_pin(
                self.detect_pin, f"SDIO{index}",
                MioDirection.IN, MioSlew.SLOW, pullup=True
            )
            print(f"\t\tdetect: {self.detect_pin}")

        allowable_protect_pins = [
            f"MIO {i}" for i in range(0, platform["mio_count"])
            if i not in platform["sdio"]["invalid_protect_pins"]
        ] + ["EMIO"]
        self.protect_pin = None
        if "protect_pin" in sdio_config:
            self.protect_pin = get_one_of(
                sdio_config, "protect_pin", f"sdio{index}", str,
                allowable_protect_pins
            )
            mio.assign_pin(
                self.protect_pin, f"SDIO{index}",
                MioDirection.IN, MioSlew.SLOW, pullup=True
            )
            print(f"\t\tprotect: {self.protect_pin}")

    def tcl_parameters(self):
        params = {
            "PCW_EN_SDIO0": 1,
            f"PCW_SD{self.index}_PERIPHERAL_ENABLE": 1,
            f"PCW_SD{self.index}_SD{self.index}_IO":
                self.pin_group["name"],
        }
        if self.detect_pin:
            params.update({
                f"PCW_SD{self.index}_GRP_CD_ENABLE": 1,
                f"PCW_SD{self.index}_GRP_CD_IO": self.detect_pin
            })
        if self.protect_pin:
            params.update({
                f"PCW_SD{self.index}_GRP_WP_ENABLE": 1,
                f"PCW_SD{self.index}_GRP_WP_IO": self.detect_pin
            })
        return params
