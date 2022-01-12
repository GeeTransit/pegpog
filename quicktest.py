"""GUI to quickly test out PegPog grammars"""

import tkinter
import tkinter.messagebox
import pprint
import traceback

import pegpog.api as pegpog

root = tkinter.Tk()
root.title("PegPog Quick Grammar Tester")

# This allows resizing the textboxes
panes = tkinter.PanedWindow(root, orient="vertical", sashpad=2, sashwidth=0)
panes.pack(expand=True, fill="both")

# The label frame adds a label to the outside of the textbox
# This sets up the grammar textbox
grammar_frame = tkinter.LabelFrame(panes, text="Grammar")
grammar_text = tkinter.Text(grammar_frame, height=8, width=60)
grammar_text.configure(undo=True)  # enable undo shortcuts
grammar_text.configure(borderwidth=0)  # already a border around label frame
grammar_text.pack(expand=True, fill="both")

# This sets up the input textbox
input_frame = tkinter.LabelFrame(panes, text="Input")
input_text = tkinter.Text(input_frame, height=8, width=60)
input_text.configure(undo=True, borderwidth=0)
input_text.pack(expand=True, fill="both")

# Code to run with the parse tree
code_frame = tkinter.LabelFrame(panes, text="Code")
code_text = tkinter.Text(code_frame, height=8, width=60)
code_text.configure(undo=True, borderwidth=0)
code_text.pack(expand=True, fill="both")

# This sets up the output textbox and the parse button
output_frame = tkinter.LabelFrame(panes, text="Result")
output_text = tkinter.Text(output_frame, height=1, width=60)
output_text.configure(borderwidth=0)
output_text.configure(state="disabled")  # disable editing
output_text.configure(bg=root["bg"])  # make background same as surroundings
output_text.grid(row=0, column=0, sticky="nsew")
parse_button = tkinter.Button(output_frame, text="Parse")
parse_button.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)

# Callback for the parse button
def on_parse():
    try:
        # The title variable indicates which stage the error occurred in
        title = "Grammar Retrieve Error"
        grammar_string = grammar_text.get("1.0", "end")  # get whole text
        title = "Grammar Error"
        grammar = pegpog.create_grammar(grammar_string)
        title = "Input Retrieve Error"
        end_string = input_text.get("1.0", "end")[:-1]  # remove last newline
        title = "Input Parse Error"
        result = grammar.parse(end_string)
        title = "Code Retrieve Error"
        code = code_text.get("1.0", "end")
        title = "Code Prepare Error"
        scope = {"tree": result}
        title = "Code Error"
        exec(code, scope)
        title = "Code Result Error"
        result = scope.get("tree", None)
        title = "Output Error"
        if isinstance(result, str):
            output_string = result
        else:
            output_string = pprint.pformat(result, indent=2)  # pretty print
        output_text["state"] = "normal"  # temporarily allow editing
        output_text.delete("1.0", "end")  # remove preexisting output
        output_text.insert("1.0", output_string)  # add result into output
        output_text["state"] = "disabled"  # disable editing again
    except Exception as e:
        # We use the title variable for the error message's title
        traceback.print_exc()  # in case the error is too long
        tkinter.messagebox.showerror(title, repr(e))  # notify user about error
parse_button.configure(command=on_parse)  # set callback function

# Make parse button not expand on resize (weight=0)
output_frame.rowconfigure(0, weight=1)
output_frame.rowconfigure(1, weight=0)
output_frame.rowconfigure(2, weight=0)
output_frame.columnconfigure(0, weight=1)

# Make the output not expand on resize (stretch="never")
# It can still be manually resized though
panes.add(grammar_frame, stretch="always")
panes.add(input_frame, stretch="always")
panes.add(code_frame, stretch="always")
panes.add(output_frame, stretch="never")

root.mainloop()
