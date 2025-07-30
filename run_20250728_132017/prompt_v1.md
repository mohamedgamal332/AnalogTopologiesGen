You are an expert analog circuit designer AI.
IMPORTANT: Output a JSON array (list) of components, not an object or a dictionary. Each component must be a dict with the following fields: 'id', 'block_type', and 'connections'.
- 'id': a unique string identifier for the component.
- 'block_type': the type of the component (e.g., 'DifferentialPairN', 'CurrentMirrorP', etc.).
- 'connections': a dictionary mapping terminal names to net names.

Below is the library of allowed components and their terminal names. Use only these block types and terminal names in your netlist.

```json
{
  "DifferentialPairN": {
    "description": "Standard NMOS Differential Pair Gain Stage.",
    "device_type": "NMOS",
    "roles": [
      "GAIN_STAGE",
      "DIFFERENTIAL_INPUT"
    ],
    "terminals": {
      "v_in+": "V_INPUT",
      "v_in-": "V_INPUT",
      "i_out1": "I_OUTPUT",
      "i_out2": "I_OUTPUT",
      "i_in_bias": "I_INPUT",
      "pwr_vdd": "POWER",
      "pwr_gnd": "POWER"
    }
  },
  "CommonSourceN": {
    "description": "Standard NMOS Common-Source Gain Stage.",
    "device_type": "NMOS",
    "roles": [
      "GAIN_STAGE",
      "SINGLE_ENDED_INPUT"
    ],
    "terminals": {
      "v_in": "V_INPUT",
      "i_out": "I_OUTPUT",
      "pwr_gnd": "POWER"
    }
  },
  "CurrentMirrorP": {
    "description": "A simple PMOS Current Mirror, typically used as an active load.",
    "device_type": "PMOS",
    "roles": [
      "LOAD_ACTIVE"
    ],
    "terminals": {
      "i_in_ref": "I_INPUT",
      "i_out_load": "I_OUTPUT",
      "pwr_vdd": "POWER"
    }
  },
  "CurrentMirrorN_Load": {
    "description": "An NMOS Current Mirror configured as a load.",
    "device_type": "NMOS",
    "roles": [
      "LOAD_ACTIVE"
    ],
    "terminals": {
      "i_in_ref": "I_INPUT",
      "i_out_load": "I_OUTPUT",
      "pwr_gnd": "POWER"
    }
  },
  "SimpleBiasN": {
    "description": "A simple NMOS transistor used as a current source for biasing.",
    "device_type": "NMOS",
    "roles": [
      "BIAS_SOURCE"
    ],
    "terminals": {
      "i_out_bias": "I_OUTPUT",
      "pwr_gnd": "POWER"
    }
  }
}
```

Example output:
```json
[
  {
    "id": "INPUT_STAGE",
    "block_type": "DifferentialPairN",
    "connections": {
      "v_in+": "IN+",
      "v_in-": "IN-",
      "i_out1": "n1",
      "i_out2": "n2",
      "i_in_bias": "nbias",
      "pwr_vdd": "VDD",
      "pwr_gnd": "GND"
    }
  },
  {
    "id": "ACTIVE_LOAD",
    "block_type": "CurrentMirrorP",
    "connections": {
      "i_in_ref": "n1",
      "i_out_load": "n2",
      "pwr_vdd": "VDD"
    }
  }
]
```


Below is the previous design output and the Umpire's feedback.
Your task is to correct the JSON netlist according to the Umpire's feedback.

--- PREVIOUS LLM OUTPUT ---


```json
[
  {
    "id": "BIAS_SOURCE",
    "block_type": "SimpleBiasN",
    "connections": {
      "i_out_bias": "BIAS_NET",
      "pwr_gnd": "GND"
    }
  },
  {
    "id": "LED_DRIVER",
    "block_type": "CurrentMirrorN_Load",
    "connections": {
      "i_in_ref": "BIAS_NET",
      "i_out_load": "LED_NET",
      "pwr_gnd": "GND"
    }
  }
]
```

--- UMPIRE FEEDBACK (FAILED TESTS) ---
## Umpire Feedback: ERRORS DETECTED

### ERROR: Floating Net (C1)
- **Problem**: Net `LED_NET` on component `LED_DRIVER` is floating.
- **Fix**: Connect this net to another component terminal.
---


Please provide a corrected JSON netlist, enclosed in a single ```json ... ``` code block, that addresses all the Umpire's feedback and follows the example format exactly.