import subprocess
from helpers import ls
print("***WARNING*** running this file will\nDELETE ALL DATA in the 'timedata' directory\nProceed? (y/n)")
answer = str(input())
while(answer!='y' and answer!='Y' and answer!='N' and answer!='n'):
    answer = str(input())
if answer=='y':
    redo = 0
    dirs = ls('timedata')    
    for dir in dirs:
        if len(dir)>4 and (dir[-4:]=='.png' or dir[-4:]=='.csv'):
            subprocess.run(['rm','timedata/'+dir])
            redo+=1
    # Repeat the deleted tests with whatever test is currently set up in 'runtimes.sh'.
    # It is assumed that there were 'redo-1' PNGs (all corresponding to a test or the 
    # overall results) and 1 'timedata.csv' file.
    for _ in range(0,redo-1):
        subprocess.call(['sh','./runtimes.sh'])

