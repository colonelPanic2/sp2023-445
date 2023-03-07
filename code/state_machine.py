from pystatemachine import *
import gpio
import signal
from auto_control import StateFunctions
from gpio import motors
import time
from sys import platform

class StateLogic(object):
    def __init__(self,control=None):
        self.control = control
        super().__init__()
        # self.transition_wait()
        return
    def function_call(self,function,args):
        try:
            function(args)
        except TimeoutError:
            print("Return to waiting point")
            return -1
    def wait(self,args=None):
        # WAIT logic # 
        # s = self.get_state()
        # if s=='START' or s=='RETURN':
        #     self.transition_wait()
        # print('waiting',self.get_state(),end=' --> ')
        return
    def chase(self,args=None):
        # CHASE logic #
        i=0
        while i<1000000000:
            i+=1
        # print('chasing',self.get_state(),end=' --> ')
        return
    def acquire(self,args=None):
        # ACQUIRE logic #
        # print('acquiring',self.get_state(),end=' --> ')
        return
    def fetch(self,args=None):
        # FETCH logic #
        # print('fetching',self.get_state(),end=' --> ')
        return
    def ret(self,args=None):
        # RETURN logic #
        # print('returning',self.get_state(),end=' --> ')
        return


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
    RETURN = State('Return')
    def __init__(self,controls=None):
        try:
            # NEEDS TESTING ON Pi/Linux
            self.ALRM = signal.SIGALRM
        except:
            # This doesn't actually work. Windows doesn't support SIGALRM
            # without WSL, so this is just to avoid errors. 
            self.ALRM = signal.SIGABRT 
        super().__init__(controls)
    
    def get_state(self):
        return StateInfo.get_current_state(self).name
    def set_state(self,state):
        StateInfo.set_current_state(self,state)
        return
    def signal_handler(self,signum,frame):
        # self.transition_return()
        raise TimeoutError
    # General protocol for starting the next state in the transition functions
    # def call_transition(self,transition_function,args):
    #     transition_function(args)
    #     return 0

    @event(from_states=(START, RETURN), to_state=(WAIT))
    def transition_wait(self,some_variables=None):
        # *Preprocessing logic before performing main task* # 
        return 0

    @event(from_states=(WAIT), to_state=(CHASE))
    def transition_chase(self,some_variables=None):
        # If we stay in the CHASE state for 60 secs, enter RETURN state. (only works on Linux)
        if platform=='linux':
            signal.signal(self.ALRM, self.signal_handler)
            signal.alarm(1)
        # *Preprocessing logic before performing main task* # 
        return 0

    @event(from_states=(CHASE), to_state=(ACQUIRE))
    def transition_acquire(self,some_variables=None):
        # If we stay in the ACQUIRE state for 30 secs, enter RETURN state. (only works on Linux)
        if platform=='linux':
            signal.signal(signal.SIGALRM, self.signal_handler)
            signal.alarm(30)
        # *Preprocessing logic before performing main task* # 
        return 0

    @event(from_states=(ACQUIRE), to_state=(FETCH))
    def transition_fetch(self,some_variables=None):
        # *Preprocessing logic before performing main task* # 
        return 0

    @event(from_states=(CHASE, ACQUIRE, FETCH), to_state=(RETURN))
    def transition_return(self,some_variables=None):
        # *Preprocessing logic before performing main task* # 
        return 0

# def main():
#     controls = None#gpio.motors() 
#     sl = FSM(controls)
#     functions = [sl.transition_wait, sl.transition_chase, sl.transition_acquire,\
#                  sl.transition_fetch,sl.transition_return]
#     for i in range(10):
#         if functions[i%len(functions)](i)==-1:
#             sl.transition_return(i)
#         # print(sl.get_state())
#     return 0

# if __name__ == '__main__':
#     main()
