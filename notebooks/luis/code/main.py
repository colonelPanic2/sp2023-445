from gpio import motors
import state_machine
from state_machine import *
from sys import platform
def main():
    # 'manual = 0' tests the FSM, 'manual = 1' tests the manual controls
    # When testing on the Pi, remove the "platform=='win32' condition"
    # The win32 condition is there because I couldn't make tkinter work
    # with WSL.
    controls = motors(manual=(1 & (platform=='win32'))) 
    fsm = FSM(controls)
    transitions = [fsm.transition_wait, fsm.transition_chase, fsm.transition_acquire,\
                 fsm.transition_fetch,fsm.transition_return]
    functions = [fsm.wait,fsm.chase,fsm.acquire,fsm.fetch,fsm.ret]
    fsm.transition_wait()
    print(fsm.get_state(),end=' ')
    next_function_index = fsm.wait()
    # This is a temporary test to run through the state transitions and 
    # functions. This is not how our transitions or function calls will
    # be handled in the final draft.
    while 1:        
        print(fsm.get_state(),end=' ')
        if next_function_index>=1:
            next_function_index = fsm.function_call(functions[next_function_index-1])
        else:
            print("ERROR: Failed to complete task")
            fsm.ret()    
            return 0

if __name__ == '__main__':
    main()
