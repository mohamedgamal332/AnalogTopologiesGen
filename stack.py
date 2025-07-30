import os
import json
import tkinter as tk
from tkinter import font
from datetime import datetime
from typing import List, Dict, Optional
import subprocess
import platform

# ==============================================================================
# ### --- MASTER CONFIGURATION --- ###
# ==============================================================================

# 1. LOOP CONTROL
# The maximum number of correction loops to run before stopping.
MAX_ITERATIONS = 4

# ==============================================================================
# ### --- COMPONENT 1: SPECIFICATION EDITOR (GUI) --- ###
# ==============================================================================

SPEC_FIELDS = [
    ("General", "Project Name:"), ("General", "Circuit Type (e.g., OpAmp):"),
    ("Topology", "Number of Stages:"), ("Topology", "Input Stage Type:"),
    ("Topology", "Load Type (e.g., Active):"), ("Performance - DC", "Open-Loop Gain (dB):"),
    ("Performance - AC/Transient", "Gain-Bandwidth Product (MHz):"), ("Power and Noise", "Supply Voltage (V):"),
    ("User Notes", "Additional Notes or Requirements:")
]

class SpecEditorApp:
    def __init__(self, root, output_path):
        self.root = root; self.output_path = output_path; self.entries = {}
        self.root.title("Analog Circuit Specification Editor"); self.root.configure(bg='#f0f0f0')
        main_frame = tk.Frame(root, padx=20, pady=20, bg='#f0f0f0'); main_frame.pack()
        header_font = font.Font(family="Helvetica", size=12, weight="bold")
        current_category = None; row_index = 0
        for category, label_text in SPEC_FIELDS:
            if category != current_category:
                tk.Label(main_frame, text=f"--- {category} ---", font=header_font, bg='#f0f0f0', pady=10).grid(row=row_index, column=0, columnspan=2, sticky='w'); row_index += 1; current_category = category
            tk.Label(main_frame, text=label_text, font=("Helvetica", 10), bg='#f0f0f0').grid(row=row_index, column=0, sticky='w', padx=5, pady=5)
            entry = tk.Entry(main_frame, font=("Helvetica", 10), width=40); entry.grid(row=row_index, column=1, sticky='e', padx=5, pady=5); self.entries[label_text] = entry; row_index += 1
        tk.Button(main_frame, text="Save and Continue", font=header_font, bg='#4CAF50', fg='white', command=self.save_and_quit).grid(row=row_index, column=0, columnspan=2, pady=20, sticky='ew')
    def save_and_quit(self):
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write("--- Analog Circuit Design Specifications ---\n")
            for label, entry in self.entries.items():
                value = entry.get().strip() or "Not Specified"; f.write(f"{label:<40} {value}\n")
        print(f"[Orchestrator] Specifications saved to '{self.output_path}'")
        self.root.destroy()

def run_spec_editor(output_path: str):
    """Launches the GUI and waits for the user to save the specs."""
    print("[Orchestrator] Waiting for user to input specifications via GUI...")
    root = tk.Tk(); app = SpecEditorApp(root, output_path); root.mainloop()

# ==============================================================================
# ### --- COMPONENT 2: LLM REQUESTER --- ###
# ==============================================================================

def run_llm_request_with_contact_two(prompt_filepath: str, output_filepath: str, llm_index: int) -> bool:
    """Calls contact_two.py as a subprocess to handle the LLM request."""
    print(f"[Orchestrator] Calling contact_two.py for LLM index {llm_index}...")
    try:
        result = subprocess.run([
            "python3", "contact_two.py",
            "--input", prompt_filepath,
            "--output", output_filepath,
            "--llm-index", str(llm_index)
        ], capture_output=True, text=True)
        print(result.stdout)
        if result.returncode == 0:
            print(f"[Orchestrator] LLM response saved to '{output_filepath}'")
            return True
        else:
            print(f"[Orchestrator] contact_two.py failed with return code {result.returncode}")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"[Orchestrator] Failed to call contact_two.py: {e}")
        return False

def parse_llm_output_to_json(llm_output_filepath: str) -> Optional[List[Dict]]:
    """Parses the LLM's text output, extracting the first JSON code block."""
    print(f"[Orchestrator] Parsing JSON netlist from '{llm_output_filepath}'...")
    try:
        with open(llm_output_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the start and end of the first JSON code block
        json_start = content.find("```json")
        if json_start == -1:
            print("  > ERROR: No JSON code block (```json) found in the LLM response.")
            return None
        
        json_end = content.find("```", json_start + 7)
        if json_end == -1:
            print("  > ERROR: Found start of JSON block but no end (```).")
            return None
            
        json_str = content[json_start + 7 : json_end].strip()
        return json.loads(json_str)

    except FileNotFoundError:
        print(f"  > ERROR: LLM output file not found.")
        return None
    except json.JSONDecodeError as e:
        print(f"  > ERROR: Failed to parse JSON. The format is invalid: {e}")
        return None
    except Exception as e:
        print(f"  > ERROR: An unexpected error occurred during parsing: {e}")
        return None

# ==============================================================================
# ### --- COMPONENT 3: UMPIRE (VALIDATOR) --- ###
# (A condensed version of the umpire_final_system.py)
# ==============================================================================

# The Umpire's knowledge base and classes are nested here for a single-file script.
COMPREHENSIVE_LIBRARY = {'DifferentialPairN': {'description': 'Standard NMOS Differential Pair Gain Stage.', 'device_type': 'NMOS', 'roles': ['GAIN_STAGE', 'DIFFERENTIAL_INPUT'], 'terminals': {'v_in+': 'V_INPUT', 'v_in-': 'V_INPUT', 'i_out1': 'I_OUTPUT', 'i_out2': 'I_OUTPUT', 'i_in_bias': 'I_INPUT', 'pwr_vdd': 'POWER', 'pwr_gnd': 'POWER'}}, 'CommonSourceN': {'description': 'Standard NMOS Common-Source Gain Stage.', 'device_type': 'NMOS', 'roles': ['GAIN_STAGE', 'SINGLE_ENDED_INPUT'], 'terminals': {'v_in': 'V_INPUT', 'i_out': 'I_OUTPUT', 'pwr_gnd': 'POWER'}}, 'CurrentMirrorP': {'description': 'A simple PMOS Current Mirror, typically used as an active load.', 'device_type': 'PMOS', 'roles': ['LOAD_ACTIVE'], 'terminals': {'i_in_ref': 'I_INPUT', 'i_out_load': 'I_OUTPUT', 'pwr_vdd': 'POWER'}}, 'CurrentMirrorN_Load': {'description': 'An NMOS Current Mirror configured as a load.', 'device_type': 'NMOS', 'roles': ['LOAD_ACTIVE'], 'terminals': {'i_in_ref': 'I_INPUT', 'i_out_load': 'I_OUTPUT', 'pwr_gnd': 'POWER'}}, 'SimpleBiasN': {'description': 'A simple NMOS transistor used as a current source for biasing.', 'device_type': 'NMOS', 'roles': ['BIAS_SOURCE'], 'terminals': {'i_out_bias': 'I_OUTPUT', 'pwr_gnd': 'POWER'}}}
class UmpireCircuit:
    def __init__(self, netlist, library):
        self.netlist = netlist
        self.library = library
        self.components = {c['id']: c for c in netlist}
        self.net_map = self._build_net_map()
    def _build_net_map(self):
        nm = {}
        [nm.setdefault(net, []).append({'component_id': c['id'], 'terminal': t}) for c in self.netlist for t, net in c.get('connections', {}).items()]
        return nm
    def get_info(self, cid):
        return self.library.get(self.components[cid]['block_type'], {})
    def get_comp_by_role(self, role):
        return [c for c in self.netlist if role in self.get_info(c['id']).get('roles', [])]
class Umpire:
    def __init__(self, l): self.l, self.r = l, [self._r_c1, self._r_k1, self._r_s1]
    def check(self, n):
        # Format check: must be a list of dicts with 'id', 'block_type', 'connections'
        if not isinstance(n, list):
            return [{'level': 'FATAL', 'rule_id': 'FORMAT', 'details': {'msg': 'Netlist must be a list of components (not a dict with a top-level key).'}}]
        for c in n:
            if not isinstance(c, dict) or 'id' not in c or 'block_type' not in c or 'connections' not in c:
                return [{'level': 'FATAL', 'rule_id': 'FORMAT', 'details': {'msg': 'Each component must be a dict with id, block_type, and connections.'}}]
        s_err = self._sanity(n)
        if s_err: return s_err
        c = UmpireCircuit(n, self.l); errs = []; [errs.extend(rule(c)) for rule in self.r]; return sorted(errs, key=lambda x: x['level'])
    def _sanity(self, n):
        if not n or not isinstance(n, list): return [{'level': 'FATAL', 'rule_id': 'F0.1'}]
        for c in n:
            if 'id' not in c or 'block_type' not in c: return [{'level': 'FATAL', 'rule_id': 'F0.3', 'details': {'c': c}}]
            if c['block_type'] not in self.l: return [{'level': 'FATAL', 'rule_id': 'F0.4', 'details': {'cid': c['id'], 'bt': c['block_type']}}]
        return []
    def _r_c1(self, c):
        return [{'level': 'ERROR', 'rule_id': 'C1', 'details': {'n': n, 'cid': s[0]['component_id']}} for n, s in c.net_map.items() if n.upper() not in ['VDD', 'GND'] and len(s) < 2]
    def _r_k1(self, c):
        errs = []
        for s in c.get_comp_by_role('GAIN_STAGE'):
            if c.get_info(s['id'])['device_type'] == 'NMOS':
                for net in {s['connections'].get(t) for t, r in c.get_info(s['id'])['terminals'].items() if r == 'I_OUTPUT'}:
                    if net:
                        for conn in c.net_map.get(net, []):
                            if conn['component_id'] != s['id'] and 'LOAD_ACTIVE' in c.get_info(conn['component_id'])['roles'] and c.get_info(conn['component_id'])['device_type'] != 'PMOS':
                                errs.append({'level': 'ERROR', 'rule_id': 'K1', 'details': {'sid': s['id'], 'lid': conn['component_id']}})
        return errs
    def _r_s1(self, c):
        errs = []
        roles = {r for co in c.netlist for r in c.get_info(co['id'])['roles']}
        if 'GAIN_STAGE' in roles:
            if 'LOAD_ACTIVE' not in roles:
                errs.append({'level': 'ERROR', 'rule_id': 'S1.1'})
            if 'BIAS_SOURCE' not in roles:
                errs.append({'level': 'WARNING', 'rule_id': 'S1.2'})
        return errs
class UmpireFeedback:
    def __init__(self, u): self.u, self.f = u, {'F0.4': self._f0_4, 'C1': self._c1, 'K1': self._k1, 'S1.1': self._s1_1, 'S1.2': self._s1_2, 'FORMAT': self._format}
    def generate(self, n, file, goals={}):
        errs = self.u.check(n)
        with open(file, 'w') as f:
            if not errs:
                f.write("## Umpire Feedback: PASS\n\nNo errors found.\n")
                return False
            f.write("## Umpire Feedback: ERRORS DETECTED\n\n")
            for e in errs:
                formatter = self.f.get(e['rule_id'], lambda d: f"### Uncategorized Error\n- **Details**: `{d}`\n\n---\n")
                f.write(formatter(e.get('details', {})))
        return True
    def _f0_4(self, d): return f"### FATAL: Unknown Block (F0.4)\n- **Problem**: Block `{d.get('cid')}` uses unknown type `{d.get('bt')}`.\n- **Fix**: Use a known `block_type`.\n---\n"
    def _c1(self, d): return f"### ERROR: Floating Net (C1)\n- **Problem**: Net `{d.get('n')}` on component `{d.get('cid')}` is floating.\n- **Fix**: Connect this net to another component terminal.\n---\n"
    def _k1(self, d): return f"### ERROR: NMOS/PMOS Mismatch (K1)\n- **Problem**: NMOS stage `{d.get('sid')}` is loaded by non-PMOS load `{d.get('lid')}`.\n- **Fix**: Change load `{d.get('lid')}` to a PMOS type (e.g., `CurrentMirrorP`).\n---\n"
    def _s1_1(self, d): return f"### ERROR: Missing Load (S1.1)\n- **Problem**: Gain stage exists but no `LOAD_ACTIVE` component found.\n- **Fix**: Add a load (e.g., `CurrentMirrorP`) to the gain stage output.\n---\n"
    def _s1_2(self, d): return f"### WARNING: Missing Bias (S1.2)\n- **Problem**: No `BIAS_SOURCE` component found.\n- **Fix**: Add a bias source (e.g., `SimpleBiasN`) to the gain stage bias input.\n---\n"
    def _format(self, d): return f"### FATAL: Netlist Format Error\n- **Problem**: {d.get('msg','Format error.')}\n- **Fix**: Output a list of components, each with id, block_type, and connections.\n---\n"

def run_umpire_check(netlist_filepath: str, feedback_filepath: str) -> bool:
    """Reads a JSON netlist, runs the Umpire, saves feedback, and returns if errors were found."""
    print(f"[Orchestrator] Running Umpire on '{netlist_filepath}'...")
    umpire_instance = Umpire(COMPREHENSIVE_LIBRARY)
    feedback_generator = UmpireFeedback(umpire_instance)
    try:
        with open(netlist_filepath, 'r') as f:
            netlist = json.load(f)
        has_errors = feedback_generator.generate(netlist, feedback_filepath)
        print(f"[Orchestrator] Umpire feedback saved to '{feedback_filepath}'. Errors found: {has_errors}")
        return has_errors
    except Exception as e:
        print(f"  > ERROR: Umpire check failed: {e}")
        return True # Treat any exception as a failure

# ==============================================================================
# ### --- MAIN ORCHESTRATOR LOGIC --- ###
# ==============================================================================

def main():
    # --- Setup ---
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = f"run_{run_timestamp}"
    os.makedirs(run_dir, exist_ok=True)
    print("="*70)
    print(f"Starting Orchestration Run: {run_timestamp}")
    print(f"All files will be saved in directory: '{run_dir}'")
    print("="*70)

    # --- Step 1: Get user specifications ---
    spec_filepath = os.path.join(run_dir, "analog_specs_initial.txt")
    run_spec_editor(spec_filepath)
    
    # --- Step 2: Create the initial prompt for the LLM ---
    initial_prompt_filepath = os.path.join(run_dir, "prompt_v0.md")
    try:
        with open(spec_filepath, 'r') as f_spec:
            specs = f_spec.read()
        with open(initial_prompt_filepath, 'w') as f_prompt:
            f_prompt.write("You are an expert analog circuit designer AI. Your task is to generate a valid JSON netlist based on the following user specifications.\n\n")
            f_prompt.write("IMPORTANT: Output a JSON array (list) of components, not an object or a dictionary. Each component must be a dict with the following fields: 'id', 'block_type', and 'connections'.\n")
            f_prompt.write("- 'id': a unique string identifier for the component.\n")
            f_prompt.write("- 'block_type': the type of the component (e.g., 'DifferentialPairN', 'CurrentMirrorP', etc.).\n")
            f_prompt.write("- 'connections': a dictionary mapping terminal names to net names.\n\n")
            f_prompt.write("Below is the library of allowed components and their terminal names. Use only these block types and terminal names in your netlist.\n\n")
            f_prompt.write("```json\n" + json.dumps(COMPREHENSIVE_LIBRARY, indent=2) + "\n```")
            f_prompt.write("\n\nExample output:\n")
            f_prompt.write("""```json
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
""")
            f_prompt.write("\n\n--- USER SPECIFICATIONS ---\n")
            f_prompt.write(specs)
            f_prompt.write("\n\n---------------------------\n\n")
            f_prompt.write("Please generate the JSON netlist now, following the example format exactly.")
        print(f"[Orchestrator] Initial prompt created at '{initial_prompt_filepath}'")
    except Exception as e:
        print(f"FATAL ERROR: Could not create initial prompt. {e}")
        return

    # --- Step 3: The Main Correction Loop ---
    current_prompt_file = initial_prompt_filepath
    final_netlist_path = None
    last_generated_netlist = None
    success = False
    llm_index = 0
    MAX_RETRIES = 3

    for i in range(MAX_ITERATIONS):
        iteration = i + 1
        print("\n" + "-"*70)
        print(f"Starting Iteration {iteration}/{MAX_ITERATIONS}")
        print("-"*70)

        # 3a: Call the LLM with the current prompt using contact_two.py
        llm_output_file = os.path.join(run_dir, f"llm_response_v{iteration}.txt")
        retry_count = 0
        parsed_netlist = None
        while retry_count < MAX_RETRIES:
            if not run_llm_request_with_contact_two(current_prompt_file, llm_output_file, llm_index):
                print("Loop stopped due to LLM API failure.")
                return
            # 3b: Parse the LLM's response to get a JSON netlist
            parsed_netlist = parse_llm_output_to_json(llm_output_file)
            if parsed_netlist is not None:
                break
            else:
                retry_count += 1
                print(f"[Orchestrator] Invalid JSON from LLM. Retrying ({retry_count}/{MAX_RETRIES})...")
        if parsed_netlist is None:
            print("Loop stopped due to repeated failure in parsing LLM output.")
            break
        
        # 3c: Save the valid JSON netlist
        current_netlist_file = os.path.join(run_dir, f"netlist_v{iteration}.json")
        with open(current_netlist_file, 'w') as f:
            json.dump(parsed_netlist, f, indent=2)
        print(f"[Orchestrator] Valid netlist saved to '{current_netlist_file}'")
        last_generated_netlist = current_netlist_file

        # 3d: Run the Umpire check
        feedback_file = os.path.join(run_dir, f"umpire_feedback_v{iteration}.md")
        has_errors = run_umpire_check(current_netlist_file, feedback_file)
        
        # 3e: Check for success condition
        if not has_errors:
            print("\n" + "="*70)
            print("SUCCESS: Umpire validation passed! The design is valid.")
            print("="*70)
            final_netlist_path = current_netlist_file
            success = True
            break
        
        # 3f: Prepare for the next loop
        # Alternate the LLM index (mod 2)
        llm_index = (llm_index + 1) % 2

        # Construct the next prompt: combine previous LLM output and umpire feedback
        next_prompt_file = os.path.join(run_dir, f"prompt_v{iteration}.md")
        with open(llm_output_file, 'r') as f_llm, open(feedback_file, 'r') as f_umpire, open(next_prompt_file, 'w') as f_next_prompt:
            f_next_prompt.write("You are an expert analog circuit designer AI.\n")
            f_next_prompt.write("IMPORTANT: Output a JSON array (list) of components, not an object or a dictionary. Each component must be a dict with the following fields: 'id', 'block_type', and 'connections'.\n")
            f_next_prompt.write("- 'id': a unique string identifier for the component.\n")
            f_next_prompt.write("- 'block_type': the type of the component (e.g., 'DifferentialPairN', 'CurrentMirrorP', etc.).\n")
            f_next_prompt.write("- 'connections': a dictionary mapping terminal names to net names.\n\n")
            f_next_prompt.write("Below is the library of allowed components and their terminal names. Use only these block types and terminal names in your netlist.\n\n")
            f_next_prompt.write("```json\n" + json.dumps(COMPREHENSIVE_LIBRARY, indent=2) + "\n```")
            f_next_prompt.write("\n\nExample output:\n")
            f_next_prompt.write("""```json
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
""")
            f_next_prompt.write("\n\nBelow is the previous design output and the Umpire's feedback.\n")
            f_next_prompt.write("Your task is to correct the JSON netlist according to the Umpire's feedback.\n\n")
            f_next_prompt.write("--- PREVIOUS LLM OUTPUT ---\n")
            f_next_prompt.write(f_llm.read())
            f_next_prompt.write("\n\n--- UMPIRE FEEDBACK (FAILED TESTS) ---\n")
            f_next_prompt.write(f_umpire.read())
            f_next_prompt.write("\n\nPlease provide a corrected JSON netlist, enclosed in a single ```json ... ``` code block, that addresses all the Umpire's feedback and follows the example format exactly.")
        current_prompt_file = next_prompt_file
    
    # --- Step 4: Final Summary ---
    if not success:
        print("\n" + "="*70)
        print(f"PROCESS FAILED: The loop completed {MAX_ITERATIONS} iterations without a valid design.")
        print("="*70)
    
    file_to_open = final_netlist_path if success else last_generated_netlist
    
    if file_to_open:
        if success:
            print(f"The final, validated netlist can be found at: '{file_to_open}'")
        else:
            print(f"The last generated (but invalid) netlist can be found at: '{file_to_open}'")
        
        try:
            if platform.system() == "Linux":
                subprocess.run(["xdg-open", file_to_open])
            elif platform.system() == "Darwin": # macOS
                subprocess.run(["open", file_to_open])
            elif platform.system() == "Windows":
                os.startfile(file_to_open)
            print(f"[Orchestrator] Automatically opening file: {os.path.basename(file_to_open)}...")
        except Exception as e:
            print(f"[Orchestrator] Could not automatically open the file. Please open it manually. Error: {e}")
    else:
        print("No valid netlist was produced.")

if __name__ == "__main__":
    main()