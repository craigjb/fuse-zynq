# Fuse-Zynq
Generate Zynq 7000 series configurations using fusesoc (or standalone).

## Example configurations
```yaml
parameters:
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
      speed_bin: 1066G
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
        t_rcd_cycles: 8
        t_rp_cycles: 8
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
      freq_mhz: 50.0
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
```

```yaml
parameters:
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
      speed_bin: 1066G
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
        t_rcd_cycles: 8
        t_rp_cycles: 8
        t_rc_ns: 48.75
        t_ras_min_ns: 35.0
        t_faw_ns: 40.0
    mio:
      voltage_bank0: "2.5V"
      voltage_bank1: "3.3V"
    uarts:
      uart0:
        rx_pin: MIO 14
        tx_pin: MIO 15
        baud_rate: 115200
      uart1:
        rx_pin: MIO 53
        tx_pin: MIO 52
        baud_rate: 115200
    qspi:
      freq_mhz: 50.0
    sdio:
      sdio0:
        ck_pin: MIO 40
        cmd_pin: MIO 41
        io0_pin: MIO 42
        io1_pin: MIO 43
        io2_pin: MIO 44
        io3_pin: MIO 45
        detect_pin: MIO 47
        protect_pin: MIO 48
    usb:
      usb0:
        reset_pin: MIO 46
```
