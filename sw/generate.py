import sys
import os
import os.path
import jinja2
import yaml

import zynq
from zynq.yml_util import ordered_load


TCL_TPLT_REL_PATH = "../data/zynq_tcl.tplt"
SPINAL_TPLT_REL_PATH = "../data/zynq_spinal.tplt"


def generate_tcl(zynq_sys, output_path):
    params = zynq_sys.tcl_parameters()
    cmds = zynq_sys.tcl_commands()

    tplt_path = os.path.join(os.path.dirname(__file__), TCL_TPLT_REL_PATH)
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


def generate_spinal(zynq_sys, output_path):
    tplt_path = os.path.join(
        os.path.dirname(__file__), SPINAL_TPLT_REL_PATH)
    with open(tplt_path) as f:
        tplt = jinja2.Template(f.read())
    with open(output_path, "w") as f:
        data = tplt.render({
            "zynq_ps": zynq_sys,
        })
        if not data:
            raise RuntimeError("Unknown error: template output is None")
        f.write(data)
    pass


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
              "<yaml input file> "
              "<TCL output file> "
              "[SpinalHDL output file]")
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
            zynq_sys = zynq.Zynq(params)
            generate_tcl(zynq_sys, sys.argv[2])
            if len(sys.argv) >= 4:
                generate_spinal(zynq_sys, sys.argv[3])
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

            zynq_sys = zynq.Zynq(params)

            if len(sys.argv) > 2:
                output_path = sys.argv[2]
            else:
                output_path = "zynq_ps7.tcl"

            generate_tcl(zynq_sys, output_path)
            core_file = config["vlnv"].split(':')[2]+'.core'
            generate_core(config, core_file)
            if "spinal_hdl_output_path" in config["parameters"]:
                output_path = os.path.join(
                    config["files_root"],
                    config["parameters"]["spinal_hdl_output_path"]
                )
                generate_spinal(zynq_sys, output_path)
    except Exception as e:
        print("Error: %s" % e)
        if verbose:
            import traceback
            print(traceback.format_exc())
        exit(1)

if __name__ == "__main__":
    main()
