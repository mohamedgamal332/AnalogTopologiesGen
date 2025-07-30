import os
from datetime import datetime
from openai import OpenAI
from typing import List, Dict, Any, Optional
import argparse

# ==============================================================================
# ### --- CONFIGURATION --- ###
# (Edit all the values in this section to fit your needs)
# ==============================================================================

# 1. LLM CONFIGURATION LIST
# This list holds the configuration for all your available LLMs.
# To add another LLM, just copy one of the blocks and add it to the list.
LLM_CONFIG: List[Dict[str, str]] = [
    {
        "name": "LLM1",
        "api_key": "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",
        "model_identifier": "tngtech/deepseek-r1t2-chimera:free"
    },
    {
        "name": "LLM2",
        "api_key": "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",
        "model_identifier": "qwen/qwen3-32b"
    }
    # You can add more LLMs here, for example:
    # {
    #     "name": "LLM 3 (OpenAI GPT-4)",
    #     "api_key": "YOUR_OPENROUTER_KEY_HERE",
    #     "model_identifier": "openai/gpt-4"
    # }
]

# 2. DEFAULTS (used if no CLI args)
DEFAULT_ACTIVE_LLM_INDEX: int = 0
OPENROUTER_API_BASE: str = "https://openrouter.ai/api/v1"
DEFAULT_INPUT_FILE: str = "requirements.txt"
DEFAULT_OUTPUT_FILE: str = None  # If None, use OUTPUT_DIR logic
OUTPUT_DIR: str = "output"

# 4. PROMPT TEMPLATE
# The script will replace `{requirement_text}` with each line from your file.
PROMPT_TEMPLATE: str = """
You are an expert analog circuit designer AI. Your task is to provide a detailed, clear, and accurate response to the following design requirement.

Your response should include:
1.  A conceptual explanation of the circuit or block.
2.  A list of key components involved.
3.  A simple text-based schematic or a SPICE netlist for the core circuit if applicable.

Here is the specific requirement:

---
{requirement_text}
---

Please provide your expert response.
"""

# ==============================================================================
# ### --- SCRIPT LOGIC (No need to edit below this line) --- ###
# ==============================================================================

def read_requirements(filepath: str) -> Optional[List[str]]:
    """Reads requirements from a file, one per line."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            requirements = [line.strip() for line in f if line.strip()]
        if not requirements:
            print(f"Error: The requirements file '{filepath}' is empty.")
            return None
        return requirements
    except FileNotFoundError:
        print(f"Error: The requirements file was not found at '{filepath}'")
        return None

def get_llm_response(api_key: str, model: str, prompt: str) -> Optional[str]:
    """Sends a prompt to the specified LLM via OpenRouter and returns the response."""
    try:
        client = OpenAI(base_url=OPENROUTER_API_BASE, api_key=api_key)
        print(f"  > Sending prompt to model: '{model}'...")
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"  > An API error occurred: {e}")
        return None

def slugify(text: str) -> str:
    """Converts a string into a simplified, filename-safe format."""
    text = text.lower().strip()
    text = ''.join(c for c in text if c.isalnum() or c in (' ', '-'))
    return text.replace(' ', '_')[:50]

def main() -> None:

    parser = argparse.ArgumentParser(description="LLM Requirements Processor v2.1")
    parser.add_argument('--input', type=str, help='Input file (prompt or requirements)', default=DEFAULT_INPUT_FILE)
    parser.add_argument('--output', type=str, help='Output file (for LLM response)', default=DEFAULT_OUTPUT_FILE)
    parser.add_argument('--llm-index', type=int, help='LLM index to use', default=DEFAULT_ACTIVE_LLM_INDEX)
    args = parser.parse_args()

    input_file = args.input
    output_file = args.output
    llm_index = args.llm_index

    print("="*70)
    print("Starting LLM Requirements Processor v2.1...")
    print("="*70)

    # Validate LLM index
    if not (0 <= llm_index < len(LLM_CONFIG)):
        print(f"Error: LLM index is set to {llm_index}, which is an invalid index.")
        print(f"Please choose an index between 0 and {len(LLM_CONFIG) - 1}.")
        return

    active_llm_config = LLM_CONFIG[llm_index]

    print("Configuration loaded:")
    print(f"  - Active LLM Index: {llm_index}")
    print(f"  - LLM Name: {active_llm_config['name']}")
    print(f"  - Model Identifier: {active_llm_config['model_identifier']}")
    print(f"  - Input File: {input_file}")
    print(f"  - Output File: {output_file if output_file else '[auto-generated in output/]'}\n")

    # If output_file is provided, treat input_file as a single prompt file
    if output_file:
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                prompt = f.read()
        except FileNotFoundError:
            print(f"Error: The input file was not found at '{input_file}'")
            return

        response = get_llm_response(
            api_key=active_llm_config['api_key'],
            model=active_llm_config['model_identifier'],
            prompt=prompt
        )

        if response:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(response)
            print(f"  > Success! Response saved to: {output_file}")
        else:
            print("  > Failed to get a response from the API.")
        print("\n" + "="*70)
        print("Processing complete.")
        print("="*70)
        return

    # Otherwise, treat as requirements file (one per line)
    requirements = read_requirements(input_file)
    if not requirements:
        print("\nProcessing stopped.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Found {len(requirements)} requirement(s) to process. All will be sent to '{active_llm_config['name']}'.\n")

    for i, req_text in enumerate(requirements, 1):
        print(f"--- Processing Requirement {i}/{len(requirements)} ---")
        print(f"  > Requirement: \"{req_text}\"")
        
        final_prompt = PROMPT_TEMPLATE.format(requirement_text=req_text)
        
        response = get_llm_response(
            api_key=active_llm_config['api_key'],
            model=active_llm_config['model_identifier'],
            prompt=final_prompt
        )
        
        if response:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_slug = slugify(req_text)
            output_filename = f"{timestamp}_{filename_slug}.txt"
            output_filepath = os.path.join(OUTPUT_DIR, output_filename)
            
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(response)
            
            print(f"  > Success! Response saved to: {output_filepath}")
        else:
            print("  > Failed to get a response from the API.")

    print("\n" + "="*70)
    print("Processing complete. All requirements have been handled.")
    print("="*70)

if __name__ == "__main__":
    main()