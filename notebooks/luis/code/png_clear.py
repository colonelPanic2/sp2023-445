import subprocess
from helpers import ls
dirs = ls()
for file in dirs:
    if file[-4:]=='.png':
        _ = subprocess.check_output(f"rm {file}")