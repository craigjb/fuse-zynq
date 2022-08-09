from . import platform
from .yml_util import get_num_in_range, get_one_of


class Ddr:
    def __init__(self, config, part):
        if "ddr" not in config:
            print("No DDR memory configured")
            self.enabled = False
        else:
            print("DDR memory configuration:")
            self.enabled = True
            ddr_config = config["ddr"]
            self.parse_config(ddr_config, part)
            self.geometry = DdrGeometry(
                ddr_config["part_geometry"],
                self.data_bus_bits
            )
            self.timing = DdrTiming(ddr_config["timing"])

    def tcl_parameters(self):
        if self.enabled:
            params = {
                "PCW_UIPARAM_DDR_ENABLE": 1,
                "PCW_UIPARAM_DDR_MEMORY_TYPE":
                    platform["ddr_types"][self.type],
                "PCW_UIPARAM_DDR_SPEED_BIN":
                    platform["ddr_speed_bins"][self.type][self.speed_bin],
                "PCW_UIPARAM_DDR_BUS_WIDTH":
                    platform["ddr_bus_widths"][self.data_bus_bits],
                "PCW_UIPARAM_DDR_PARTNO": "Custom"
            }
            params.update(self.geometry.tcl_parameters())
            params.update(self.timing.tcl_parameters())
            return params
        else:
            return {"PCW_UIPARAM_DDR_ENABLE": 0}
        
    def parse_config(self, ddr_config, part):
        self.type = get_one_of(
            ddr_config, "type", "ddr", str,
            platform["ddr_types"]
        )
        print(f"\tType: {self.type}")

        self.speed_bin = get_one_of(
            ddr_config, "speed_bin", "ddr", str,
            platform["ddr_speed_bins"][self.type]
        )
        print(f"\tSpeed bin: {self.speed_bin}")

        self.data_rate_mbps = get_num_in_range(
            ddr_config, "data_rate_mbps", "ddr", int,
            0, platform["ddr_data_max_rate"][self.type][part.speed_grade]
        )
        print(f"\tTarget Data Rate: {self.data_rate_mbps} Mbps")

        self.data_bus_bits = get_one_of(
            ddr_config, "data_bus_bits", "ddr", int,
            platform["ddr_bus_widths"].keys()
        )
        print(f"\tData bus width: {self.data_bus_bits} bits")


class DdrGeometry:
    def __init__(self, geometry_config, data_bus_width):
        print("\tDDR Geometry:")
        self.part_bit_width = get_one_of(
            geometry_config, "bit_width", "ddr part_geometry", int,
            platform["ddr_part_widths"].keys()
        )
        print(f"\t\tData bit width per part: {self.part_bit_width} bits")

        self.num_parts = int(data_bus_width / self.part_bit_width)
        print(f"\t\tNumber of parts: {self.num_parts}")

        self.bank_bits = get_num_in_range(
            geometry_config, "bank_bits", "ddr part_geometry", int,
            platform["ddr_bank_bits"]["min"],
            platform["ddr_bank_bits"]["max"],
        )
        print(f"\t\tBank address bits: {self.bank_bits} bits")
        self.row_bits = get_num_in_range(
            geometry_config, "row_bits", "ddr part_geometry", int,
            platform["ddr_row_bits"]["min"],
            platform["ddr_row_bits"]["max"],
        )
        print(f"\t\tRow address bits: {self.row_bits} bits")
        self.col_bits = get_num_in_range(
            geometry_config, "col_bits", "ddr part_geometry", int,
            platform["ddr_col_bits"]["min"],
            platform["ddr_col_bits"]["max"],
        )
        print(f"\t\tColumn address bits: {self.col_bits} bits")

        self.mbits_per_part = get_one_of(
            geometry_config, "mbits", "ddr part_geometry", int,
            platform["ddr_part_capacities"]
        )
        print(f"\t\tCapacity per component: {self.mbits_per_part} Mbits")
        total_cap = self.mbits_per_part * self.num_parts
        self.total_bytes = int(total_cap / 8)
        print(f"\t\tTotal memory capacity: {total_cap} Mbits"
               " ({self.total_bytes} MB)")

        expected_mbits_per_part = ddr_capacity(
            self.bank_bits, self.row_bits, self.col_bits,
            self.part_bit_width
        )
        if self.mbits_per_part != expected_mbits_per_part:
            print("Error: DDR capacity does not match bank, row, column bit config:")
            print(f"\tCalculated: {expected_mbits_per_part} Mbit per component")
            print(f"\tConfigured: {self.mbits_per_part} Mbit per component")
            raise RuntimeError(
                "DDR bank, row, and column bit config does not match mbits_per_component"
            )

    def tcl_parameters(self):
        return {
            "PCW_UIPARAM_DDR_DRAM_WIDTH":
                platform["ddr_part_widths"][self.part_bit_width],
            "PCW_UIPARAM_DDR_DEVICE_CAPACITY":
                platform["ddr_part_capacities"][self.mbits_per_part],
            "PCW_UIPARAM_DDR_BANK_ADDR_COUNT": self.bank_bits,
            "PCW_UIPARAM_DDR_ROW_ADDR_COUNT": self.row_bits,
            "PCW_UIPARAM_DDR_COL_ADDR_COUNT": self.col_bits,
            "PCW_DDR_RAM_HIGHADDR": f"0x{(self.total_bytes - 1):08X}"
        }


def ddr_capacity(bank_bits, row_bits, col_bits, data_bits):
    return int(((2**bank_bits) * (2**row_bits) * (2**col_bits) * data_bits)
               / 1024 / 1024)


class DdrTiming:
    def __init__(self, timing_config):
        print("\tDDR Timing:")
        self.cl = get_num_in_range(
            timing_config, "cl", "ddr timing", int,
            platform["ddr_timing_cl"]["min"],
            platform["ddr_timing_cl"]["max"],
        )
        print(f"\t\tCL: {self.cl}")
        self.cwl = get_num_in_range(
            timing_config, "cwl", "ddr timing", int,
            platform["ddr_timing_cwl"]["min"],
            platform["ddr_timing_cwl"]["max"],
        )
        print(f"\t\tCWL: {self.cwl}")
        self.t_rcd = get_num_in_range(
            timing_config, "t_rcd_cycles", "ddr timing", int,
            platform["ddr_timing_t_rcd"]["min"],
            platform["ddr_timing_t_rcd"]["max"],
        )
        print(f"\t\ttRCD: {self.t_rcd}")
        self.t_rp = get_num_in_range(
            timing_config, "t_rp_cycles", "ddr timing", int,
            platform["ddr_timing_t_rp"]["min"],
            platform["ddr_timing_t_rp"]["max"],
        )
        print(f"\t\ttRP: {self.t_rp}")
        self.t_rc = get_num_in_range(
            timing_config, "t_rc_ns", "ddr timing", float,
            platform["ddr_timing_t_rc"]["min"],
            platform["ddr_timing_t_rc"]["max"],
        )
        print(f"\t\ttRC: {self.t_rc}")
        self.t_ras_min = get_num_in_range(
            timing_config, "t_ras_min_ns", "ddr timing", float,
            platform["ddr_timing_t_ras_min"]["min"],
            platform["ddr_timing_t_ras_min"]["max"],
        )
        print(f"\t\ttRAS min: {self.t_ras_min}")
        self.t_faw = get_num_in_range(
            timing_config, "t_faw_ns", "ddr timing", float,
            platform["ddr_timing_t_faw"]["min"],
            platform["ddr_timing_t_faw"]["max"],
        )
        print(f"\t\ttFAW: {self.t_faw}")

    def tcl_parameters(self):
        return {
            "PCW_UIPARAM_DDR_CL": self.cl,
            "PCW_UIPARAM_DDR_CWL": self.cwl,
            "PCW_UIPARAM_DDR_T_RCD": self.t_rcd,
            "PCW_UIPARAM_DDR_T_RP": self.t_rp,
            "PCW_UIPARAM_DDR_T_RC": self.t_rc,
            "PCW_UIPARAM_DDR_T_RAS_MIN": self.t_ras_min,
            "PCW_UIPARAM_DDR_T_FAW": self.t_faw,
        }
