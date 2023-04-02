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