from subprocess import check_output
from shlex import split
# Once the time data implementation has been debugged, I will add some extra logic so that running this file
# will sample the runtimes of each state function exactly once over some time interval. 
for state in ['WAIT','CHASE','ACQUIRE','FETCH']:
    output = check_output(split(f"python3 main.py time {state}"))
    print(f"\n'{state}' : RUNTIME TEST COMPLETE\n{output}")