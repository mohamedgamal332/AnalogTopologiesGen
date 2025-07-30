from typing import List, Dict, Any
import os
import json

# ==============================================================================
# 1. The Comprehensive Subcircuit Library
# ==============================================================================
COMPREHENSIVE_LIBRARY = {
    'DifferentialPairN': {'description': 'Standard NMOS Differential Pair Gain Stage.', 'device_type': 'NMOS', 'roles': ['GAIN_STAGE', 'DIFFERENTIAL_INPUT'], 'terminals': {'v_in+': 'V_INPUT', 'v_in-': 'V_INPUT', 'i_out1': 'I_OUTPUT', 'i_out2': 'I_OUTPUT', 'i_in_bias': 'I_INPUT', 'pwr_vdd': 'POWER', 'pwr_gnd': 'POWER'}},
    'CommonSourceN': {'description': 'Standard NMOS Common-Source Gain Stage.', 'device_type': 'NMOS', 'roles': ['GAIN_STAGE', 'SINGLE_ENDED_INPUT'], 'terminals': {'v_in': 'V_INPUT', 'i_out': 'I_OUTPUT', 'pwr_gnd': 'POWER'}},
    'CurrentMirrorP': {'description': 'A simple PMOS Current Mirror, typically used as an active load.', 'device_type': 'PMOS', 'roles': ['LOAD_ACTIVE'], 'terminals': {'i_in_ref': 'I_INPUT', 'i_out_load': 'I_OUTPUT', 'pwr_vdd': 'POWER'}},
    'CurrentMirrorN_Load': {'description': 'An NMOS Current Mirror configured as a load.', 'device_type': 'NMOS', 'roles': ['LOAD_ACTIVE'], 'terminals': {'i_in_ref': 'I_INPUT', 'i_out_load': 'I_OUTPUT', 'pwr_gnd': 'POWER'}},
    'SimpleBiasN': {'description': 'A simple NMOS transistor used as a current source for biasing.', 'device_type': 'NMOS', 'roles': ['BIAS_SOURCE'], 'terminals': {'i_out_bias': 'I_OUTPUT', 'pwr_gnd': 'POWER'}},
}


# ==============================================================================
# 2. The Circuit Representation
# ==============================================================================
class Circuit:
    def __init__(self, n, l): self.n, self.l, self.c, self.m = n, l, {c['id']: c for c in n}, self._bm()
    def _bm(self): nm = {}; [nm.setdefault(net, []).append({'component_id': c['id'], 'terminal': t}) for c in self.n for t, net in c.get('connections', {}).items()]; return nm
    def get_info(self, cid): return self.l.get(self.c[cid]['block_type'], {})
    def get_components_by_role(self, r): return [c for c in self.n if r in self.get_info(c['id']).get('roles', [])]


# ==============================================================================
# 3. The Diagnostic Umpire
# ==============================================================================
class DiagnosticUmpire:
    """The enhanced validation engine that categorizes errors."""
    def __init__(self, library: Dict[str, Any]):
        self.library = library
        self.rules = [self._rule_c1_floating_nets, self._rule_k1_nmos_gain_pmos_load, self._rule_s1_missing_essential_blocks, self._rule_g1_goal_mismatch_input_type]
    def check(self, netlist: List[Dict[str, Any]], goals: Dict[str, Any] = {}) -> List[Dict[str, Any]]:
        sanity_errors = self._run_sanity_checks(netlist)
        if sanity_errors: return sanity_errors
        circuit = Circuit(netlist, self.library); errors = []
        [errors.extend(rule(circuit, goals)) for rule in self.rules]
        return sorted(errors, key=lambda x: (x['category'], x['level']))
    def _run_sanity_checks(self, netlist: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not isinstance(netlist, list) or not netlist: return [{'level': 'FATAL', 'category': 'Component Error', 'rule_id': 'F0.1', 'details': {}}]
        for comp in netlist:
            if 'id' not in comp or 'block_type' not in comp: return [{'level': 'FATAL', 'category': 'Component Error', 'rule_id': 'F0.3', 'details': {'component': comp}}]
            if comp['block_type'] not in self.library: return [{'level': 'FATAL', 'category': 'Component Error', 'rule_id': 'F0.4', 'details': {'component_id': comp['id'], 'block_type': comp['block_type']}}]
        return []
    def _rule_c1_floating_nets(self, c: Circuit, g: Dict) -> List[Dict]: return [{'level': 'ERROR', 'category': 'Connection Error', 'rule_id': 'C1', 'details': {'net_name': n, 'component_id': s[0]['component_id'], 'terminal': s[0]['terminal']}} for n,s in c.net_map.items() if n.upper() not in ['VDD','GND'] and len(s)<2]
    def _rule_k1_nmos_gain_pmos_load(self, c: Circuit, g: Dict) -> List[Dict]:
        errors = []
        for stage in c.get_components_by_role('GAIN_STAGE'):
            if c.get_info(stage['id'])['device_type'] == 'NMOS':
                for net in {stage['connections'].get(t) for t, r in c.get_info(stage['id'])['terminals'].items() if r == 'I_OUTPUT'}:
                    if not net: continue
                    for conn in c.net_map.get(net, []):
                        if conn['component_id'] != stage['id'] and 'LOAD_ACTIVE' in c.get_info(conn['component_id'])['roles'] and c.get_info(conn['component_id'])['device_type'] != 'PMOS':
                            errors.append({'level': 'ERROR', 'category': 'Component Error', 'rule_id': 'K1', 'details': {'stage_id': stage['id'], 'load_id': conn['component_id'], 'net_name': net}})
        return errors
    def _rule_s1_missing_essential_blocks(self, c: Circuit, g: Dict) -> List[Dict]:
        errors = []; roles = {r for co in c.n for r in c.get_info(co['id'])['roles']}
        if 'GAIN_STAGE' in roles:
            if 'LOAD_ACTIVE' not in roles: errors.append({'level': 'ERROR', 'category': 'Component Error', 'rule_id': 'S1.1', 'details': {'missing_role': 'LOAD_ACTIVE'}})
            if 'BIAS_SOURCE' not in roles: errors.append({'level': 'WARNING', 'category': 'Component Error', 'rule_id': 'S1.2', 'details': {'missing_role': 'BIAS_SOURCE'}})
        return errors
    def _rule_g1_goal_mismatch_input_type(self, c: Circuit, g: Dict) -> List[Dict]:
        if g.get('input_type') == 'differential' and not c.get_components_by_role('DIFFERENTIAL_INPUT'):
            return [{'level': 'ERROR', 'category': 'Component Error', 'rule_id': 'G1', 'details': {'goal': 'differential input', 'found': [c['id'] for c in c.get_components_by_role('SINGLE_ENDED_INPUT')]}}]
        return []


# ==============================================================================
# 4. FeedbackGenerator with Focused Error Reporting
# ==============================================================================
class DiagnosticFeedbackGenerator:
    """Writes a grouped and highly detailed feedback file without the original code."""
    def __init__(self, umpire: DiagnosticUmpire):
        self.umpire = umpire
        self._formatters = {'F0.4': self._f0_4, 'C1': self._c1, 'K1': self._k1, 'S1.1': self._s1_1, 'S1.2': self._s1_2, 'G1': self._g1}

    def generate_feedback_file(self, netlist: List[Dict], filename: str, goals: Dict = {}):
        """
        Checks the netlist and writes a file containing ONLY the error report.
        """
        errors = self.umpire.check(netlist, goals)
        
        with open(filename, 'w') as f:
            if not errors:
                f.write("## Umpire Feedback: PASS\n\nNo errors found.\n")
                print(f"Feedback file '{filename}' written: Circuit PASS.")
                return

            # The initial prompt to the LLM is now more direct.
            f.write("You are an expert AI. Your previous circuit design contained errors. Please provide a corrected JSON netlist that fixes the following problems.\n\n")
            f.write("## Umpire Feedback: ERRORS DETECTED\n\n")
            
            # Group errors by category
            conn_errors = [e for e in errors if e['category'] == 'Connection Error']
            comp_errors = [e for e in errors if e['category'] == 'Component Error']

            if conn_errors:
                f.write("### Connection Errors\nThese are problems with how components are wired together.\n\n")
                for error in conn_errors:
                    f.write(self._formatters.get(error['rule_id'], self._default_fmt)(error.get('details', {})))
            
            if comp_errors:
                f.write("### Component Errors\nThese are problems with the choice or absence of components.\n\n")
                for error in comp_errors:
                    f.write(self._formatters.get(error['rule_id'], self._default_fmt)(error.get('details', {})))
            
            print(f"Feedback file '{filename}' written: {len(errors)} error(s) found.")

    # --- Formatter functions (no changes needed, they are already detailed) ---
    def _default_fmt(self, d: Dict) -> str: return f"- **Uncategorized Error**: `{d}`\n---\n"
    def _f0_4(self, d: Dict) -> str: return f"- **Rule F0.4: Unknown Block Type**\n  - **Location**: Component `{d.get('component_id')}`.\n  - **Problem**: It uses `block_type` '{d.get('block_type')}', which is not in the library.\n  - **Fix**: Correct the typo or add the block to the library.\n---\n"
    def _c1(self, d: Dict) -> str: return f"- **Rule C1: Floating Net**\n  - **Location**: Net `{d.get('net_name')}`.\n  - **Problem**: This net is only connected to terminal `{d.get('terminal')}` on component `{d.get('component_id')}`.\n  - **Fix**: Connect this net to a second terminal.\n---\n"
    def _k1(self, d: Dict) -> str: return f"- **Rule K1: NMOS/PMOS Mismatch**\n  - **Location**: The load component `{d.get('load_id')}`.\n  - **Problem**: This component is an incorrect load type for the NMOS gain stage `{d.get('stage_id')}`. They are connected via net `{d.get('net_name')}`.\n  - **Fix**: Change the `block_type` of `{d.get('load_id')}` to a PMOS equivalent (e.g., `CurrentMirrorP`).\n---\n"
    def _s1_1(self, d: Dict) -> str: return f"- **Rule S1.1: Missing Essential Component**\n  - **Location**: Circuit-wide.\n  - **Problem**: The design is missing a component with the `{d.get('missing_role')}` role.\n  - **Fix**: Add a component that fulfills this role (e.g., a `CurrentMirrorP` for a load).\n---\n"
    def _s1_2(self, d: Dict) -> str: return f"- **Rule S1.2: Missing Essential Component (Warning)**\n  - **Location**: Circuit-wide.\n  - **Problem**: The design is likely missing a `{d.get('missing_role')}` component.\n  - **Fix**: Add a component with this role (e.g., `SimpleBiasN` for biasing).\n---\n"
    def _g1(self, d: Dict) -> str: return f"- **Rule G1: Goal Mismatch**\n  - **Location**: The input stage of the circuit.\n  - **Problem**: The design goal was `{d.get('goal')}`, but the wrong type of input component (e.g., `{d.get('found', ['unknown'])[0]}`) was used.\n  - **Fix**: Replace the input stage with a component that has the `DIFFERENTIAL_INPUT` role.\n---\n"

# ==============================================================================
# 5. Main Execution Block and Test Suite
# ==============================================================================
if __name__ == '__main__':
    umpire = DiagnosticUmpire(COMPREHENSIVE_LIBRARY)
    feedback_gen = DiagnosticFeedbackGenerator(umpire)

    # --- Define Test Cases ---
    valid_circuit = [{'id': 'INPUT_STAGE', 'block_type': 'DifferentialPairN', 'connections': {'v_in+': 'IN+', 'v_in-': 'IN-', 'i_out1': 'n1', 'i_out2': 'n2', 'i_in_bias': 'nbias', 'pwr_vdd': 'VDD', 'pwr_gnd': 'GND'}}, {'id': 'ACTIVE_LOAD', 'block_type': 'CurrentMirrorP', 'connections': {'i_in_ref': 'n1', 'i_out_load': 'n2', 'pwr_vdd': 'VDD'}}, {'id': 'BIAS_GEN', 'block_type': 'SimpleBiasN', 'connections': {'i_out_bias': 'nbias', 'pwr_gnd': 'GND'}}]
    invalid_circuit = [{'id': 'INPUT_STAGE', 'block_type': 'DifferentialPairN', 'connections': {'v_in+': 'IN+', 'v_in-': 'IN-', 'i_out1': 'n1', 'i_out2': 'n2', 'i_in_bias': 'floating_bias', 'pwr_vdd': 'VDD', 'pwr_gnd': 'GND'}}, {'id': 'BAD_LOAD', 'block_type': 'CurrentMirrorN_Load', 'connections': {'i_in_ref': 'n1', 'i_out_load': 'n2', 'pwr_gnd': 'GND'}}]

    tests = {
        "feedback_for_valid_circuit.md": (valid_circuit, {}),
        "feedback_for_invalid_circuit.md": (invalid_circuit, {}),
    }

    print("="*70)
    print("RUNNING DIAGNOSTIC UMPIRE SYSTEM (FOCUSED FEEDBACK)")
    print("="*70)

    try:
        for filename, (netlist, goals) in tests.items():
            print(f"\n--- Generating feedback for '{filename}' ---")
            feedback_gen.generate_feedback_file(netlist, filename, goals)
            
        print("\n--- Example Feedback File Content (`feedback_for_invalid_circuit.md`) ---")
        with open("feedback_for_invalid_circuit.md", 'r') as f:
            print(f.read())
    finally:
        print("\nCleaning up...")
        for filename in tests.keys():
            if os.path.exists(filename):
                os.remove(filename)
        print("Cleanup complete.")