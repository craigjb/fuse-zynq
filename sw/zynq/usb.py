from . import platform
from .mio import MioDirection, MioSlew
from .yml_util import get_one_of


class Usbs:
    def __init__(self, config, mio):
        if "usb" not in config:
            print("No USBs configured")
        else:
            print("USB configuration:")
            self.usbs = []
            for index in platform["usb"]["peripherals"].keys():
                config_name = f"usb{index}"
                if config_name in config["usb"]:
                    usb_config = config["usb"][config_name]
                    self.usbs.append(Usb(index, usb_config, mio))

    def tcl_parameters(self):
        params = {}
        params.update(platform["usb"]["params"])
        for usb in self.usbs:
            params.update(usb.tcl_parameters())
        return params

class Usb:
    def __init__(self, index, usb_config, mio):
        self.index = index
        print(f"\tUSB{index}:")

        peripheral = platform["usb"]["peripherals"][index]
        for name, pin in peripheral["pins"].items():
            mio.assign_pin(
                pin["loc"], f"USB{self.index}",
                MioDirection(pin["dir"]), MioSlew(pin["slew"]),
                pullup=pin["pullup"]
            )
            print(f"\t\t{name}: {pin['loc']}")

        if usb_config and "reset_pin" in usb_config:
            mio_pins = [f"MIO {i}" for i in range(platform["mio_count"])]
            self.reset_pin = get_one_of(
                usb_config, "reset_pin", f"usb{self.index}", str,
                mio_pins
            )
            mio.assign_pin(
                self.reset_pin, f"USB{self.index}",
                MioDirection.OUT, MioSlew.SLOW, pullup=True
            )
            print(f"\t\treset: {self.reset_pin}")
        else:
            self.reset_pin = None
            

    def tcl_parameters(self):
        peripheral = platform["usb"]["peripherals"][self.index]
        params = {
            f"PCW_EN_USB{self.index}": 1,
            f"PCW_USB{self.index}_PERIPHERAL_ENABLE": 1,
            f"PCW_USB{self.index}_USB{self.index}_IO":
                peripheral["pin_grp_name"]
        }
        if self.reset_pin:
            params.update({
                f"PCW_USB{self.index}_RESET_ENABLE": 1,
                f"PCW_USB{self.index}_RESET_IO": self.reset_pin
            })
        return params
