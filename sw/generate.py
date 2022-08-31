import sys
import os
import os.path
import jinja2
import yaml

import zynq
from zynq.yml_util import ordered_load


TPLT_REL_PATH = "../data/zynq_tcl.tplt"


def generate_tcl(config, output_path):
    generated = zynq.Zynq(config)
    params = generated.tcl_parameters()
    cmds = generated.tcl_commands()

    tplt_path = os.path.join(os.path.dirname(__file__), TPLT_REL_PATH)
    with open(tplt_path) as f:
        tplt = jinja2.Template(f.read())
    with open(output_path, "w") as f:
        data = tplt.render({
            "zynqps_properties": params,
            "zynqps_tcl_cmds": cmds
        })
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


def print_usage_and_exit():
        print("usage: python generate.py "
              "<yaml input file> <TCL output file>")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print_usage_and_exit()
    verbose = True

    try:
        with open(sys.argv[1]) as f:
            config = ordered_load(f)

        # when run by fusesoc as a generator,
        # the config comes in throug the parameters key
        if "parameters" not in config:
            # standalone mode
            if len(sys.argv) < 3:
                print_usage_and_exit()
            params = config
            generate_tcl(params, sys.argv[2])
        else:
            # fusesoc generator mode
            verbose = "-v" in sys.argv
            zynq_config_file = config["parameters"].get("zynq_config_file", None)
            if zynq_config_file:
                zynq_config_path = os.path.join(
                    config["files_root"], zynq_config_file)
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
        if verbose:
            import traceback
            print(traceback.format_exc())
        exit(1)

if __name__ == "__main__":
    main()
