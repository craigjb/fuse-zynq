from enum import Enum
from collections import OrderedDict

from . import platform
from .yml_util import get_one_of


class Mio:
    def __init__(self, config):
        self.assignments = OrderedDict(
            (f"MIO {i}", None) for i in range(platform["mio_count"])
        )

        print("MIO:")
        if "mio" not in config:
            raise RuntimeError("mio config section must be specified")
        mio_config = config["mio"]
        self.parse_config(mio_config)
        self.generated_gpio = False

    def assign_pin(self, pin, peripheral, dir, slew, pullup):
        if pin == "EMIO":
            return
        if pin not in self.assignments:
            raise RuntimeError(f"Tried to assign non-existing pin: {pin}")
        assignment = self.assignments[pin]
        if assignment is not None:
            print("Error: peripherals configured to "
                   "use the same MIO pin")
            print(f"\t{pin} assigned to {assignment.peripheral}"
                  f" and {peripheral}")
            raise RuntimeError(
                "Peripherals configured to use the same MIO pin")
        else:
            self.assignments[pin] = MioAssignment( # type: ignore
                peripheral, dir, slew, pullup
            ) 

    def tcl_parameters(self):
        if not self.generated_gpio:
            self.gen_gpio()
        params = {}
        for pin, asmt in self.assignments.items():
            assert(asmt is not None)
            pin_no = int(pin.split(" ")[1])
            voltage = self.pin_voltage(pin)

            params.update({
                f"PCW_MIO_{pin_no}_PULLUP":
                    "enabled" if asmt.pullup else "disabled",
                f"PCW_MIO_{pin_no}_IOTYPE":
                    platform["mio_io_types"][voltage],
                f"PCW_MIO_{pin_no}_DIRECTION": asmt.dir.value,
                f"PCW_MIO_{pin_no}_SLEW": asmt.slew.value,
            })
        return params

    def pin_voltage(self, pin):
        for bank in self.bank_ranges.keys():
            pin_no = int(pin.split(" ")[1])
            if pin_no in self.bank_ranges[bank]:
                return self.bank_voltages[bank]
        return None

    def parse_config(self, mio_config):
        self.bank_voltages = {}
        self.bank_ranges = {}
        for bank in platform["mio_banks"]:
            self.bank_voltages[bank] = get_one_of(
                mio_config, f"voltage_bank{bank}", "mio", str,
                platform["mio_bank_voltages"]
            )
            print(f"\tBank {bank}: {self.bank_voltages[bank]}")

            start, end = platform["mio_banks"][bank].split("-")
            self.bank_ranges[bank] = range(int(start), int(end) + 1)

    def gen_gpio(self):
        for pin, asmt in self.assignments.items():
            if asmt is None:
                self.assign_pin(
                    pin, "GPIO",
                    MioDirection.INOUT, MioSlew.SLOW, pullup=True
                )


class MioAssignment:
    def __init__(self, peripheral, dir, slew, pullup):
        self.peripheral = peripheral
        self.dir = dir
        self.slew = slew
        self.pullup = pullup


class MioDirection(Enum):
    INOUT = "inout"
    IN = "in"
    OUT = "out"


class MioSlew(Enum):
    SLOW = "slow"
    FAST = "fast"
