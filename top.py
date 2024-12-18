# top.py
import subprocess

# Run vol.py and capture its output
result = subprocess.run(['python', 'vol.py'], capture_output=True, text=True)

# Capture the output as a list of lines
output_lines = result.stdout.strip().split('\n')

# Get the last line of the output
last_output = output_lines[-1] if output_lines else ''

# Run gFormAuto.py, passing the last line from vol.py as an argument
subprocess.run(['python', 'gFormAuto.py', last_output])
