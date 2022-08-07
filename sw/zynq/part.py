from . import platform
from .yml_util import get_one_of


class Part:
    def __init__(self, config):
        self.parse_part(config)
        self.parse_speed_grade(config)
        print(f"Part: {self.part} \tGrade: {self.speed_grade}")

    def tcl_parameters(self):
        return {}

    def parse_part(self, config):
        self.part = get_one_of(
            config, "part", None, str,
            platform["parts"]
        )
                
    def parse_speed_grade(self, config):
        self.speed_grade = get_one_of(
            config, "speed_grade", None, str,
            platform["speed_grades"]
        )
