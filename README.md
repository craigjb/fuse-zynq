# Fuse-Zynq
Generate Zynq 7000 series configurations without using the vendor GUI.

Use as a [fusesoc generator](https://fusesoc.readthedocs.io/en/latest/user/build_system/generators.html) or as a standalone Python script.

## Table of Contents
- [Background](#background)
- [Standalone usage](#standalone-usage)
- [fusesoc usage](#fusesoc-usage)
- [Example configurations](#example-configurations)
- [Status and limitations](#status-and-limitations)

## Background
The [Zynq 7000 series](https://www.xilinx.com/products/silicon-devices/soc/zynq-7000.html) parts combine an ARM processing system (PS) with 7-Series FPGA fabric in a single chip. The PS boot-up process involves setting hundreds of configuration registers depending on desired peripherals and I/O. Previously, this configuration would be done using a GUI provided in the [vendor tooling](https://www.xilinx.com/products/design-tools/vivado.html). Open-source FPGA tooling, specifically [fusesoc](https://github.com/olofk/fusesoc) and [edalize](https://github.com/olofk/edalize), have advanced where it's no longer necessary to use the vendor GUI for other tasks.

This goal of this project is to eventually allow full configuration of the Zynq 7000 series parts without using the vendor GUI.

## Standalone usage
1. Configure peripherals and I/O with yaml (examples below)
2. Run the generator: `python sw/generate.py zynqps_config.yml zynqps.tcl`
3. The resulting TCL file can be included in a project built with the vendor tool; when built:
    - The block design is named zynqps, and a wrapper `zynqps_wrapper.v` will be generated
    - C files to build into u-boot or other software will also be generated:
        ```
        <project_name>.srcs/sources_1/bd/zynqps/ip/zynqps_zynqps_0/ps7_init_gpl.h
        <project_name>.srcs/sources_1/bd/zynqps/ip/zynqps_zynqps_0/ps7_init_gpl.c
        ```

## fusesoc usage
1. Add the fuse-zynq library:
    ```
    fusesoc library add fusesoc-cores https://github.com/craigjb/fuse-zynq`
    ```
2. Configure peripherals and I/O with yaml (examples below)
3. Configure fuse-zynq as a [generator](https://fusesoc.readthedocs.io/en/latest/user/build_system/generators.html) in your core, for example:
    ```
    CAPI=2:
    name: craigjb::fuse_zynq_test:0.1.0
    description: Test of the Fuse-Zynq generator

    filesets:
      tcl:
        file_type: tclSource
        depend:
          [craigjb::zynq_ps7]

    targets:
      default:
        default_tool: vivado
        toplevel: Top
        filesets: [tcl]
        generate: [zynq_ps7]
        tools:
          vivado:
            part: xc7z035ffg676-2

    generate:
      zynq_ps7:
        generator : zynq_ps7_gen
        parameters:
            zynq_config_file: zynq_config.yml
    ```
4. Run fusesoc: `fusesoc run craigjb::fuse_zynq_test`
5. fusesoc will include the generated TCL configuration for the Zynq PS into the vendor build; when built:
    - The block design is named zynqps, and a wrapper `zynqps_wrapper.v` will be generated
    - C files to build into u-boot or other software will also be generated:
        ```
        <project_name>.srcs/sources_1/bd/zynqps/ip/zynqps_zynqps_0/ps7_init_gpl.h
        <project_name>.srcs/sources_1/bd/zynqps/ip/zynqps_zynqps_0/ps7_init_gpl.c
        ```

## Example configurations
Documentation of the available configuration is not available yet. However, these examples should help getting started.

```yaml
part: XC7Z035
speed_grade: '-2I'
ps_in_freq_mhz: 50
cpu:
  ratio_mode: '6:2:1'
  freq_mhz: 667
io_pll:
  freq_mhz: 1000.0
ddr:
  type: DDR3
  data_rate_mbps: 1066
  speed_bin: 1066F
  data_bus_bits: 16
  part_geometry:
    bit_width: 16
    mbits: 4096
    bank_bits: 3
    row_bits: 15
    col_bits: 10
  timing:
    cl: 7
    cwl: 6
    t_rcd_cycles: 7
    t_rp_cycles: 7
    t_rc_ns: 48.75
    t_ras_min_ns: 35.0
    t_faw_ns: 40.0
mio:
  voltage_bank0: "3.3V"
  voltage_bank1: "3.3V"
uarts:
  uart0:
    rx_pin: MIO 14
    tx_pin: MIO 15
    baud_rate: 115200
qspi:
  freq_mhz: 200.0
sdio:
  sdio0:
    ck_pin: MIO 40
    cmd_pin: MIO 41
    io0_pin: MIO 42
    io1_pin: MIO 43
    io2_pin: MIO 44
    io3_pin: MIO 45
    detect_pin: MIO 47
usb:
  usb0:
    reset_pin: MIO 46
ps_pl:
  m_axi_gp0: yes
  m_axi_gp1: yes
```

```yaml
part: XC7Z035
speed_grade: '-2I'
ps_in_freq_mhz: 50
cpu:
  ratio_mode: '6:2:1'
  pll_mul: 27
  pll_div: 2
io_pll:
  pll_mul: 20
ddr:
  type: DDR3
  data_rate_mbps: 1066
  speed_bin: 1066F
  data_bus_bits: 16
  part_geometry:
    bit_width: 16
    mbits: 4096
    bank_bits: 3
    row_bits: 15
    col_bits: 10
  timing:
    cl: 7
    cwl: 6
    t_rcd_cycles: 7
    t_rp_cycles: 7
    t_rc_ns: 48.75
    t_ras_min_ns: 35.0
    t_faw_ns: 40.0
mio:
  voltage_bank0: "3.3V"
  voltage_bank1: "3.3V"
uarts:
  uart0:
    rx_pin: MIO 14
    tx_pin: MIO 15
    baud_rate: 115200
  uart1:
    rx_pin: EMIO
    tx_pin: EMIO
    baud_rate: 115200
qspi:
  freq_mhz: 200.0
sdio:
  sdio0:
    ck_pin: EMIO
    cmd_pin: EMIO
    io0_pin: EMIO
    io1_pin: EMIO
    io2_pin: EMIO
    io3_pin: EMIO
    detect_pin: EMIO
usb:
  usb0:
    reset_pin: MIO 46
ps_pl:
  m_axi_gp0: yes
  m_axi_gp1: yes
```

## Status and limitations
- :white_check_mark: Clocking
- :white_check_mark: DDR
  - :white_check_mark: DDR3
  - :white_check_mark: DDR3L
  - &#9744; DDR2
  - &#9744; LPDDR2
- :white_check_mark: GPIO
- :white_check_mark: UART
- :white_check_mark: QSPI (single chip, single select)
- :white_check_mark: SDIO
- :white_check_mark: USB
- &#9744; PS-PL clocks & resets (1st priority)
- &#9744; PS-PL AXI interfaces (2nd priority)
  - :white_check_mark: M_AXI_GP
- &#9744; SMC
- &#9744; CAN
- &#9744; Ethernet
- &#9744; SPI
- &#9744; I2C
