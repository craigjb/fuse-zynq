from . import platform
from .yml_util import get_num_in_range
from .mio import MioDirection, MioSlew

class Qspi:
    def __init__(self, config, mio, clocks):
        if "qspi" not in config:
            print("QSPI not configured")
            self.enabled = False
            return

        print("QSPI configuration:")
        qspi_config = config["qspi"]
        self.enabled = True

        self.parse_config(qspi_config)
        self.assign_pins(mio)
        self.gen_clock(clocks)

    def tcl_parameters(self):
        if self.enabled:
            params = {
                "PCW_QSPI_PERIPHERAL_ENABLE": 1,
                "PCW_QSPI_PERIPHERAL_FREQMHZ": self.freq_mhz,
                "PCW_QSPI_GRP_SINGLE_SS_ENABLE": 1,
                "PCW_QSPI_PERIPHERAL_DIVISOR0": self.clk_divisor,
                "PCW_QSPI_PERIPHERAL_CLKSRC": self.clk_source,
                "PCW_QSPI_PERIPHERAL_FREQMHZ": self.freq_mhz
            }
            if self.feedback_clk:
                params.update({
                    "PCW_QSPI_GRP_FBCLK_ENABLE": 1,
                    "PCW_QSPI_GRP_FBCLK_IO":
                        platform["qspi"]["pins"]["fbck"]
                })
            # include default params for single stack one chip
            params.update(platform["qspi"]["grp_ss_params"])
            return params
        else:
            return {}

    def parse_config(self, qspi_config):
        self.target_freq_mhz = get_num_in_range(
            qspi_config, "freq_mhz", "qspi", float,
            platform["qspi"]["freq_mhz"]["min"],
            platform["qspi"]["freq_mhz"]["max"]
        )
        print(f"\tTarget peripheral frequency: {self.target_freq_mhz} MHz")

        self.feedback_clk = False
        if "feedback_clk" in qspi_config:
            self.feedback_clk = qspi_config["feedback_clk"]
        print(f"\tFeedback clock: {'Yes' if self.feedback_clk else 'No'}")

    def assign_pins(self, mio):
        pins = platform["qspi"]["pins"]
        mio.assign_pin(
            pins["io0"], "QSPI",
            MioDirection.INOUT, MioSlew.SLOW, pullup=False
        )
        mio.assign_pin(
            pins["io1"], "QSPI",
            MioDirection.INOUT, MioSlew.SLOW, pullup=False
        )
        mio.assign_pin(
            pins["io2"], "QSPI",
            MioDirection.INOUT, MioSlew.SLOW, pullup=False
        )
        mio.assign_pin(
            pins["io3"], "QSPI",
            MioDirection.INOUT, MioSlew.SLOW, pullup=False
        )
        mio.assign_pin(
            pins["sclk"], "QSPI",
            MioDirection.OUT, MioSlew.SLOW, pullup=False
        )
        mio.assign_pin(
            pins["cs"], "QSPI",
            MioDirection.OUT, MioSlew.SLOW, pullup=True
        )
        if self.feedback_clk:
            mio.assign_pin(
                pins["fbck"], "QSPI",
                MioDirection.OUT, MioSlew.SLOW, pullup=False
            )

    def gen_clock(self, clocks):
        self.clk_source = "IO PLL"
        self.clk_divisor, self.freq_mhz = clocks.calculate_io_div_and_freq(
            "QSPI",
            self.target_freq_mhz,
            platform["qspi"]["freq_mhz"]["min"],
            platform["qspi"]["freq_mhz"]["max"]
        )
