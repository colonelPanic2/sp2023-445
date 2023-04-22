import signal,time
from helpers.pystatemachine import *
from helpers.helpers import writefile,time_data

class StateLogic(object):
    def __init__(self):
        super().__init__()
        return
    def function_call(self,function,args=None):
        try:
            return function(args)
        except TimeoutError:
            signal.alarm(0)
            if not self.noprint: 
                writefile(self.logfile,"{} timed out. Return to waiting point\n".format(self.get_state()))
            return -1
    # WAIT logic #
    def wait(self,args=None):
        if self.gettimes is not None and self.start_state!=self.get_state():
            self.transition_chase()
            return 2
        time_data(self.gettimes,'WAIT',1)
        while self.get_state()=='WAIT': 
            if time_data(self.gettimes,'WAIT',2,self.init_time)==-13:
                return -13
            # If the ball has been in the same region(s) of the camera view
            # for some amount of time, then transition to the CHASE state and
            # tell the main loop to execute the "chase()" function.
            timers = self.img.update_goal_position('ball_W',time.time())
            if not all(dt<self.img.goal_timelimits['ball_W'] for dt in timers): # NOTE: software simulation/testing change2 in self.img.regions.values():
                if not self.noprint: 
                    writefile(self.logfile,"{} - Final region data: {}\n".format(self.get_state(),list(self.img.regions.values())))
                for region in range(6):
                    self.img.timers[region]=0
                self.transition_chase()
                return 2
        return -2
    # CHASE logic #
    def chase(self,args=None):
        if self.gettimes is not None and self.start_state!=self.get_state():
            self.transition_acquire()
            return 3
        time_data(args,'CHASE',1)
        while self.get_state()=='CHASE':
            if time_data(args,'CHASE',2,self.init_time)==-13:
                return -13
            timers = self.img.update_goal_position('ball_C',time.time())
            positions = self.img.get_goal_regions()
            # Tell the microcontroller the position of the ball
            # relative to the camera view. If the ball has been 
            # reached, then transition to the ACQUIRE state and 
            # tell the main loop to execute the "acquire()" function.
            if self.chase_commands(positions,timers)==3:
                return 3
        return -2
    # ACQUIRE logic #
    def acquire(self,args=None):
        if self.gettimes is not None and self.start_state!=self.get_state():
            self.transition_fetch()
            return 4
        time_data(args,'ACQUIRE',1)
        while self.get_state()=='ACQUIRE':
            if time_data(args,'ACQUIRE',2,self.init_time)==-13:
                return -13
            timers = self.img.update_goal_position('ball_A',time.time())
            positions = self.img.get_goal_regions()
            # Tell the microcontroller when the ball is inside of 
            # the pincers and wait for the pincers to close. If 
            # the ball has been acquired, then transition to the 
            # FETCH state and tell the main loop to execute the
            # "fetch()" function. 
            next_state_index = self.acquire_commands(positions,timers)
            if next_state_index!=0:
                return next_state_index
        return -2
    # FETCH logic #
    def fetch(self,args=None):
        if self.gettimes is not None and self.start_state!=self.get_state():
            self.transition_return()
            return 5
        time_data(args,'FETCH',1)
        while self.get_state()=='FETCH':
            if time_data(args,'FETCH',2,self.init_time)==-13:
                return -13
            timers = self.img.update_goal_position('user',time.time())
            positions = self.img.get_goal_regions()
            # Tell the microcontroller the position of the user
            # relative to the camera view. If the user has been 
            # given the acquired ball, then transition to the 
            # RETURN state and tell the main loop to execute the 
            # "ret()" function. Otherwise, if the ball has gone
            # outside of the range of the sensors, then transition
            # to the ACQUIRE state and tell the main loop to execute
            # the "acquire()" function.
            if self.fetch_commands(positions,timers)==5:
                return 5
        return -2
    # RETURN logic #
    def ret(self,args=None):
        if self.gettimes is not None and self.start_state!=self.get_state():
            self.transition_wait()
            return 1
        time_data(args,'RETURN',1)
        while self.get_state()=="RETURN":
            if time_data(args,'RETURN',2,self.init_time)==-13:
                return -13
            timers = self.img.update_goal_position('waitpoint',time.time())
            positions = self.img.get_goal_regions()
            # Tell the microcontroller the position of the waiting
            # point relative to the camera view. If the waiting point
            # has been reached, then transition to the WAIT state
            # and tell the main loop to execute the "wait()" function.
            if self.return_commands(positions,timers)==1:
                return 1
        return -2
    # The following 3 functions define the fetching subsystem's output to
    # the control subsytem for the CHASE, ACQUIRE, FETCH, and RETURN states, 
    # respectively. They also decide when to transition between states 
    # (given that the current state hasn't failed yet)
    def chase_commands(self,positions,timers):
        # No ball was detected in the camera view
        if positions==[]: 
            # The ball may have gone off the left side of the camera view
            if not all(region==0 for region in self.img.last_regions[::3]):
                self.control.right_move()
                self.control.left_stop() 
            # The ball may have gone off the right side of the camera view
            elif not all(region==0 for region in self.img.last_regions[2::3]):
                self.control.right_stop()
                self.control.left_move()
            # The ball may have gone behind the camera view, or it might be
            # too far to be detected (this may need extra logic later).
            else:
                self.control.right_move(1)
                self.control.left_move()
        # top-left
        elif 0 in positions:
            self.control.right_move()
            self.control.left_stop()
        # top-middle
        elif 1 in positions:
            self.control.right_move()
            self.control.left_move()
        # top-right
        elif 2 in positions:
            self.control.right_stop()
            self.control.left_move()
        # bottom-left
        elif 3 in positions:
            self.control.right_stop()
            self.control.left_move(1)
        # bottom-middle
        elif 4 in positions:
            if self.control.proximity==1 and not all(dt<self.img.goal_timelimits['ball_C'] for dt in timers):
                self.control.right_stop()
                self.control.left_stop()
                self.control.INT_start_time=time.time()
                #print(self.control.INT_start_time)
                self.control.pi_int()
                if not self.noprint: 
                    writefile(self.logfile,"{} - Final region data: {}\n".format(self.get_state(),list(self.img.regions.values())))             
                self.transition_acquire()
                return 3
            else:
                return 0
        # bottom-right
        elif 5 in positions:
            self.control.right_move(1)
            self.control.left_stop()
        self.control.INT_start_time=time.time()
        #print(self.control.INT_start_time)
        self.control.pi_int()
        return 0
    def acquire_commands(self,positions,timers):
        if 4 in positions:
            if self.control.proximity==1 and not all(dt<self.img.goal_timelimits['ball_A'] for dt in timers):
                self.control.right_stop()
                self.control.left_stop()
                self.control.pincers_move(1)
                self.control.INT_start_time=time.time()
                #print(self.control.INT_start_time)
                self.control.pi_int()
                #time.sleep(2) 
                while not self.control.DONE:
                    pass
                self.control.pincers_stop()
                self.control.INT_start_time=time.time()
                #print(self.control.INT_start_time)
                self.control.pi_int()
                if not self.noprint:
                    writefile(self.logfile,"{} - Final region data: {}\n".format(self.get_state(),list(self.img.regions.values())))             
                self.transition_fetch()
                return 4
            else:
                return 0
        # bottom-left
        elif 3 in positions:
            self.control.right_stop()
            self.control.left_move(1)
        # bottom-right
        elif 5 in positions:
            self.control.right_move(1)
            self.control.left_stop()
        else:
            # If the ball is no longer in the bottom half 
            # of the camera view, then return to chasing. 
            self.control.right_stop()
            self.control.left_stop()
            self.control.INT_start_time=time.time()
            #print(self.control.INT_start_time)
            self.control.pi_int()
            if not self.noprint: 
                writefile(self.logfile,"{} - Final region data: {}\n".format(self.get_state(),list(self.img.regions.values())))             
            self.transition_chase()
            return 2
        self.control.INT_start_time=time.time()
        #print(self.control.INT_start_time)
        self.control.pi_int()
        return 0
    def fetch_commands(self,positions,timers):
        # NOTE: I don't know how we're planning on setting up the tag for the user,
        # so I don't know how to set up the commands for the fetch protocol. For now,
        # The fetch commands are basically just a copy-paste of the acquire commands.
        # User wasn't detected in the camera view
        if positions==[]: 
            # The user may be off the left side of the camera view
            if not all(region==0 for region in self.img.last_regions[::3]):
                # self.control.right_move()
                self.control.left_move(1)
                # self.control.left_stop()
                self.control.right_stop()
            # The user may be off the right side of the camera view
            elif not all(region==0 for region in self.img.last_regions[2::3]):
                # self.control.right_stop()
                self.control.left_stop()
                # self.control.left_move()
                self.control.right_move(1)
            # The user may be behind the camera view, or they might be
            # too far to be detected (NOTE: this may need extra logic later).
            else:
                # self.control.right_move(1)
                self.control.left_move()
                # self.control.left_move()
                self.control.right_move(1)
        # top-left
        elif 0 in positions:
            # self.control.right_move()
            self.control.left_move(1)
            # self.control.left_stop()
            self.control.right_stop()
        # top-middle
        elif 1 in positions:
            # self.control.right_move()
            self.control.left_move(1)
            # self.control.left_move()
            self.control.right_move(1)
        # top-right
        elif 2 in positions:
            # self.control.right_stop()
            self.control.left_stop()
            # self.control.left_move()
            self.control.right_move(1)
        # bottom-left
        elif 3 in positions:
            # self.control.right_stop()
            self.control.left_stop()
            # self.control.left_move(1)
            self.control.right_move()
        # bottom-middle
        elif 4 in positions:
            if self.control.proximity==1 and not all(dt<self.img.goal_timelimits['user'] for dt in timers):
                self.control.right_stop()
                self.control.left_stop()
                self.control.pincers_move()
                self.control.INT_start_time=time.time()
                #print(self.control.INT_start_time)
                self.control.pi_int()
                while not self.control.DONE:
                    pass
                self.control.pincers_stop()
                self.control.INT_start_time=time.time()
                #print(self.control.INT_start_time)
                self.control.pi_int()
                if not self.noprint: 
                    writefile(self.logfile,"{} - Final region data: {}\n".format(self.get_state(),list(self.img.regions.values())))             
                self.transition_return()
                return 5
            return 0
        # bottom-right
        elif 5 in positions:
            # self.control.right_move(1)
            self.control.left_move()
            # self.control.left_stop()   
            self.control.right_stop()
        self.control.INT_start_time=time.time()
        #print(self.control.INT_start_time)
        self.control.pi_int()             
        return 0
    def return_commands(self,positions,timers):
        # NOTE: Since the waiting point flag will be at about the same height as the 
        # ball, it makes sense that the return commands should look similar to the 
        # acquire commands in the final version of the code. 
        # The waiting point wasn't detected in the camera view
        if positions==[]: 
            # The waiting point may be off the left side of the camera view
            if not all(region==0 for region in self.img.last_regions[::3]):
                # self.control.right_move()
                self.control.left_move(1)
                # self.control.left_stop()
                self.control.right_stop()
            # The waiting point may be off the right side of the camera view
            elif not all(region==0 for region in self.img.last_regions[2::3]):
                # self.control.right_stop()
                self.control.left_stop()
                # self.control.left_move()
                self.control.right_move(1)
            # The waiting point may be behind the camera view, or it may be
            # too far to be detected (NOTE: this may need extra logic later).
            else:
                # self.control.right_move(1)
                self.control.left_move()
                # self.control.left_move()
                self.control.right_move(1)
        # top-left
        elif 0 in positions:
            # self.control.right_move()
            self.control.left_move(1)
            # self.control.left_stop()
            self.control.right_stop()
        # top-middle
        elif 1 in positions:
            # self.control.right_move()
            self.control.left_move(1)
            # self.control.left_move()
            self.control.right_move(1)
        # top-right
        elif 2 in positions:
            # self.control.right_stop()
            self.control.left_stop()
            # self.control.left_move()
            self.control.right_move(1)
        # bottom-left
        elif 3 in positions:
            # self.control.right_stop()
            self.control.left_move()
            # self.control.left_move(1)
            self.control.right_move()
        # bottom-middle
        elif 4 in positions:
            if self.control.proximity==1 and not all(dt<self.img.goal_timelimits['waitpoint'] for dt in timers):
                print(timers)
                self.control.right_stop()
                self.control.left_stop()
                self.control.INT_start_time=time.time()
                #print(self.control.INT_start_time)
                self.control.pi_int()
                if not self.noprint: 
                    writefile(self.logfile,"{} - Final region data: {}\n".format(self.get_state(),list(self.img.regions.values())))             
                self.transition_wait()
                return 1
            else:
                return 0
        # bottom-right
        elif 5 in positions:
            # self.control.right_move(1)
            self.control.left_move()
            # self.control.left_stop()  
            self.control.right_stop()
        self.control.INT_start_time=time.time()
        #print(self.control.INT_start_time)
        self.control.pi_int()
        return 0
    def manual_off(self):
        self.control.manual=0
        self.img.manual=0
        self.img.camera_.manual=0
        self.manual=0

# RETURN if...
# -  CHASE   for 60 seconds
# -  ACQUIRE for 30 seconds
# -  FETCH   successful
@acts_as_state_machine
class FSM(StateLogic):
    START = State('START',initial=True)
    WAIT = State('WAIT')
    CHASE = State('CHASE')
    ACQUIRE = State('ACQUIRE')
    FETCH = State('FETCH')
    RETURN = State('RETURN')
    def __init__(self,control,camera,gettimes,noprint,demo,manual,init_time,logfile,start_state):
        signal.signal(signal.SIGALRM,self.signal_handler)
        self.control = control
        self.img = camera
        self.gettimes=gettimes
        self.noprint = noprint
        self.demo = demo
        self.manual = manual
        self.init_time = init_time
        self.logfile = logfile
        self.start_state = start_state
        if start_state=='WAIT':
            self.img.goal_timelimits['ball'] = 5
        else:
            self.img.goal_timelimits['ball'] = 0.005
        self.manual_off() # This object is can only be initialized in auto control mode.
        self.control.INT_start_time = 0
        self.control.proximity = 0
        self.control.DONE = False
        super().__init__()
    # Get the name of the current state of the FSM as a string
    def get_state(self):
        return StateInfo.get_current_state(self).name
    # If the timer expires in CHASE or ACQUIRE, then catch the resulting
    # SIGALRM signal and raise a TimeoutError which will be caught in the 
    # 'function_call' function defined in StateLogic.
    def signal_handler(self,signum,frame):
        raise TimeoutError
    # General state transition functions
    @event(from_states=(START, RETURN), to_state=(WAIT))
    def transition_wait(self,some_variables=None):
        # *Other pre-processing logic before changing to next state* # 
        signal.alarm(0)
        self.control.proximity = 0
        self.control.DONE = False
        return 0
    @event(from_states=(START,WAIT,ACQUIRE), to_state=(CHASE))
    def transition_chase(self,some_variables=None):
        # If we stay in the CHASE state for 60 secs, enter RETURN state. (only works on Linux)
        signal.alarm(0)
        self.control.proximity = 0
        self.control.DONE = False
        signal.alarm(5) # NOTE: Remember to change back to 60!
        # *Other pre-processing logic before changing to next state* # 
        return 0
    @event(from_states=(START,CHASE), to_state=(ACQUIRE))
    def transition_acquire(self,some_variables=None):
        # If we stay in the ACQUIRE state for 30 secs, enter RETURN state. (only works on Linux)
        signal.alarm(0)
        self.control.proximity = 0
        self.control.DONE = False
        signal.signal(signal.SIGALRM,self.signal_handler)
        signal.alarm(5) # NOTE: Remember to change back to 30!
        # *Other pre-processing logic before changing to next state* # 
        return 0
    @event(from_states=(START,ACQUIRE), to_state=(FETCH))
    def transition_fetch(self,some_variables=None):
        # *Other pre-processing logic before changing to next state* # 
        signal.alarm(0)
        self.control.proximity = 0
        self.control.DONE = False
        return 0
    @event(from_states=(START,CHASE, ACQUIRE, FETCH), to_state=(RETURN))
    def transition_return(self,some_variables=None):
        # *Other pre-processing logic before changing to next state* # 
        signal.alarm(0)
        self.control.proximity = 0
        self.control.DONE = False
        return 0
