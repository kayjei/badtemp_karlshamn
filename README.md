README.md
Home assistant integration to read and display temperatures for swimareas in Karlshamn, Sweden.

Download the folder badtemp_karlshamn into $CONFIG/custom_components/ or download via HACS
Add configuration to your configuration.yaml
```
sensor:
    - platform: badtemp_karlshamn
```
Sensors will be available as sensor.badtemp_xxxxxxx and positioned at your map in HA.
