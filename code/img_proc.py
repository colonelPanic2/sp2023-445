import random
import torch
TL = 0 # Top-left region of camera view
TM = 1 # Top-middle region of camera view
TR = 2 # Top-right region of camera view
BL = 3 # Bottom-left region of camera view
BM = 4 # Bottom-middle region of camera view
BR = 5 # Bottom-right region of camera view
class images:
    def __init__(self):
        # This array will keep track of where the ball is located in the 6 regions
        # Of the camera view. The ball can be in multiple regions at once.
        self.regions= { TL:0, TM:0, TR:0, BL:0, BM:0, BR:0 }
        self.last_regions = list(self.regions.values())
    def update_goal_position(self,goal):
        # NOTE: REPLACE ALL CODE BELOW FOR IMAGE PROCESSING
        image = torch.randint(0,255,(1280,720)) # Get image from camera
        if goal=='ball':
            # NOTE: Replace with the correct criteria for identifying the ball
            GOAL_COLOR = 127
        elif goal=='user':
            # NOTE: Replace with the correct criteria for identifying the user
            GOAL_COLOR = 191
        elif goal=='waitpoint':
            # NOTE: Replace with the correct criteria for identifying the waiting point
            GOAL_COLOR = 255
        margin = 0
        new_image = torch.where(image<=GOAL_COLOR+margin,GOAL_COLOR,0)     # Apply the upper bound to the color
        new_image = torch.where(GOAL_COLOR-margin<=new_image,GOAL_COLOR,0) # Apply the lower bound to the color
        # print(new_image.nonzero().flatten())
        # ball_position>5 is the case in which the ball isn't on the screen   
        goal_positions = random.choices(list(range(7)),k=2) 
        # NOTE: REPLACE ALL CODE ABOVE FOR IMAGE PROCESSING 

        # Only change the last location of the goal if the goal 
        # is currently in the camera view
        region_vals = list(self.regions.values())
        if not (all(pos>5 for pos in goal_positions) or all(pos==0 for pos in region_vals)):
            self.last_regions = region_vals
        # Change the current goal position
        for i in range(6):
            if i not in goal_positions:
                self.regions[i]=0
            else:
                self.regions[i]+=1
        return 0
    # This function shouldn't need to be changed for image processing
    def get_goal_regions(self):
        # If the goal is in the camera view, then find the region(s) where it is present
        if not all(self.regions[i]==0 for i in range(6)):
            return [i for i in range(6) if self.regions[i]>0]
        # Otherwise, get the last known region(s) in which the goal was in the camera view
        return [j for j in range(6) if self.last_regions[j]>0]
        

# Special function for testing the image processing code directly
def iproc_main():
    import time
    iproc = images()
    t0 = time.perf_counter()
    # NOTE: REPLACE CODE BELOW FOR IMAGE PROCESSING
    time.sleep(0.25) # Added for testing worst-case scenarios with the camera. Waits for 0.25s
    # This should be the master function that handles image data
    # and condenses it into an output.
    iproc.update_goal_position('ball')
    # NOTE: REPLACE CODE ABOVE FOR IMAGE PROCESSING
    iproc.get_goal_regions()
    t1 = time.perf_counter()
    dt = round(1000*(t1-t0),2) # total runtime in milliseconds
    if dt>=300:
        print("***WARNING*** IMAGE PROCESSING RUNTIME MUST NOT EXCEED 300ms")
    print("Runtime: {} ms ".format(dt))
    return 0

if __name__=='__main__':
    iproc_main()
