import random
import torch,time
from camera import camera
TL = 0 # Top-left region of camera view
TM = 1 # Top-middle region of camera view
TR = 2 # Top-right region of camera view
BL = 3 # Bottom-left region of camera view
BM = 4 # Bottom-middle region of camera view
BR = 5 # Bottom-right region of camera view

T = ['TL','TM','TR','BL','BM','BR']
def map_to_block_index(col_row,dims=(720,1278)):
    col_blocks = dims[1]//3
    row_blocks = dims[0]//2
    region_index = (col_row[0]//col_blocks) + 3*(col_row[1]>=row_blocks)
    return region_index
class images:
    def __init__(self):
        # This array will keep track of where the ball is located in the 6 regions
        # Of the camera view. The ball can be in multiple regions at once.
        self.regions= { TL:0, TM:0, TR:0, BL:0, BM:0, BR:0 }
        self.last_regions = list(self.regions.values())
        self.cam = camera()
        self.cam.start_read()
        self.goal_timelimits = {'ball':5,'user':2,'waitpoint':2}
        self.timer = 0
    def update_goal_position(self,goal,t0=None):
        # NOTE: REPLACE ALL CODE BELOW FOR IMAGE PROCESSING
        position_xy,image = self.cam.getimage() #torch.randint(0,255,(1280,720)) # Get image from camera
        if position_xy is not None:
            image = torch.from_numpy(image)
            # Find the region(s) in which the ball was located, if it was
            # in the frame NOTE: need to update this to include all regions
            # that the ball is in, not just the center of the ball
            region_index = map_to_block_index(position_xy,image.shape)
            goal_positions = [region_index]
        else:
            goal_positions = [0] # The goal is not in the image
            
        # # NOTE: Saving this part for non-hardware simulation/testing
        # # ball_position>5 is the case in which the ball isn't on the screen   
        # goal_positions = random.choices(list(range(7)),k=2) 
        
        # Only change the last location of the goal if the goal 
        # is currently in the camera view
        if not (all(pos==0 for pos in goal_positions)):# or all(pos>5 for pos in goal_positions)):
            region_vals = list(self.regions.values())
            self.last_regions = region_vals
        # Change the current goal position
        if t0 is None:
            # If we only want the position of the goal without timing data,
            # then update the positions
            for i in range(6):
                if i in goal_positions:
                    self.regions[i]+= 1
                else:
                    self.regions[i]=0
        else:
            # We need to be able to check the amount of time that the goal has 
            # been in the given locations
            t1 = time.time()
            for i in range(6):
                if i in goal_positions and t1-t0>=self.goal_timelimits[goal]:
                    self.regions[i]+= 1
                    self.timer += t1-t0
                else:
                    self.regions[i]=0
                    self.timer=0
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
