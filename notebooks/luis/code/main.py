from sys import platform
import sys,subprocess,traceback
from gpio import motors
from state_machine import *
from helpers import ls,writefile,logdata
from img_proc import images,camera
def signal_handler(signum,frame):
    global cam
    cam.destroy()
    time.sleep(1)
    exit(0)

def main(args,init_time,logfile):
    global cam
    gettimes,noprint,demo=args[:3]
    if len(args)==4:
        runtime_cap = args[3]
        runtime = 0
        t0 = time.perf_counter()
    # 'manual = 0' tests the FSM, 'manual = 1' tests the manual controls
    # When testing on the Pi, remove the "platform=='win32' condition"
    # The win32 condition is there because I couldn't make tkinter work
    # with WSL.
    cam = camera(demo,init_time,logfile)
    controls = motors(manual=1,init_time=init_time,logfile=logfile,cam=cam,demo=demo) 
    fsm = FSM(controls,noprint,cam,demo,init_time,logfile)
    signal.signal(signal.SIGINT, signal_handler)


    functions = [fsm.wait,fsm.chase,fsm.acquire,fsm.fetch,fsm.ret]
    fsm.transition_wait()
    if not noprint:
        writefile(logfile,fsm.get_state() + ' ')
    next_function_index = fsm.wait()
    # This is a temporary test to run through the state transitions and 
    # functions. This is not how our transitions or function calls will
    # be handled in the final draft.
    while True: 
        if len(args)==4:
            t1 = time.perf_counter()
            runtime+= t1-t0
            if runtime>=runtime_cap:
                raise KeyboardInterrupt
            t0 = t1
        if not noprint:
            writefile(logfile,fsm.get_state()+' ')
        if next_function_index>=1:
            next_function_index = fsm.function_call(functions[next_function_index-1],gettimes)
        else:
            writefile(logfile,f"ERROR: Failed in {fsm.get_state()}. Returning to waiting point\n")
            if not noprint and fsm.get_state()!='RETURN':
                writefile(logfile,f"Attempting to transition to RETURN from {fsm.get_state()}...")
                fsm.transition_return()
            if not noprint:
                writefile(logfile,'\n'+fsm.get_state()+' ')
            next_function_index = fsm.ret()    
        

def main_fetching(args,init_time,logfile):
    if platform=='linux':
        # Keeping track of the runtimes of the state functions
        if len(args)==5:
            max_its = args[4]
            writefile(logfile,"\nRunning the simulation with a {}-second time limit {} times. If 0 full loops of any state function are recorded, main will be executed more than {} times until there is valid data to write to 'runtimes.csv'.\n**NOTE: This can be avoided by choosing a larger time limit.\n".format(args[3],max_its,max_its))
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
                if len(args)==5:
                    main(args[:4],init_time,logfile)

                else:
                    writefile(logfile,"Let the simulation run for a bit, and then press CTRL+C to get the\naverage runtimes (in milliseconds) of each of the state functions.\n")
                    main(args[:3],init_time,logfile)
            except KeyboardInterrupt:
                if str(type(args[0]))!="<class 'NoneType'>":
                    time_data_dict = time_data(args[0],'',3)
                    writefile(logfile,"\n{}: -------- RUNTIME DATA ACQUIRED --------\n".format(its))
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
                                writefile(logfile,"{}:  Averaged {} ms over {} loops\n".format(\
                                            state,str(runtime_loopnum[0]),str(runtime_loopnum[1])))
                        its += 1
                else:
                    writefile(logfile,"Done.\n")
                    its += 1
    else:
        try:
            main([None,args[1],1],init_time,logfile)
        except KeyboardInterrupt:
            writefile(logfile,"\n\n------ DESIGN TERMINATED ------\n\n")
    return 0

if __name__ == '__main__':
    init_time,logfile,errfile = logdata()
    try:
        argv = sys.argv[1:]
        if len(argv)==5:
            # time noprint demo_ runtime_limit num_its
            args = [str(argv[0]),int(argv[1]),int(argv[2]),int(argv[3]),int(argv[4])]
        elif len(argv)==4:
            # time noprint demo_ runtime_limit default_num_its=1
            args=[str(argv[0]),int(argv[1]),int(argv[2]),int(argv[3]),1]
        elif len(argv)==3:
            # time noprint demo_
            args = [str(argv[0]),int(argv[1]),int(argv[2])]
        elif len(argv)==2:
            # time noprint default_demo=1
            args = [str(argv[0]),int(argv[1]),0]
        elif len(argv)==1:
            # time(manual interrupt), allow printing, default_demo=1
            if argv[0]=='time':
                args=[argv[0],0,1]
            # don't time, choose noprint value, default_demo=1
            else:
                args=[None,int(argv[0]),1]
        else:
            # no timing information, allow printing, default_demo=1
            args=[None,0,1]
        main_fetching(args,init_time,logfile)
    except Exception as e:
        writefile(errfile,f"ERROR: {e}\n")
        backtrace = traceback.format_exc()
        writefile(errfile,backtrace + '\n')
        writefile(errfile,f'Ran for {time.time()-init_time:.2f} seconds.\n\n')
        print(f"Error, traceback, or warning generated in {errfile}")
