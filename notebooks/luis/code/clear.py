import subprocess
print("***WARNING*** running this file will\nDELETE ALL DATA in the 'timedata' directory\nProceed? (y/n)")
answer = str(input())
while(answer!='y' and answer!='Y' and answer!='N' and answer!='n'):
    answer = str(input())
if answer=='y':
    redo = 0
    dirs = str(subprocess.check_output(["ls",'timedata']))[2:-1].split("\\n")[:-1]
    for dir in dirs:
        if len(dir)>4 and (dir[-4:]=='.png' or dir[-4:]=='.csv'):
            subprocess.run(['rm','timedata/'+dir])