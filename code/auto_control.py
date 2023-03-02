from gpio import motors

class StateFunctions:
    def __init__(self,cur_state_function=None):
        self.functions = [self.wait, self.chase, self.acquire, self.fetch, self.ret]
        self.cur_state_function=None
        if cur_state_function is None:
            self.cur_state_function=self.wait
        else:
            for function in self.functions:
                if cur_state_function == function.__name__:
                    self.cur_state_function=function
                    break
        if self.cur_state_function is None:
            Exception("Invalid function name: {}".format(cur_state_function))
        return
    
    def wait(self,new_image):
        # 1. Look for a ball below the user-defined, horizontal lower threshold of the image. 
        # 2. If no ball is detected in said region, return a value such that the caller knows this.
        # 3. Otherwise, determine which regions on the screen are occupied by the ball
        # 4. If the ball is in the lower region for more than 5 seconds, trigger a state change in 
        #    the FSM. 
        return
    def chase(self):
        return
    
    def acquire(self):
        return
    
    def fetch(self):
        return
    
    def ret(self):
        return
