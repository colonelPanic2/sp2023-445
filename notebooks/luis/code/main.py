from gpio import motors
import state_machine
from state_machine import *
from sys import platform
import sys,getopt,subprocess
from pprint import pprint 

def main(args=None):
    gettimes,noprint=args
    # 'manual = 0' tests the FSM, 'manual = 1' tests the manual controls
    # When testing on the Pi, remove the "platform=='win32' condition"
    # The win32 condition is there because I couldn't make tkinter work
    # with WSL.
    controls = motors(manual=(1 & (platform=='win32'))) 
    fsm = FSM(controls,noprint)
    functions = [fsm.wait,fsm.chase,fsm.acquire,fsm.fetch,fsm.ret]
    fsm.transition_wait()
    if not noprint:
        print(fsm.get_state(),end=' ')
    next_function_index = fsm.wait()
    # This is a temporary test to run through the state transitions and 
    # functions. This is not how our transitions or function calls will
    # be handled in the final draft.
    while 1:        
        if not noprint:
            print(fsm.get_state(),end=' ')
        if next_function_index>=1:
            next_function_index = fsm.function_call(functions[next_function_index-1],gettimes)
        else:
            print("ERROR: Failed to complete task")
            fsm.ret()    
            return 0

def main_():
    argv = sys.argv[1:]
    _,arguments = getopt.getopt(argv,'')
    if len(arguments)==2:
        args = [str(arguments[0]),int(arguments[1])]
    elif len(arguments)==1:
        if arguments[0]=='time':
            args=[arguments[0],0]
        else:
            args=[None,arguments[0]]
    else:
        args=[None,0]
    if platform=='linux' and args[0]=='time':
        # Keeping track of the runtimes of the state functions
        time_data(args[0],'',0) 
        try:
            print("Let the program run for a bit, and then press CTRL+C to get the\naverage runtimes (in milliseconds) of each of the state functions.")
            main(args[:2])
        except KeyboardInterrupt:
            time_data_dict = time_data(args[0],'',3)
            print("\n-------- RUNTIME DATA ACQUIRED --------")
            try:
                plot_time_data(args[0])
            except:
                ### I was originally planning to write the data to a .txt file
                # dirs = str(subprocess.check_output(["ls"]))[2:-1].split("\\n")[:-1]
                # if "time-data.txt" not in dirs:
                #     subprocess.run(["touch","time-data.txt"])
                for state,runtime_loopnum in list(time_data_dict.items()):
                    print("{}:  Averaged {} ms over {} loops".format(state,str(runtime_loopnum[0]),str(runtime_loopnum[1])))
    else:
        main(args)

if __name__ == '__main__':
    main_()
