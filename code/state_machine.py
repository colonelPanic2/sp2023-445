from pystatemachine import *
import signal
from sys import platform
from img_proc import images
import random # Temporary means of testing state transitions
import time
class StateLogic(object):
    def __init__(self,control=None):
        self.control = control
        self.img = images()
        super().__init__()
        return
    def function_call(self,function,args=None):
        try:
            return function(args)
        except TimeoutError:
            print("{} timed out. Return to waiting point".format(self.get_state()))
            return -1
    # WAIT logic #
    def wait(self,args=None):
        while self.get_state()=='WAIT': 
            # If the ball has been in the same region(s) of the camera view
            # for some amount of time, then transition to the CHASE state and
            # tell the main loop to execute the "chase()" function.
            self.img.update_goal_position('ball')
            # NOTE: change this later to make the condition check for the number of
            # seconds that the ball has been in a given region in the camera view
            # '2', like the randomized algorithm that generates it, it a placeholder
            # to be replaced when the image processing has been implemented
            if 2 in self.img.regions.values():
                print("\nFinal region data: {}\n".format(list(self.img.regions.values())))
                self.transition_chase()
                return 2
        return -2
    
    # CHASE logic #
    def chase(self,args=None):
        while self.get_state()=='CHASE':
            self.img.update_goal_position('ball')
            positions = self.img.get_goal_regions()
            # Tell the microcontroller the position of the ball
            # relative to the camera view. If the ball has been 
            # reached, then transition to the ACQUIRE state and 
            # tell the main loop to execute the "acquire()" function.
            if self.chase_commands(positions)==3:
                return 3
        return -2
    
    # ACQUIRE logic #
    def acquire(self,args=None):
        while self.get_state()=='ACQUIRE':
            self.img.update_goal_position('ball')
            positions = self.img.get_goal_regions()
            # Tell the microcontroller when the ball is inside of 
            # the pincers and wait for the pincers to close. If 
            # the ball has been acquired, then transition to the 
            # FETCH state and tell the main loop to execute the
            # "fetch()" function. 
            next_state_index = self.acquire_commands(positions)
            if next_state_index!=0:
                return next_state_index
        return -2
    # FETCH logic #
    def fetch(self,args=None):
        while self.get_state()=='FETCH':
            # NOTE: These 2 functions still need to be 
            # defined/implemented in 'img_proc.py'
            self.img.update_goal_position('user')
            positions = self.img.get_goal_regions()
            # Tell the microcontroller the position of the user
            # relative to the camera view. If the user has been 
            # given the acquired ball, then transition to the 
            # RETURN state and tell the main loop to execute the 
            # "ret()" function. Otherwise, if the ball has gone
            # outside of the range of the sensors, then transition
            # to the ACQUIRE state and tell the main loop to execute
            # the "acquire()" function.
            if self.fetch_commands(positions)==5:
                return 5
        return -2
    # RETURN logic #
    def ret(self,args=None):
        while self.get_state()=="RETURN":
            # NOTE: These 2 functions still need to be
            # defined/implemented in 'img_proc.py'
            self.img.update_goal_position('waitpoint')
            positions = self.img.get_goal_regions()
            # Tell the microcontroller the position of the waiting
            # point relative to the camera view. If the waiting point
            # has been reached, then transition to the waiting state
            # and tell the main loop to execute the "wait()" function.
            if self.return_commands(positions)==1:
                return 1
        return -2
    
    def chase_commands(self,positions):
        # No ball was detected in the camera view
        if positions==[]: 
            # The ball may have gone off the left side of the camera view
            if not all(region==0 for region in self.img.last_regions[::3]):
                self.control.right_stop()
                self.control.left_move()
            # The ball may have gone off the right side of the camera view
            elif not all(region==0 for region in self.img.last_regions[2::3]):
                self.control.right_move()
                self.control.left_stop()
            # The ball may have gone behind the camera view, or it might be
            # too far to be detected (this may need extra logic later).
            else:
                self.control.right_move(1)
                self.control.left_move()
        # top-left
        elif 0 in positions:
            self.control.right_stop()
            self.control.left_move()
        # top-middle
        elif 1 in positions:
            self.control.right_move()
            self.control.left_move()
        # top-right
        elif 2 in positions:
            self.control.right_move()
            self.control.left_move()
        # bottom-left
        elif 3 in positions:
            self.control.right_stop()
            self.control.left_move(1)
        # bottom-middle
        elif 4 in positions:
            self.control.right_stop()
            self.control.left_stop()
            print("\nFinal region data: {}\n".format(list(self.img.regions.values())))
            self.transition_acquire()
            return 3
        # bottom-right
        elif 5 in positions:
            self.control.right_move(1)
            self.control.left_stop()
        return 0
    def acquire_commands(self,positions):
        if 4 in positions:
            self.control.right_stop()
            self.control.left_stop()
            # NOTE: I don't know how we're going to confirm that the ball has
            # been acquired successfully, so my temporary solution is to wait 
            # for 2 seconds after telling the microcontroller to close the pincers,
            # and then simply assume that it worked and move on. THIS WILL NEED
            # TO BE ADDRESSED LATER.
            time.sleep(2) 
            print("\nFinal region data: {}\n".format(list(self.img.regions.values())))
            self.transition_fetch()
            return 4
        elif 3 in positions:
            self.control.right_stop()
            self.control.left_move(1)
        elif 5 in positions:
            self.control.right_move(1)
            self.control.left_stop()
        else:
            # If the ball is no longer in the bottom half 
            # of the camera view, then return to chasing. 
            self.control.right_stop()
            self.control.left_stop()
            print("\nFinal region data: {}\n".format(list(self.img.regions.values())))
            self.transition_chase()
            return 2
        return 0
    def fetch_commands(self,positions):
        # NOTE: I don't know how we're planning on setting up the tag for the user,
        # so I don't know how to set up the commands for the fetch protocol. For now,
        # The fetch commands are basically just a copy-paste of the acquire commands.

        # User wasn't detected in the camera view
        if positions==[]: 
            # The user may be off the left side of the camera view
            if not all(region==0 for region in self.img.last_regions[::3]):
                self.control.right_stop()
                self.control.left_move()
            # The user may be off the right side of the camera view
            elif not all(region==0 for region in self.img.last_regions[2::3]):
                self.control.right_move()
                self.control.left_stop()
            # The user may be behind the camera view, or they might be
            # too far to be detected (NOTE: this may need extra logic later).
            else:
                self.control.right_move(1)
                self.control.left_move()
        # top-left
        elif 0 in positions:
            self.control.right_stop()
            self.control.left_move()
        # top-middle
        elif 1 in positions:
            self.control.right_move()
            self.control.left_move()
        # top-right
        elif 2 in positions:
            self.control.right_move()
            self.control.left_move()
        # bottom-left
        elif 3 in positions:
            self.control.right_stop()
            self.control.left_move(1)
        # bottom-middle
        elif 4 in positions:
            self.control.right_stop()
            self.control.left_stop()
            print("\nFinal region data: {}\n".format(list(self.img.regions.values())))
            self.transition_return()
            return 5
        # bottom-right
        elif 5 in positions:
            self.control.right_move(1)
            self.control.left_stop()                
        return 0
    def return_commands(self,positions):
        # NOTE: Since the waiting point flag will be at about the same height as the 
        # ball, it makes sense that the return commands should look similar to the 
        # acquire commands in the final version of the code. 

        # The waiting point wasn't detected in the camera view
        if positions==[]: 
            # The waiting point may be off the left side of the camera view
            if not all(region==0 for region in self.img.last_regions[::3]):
                self.control.right_stop()
                self.control.left_move()
            # The waiting point may be off the right side of the camera view
            elif not all(region==0 for region in self.img.last_regions[2::3]):
                self.control.right_move()
                self.control.left_stop()
            # The waiting point may be behind the camera view, or it may be
            # too far to be detected (NOTE: this may need extra logic later).
            else:
                self.control.right_move(1)
                self.control.left_move()
        # top-left
        elif 0 in positions:
            self.control.right_stop()
            self.control.left_move()
        # top-middle
        elif 1 in positions:
            self.control.right_move()
            self.control.left_move()
        # top-right
        elif 2 in positions:
            self.control.right_move()
            self.control.left_move()
        # bottom-left
        elif 3 in positions:
            self.control.right_stop()
            self.control.left_move(1)
        # bottom-middle
        elif 4 in positions:
            self.control.right_stop()
            self.control.left_stop()
            print("\nFinal region data: {}\n".format(list(self.img.regions.values())))
            self.transition_wait()
            return 1
        # bottom-right
        elif 5 in positions:
            self.control.right_move(1)
            self.control.left_stop()  
        return 0

# RETURN to WAIT:
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
    def __init__(self,controls):
        try:
            # NEEDS TESTING ON Pi
            self.ALRM = signal.SIGALRM
        except:
            # This doesn't actually work. Windows doesn't support SIGALRM
            # without WSL, so this is just to avoid errors. 
            self.ALRM = signal.SIGABRT 
        super().__init__(controls)
    # Define a signal handler for when the CHASE or ACQUIRE states time out
    def signal_handler(self,signum,frame):
        raise TimeoutError
    # Get the name of the current state of the FSM as a string
    def get_state(self):
        return StateInfo.get_current_state(self).name

    # General state transition functions
    @event(from_states=(START, RETURN), to_state=(WAIT))
    def transition_wait(self,some_variables=None):
        # *Other pre-processing logic before changing to next state* # 
        return 0
    @event(from_states=(WAIT,ACQUIRE), to_state=(CHASE))
    def transition_chase(self,some_variables=None):
        # If we stay in the CHASE state for 60 secs, enter RETURN state. (only works on Linux)
        if platform=='linux':
            signal.signal(self.ALRM, self.signal_handler)
            signal.alarm(60)
        # *Other pre-processing logic before changing to next state* # 
        return 0
    @event(from_states=(CHASE), to_state=(ACQUIRE))
    def transition_acquire(self,some_variables=None):
        # If we stay in the ACQUIRE state for 30 secs, enter RETURN state. (only works on Linux)
        if platform=='linux':
            signal.signal(signal.SIGALRM, self.signal_handler)
            signal.alarm(30)
        # *Other pre-processing logic before changing to next state* # 
        return 0
    @event(from_states=(ACQUIRE), to_state=(FETCH))
    def transition_fetch(self,some_variables=None):
        # *Other pre-processing logic before changing to next state* # 
        return 0
    @event(from_states=(CHASE, ACQUIRE, FETCH), to_state=(RETURN))
    def transition_return(self,some_variables=None):
        # *Other pre-processing logic before changing to next state* # 
        return 0


