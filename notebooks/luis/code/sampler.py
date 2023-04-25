from subprocess import check_output,run
from timedata.plots import process_data
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
else:
    # *** IGNORE THE NUMPY WARNINGS IN THE OUTPUTS ***
    if len(argv[1:])>0:
        try:
            num_samples = int(argv[1])
        except:
            num_samples = 20
    else:
        num_samples = 20
    for state in ['WAIT','CHASE','ACQUIRE','FETCH','RETURN']:
        output = check_output(split(f"python3 main.py time 1 0 0 {state} {num_samples}")) # The last argument is the number of samples
        print(f"\n'{state}' : RUNTIME TEST COMPLETE")
    process_data()
