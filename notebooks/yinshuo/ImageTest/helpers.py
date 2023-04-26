import subprocess,time,signal,sys,shlex,os
from timedata.plots import process_data
import numpy as np
platform=sys.platform
# Class for remote testing of the manual controls. Mimics
# the behavior of the RPi.GPIO library functions. Don't
# try to implement any of these functions. They are only
# placeholders for the actual versions that we will be 
# using from the RPi.GPIO library.
class remote_gpio:
    def __init__(self,pins=[17,27,12,13,4,25,5,6,16,26,18,24, 20,21]):
        self.pins=pins
        self.pinout={}
        self.OUT = 'OUT'
        self.BCM = 'BCM'
        self.BOARD = 'BOARD' # *****
        self.mode = None
        self.warnings=None
        self.IN = 'IN'
        self.PUD_DOWN = 'PUD_DOWN'
        self.PUD_UP = 'PUD_UP'
        self.RISING = 'STANDING HEEEEEEERE I REALIIIIIIIIIZE YOU WERE JUST LIKE ME TRYING TO MAKE HISTORYYYYYYYYY~'
        return
    def setmode(self,mode):
        self.mode=mode
    def setwarnings(self,val):
        self.warnings=val
    def setup(self,pin,direction,pull_up_down=None):
        self.pinout[pin]=0
        return
    def output(self,pin,val):
        self.pinout[pin]=val
    def input(self,pin):
        return self.pinout[pin]
    # NOTE: UNTESTED MICROCONTROLLER COMMS CODE
    def add_event_detect(self,pin,condition,callback=None,bouncetime=None):
        # This function should set up an event listener that runs the 'callback' function
        # when the given condition is met on the given pin.
        return
io = remote_gpio()
def decode_signal(signal):
    signal_map={'L':{'00':'LS','01':'LF','11':'LB',  '10':'CS0'},\
                'R':{'00':'RS','01':'RF','11':'RB',  '10':'CS1'},\
                'P':{'00':'PS','10':'PO','11':'PC',  '01':'CS2'}}
    return f"{signal_map['L'][signal[0:2]]}-{signal_map['R'][signal[2:4]]}-{signal_map['P'][signal[4:6]]} "
def teardown_timeout_handler(signum,frame):
    current_time = time.localtime()
    current_date = time.strftime("%Y-%m-%d", current_time)[5:]
    current_time = time.strftime("%Y-%m-%d_%H.%M.%S", current_time)[11:]
    # backtrace = traceback.format_exc()
    err_message = "ERROR: TIMEOUT IN 'camera.destroy()' WHILE TRYING TO RELEASE\nTHE CAMERA OR JOIN THE CAMERA THREAD WITH THE MAIN THREAD.\n\nAttempting processicide..."
    output = f"\n\n{current_time}\n{err_message}"
    writefile(f'logs/{current_date}/err.txt',output)
    print(f'{err_message}')
    os.kill(os.getpid(), signal.SIGKILL)
# Write the input string to the end of the file with the given name. 
def writefile(fname,content):
    dirs = ls()
    if 'init-err.txt' not in dirs:
        subprocess.run(shlex.split("touch init-err.txt"))
    with open(fname,'a') as f:
        f.write(content)
# Calculate the index corresponding to the region of the image with the given dimensions
# in which the pixel with the given column and row is located.
def map_to_block_index(col_row,dims=(1080,1920)):
    col_blocks = dims[1]//3
    row_blocks = dims[0]//2
    region_index = (col_row[0]//col_blocks) + 3*(col_row[1]>=row_blocks)
    return region_index
# 18 SEGMENTS
# # Calculate the index corresponding to the region of the image with the given dimensions
# # in which the pixel with the given column and row is located.
# def map_to_block_index(col_row,dims=(1080,1920)):
#     col_blocks = dims[1]//9
#     row_blocks = dims[0]//2
#     region_index = (col_row[0]//col_blocks) + 9*(col_row[1]>=row_blocks)
#     return region_index
# Get a list of all files/subdirectories in the passed in directory.
# *** Doesn't seem to work with '..' directory.
def ls(dir=None):
    if dir==None:
        dirs = str(subprocess.check_output(shlex.split(["dir","ls"][int(platform=='linux')])))[2:-1].split("\\n")[:-1]
    else:
        dirs = str(subprocess.check_output(shlex.split(["dir "+dir,"ls "+dir][int(platform=='linux')])))[2:-1].split("\\n")[:-1]
    return dirs
# Clear the terminal
def clear():
    clear_command = shlex.split(['cls','clear'][int(platform=='linux')])
    if platform=='linux':
        subprocess.run(clear_command)
    else:
        subprocess.run(clear_command,shell=True)
# Creates an error and a logging file. Returns the paths to each file as strings
# along withe the time of creation.
def logdata():
    current_time = time.localtime()
    current_date = time.strftime("%Y-%m-%d", current_time)[5:]
    current_time = time.strftime("%Y-%m-%d_%H.%M.%S", current_time)[11:]
    dirs = ls('logs')
    if current_date not in dirs:
        print(dirs)
        subprocess.run(shlex.split(f'mkdir logs/{current_date}'))
    logs = ls(f"logs/{current_date}")
    if f'{current_time}.txt' not in logs:
        subprocess.run(shlex.split(f"touch logs/{current_date}/{current_time}.txt"))
    if 'err.txt' not in logs:
        subprocess.run(shlex.split(f'touch logs/{current_date}/err.txt'))
    logfile = f"logs/{current_date}/{current_time}.txt"
    errfile = f"logs/{current_date}/err.txt"
    init_time = time.time()
    return (init_time,logfile,errfile)
# Keep track of the runtime data for the fetching subsystem. 
# (unusable with the current code)
def time_data(args,state,step,t0=0,noprint=0,logfile=None,num_samples=None):
    global T0_SET
    global T0
    global T1
    global no_print
    global log_file
    global time_data_dict
    global microcontroller_time_data_list
    global n_samples
    if args=='time':
        if step==0:
            T0_SET = 0
            T0 = 0
            T1 = 0
            time_data_dict={'WAIT':[],'CHASE':[],'ACQUIRE':[],'FETCH':[],'RETURN':[]}
            microcontroller_time_data_list=[]
            no_print=noprint
            log_file = logfile
            n_samples = num_samples
        elif step==1:
            T0_SET = 0
        elif step==2:
            T1 = time.perf_counter()
            if T0_SET==1:
                time_data_dict[state].append(round(1000*(T1-T0),2))
            T0=time.perf_counter()
            T0_SET = 1
            if n_samples is not None and len(time_data_dict[state])>n_samples:
                return -13
        elif step==3:
            for state,runtimes in list(time_data_dict.items()):
                # TODO: ENCOUNTERED AN ERROR IN WHICH THE FIRST ENTRY IN THE TIMEDATA
                # IS OFTEN DISPROPORTIONATELY LARGER THAN THE REST OF THE RUNTIME
                # DATA. THE MODIFICATIONS BELOW ARE AN ATTEMPT AT A TEMPORARY SOLUTION
                if len(runtimes)==1:
                    runtimes=[]
                elif len(runtimes)>1:
                    runtimes=runtimes[1:]
                time_data_dict[state] = (round(np.mean(np.array(runtimes)),2),len(time_data_dict[state])-int(len(time_data_dict[state])>1))
            return time_data_dict
        elif step==5:
            return microcontroller_time_data_list
    elif step == 4 and args[0] is not None and str(args[0])=='time' and args[1]!=0:
        _, INT_start_time, INT_end_time = args
        microcontroller_time_data_list.append(round((INT_end_time-INT_start_time)*1000,2))

    return 0
# If we were collecting time data for a complete run of the program
# then write the data to the .csv file in the 'timedata' directory.
def timedata_files(gettimes,init_time):
    if gettimes is not None and gettimes=='time':
        dirs = ls()
        if "timedata" not in dirs:
            subprocess.run(shlex.split("mkdir timedata"))
        dirs = ls('timedata')
        if "timedata.csv" not in dirs:
            subprocess.run(shlex.split("touch timedata/timedata.csv"))
        time_data_dict                 = time_data(gettimes,'',3)
        print("\n -------- RUNTIME DATA ACQUIRED --------")
        for state,runtime_loopnum in list(time_data_dict.items()):
            if runtime_loopnum[1]==0:
                data_content_csv=f"{state},{0},{0}\n"
            else:
                data_content_csv=f"{state},{runtime_loopnum[1]},{runtime_loopnum[0]}\n"
            writefile('timedata/timedata.csv',data_content_csv)
        # number of times "main" was called, runtime of call to main
        writefile('timedata/timedata.csv',f"{1},{round(time.time()-init_time,2)}\n")
        microcontroller_time_data_list = time_data(gettimes,'',5)
        process_data(microcontroller_time_data_list)
