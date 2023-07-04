import textwrap

from . import platform
from .yml_util import get_num_in_range, get_one_of


class PsPl:
    def __init__(self, config, clocks):
        self.m_axi_gps = []
        self.fclks = []

        if "ps_pl" not in config:
            print("No PS-PL signals configured")
        else:
            print("PS-PL configuration:")
            m_axis_gp_ports = platform["ps_pl"]["m_axi_gp_ports"]
            for index in m_axis_gp_ports["peripherals"].keys():
                config_name = f"m_axi_gp{index}"
                if config_name in config["ps_pl"]:
                    port_config = config["ps_pl"][config_name]
                    self.m_axi_gps.append(MAxiGp(index, port_config))
            fclks = platform["ps_pl"]["fclks"]
            for index in fclks["peripherals"].keys():
                config_name = f"fclk{index}"
                if config_name in config["ps_pl"]:
                    port_config = config["ps_pl"][config_name]
                    self.fclks.append(Fclk(index, port_config, clocks))


    def tcl_parameters(self):
        params = {}
        for port in self.m_axi_gps:
            params.update(port.tcl_parameters())
        for fclk in self.fclks:
            params.update(fclk.tcl_parameters())
        return params

    def tcl_commands(self):
        return "\n".join(
            [port.tcl_commands() for port in self.m_axi_gps]
        )


class MAxiGp:
    def __init__(self, index, port_config):
        self.index = index
        
        # TODO: support port configuration options
        if not isinstance(port_config, bool):
            raise RuntimeError("m_axi_gp{index} must be a bool value")
        print(f"\tM_AXI_GP{self.index}: enabled")

    def tcl_parameters(self):
        return {
            f"PCW_USE_M_AXI_GP{self.index}": 1
        }

    def tcl_commands(self):
        port_data = platform["ps_pl"]["m_axi_gp_ports"]
        peripheral = port_data["peripherals"][self.index]

        return textwrap.dedent(f"""\
            # Create M_AXI_GP{self.index} ports
            create_bd_intf_port \\
                -mode Master \\
                -vlnv xilinx.com:interface:aximm_rtl:1.0 \\
                M_AXI_GP{self.index}
            create_bd_port -dir I -type clk M_AXI_GP{self.index}_ACLK
            set_property -dict [ list \\
                CONFIG.ADDR_WIDTH {{{port_data["addr_width"]}}} \\
                CONFIG.DATA_WIDTH {{{port_data["data_width"]}}} \\
                CONFIG.HAS_REGION {{{port_data["has_region"]}}} \\
                CONFIG.NUM_READ_OUTSTANDING {{{port_data["num_read_outstanding"]}}} \\
                CONFIG.NUM_WRITE_OUTSTANDING {{{port_data["num_write_outstanding"]}}} \\
                CONFIG.PROTOCOL {{{port_data["protocol"]}}} \\
            ] [get_bd_intf_ports M_AXI_GP{self.index}]

            # Connect M_AXI_GP{self.index} ports to Zynq PS
            connect_bd_intf_net \\
                [get_bd_intf_ports M_AXI_GP{self.index}] \\
                [get_bd_intf_pins zynqps/M_AXI_GP{self.index}]
            connect_bd_net \\
                [get_bd_ports M_AXI_GP{self.index}_ACLK] \\
                [get_bd_pins zynqps/M_AXI_GP{self.index}_ACLK]

            # Map full 1G address spaces so Vivado does not complain
            create_bd_addr_seg \\
                -range 0x{peripheral["addr_map_range"]:08X} \\
                -offset 0x{peripheral["addr_map_offset"]:08X} \\
                [get_bd_addr_spaces zynqps/Data] \\
                [get_bd_addr_segs M_AXI_GP{self.index}/Reg] \\
                SEG_M_AXI_GP{self.index}_Reg
            """)


class Fclk:
    def __init__(self, index, fclk_config, clocks):
        self.index = index
        self.name = f"fclk{index}"

        self.clk_src = platform["ps_pl"]["fclks"]["default_clk_src"]
        self.target_freq_mhz = None
        self.div0 = None
        self.div1 = None

        self.parse_config(fclk_config, clocks)
        self.gen_clocks(clocks)

    def parse_config(self, fclk_config, clocks):
        if "clk_src" in fclk_config:
            possible_srcs = platform["ps_pl"]["fclks"]["clk_srcs"]
            self.clk_src = get_one_of(
                fclk_config, "clk_src", self.name, str, possible_srcs)
        pll_freq_mhz = clocks.get_pll_freq_mhz(self.clk_src)

        if "freq_mhz" in fclk_config:
            self.target_freq_mhz = get_num_in_range(
                fclk_config, "freq_mhz", self.name, float,
                0.0, pll_freq_mhz)
        else:
            self.div0 = get_num_in_range(
                fclk_config, "pll_div0", self.name, int,
                platform["ps_pl"]["fclks"]["divisor0"]["min"],
                platform["ps_pl"]["fclks"]["divisor0"]["max"]
            )
            self.div1 = get_num_in_range(
                fclk_config, "pll_div1", self.name, int,
                platform["ps_pl"]["fclks"]["divisor1"]["min"],
                platform["ps_pl"]["fclks"]["divisor1"]["max"]
            )

    def gen_clocks(self, clocks):
        pll_freq_mhz = clocks.get_pll_freq_mhz(self.clk_src)
        if self.target_freq_mhz is not None:
            self.div0, self.div1, self.freq_mhz = \
                clocks.calculate_pll_divs_and_freq(
                    self.name, self.clk_src,
                    self.target_freq_mhz, 0.0, pll_freq_mhz,
                    platform["ps_pl"]["fclks"]["divisor0"]["min"],
                    platform["ps_pl"]["fclks"]["divisor0"]["max"],
                    platform["ps_pl"]["fclks"]["divisor1"]["min"],
                    platform["ps_pl"]["fclks"]["divisor1"]["max"]
                )
        else:
            self.freq_mhz = float(pll_freq_mhz) / float(self.div0) / float(self.div1)
            print(f"\t{self.name} frequency: {self.freq_mhz:.3f} MHz")

    def tcl_parameters(self):
        return {
            f"PCW_FCLK{self.index}_PERIPHERAL_CLKSRC": self.clk_src,
            f"PCW_FPGA{self.index}_PERIPHERAL_FREQMHZ": self.freq_mhz,
            f"PCW_FCLK{self.index}_PERIPHERAL_DIVISOR0": self.div0,
            f"PCW_FCLK{self.index}_PERIPHERAL_DIVISOR1": self.div1,
            f"PCW_EN_CLK{self.index}_PORT": 1
        }

