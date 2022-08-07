import sys
import os
import os.path
import jinja2
import yaml

import zynq
from zynq.yml_util import ordered_load


TPLT_REL_PATH = "../data/zynq_tcl.tplt"


def generate_tcl(config, output_path):
    params = zynq.Zynq(config).tcl_parameters()

    tplt_path = os.path.join(os.path.dirname(__file__), TPLT_REL_PATH)
    with open(tplt_path) as f:
        tplt = jinja2.Template(f.read())
    with open(output_path, "w") as f:
        data = tplt.render({"zynqps_properties": params})
        if not data:
            raise RuntimeError("Unknown error: template output is None")
        f.write(data)


def generate_core(config, output_path):
    vlnv = config["vlnv"]
    with open(output_path, 'w') as f:
        f.write("CAPI=2:\n")
        files = [{"zynq_ps7.tcl": {"file_type" : "tclSource"}}]
        coredata = {
            "name" : vlnv,
            "targets" : {"default" : {}},
        }
        coredata['filesets'] = {'tcl' : {'files' : files}}
        coredata['targets']['default']['filesets'] = ['tcl']
        f.write(yaml.dump(coredata))


def main():
    try:
        with open(sys.argv[1]) as f:
            config = ordered_load(f)

        zynq_config_path = config["parameters"].get("zynq_config_path", None)
        if zynq_config_path:
            with open(zynq_config_path) as f:
                params = ordered_load(f)
        else:
            params = config["parameters"]

        if len(sys.argv) > 2:
            generate_tcl(params, sys.argv[2])
        else:
            generate_tcl(params, "zynq_ps7.tcl")
            core_file = config["vlnv"].split(':')[2]+'.core'
            generate_core(config, core_file)
    except Exception as e:
        print("Error: %s" % e)
        if "-v" in sys.argv:
            import traceback
            print(traceback.format_exc())
        exit(1)

if __name__ == "__main__":
    main()
