import textwrap

from . import platform


class PsPl:
    def __init__(self, config):
        self.m_axi_gps = []
        if "ps_pl" not in config:
            print("No PS-PL signals configured")
        else:
            for index in platform["ps_pl"]["m_axi_gp_ports"]["peripherals"]:
                config_name = f"m_axi_gp{index}"
                if config_name in config["ps_pl"]:
                    port_config = config["ps_pl"][config_name]
                    self.m_axi_gps.append(MAxiGp(index, port_config))

    def tcl_parameters(self):
        params = {}
        for port in self.m_axi_gps:
            params.update(port.tcl_parameters())
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
        print(f"General purpose master AXI port {self.index}"
              f" (M_AXI_GP{self.index}) enabled")

    def tcl_parameters(self):
        return {
            f"PCW_USE_M_AXI_GP{self.index}": 1
        }

    def tcl_commands(self):
        port_data = platform["ps_pl"]["m_axi_gp_ports"]

        return textwrap.dedent(f"""\
            create_bd_intf_port \\
                -mode Master \\
                -vlnv xilinx.com:interface:aximm_rtl:1.0 \\
                M_AXI_GP{self.index}
            set_property -dict [ list \\
                CONFIG.ADDR_WIDTH {{{port_data["addr_width"]}}} \\
                CONFIG.DATA_WIDTH {{{port_data["data_width"]}}} \\
                CONFIG.HAS_REGION {{{port_data["has_region"]}}} \\
                CONFIG.NUM_READ_OUTSTANDING {{{port_data["num_read_outstanding"]}}} \\
                CONFIG.NUM_WRITE_OUTSTANDING {{{port_data["num_write_outstanding"]}}} \\
                CONFIG.PROTOCOL {{{port_data["protocol"]}}} \\
            ] [get_bd_intf_ports M_AXI_GP{self.index}]
            connect_bd_intf_net \\
                [get_bd_intf_ports M_AXI_GP{self.index}] \\
                [get_bd_intf_pins zynqps/M_AXI_GP{self.index}]
            create_bd_port -dir I -type clk M_AXI_GP{self.index}_ACLK
            connect_bd_net \\
                [get_bd_ports M_AXI_GP{self.index}_ACLK] \\
                [get_bd_pins zynqps/M_AXI_GP{self.index}_ACLK]
            """)
