import sys,traceback,signal,time
from helpers.helpers import writefile,logdata,time_data,timedata_files
from camera import camera
from gpio import control
from state_machine import FSM
# In case of a SIGINT, allow the camera thread to release the 
# camera and finish. Then raise a KeyboardInterrupt to exit
# gracefully
def signal_handler(signum,frame):
    global cam
    signal.alarm(0)
    cam.destroy()
    # The program should never be able to reach this
    # call to 'exit(0)'. It is just a precaution.
    exit(0)
# Use this for files/directories whose changes you want to ignore (after having added said files/directories to the .gitignore file in the main directory):
# git rm -r --cached directory_name
# NOTE: UNTESTED MICROCONTROLLER COMMS CODE
def microcontroller_signal_handler(signum,frame):
    global ctrl 
    if signum==10: # SIGUSR1 (I think): record response time of the microcontroller
        time_data([ctrl.gettimes,ctrl.INT_start_time,time.time()],'fsm.get_state()',4)
        ctrl.DONE = True
        print(ctrl.DONE,'\n')
    elif signum==12: # SIGUSR2 (I think): Update the proximity parameter for the fetching subsystem
        ctrl.proximity = int(not ctrl.proximity)
        print(ctrl.proximity,'\n')
    signal.signal(signum,microcontroller_signal_handler)
    return

def main(gettimes,noprint,demo,manual,start_state):
    global init_time
    global errfile
    init_time,logfile,errfile = logdata()
    # Declare the global variables that will be used by our 
    # signal handlers for SIGINT, SIGUSR1, and SIGUSR2.
    global cam
    global ctrl
    # Initialize the camera, control, and fsm objects.
    cam  = camera(               noprint,demo,manual,0,logfile)
    # Set up the signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    ctrl = control(     gettimes,noprint,demo,manual,0,logfile) 
    if manual==1:
        ctrl.init_manual_control(cam)
    # NOTE: UNTESTED MICROCONTROLLER COMMS CODE
    signal.signal(signal.SIGUSR1, microcontroller_signal_handler)
    signal.signal(signal.SIGUSR2, microcontroller_signal_handler)
    fsm  = FSM(ctrl,cam,gettimes,noprint,demo,manual,0,logfile,start_state)


    # Make a list of state functions in their intended order of 
    # execution. The output of each state function will be used 
    # as an index into this list.
    states = ['WAIT','CHASE','ACQUIRE','FETCH','RETURN']
    transitions = [fsm.transition_wait, fsm.transition_chase,fsm.transition_acquire,\
                   fsm.transition_fetch,fsm.transition_return]
    functions = [fsm.wait,fsm.chase,fsm.acquire,fsm.fetch,fsm.ret]
    init_time = time.time()
    cam.init_time=init_time
    ctrl.init_time=init_time
    fsm.init_time=init_time
    # Before entering the main loop, enter the WAIT state and run the
    # wait() function to get the first index into the functions list.
    transitions[states.index(fsm.start_state)]() # fsm.transition_wait()
    if not noprint:
        writefile(logfile,fsm.get_state()+' ')
    next_function_index = fsm.function_call(functions[states.index(fsm.start_state)],gettimes) # fsm.wait()
    # MAIN LOOP
    while True: 
        if not noprint:
            writefile(logfile,fsm.get_state()+' ')
        # If the function index is the index + 1 of one of the 5 state
        # functions, then the previous function did not fail.
        if next_function_index>=1:
            next_function_index = fsm.function_call(functions[next_function_index-1],gettimes)
        # Otherwise, the previous state function failed due to a timeout. This should mean 
        # that the previous state was either CHASE or ACQUIRE, as these are the only 2 states 
        # with a time limit.
        elif next_function_index!=-13:
            if not noprint:
                writefile(logfile,f"ERROR: Failed in {fsm.get_state()}. Attempting to transition to RETURN from {fsm.get_state()}...\n")
            time_data(gettimes,fsm.get_state(),2)
            fsm.transition_return()
            if not noprint:
                writefile(logfile,fsm.get_state()+' ')
            next_function_index = fsm.ret()  
        else:
            if gettimes is not None:
                print(f"\nDone collecting runtime data for {fsm.start_state}")
            fsm.img.camera_.destroy()

        

def init_fetching(args):
    gettimes,noprint,demo,manual,start_state=args[:5]
    # Run main with the processed command line arguments as well as the time
    # of initialization and the log file.
    try:
        main(gettimes,noprint,demo,manual,start_state)
    # If there is a Keyboard interrupt, assume that it was raised 
    # by the program's response to user input and that the program 
    # exited normally
    except KeyboardInterrupt:
        # If we were collecting time data for that run, then write
        # it to the .csv file in the 'timedata' directory.
        signal.alarm(0)
        timedata_files(gettimes,init_time)
        print("\nDone.\nTerminated by user input.")
    return 0

def parse_args():
    global init_time
    global errfile
    init_time = time.time()
    errfile = 'init-err.txt'
    try:        
        # time    - ("time" if recording timedata)   Choose whether time data is recorded 
        # noprint - (0 if allowed, 1 else)           Choose whether printing/logging during runtime is allowed 
        # demo    - (0 if no demo, 1 if demo)        Choose whether we boot in to demo mode or not 
        # manual  - (0 if auto,    1 if manual)      Choose whether the design boots with auto/manual control 
        # start_state - (the state to be unit tested) Choose the name (all caps) of the initial FSM state (default is WAIT)
        argv = sys.argv[1:]
        # DEFAULT: No timedata, allow printing, boot in demo mode, 
        # boot with manual controls, start the FSM in the WAIT state
        if len(argv)==0:
            # argv = []
            args = [None,0,1,1,'WAIT']
        elif len(argv)==5:
            ### Unit test the state specified in the 5th argument ###
            # argv = [time noprint demo manual start_state]
            args = [str(argv[0]),int(argv[1]),int(argv[2]),int(argv[3]),str(argv[4])]
        elif len(argv)==4:
            ### Unit test the state specified in the 4th argument ###
            # argv = [time noprint manual start_state]
            args = [str(argv[0]),int(argv[1]),1,int(argv[2]),str(argv[3])]
        elif len(argv)==3:
            if argv[0]=='time':
                ### Unit test the state specified in the 3rd argument ###
                # argv = [time noprint start_state]
                args = [str(argv[0]),int(argv[1]),0,0,str(argv[2])] 
            else:
                # argv = [noprint demo manual]
                args = [None,int(argv[0]),int(argv[1]),int(argv[2]),'WAIT']
        elif len(argv)==2:
            if argv[0]=='time':
                ### Unit test the state specified in the 2nd argument ###
                # argv = [time start_state]
                args = [str(argv[0]),0,1,0,str(argv[1])]
            else:
                # argv = [time=None noprint default_demo=1 manual WAIT]
                args = [None,int(argv[0]),1,int(argv[1]),'WAIT']
        elif len(argv)==1:
            if argv[0]=='time':
                ### Unit test the WAIT state ###
                # argv = [time]
                args = [str(argv[0]),0,0,1,'WAIT']
            elif len(argv[0])>1:
                ### start in default mode at a given state (not START)
                # argv = [<state>]
                args = [None,0,1,0,argv[0]]
            else:
                # argv = [demo]
                args = [None,0,int(argv[0]),0,'WAIT']
        init_fetching(args)
    except Exception as e:
        # If an unexpected Exception has occured, then write an error log
        # to the err.txt file generated for the date and time when the 
        # exception occured.
        current_time = time.strftime("%Y-%m-%d_%H.%M.%S", time.localtime())[11:]
        writefile(errfile,f"Time: {current_time}\nERROR: {e}\n")
        backtrace = traceback.format_exc()
        writefile(errfile,backtrace + '\n')
        writefile(errfile,f'Ran for {time.time()-init_time:.2f} seconds.\n\n')
        print(f"Error, traceback, or warning generated in {errfile}")





if __name__ == '__main__':
    parse_args()
