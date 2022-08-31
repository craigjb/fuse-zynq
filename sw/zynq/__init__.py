import os.path

from .yml_util import ordered_load


_PLATFORM_DATA_REL_PATH = "../../data/zynq7000.yml"


_platform_data_path = os.path.join(
    os.path.dirname(__file__),
    _PLATFORM_DATA_REL_PATH)
with open(_platform_data_path) as f:
    platform = ordered_load(f)


from .part import Part
from .ddr import Ddr
from .clocks import Clocks
from .mio import Mio
from .uart import Uarts
from .qspi import Qspi
from .sdio import Sdios
from .usb import Usbs

class Zynq:
    def __init__(self, config):
        self.part = Part(config)
        self.ddr = Ddr(config, self.part)
        self.clocks = Clocks(config, self.part, self.ddr)
        self.mio = Mio(config)
        self.uarts = Uarts(config, self.mio, self.clocks)
        self.qspi = Qspi(config, self.mio, self.clocks)
        self.sdios = Sdios(config, self.mio, self.clocks)
        self.usbs = Usbs(config, self.mio)

    def tcl_parameters(self):
        tcl_parameters = {}
        tcl_parameters.update(self.part.tcl_parameters())
        tcl_parameters.update(self.clocks.tcl_parameters())
        tcl_parameters.update(self.ddr.tcl_parameters())
        tcl_parameters.update(self.uarts.tcl_parameters())
        tcl_parameters.update(self.qspi.tcl_parameters())
        tcl_parameters.update(self.sdios.tcl_parameters())
        tcl_parameters.update(self.usbs.tcl_parameters())
        tcl_parameters.update(self.mio.tcl_parameters())

        # Explicitly disable for now
        tcl_parameters.update({
            "PCW_USE_M_AXI_GP0": 0,
            # TODO, remove once FPGA clocks are supported
            "PCW_EN_CLK0_PORT": 0,
            "PCW_EN_RST0_PORT": 0
        })
        return tcl_parameters

    def tcl_commands(self):
        return "\n\n".join([
            self.uarts.tcl_commands(),
            self.sdios.tcl_commands(),
            self.usbs.tcl_commands()
        ])
