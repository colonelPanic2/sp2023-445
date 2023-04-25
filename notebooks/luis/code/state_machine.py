import signal,time
from helpers.pystatemachine import *
from helpers.helpers import writefile,time_data,decode_signal

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
                writefile(self.logfile,"\n{} timed out. Return to waiting point\n\n".format(self.get_state()))
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
                    writefile(self.logfile,"\n{} - Final region data: {}\n".format(self.get_state(),list(self.img.regions.values())))
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
            dist = self.control.distance_front()
            # sTell the microcontroller the position of the ball
            # relative to the camera view. If the ball has been 
            # reached, then transition to the ACQUIRE state and 
            # tell the main loop to execute the "acquire()" function.
            if self.chase_commands(positions,timers,dist)==3:
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
            dist = self.control.distance_front()
            # Tell the microcontroller when the ball is inside of 
            # the pincers and wait for the pincers to close. If 
            # the ball has been acquired, then transition to the 
            # FETCH state and tell the main loop to execute the
            # "fetch()" function. 
            next_state_index = self.acquire_commands(positions,timers,dist)
            if next_state_index!=0:
                self.img.last_regions = [0 for r in range(18)]
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
            dist = self.control.distance_back()
            # Tell the microcontroller the position of the user
            # relative to the camera view. If the user has been 
            # given the acquired ball, then transition to the 
            # RETURN state and tell the main loop to execute the 
            # "ret()" function. Otherwise, if the ball has gone
            # outside of the range of the sensors, then transition
            # to the ACQUIRE state and tell the main loop to execute
            # the "acquire()" function.
            if self.fetch_commands(positions,timers,dist)==5:
                self.img.last_regions = [0 for r in range(18)]
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
            dist = self.control.distance_back()
            # Tell the microcontroller the position of the waiting
            # point relative to the camera view. If the waiting point
            # has been reached, then transition to the WAIT state
            # and tell the main loop to execute the "wait()" function.
            if self.return_commands(positions,timers,dist)==1:
                self.img.last_regions = [0 for r in range(18)]
                return 1
        return -2
    # The following 4 functions define the fetching subsystem's output to
    # the control subsystem for the CHASE, ACQUIRE, FETCH, and RETURN states, 
    # respectively. They also decide when to transition between states 
    # (given that the current state hasn't failed yet)
    def chase_commands(self,positions,timers,dist):
        # Ball wasn't detected in the camera view
        if positions==[]: 
            last_regions = self.img.last_regions
            # The ball may have gone off the left side of the camera view or was not detected by the image processing
            if not all(region==0 for region in last_regions[0::9]+last_regions[1:9]+last_regions[2:9]):
                self.control.right_move()
                self.control.left_stop() 
            # The ball may have gone off the right side of the camera view or was not detected by the image 
            elif not all(region==0 for region in last_regions[6::9]+last_regions[7::9]+last_regions[8::9]):
                self.control.right_stop()
                self.control.left_move()
            # The ball may have gone above the top of the camera view or was not detected by the image processing
            elif not all(region==0 for region in last_regions[3::9]+last_regions[4::9]+last_regions[5::9]):
                self.control.right_move()
                self.control.left_move()
            #TODO: CHASE - establish logic for the case where there is no ball in the frame and there is 
            # no prior ball position (should be impossible)
            else:
                writefile(self.logfile,"CHASE - 'IMPOSSIBLE' CASE REACHED\n")
                self.control.right_stop()
                self.control.left_stop()
        # top-left
        elif not all(pos>2 for pos in positions):
            self.control.right_move()
            self.control.left_stop()
        # top-middle
        elif not all(pos>5 for pos in positions):
            self.control.right_move()
            self.control.left_move()
        # top-right
        elif not all(pos>8 for pos in positions):
            self.control.right_stop()
            self.control.left_move()
        # bottom-left
        elif not all(pos>11 for pos in positions):
            self.control.right_stop()
            self.control.left_move(1)
        # bottom-middle-left
        elif 12 in positions:
            self.control.right_move()
            self.control.left_stop()
        # bottom-middle-middle
        elif 13 in positions:
            #TODO: CHASE - Adjust the transition case based on field testing
            if not all(dt<self.img.goal_timelimits['ball_C'] for dt in timers):
                self.control.right_stop()
                self.control.left_stop()
                self.control.pi_int()
                if not self.noprint: 
                    writefile(self.logfile,"{} - Final region data: {}\n".format(self.get_state(),list(self.img.regions.values())))             
                self.transition_acquire()
                return 3
            elif dist>self.dist_threshold:
                self.control.right_move()
                self.control.left_move()
            else:
                self.control.right_move(1)
                self.control.left_move(1)
        # bottom-middle-right
        elif 14 in positions:
            self.control.right_stop()
            self.control.left_move()
        # bottom-right
        else:
            self.control.right_move(1)
            self.control.left_stop()
        # if not self.noprint:
        #     writefile(self.logfile,f"{decode_signal(self.control.readall())}  ")
        print(f'{self.get_state()}: {decode_signal(self.control.readall())}')
        self.control.pi_int()
        #time.sleep(1)
        return 0
    def acquire_commands(self,positions,timers,dist):
        # Ball wasn't detected in the camera view
        if positions==[]: 
            last_regions = self.img.last_regions
            # The ball may have gone off the left side of the camera view or was not detected by the image processing
            if not all(region==0 for region in last_regions[0::9]+last_regions[1:9]+last_regions[2:9]):
                self.control.right_move()
                self.control.left_stop() 
            # The ball may have gone off the right side of the camera view or was not detected by the image processing
            elif not all(region==0 for region in last_regions[6::9]+last_regions[7::9]+last_regions[8::9]):
                self.control.right_stop()
                self.control.left_move()
            # The ball may have gone above the camera view or was not detected by the image processing
            elif not all(region==0 for region in last_regions[3::9]+last_regions[4::9]+last_regions[5::9]):
                self.control.right_stop()
                self.control.left_move()
            #TODO: ACQUIRE - establish logic for the case where there is no ball in the frame and there is no prior
            # ball position (should be impossible)
            else:
                writefile(self.logfile,"ACQUIRE - 'IMPOSSIBLE' CASE REACHED\n")
                self.control.right_stop()
                self.control.left_stop()
        # top-left
        elif not all(pos>2 for pos in positions):
            self.control.right_move()
            self.control.left_stop()
        # top-middle
        elif not all(pos>5 for pos in positions):
            self.control.right_move()
            self.control.left_move()
        # top-right
        elif not all(pos>8 for pos in positions):
            self.control.right_stop()
            self.control.left_move()
        # bottom-left
        elif not all(pos>11 for pos in positions):
            self.control.right_stop()
            self.control.left_move(1)
        # bottom-middle-left
        elif 12 in positions:
            if not self.control.flag_sent:
                self.control.send_flag()
            self.control.right_move()
            self.control.left_stop()
        # bottom-middle-middle
        elif 13 in positions:
            #TODO: ACQUIRE - Adjust the transition case based on field testing
            if self.control.proximity==1 and not all(dt<self.img.goal_timelimits['ball_A'] for dt in timers):
                self.control.pincers_move(1)
                self.control.pi_int()
                self.control.right_stop()
                self.control.left_stop()
                self.control.pi_int()
                time.sleep(0.5)
                self.control.pincers_stop()
                self.control.pi_int()
                if not self.noprint:
                    writefile(self.logfile,"\n{} - Final region data: {}\n".format(self.get_state(),list(self.img.regions.values())))             
                self.transition_fetch()
                return 4
            if not self.control.flag_sent:
                self.control.send_flag()
            self.control.right_move()
            self.control.left_move()
        # bottom-middle-left
        elif 14 in positions:
            if not self.control.flag_sent:
                self.control.send_flag()
            self.control.right_stop()
            self.control.left_move()
        # bottom-right
        else:
            self.control.right_move(1)
            self.control.left_stop()
        print(f"{self.get_state()}: {decode_signal(self.control.readall())}")
        self.control.pi_int()
        #time.sleep(1)
        return 0
    def fetch_commands(self,positions,timers,dist):
        # User wasn't detected in the camera view
        if positions==[]: 
            last_regions = self.img.last_regions
            # The user may be off the left side of the camera view or was not detected by the image processing
            if not all(region==0 for region in last_regions[0::9]+last_regions[1:9]+last_regions[2:9]):
                self.control.left_move(1)
                self.control.right_stop()
            # The user may be off the right side of the camera view or was not detected by the image processing
            elif not all(region==0 for region in last_regions[6::9]+last_regions[7::9]+last_regions[8::9]):
                self.control.left_stop()
                self.control.right_move(1)
            # The user may be above the camera view or was not detected by the image processing
            # NOTE: IDEA - add a proximity condition to avoid crashes due to blind driving and 
            # still allow the fetching subsystem to account for error in the image processing code
            elif not all(region==0 for region in last_regions[3::9]+last_regions[4::9]+last_regions[5::9]): 
                self.control.right_move(1)
                self.control.left_move(1)
            #TODO: FETCH - establish logic for the case where there is no user in the frame and there is
            # no prior user position
            else:
                # Protocol to look for the user
                self.control.left_move()
                # self.control.right_move(1)
                self.control.right_stop()
                self.control.pi_int()
                time.sleep(0.5)
                self.control.left_stop()
                self.control.pi_int()
                return 0
        # top-left
        elif not all(pos>2 for pos in positions):
            self.control.left_move(1)
            self.control.right_stop()
        # top-middle
        elif not all(pos>5 for pos in positions):
            self.control.left_move(1)
            self.control.right_move(1)
        # top-right
        elif not all(pos>8 for pos in positions):
            self.control.left_stop()
            self.control.right_move(1)
        # bottom-left
        elif not all(pos>11 for pos in positions):
            self.control.left_stop()
            self.control.right_move()
        # bottom-middle-left
        elif 12 in positions:
            self.control.left_move(1)
            self.control.right_stop()
        # bottom-middle-middle
        elif 13 in positions:
            #TODO: FETCH - Adjust the transition case based on field testing
            if dist<self.dist_threshold and not all(dt<self.img.goal_timelimits['user'] for dt in timers):
                self.control.pincers_move()
                self.control.pi_int()
                self.control.right_stop()
                self.control.left_stop()
                self.control.pi_int()
                # while not self.control.DONE:
                #     pass
                # self.control.DONE = False
                time.sleep(0.5)
                self.control.pincers_stop()
                self.control.pi_int()
                if not self.noprint: 
                    writefile(self.logfile,"\n{} - Final region data: {}\n".format(self.get_state(),list(self.img.regions.values())))             
                self.transition_return()
                return 5
            elif dist>self.dist_threshold:
                self.control.right_move(1)
                self.control.left_move(1)
            else:
                self.control.right_move()
                self.control.left_move()
        # bottom-middle-right
        elif 14 in positions:
            self.control.left_stop()
            self.control.right_move(1)
        # bottom-right
        else:
            self.control.left_stop()
            self.control.right_move(1)
        print(f"{self.get_state()}: {decode_signal(self.control.readall())}")
        self.control.pi_int()             
        #time.sleep(1)
        return 0
    def return_commands(self,positions,timers,dist):
        if positions==[]: 
            last_regions = self.img.last_regions
            # The waitpoint may be off the left side of the camera view or was not detected by the image processing
            if not all(region==0 for region in last_regions[0::9]+last_regions[1:9]+last_regions[2:9]):
                self.control.left_move(1)
                self.control.right_stop()
            # The waitpoint may be off the right side of the camera view or was not detected by the image processing
            elif not all(region==0 for region in last_regions[6::9]+last_regions[7::9]+last_regions[8::9]):
                self.control.left_stop()
                self.control.right_move(1)
            # The waitpoint may be above the camera view or was not detected by the image processing
            elif not all(region==0 for region in last_regions[3::9]+last_regions[4::9]+last_regions[5::9]):
                self.control.left_move(1)
                self.control.right_move(1)
            #TODO: RETURN - establish logic for the case where there is no waitpoint in the frame and there is
            # no prior waitpoint position
            else:
                # Protocol to look for the waiting point
                self.control.left_stop()
                # self.control.right_move(1)
                self.control.right_move()
                self.control.pi_int()
                time.sleep(0.5)
                self.control.right_stop()
                self.control.pi_int()
                return 0
        # top-left
        elif not all(pos>2 for pos in positions):
            self.control.left_move(1)
            self.control.right_stop()
        # top-middle
        elif not all(pos>5 for pos in positions):
            self.control.left_move(1)
            self.control.right_move(1)
        # top-right
        elif not all(pos>8 for pos in positions):
            self.control.left_stop()
            self.control.right_move(1)
        # bottom-left
        elif not all(pos>11 for pos in positions):
            self.control.left_move()
            self.control.right_move()
        # bottom-middle-left
        elif 12 in positions:
            self.control.left_move(1)
            self.control.right_stop()
        # bottom-middle-middle
        elif 13 in positions:
            #TODO: RETURN - Adjust the transition case based on field testing
            if dist<self.dist_threshold and not all(dt<self.img.goal_timelimits['waitpoint'] for dt in timers):
                self.control.right_stop()
                self.control.left_stop()
                self.control.pi_int()
                if not self.noprint: 
                    writefile(self.logfile,"\n{} - Final region data: {}\n".format(self.get_state(),list(self.img.regions.values())))             
                self.transition_wait()
                return 1
            elif dist>self.dist_threshold:
                self.control.right_move(1)
                self.control.left_move(1)
            else:
                self.control.right_move()
                self.control.left_move()
        # bottom-middle-right
        elif 14 in positions:
            self.control.left_stop()
            self.control.right_move(1)
        # bottom-right
        else:
            self.control.left_stop()
            self.control.right_move(1)
        print(f"{self.get_state()}: {decode_signal(self.control.readall())}")
        self.control.pi_int()
        #time.sleep(1)
        return 0
    def set_manual(self,mode_num):
        self.control.manual=mode_num
        self.img.manual=mode_num
        self.img.camera_.manual=mode_num
        self.manual=mode_num
    def control_switch(self):
        self.control.stop_all()
        self.set_manual(int(not self.manual))
        if self.manual==1:
            self.control.init_manual_control(self.img)
            self.set_manual(0)
        else:
            self.control.exit_()
        print("\nRe-entering auto control mode...\n")
        return 0

# RETURN if...
# -  CHASE   for 60 seconds
# -  ACQUIRE for 45 seconds
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
        self.set_manual(0) # This object can only be initialized in auto control mode.
        self.control.INT_start_time = 0
        self.control.proximity = 0
        self.dist_threshold = 50
        self.control.DONE = False
        self.control.pincers_move(0)
        self.control.pi_int()
        self.control.stop_all()
        super().__init__()
    def set_manual(self,mode_num):
        self.control.manual=mode_num
        self.img.manual=mode_num
        self.img.camera_.manual=mode_num
        self.manual=mode_num
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
        signal.alarm(0)
        if self.img.camera_.index != 0:
            self.img.camera_.camswitch()
        self.control.DONE = False
        self.control.proximity=0
        return 0
    @event(from_states=(START,WAIT), to_state=(CHASE))
    def transition_chase(self,some_variables=None):
        # If we stay in the CHASE state for 60 secs, enter RETURN state. (only works on Linux)
        signal.alarm(0)
        self.control.DONE = False
        self.control.proximity=0
        signal.alarm(3) # Change back to 60
        return 0
    @event(from_states=(START,CHASE), to_state=(ACQUIRE))
    def transition_acquire(self,some_variables=None):
        # If we stay in the ACQUIRE state for 30 secs, enter RETURN state. (only works on Linux)
        signal.alarm(0)
        self.control.DONE = False
        signal.signal(signal.SIGALRM,self.signal_handler)
        # self.control.communication_start()
        signal.alarm(3) # Change back to 45
        return 0
    @event(from_states=(START,ACQUIRE), to_state=(FETCH))
    def transition_fetch(self,some_variables=None):
        signal.alarm(0)
        if self.img.camera_.index != 1:
            self.img.camera_.camswitch()
        self.control.DONE = False
        self.control.proximity = 0
        return 0
    @event(from_states=(START,CHASE, ACQUIRE, FETCH), to_state=(RETURN))
    def transition_return(self,some_variables=None):
        signal.alarm(0)
        if self.img.camera_.index != 1:
            self.img.camera_.camswitch()
        self.control.DONE = False
        self.control.proximity=0
        return 0
