from subprocess import check_output,run
from shlex import split
from sys import argv
from helpers.helpers import ls
# To delete all files (except for 'runtime-plots.py') from the 'timedata' directory
# pass "'!CLEAR'" as an argument as follows: "python3 sampler.py '!CLEAR'"
if len(argv[1:])>0 and argv[1]=='!CLEAR':
    dirs = ls()
    if 'timedata' not in dirs:
        pass
    else:
        dirs = ls('timedata')
        for dir in dirs:
            if dir[-4:]=='.png' or dir[-4:]=='.csv':
                run(split(f'rm timedata/{dir}')) 
# *** IGNORE THE NUMPY WARNINGS IN THE OUTPUTS ***
# Once the time data implementation has been debugged, I will add some extra logic so that running this file
# will sample the runtimes of each state function exactly once over some time interval. 
for state in ['WAIT','CHASE','ACQUIRE','FETCH','RETURN']:
    output = check_output(split(f"python3 main.py time 0 0 0 {state}"))
    print(f"\n'{state}' : RUNTIME TEST COMPLETE")
run(split(f"python3 timedata/runtime-plots.py"))
