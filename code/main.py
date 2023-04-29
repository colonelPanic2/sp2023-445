import sys,traceback,signal,time
from helpers.helpers import writefile,logdata,time_data,timedata_files
from camera import camera
from gpio import control
from state_machine import FSM
def control_switch_handler(signum,frame):
    signal.alarm(0)
    global fsm
    fsm.control_switch()
def microcontroller_CTRL_ACK_handler(signum,frame): # SIGUSR1
    # signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGUSR1, signal.SIGUSR2})
    signal.signal(signal.SIGUSR2,signal.SIG_IGN)
    print("END\n")
    time_data('time','',7)
    global fsm
    global ctrl
    if fsm is not None:
        control_ = fsm.control
        state = fsm.get_state()
    else:
        control_ = ctrl
        state = 'NO_FSM'
    if control_.gettimes is not None:
        t1 = time.time()
        time_data([control_.gettimes,control_.INT_start_time,t1],state,4)
        control_.INT_start_time=0
    time_data('time','loop_end',6)
    signal.signal(signal.SIGUSR2,microcontroller_PROX_handler)
    # signal.pthread_sigmask(signal.SIG_UNBLOCK,{signal.SIGUSR1, signal.SIGUSR2})
def microcontroller_PROX_handler(signum,frame): # SIGUSR2
    # signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGUSR1,signal.SIGUSR2})
    signal.signal(signal.SIGUSR2,signal.SIG_IGN)
    print("START",end=' ')
    time_data('time','loop_init',6)
    signal.signal(signal.SIGUSR2,microcontroller_PROX_handler)
    # signal.pthread_sigmask(signal.SIG_UNBLOCK,{signal.SIGUSR1})
def main(gettimes,noprint,demo,manual,start_state,num_samples):
    global init_time
    global errfile
    init_time,logfile,errfile = logdata()
    # If gettimes=='time', then set up for runtime data collection
    # for each of the state function loops
    print(logfile)
    time_data(gettimes,'',0,noprint=noprint,logfile=logfile,num_samples=num_samples)
    # Declare the global variables that will be used by our 
    # signal handlers for SIGINT, SIGUSR1, and SIGUSR2.
    global fsm
    fsm = None
    global ctrl
    # Initialize the camera, control, and fsm objects.
    cam  = camera(               noprint,demo,manual,0,logfile)
    # signal.signal(signal.SIGUSR2,signal.SIG_IGN)
    signal.signal(signal.SIGUSR1,microcontroller_CTRL_ACK_handler)
    signal.signal(signal.SIGUSR2,microcontroller_PROX_handler)
    ctrl = control(     gettimes,noprint,demo,manual,0,logfile,num_samples) 

    # If we were told to start the program in manual mode, then 
    # do it. Note that the FSM object won't be initialized until 
    # manual mode is exited.
    if manual==1:
        ctrl.init_manual_control(cam)
    fsm  = FSM(ctrl,cam,gettimes,noprint,demo,manual,0,logfile,start_state,ACK_HANDLER=microcontroller_CTRL_ACK_handler,PROX_HANDLER=microcontroller_PROX_handler)
    signal.signal(signal.SIGQUIT, control_switch_handler)

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
    global ctrl
    gettimes,noprint,demo,manual,start_state=args[:5]
    n_samples=None
    if len(args)==6:
        n_samples=args[5]
    # Run main with the processed command line arguments as well as the time
    # of initialization and the log file.
    try:
        main(gettimes,noprint,demo,manual,start_state,n_samples)
    # If there is a Keyboard interrupt, assume that it was raised 
    # by the program's response to user input and that the program 
    # exited normally
    except KeyboardInterrupt:
        # If we were collecting time data for that run, then write
        # it to the .csv file in the 'timedata' directory.
        signal.alarm(0)
        try:
            ctrl.pincers_move(1)
            ctrl.pi_int()
            time.sleep(0.5)
            ctrl.stop_all()
        except:
            print("Couldn't stop the motors (init_fetching)")
        timedata_files(gettimes,init_time)
        print("\nDone.\nTerminated by user input.")
    return 0

def parse_args():
    signal.alarm(0)
    global init_time
    global errfile
    global ctrl
    init_time = time.time()
    errfile = 'init-err.txt'
    try:        
        # time    - ("time" if recording timedata)   Choose whether time data is recorded 
        # noprint - (0 if allowed, 1 else)           Choose whether printing/logging during runtime is allowed 
        # demo    - (0 if no demo, 1 if demo)        Choose whether we boot in to demo mode or not 
        # manual  - (0 if auto,    1 if manual)      Choose whether the design boots with auto/manual control 
        # start_state - (the state to be unit tested) Choose the name (all caps) of the initial FSM state (default is WAIT)
        # n_samples - (runtime sampling only)         Choose the number of iterations to be sampled from the initial state's state function
        argv = sys.argv[1:]
        # DEFAULT: No timedata, allow printing, boot in demo mode, 
        # boot with manual controls, start the FSM in the WAIT state
        if len(argv)==0:
            # argv = []
            args = [None,0,1,1,'WAIT']
        elif len(argv)==6:
            args = [str(argv[0]),int(argv[1]),int(argv[2]),int(argv[3]),str(argv[4]),int(argv[5])]
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
        try:
            ctrl.pincers_move(1)
            ctrl.pi_int()
            time.sleep(0.5)
            ctrl.stop_all()
        except:
            print("Couldn't stop the motors (parse_args)")
        current_time = time.strftime("%Y-%m-%d_%H.%M.%S", time.localtime())[11:]
        writefile(errfile,f"Time: {current_time}\nERROR: {e}\n")
        backtrace = traceback.format_exc()
        writefile(errfile,backtrace + '\n')
        writefile(errfile,f'Ran for {time.time()-init_time:.2f} seconds.\n\n')
        print(f"Error, traceback, or warning generated in {errfile}")





if __name__ == '__main__':
    parse_args()
