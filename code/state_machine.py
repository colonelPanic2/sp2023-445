from pystatemachine import *
import gpio
import signal
from auto_control import *

@acts_as_state_machine
class FSM(object):
    WAIT = State('WAIT', initial=True)
    CHASE = State('CHASE')
    ACQUIRE = State('ACQUIRE')
    FETCH = State('FETCH')
    Return = State('Return')

    def signal_handler(self,signum,frame):
        raise Exception("Timed out")

    @event(from_states=(WAIT), to_state=(CHASE))
    def init_chase_ball(self,some_variables=None):
        # If this function runs for longer than 200ms
        signal.signal(signal.SIGALRM, self.signal_handler)
        signal.alarm(60)
        # *Preprocessing logic before performing main task* # 
        try:
            gpio.send_directional_data(some_variables)
        except:
            Exception("back to waiting!")
        return
    @event(from_states=(CHASE), to_state=(ACQUIRE))
    def init_acquire_ball(self,some_variables=None):
        # *Preprocessing logic before performing main task* # 
        return
