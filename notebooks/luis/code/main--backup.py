from gpio import motors
from state_machine import *
from sys import platform
import sys,subprocess
from helpers import ls,writefile
from img_proc import *
def signal_handler(signum,frame):
    global cam
    cam.destroy()


def main(args):
    global cam
    gettimes,noprint=args[:2]
    if len(args)==3:
        runtime_cap = args[2]
        runtime=0
        t0=time.perf_counter()

    # 'manual = 0' tests the FSM, 'manual = 1' tests the manual controls
    # When testing on the Pi, remove the "platform=='win32' condition"
    # The win32 condition is there because I couldn't make tkinter work
    # with WSL.
    controls = motors(manual=(1 & (platform=='win32'))) 
    cam = camera()
    fsm = FSM(controls,noprint,cam)
    signal.signal(signal.SIGINT, signal_handler)
    functions = [fsm.wait,fsm.chase,fsm.acquire,fsm.fetch,fsm.ret]
    fsm.transition_wait()
    if not noprint:
        print(fsm.get_state(),end=' ')
    next_function_index = fsm.wait()
    # This is a temporary test to run through the state transitions and 
    # functions. This is not how our transitions or function calls will
    # be handled in the final draft.
    while True: 
        if len(args)==3:
            t1 = time.perf_counter()
            runtime+= t1-t0
            if runtime>=runtime_cap:
                raise KeyboardInterrupt
            t0 = t1
        if not noprint:
            print(fsm.get_state(),end=' ')
        if next_function_index>=1 and not fsm.get_state()=='RETURN':
            next_function_index = fsm.function_call(functions[next_function_index-1],gettimes)
        else:
            writefile('error.txt',f"ERROR: Failed in {fsm.get_state()}. Returning to waiting point\n")
            fsm.ret()    
        

def main_fetching(args):
    if platform=='linux' and args[0]=='time':
        # Keeping track of the runtimes of the state functions
        if len(args)==4:
            max_its = args[3]
            print("\nRunning the simulation with a {}-second time limit {} times. If 0 full loops of any state function are recorded, main will be executed more than {} times until there is valid data to write to 'runtimes.csv'.\n**NOTE: This can be avoided by choosing a larger time limit.\n".format(args[2],max_its,max_its))
            dirs = ls()
            if "timedata" not in dirs:
                subprocess.run(['mkdir','timedata'])
            dirs = ls('timedata')
            if "timedata.csv" not in dirs:
                subprocess.run(["touch",'timedata/timedata.csv'])
                # categories_csv = "{},{},{},{},{}\n".format("num_its_main","runtime_cap_main","state","num_its_state_function","avg_runtime_state_function")
                # writefile('timedata.csv',categories_csv)
            # number of times "main" was called, runtime limit (seconds) for each call to "main"
            writefile('timedata/timedata.csv',"{},{}\n".format(max_its,args[2]))
        else:
            max_its = 1
        its = 0
        while its < max_its:
            try:
                time_data(args[0],'',0) 
                if len(args)==4:
                    main(args[:3])
                else:
                    print("Let the simulation run for a bit, and then press CTRL+C to get the\naverage runtimes (in milliseconds) of each of the state functions.")
                    main(args[:2])
            except KeyboardInterrupt:
                time_data_dict = time_data(args[0],'',3)
                print("\n{}: -------- RUNTIME DATA ACQUIRED --------".format(its))
                invalid_data_flag = False
                if len(args)==4: 
                    for state,runtime_loopnum in list(time_data_dict.items()):
                        if runtime_loopnum[1]==0:
                            invalid_data_flag = True
                            break
                if invalid_data_flag==False:
                    for state,runtime_loopnum in list(time_data_dict.items()):
                        if len(args)==4:
                            data_content_csv="{},{},{}\n".format(state,runtime_loopnum[1],runtime_loopnum[0])
                            writefile('timedata/timedata.csv',data_content_csv)
                        else:
                            print("{}:  Averaged {} ms over {} loops".format(state,str(runtime_loopnum[0]),str(runtime_loopnum[1])))
                    its += 1

    else:
        try:
            main([None,args[1]])
        except KeyboardInterrupt:
            print("\n\n------ DESIGN TERMINATED ------\n")
    return 0

if __name__ == '__main__':
    argv = sys.argv[1:]
    if len(argv)==4:
        args = [str(argv[0]),int(argv[1]),int(argv[2]),int(argv[3])]
    elif len(argv)==3:
        args=[str(argv[0]),int(argv[1]),int(argv[2]),1]
    elif len(argv)==2:
        args = [str(argv[0]),int(argv[1])]
    elif len(argv)==1:
        if argv[0]=='time':
            args=[argv[0],0]
        else:
            args=[None,argv[0]]
    else:
        args=[None,0]
    main_fetching(args)
