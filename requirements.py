import tkinter as tk
from tkinter import font
from datetime import datetime

# ==============================================================================
# 1. Define the Specification Fields
#    This list drives the entire GUI. To add, remove, or reorder fields,
#    simply edit this list.
# ==============================================================================
SPEC_FIELDS = [
    # Category Title, Label Text
    ("General", "Project Name:"),
    ("General", "Circuit Type (e.g., OpAmp, LDO):"),
    
    ("Topology", "Number of Stages:"),
    ("Topology", "Input Stage Type (e.g., Diff. Pair):"),
    ("Topology", "Output Stage Type (e.g., Common Source):"),
    ("Topology", "Load Type (e.g., Active, Resistive):"),
    ("Topology", "Compensation Type (e.g., Miller):"),

    ("Performance - DC", "Open-Loop Gain (dB):"),
    ("Performance - DC", "Common-Mode Rejection Ratio (CMRR, dB):"),
    ("Performance - DC", "Power Supply Rejection Ratio (PSRR, dB):"),
    ("Performance - DC", "Input Offset Voltage (mV):"),

    ("Performance - AC/Transient", "Gain-Bandwidth Product (MHz):"),
    ("Performance - AC/Transient", "Phase Margin (degrees):"),
    ("Performance - AC/Transient", "Slew Rate (V/µs):"),
    ("Performance - AC/Transient", "Settling Time (ns):"),

    ("Power and Noise", "Total Power Consumption (mW):"),
    ("Power and Noise", "Supply Voltage (V):"),
    ("Power and Noise", "Input-Referred Noise (nV/√Hz):"),

    ("User Notes", "Additional Notes or Requirements:")
]


class SpecEditorApp:
    """
    The main application class for the GUI specification editor.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Analog Circuit Specification Editor")
        self.root.configure(bg='#f0f0f0')
        self.root.resizable(False, False)  # Prevent resizing

        # Store the Entry widgets to retrieve their values later
        self.entries = {}

        # Create a main frame for content
        main_frame = tk.Frame(root, padx=20, pady=20, bg='#f0f0f0')
        main_frame.pack()

        # Define fonts
        self.header_font = font.Font(family="Helvetica", size=12, weight="bold")
        self.label_font = font.Font(family="Helvetica", size=10)
        self.entry_font = font.Font(family="Helvetica", size=10)

        # Create the GUI elements dynamically from the SPEC_FIELDS list
        self.create_form_widgets(main_frame)

    def create_form_widgets(self, parent_frame):
        """Creates and lays out the labels, entry boxes, and button."""
        current_category = None
        row_index = 0

        for category, label_text in SPEC_FIELDS:
            # Add a category header if it's a new one
            if category != current_category:
                header = tk.Label(
                    parent_frame,
                    text=f"--- {category} Specifications ---",
                    font=self.header_font,
                    bg='#f0f0f0',
                    pady=10
                )
                header.grid(row=row_index, column=0, columnspan=2, sticky='w')
                row_index += 1
                current_category = category

            # Create the label for the field
            label = tk.Label(
                parent_frame, text=label_text, font=self.label_font, bg='#f0f0f0'
            )
            label.grid(row=row_index, column=0, sticky='w', padx=5, pady=5)

            # Create the entry box for the user to type in
            entry = tk.Entry(
                parent_frame, font=self.entry_font, width=40, relief=tk.SUNKEN, bd=2
            )
            entry.grid(row=row_index, column=1, sticky='e', padx=5, pady=5)
            
            # Store the entry widget, keyed by its label text
            self.entries[label_text] = entry
            row_index += 1

        # Add the Save and Close button
        save_button = tk.Button(
            parent_frame,
            text="done",
            font=self.header_font,
            bg='#4CAF50',
            fg='white',
            relief=tk.RAISED,
            bd=3,
            command=self.save_and_quit
        )
        save_button.grid(row=row_index, column=0, columnspan=2, pady=20, sticky='ew')

    def save_and_quit(self):
        """
        Gathers data from the form, handles empty fields, saves to a file,
        and closes the application.
        """
        collected_specs = {}
        print("Gathering specifications from the form...")

        for label, entry_widget in self.entries.items():
            value = entry_widget.get().strip()
            
            # This is the key logic for handling empty fields
            if not value:
                collected_specs[label] = "Not Specified"
            else:
                collected_specs[label] = value
        
        # Define the output filename
        output_filename = "analog_specs.txt"
        
        # Write the collected data to the file
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write("="*50 + "\n")
                f.write("Analog Circuit Design Specifications\n")
                f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*50 + "\n\n")

                for label, value in collected_specs.items():
                    # Align the values for better readability
                    f.write(f"{label:<40} {value}\n")

            print(f"\nSuccess! Specifications have been saved to '{output_filename}'")
        except IOError as e:
            print(f"\nError: Could not write to file '{output_filename}'. Reason: {e}")
        
        # Close the GUI window
        self.root.destroy()


# ==============================================================================
# 3. Main Execution Block
# ==============================================================================
if __name__ == "__main__":
    print("Launching Analog Circuit Specification Editor...")
    
    # Create the main window
    root = tk.Tk()
    
    # Create the application instance
    app = SpecEditorApp(root)
    
    # Start the GUI event loop
    root.mainloop()
    
    print("Application closed.")