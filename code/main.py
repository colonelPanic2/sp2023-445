from gpio import motors
import state_machine
from state_machine import *
from sys import platform
def main():
    # 'manual = 0' tests the FSM, 'manual = 1' tests the manual controls
    # When testing on the Pi, remove the "platform=='win32' condition"
    controls = motors(manual=(1 & (platform=='win32'))) 
    sl = FSM(controls)
    transitions = [sl.transition_wait, sl.transition_chase, sl.transition_acquire,\
                 sl.transition_fetch,sl.transition_return]
    functions = [sl.wait,sl.chase,sl.acquire,sl.fetch,sl.ret]
    for i in range(10):
        transitions[i%len(transitions)](i)
        print(sl.get_state(),end=' ')
        if functions[i%len(functions)](i)==-1:
            sl.transition_return(i)
    return 0

if __name__ == '__main__':
    main()
