# Luis Notebook

# Table of contents
- [2023-02-14](#2023-02-14---initial-pcb-design)
- [2023-02-26](#2023-02-26---re-evaluating-the-power-subsystem)
- [2023-03-02](#2023-03-02---pcb-redesign-1)
- [2023-03-05](#2023-03-0506---buck-converters-for-power-subsystem)
- [2023-03-06](#2023-03-0506---buck-converters-for-power-subsystem)
- [2023-03-13](#2023-03-13---fetching-subsystem-rough-draft)
- [2023-03-15](#2023-03-15---microcontroller-code-rough-draft)
- [2023-03-29](#2023-03-29---image-processing-update)
- [2023-04-01](#2023-04-01---parallelization)
- [2023-04-04](#2023-04-04---pcb-redesign-2)
- [2023-04-16](#2023-04-16---working-software-demo)

# 2023-02-14 - Initial PCB design

We've set up what is expected to be the base of the final version of the PCB. We still need to decide on the power supply that we're going to use, and how we should connect it to the rest of the design. For now, our best idea for the power subsystem is to connect a high-voltage battery to the design with resistors to control the power supplied to each component.


# 2023-02-26 - Re-evaluating the power subsystem

Due to conflicting research data, we'll have to test our design's motors ourselves. With the data we've acquired beforehand, its hard to know for sure if the car we bought will be powerful enough to move under the weight of the full design. Also, we need to know how much power will be consumed at different weights.

It looks like the motors can be relied upon to handle about 0.8kg with a power supply of 6V-9V, but we need to rethink how we're actually going to connect the power supply to the rest of the design. The motors in particular would cause way too many fluctuations in the current, and a slowly decreasing voltage would make the behavior of the power subsystem even less predictable. Additionally, the design would slow down over time as the battery loses power, making the design inconvenient for long-term use. We have changed the power subsystem to use one power supply for the Pi (5V, 3A, 5Ah), and another for the PCB/motors. The second battery (11.1V, 9A, 5.2Ah) and we're going to use 2 buck converters to keep the voltage at the motors and PCB at about 5V with a maximum total current of about 2A. 
####GET INFORMATION ABOUT FETCHING SUBSYSTEM POWER CONSUMPTION?####
####MAKE SURE TO INCLUDE CALCULATIONS                          ####

# 2023-03-02 - PCB redesign 1
(microcontroller interrupts, new H-bridges, full fetching output to control)

We need to review our PCB to make sure that the control and fetching subsystems can communicate with each other and the ultrasonic sensors asynchronously without using extra resources. Also, we need to establish the mappings of the fetching subsystem's outputs to the control subsystem. 

Our design wasn't making use of the interrupt pins on the microcontroller. We've added an interrupt for the Pi and an interrupt for the ultrasonic sensors. We don't know if the sensor interrupt will be helpful because we don't know how long they will take to respond with data after being triggered. We've decided to keep the interrupt for now as a precaution. The Pi interrupt will be necessary if we want the microcontroller read the Pi input as a byte of data. Using interrupts will also prevent us from using unnecessary resources on polling all of the input pins on each iteration of the main loop for the microcontroller code. The Pi's output will consist of 2 bits per pair of motors, 1 bit to tell the control subsystem whether the design is in manual or auto control mode, and another bit to generate the microcontroller interrupt to read data from the Pi. The Pi's inputs to the microcontroller will be mapped as shown below:

![](Pi_to_microcontroller_pin_mapping.png)

Also, we'll have to use different H-bridges if we want to free up enough pins on the microcontroller to be able to include the Pi inputs and the sensor inputs.

# 2023-03-05/06 - Buck converters for power subsystem

We're testing the power consumption of the motors under weights of up to 1.3kg. We need to know if our new approach with the Pi battery and the PCB/motors battery combined with buck converters will be able to provide a sufficient power supply to move the design and power the PCB components at maximum power consumption for up to 45 minutes. 

It looks like we've underestimated our motors. The car motors can move at a moderate speed while carrying 1.3kg and with a supply voltage of 5V at 0.7A. We expect the pincer motors and the rest of the PCB to consume no more than 1A at any given point in time. So if we convert the supply voltage down to 5V and use 2 buck converters with a current capacity of about 1A each, we whould be able to run the design with maximum power consumption for about (11.1-5)(5.2)/(5)(1.7) = 3.7 hours, where 5 is subtracted from the battery voltage because 5V is the minimum cutoff voltage that can be supplied to the converters.


# 2023-03-13 - Fetching subsystem rough draft

We need to get started on the code base for the fetching subsystem. Since the image processing code is unavailable, we'll also have to implement some way to simulate an input from the image processing code.

The structure for the fetching subsystem has been implemented using a state machine library found online called 'pystatemachine'. The state machine is initialized by defining an object from the 'FSM' class, which then initializes a parent class called 'StateLogic'. The 'FSM' class defines all of state objects and functions called when the conditions for a state transition are satisfied. The 'StateLogic' class defines the functions which dictate the design's behavior in each state. Both of these classes are implemented in state_machine.py, and the 'FSM' class uses the pystatemachine library. All functions directly involved in the handling of the fetching subsystem's output to the control subsystem are implemented in a class called 'control' in gpio.py. In order to run/debug the fetching subsystem, we've implemented functions in img_proc.py that generate a random output in the format of the expected output from the image processing code. Once the image processing code is ready, calls to these functions will be replaced with calls to their counterparts in the image processing code.

# 2023-03-15 - Microcontroller code rough draft

In preparation for the hardware integration, we should have a code base that sets up and implements the interrupt handlers for the Pi and sensor interrupts, and uses this input data to define the necessary outputs to the motors.

A rough draft of the microcontroller code has been implemnted. The input and output pins are all defined as specified on the PCB design document, and logic has been implemented to interpret inputs from the sensors/Pi into commands for the motors. Unfortunately, we won't be able to test this code until the hardware is ready. Also, some research suggests that the delay on the response of the ultrasonic sensors is shorter than we anticipated when we reserved an interrupt pin for the ultrasonic sensors on the microcontroller. It looks like we might not need the sensor interrupt.

# 2023-03-29 - Image processing update

Now that we have the image processing code, we need to update the fetching subsystem to use the new functions instead of the randomized ones. Since we have a program built in to measure the runtimes of the state functions using the randomized functions, it should be easy to measure the average runtimes of each of the state functions using the image processing code once they've replaced the randomized functions.

The image processing code has been implemented into the rough draft, but it looks like we'll have to get rid of the runtime sampling program and re-implement it with the image processing code. Since the tests are being run by us rather than the computer, it takes much longer to get enough samples for each state function in the state machine. Now that the image processing is integrated, we should start focusing on how our code will handle state changes that require the state machine to effectively pause for an unknown amount of time.

# 2023-04-01 - Parallelization

The frame rate of the image processing code is somewhat low. Our goal is to parallelize this part of the code somehow so in order to get a more acceptable framerate without sacrificing too much of the runtime for the fetching subsystem. 

After trying both thread and process-wise parallelization, we have decided that creating the simplest and most effective way to parallelize the image processing code, given our experience and time constraints, would be to simply spawn a second thread that constantly reads the input from the camera and saves it in a queue to be read by the main thread in the state machine. The queue was maintained as a means to ensure that the 2 threads never attempted to access the same data during normal operation. 
####CHECK THE DIFFERENCES IN PERFORMANCE FOR THE PARALLEL APPROACH AND THE REGULAR, SEQUENTIAL APPROACH OF READING FROM THE CAMERA

# 2023-04-04 - PCB redesign 2

(remove ultrasonic sensor interrupt, forward 1 bit of proximity data to the pi, replace a second, redundant trigger for the ultrasonic sensors with an output to the Pi for recording runtime data/determining when to send the next signal from the Pi)

While setting up the code base for the microcontroller, we found that the interrupt for the ultrasonic sensors had no practical value. Also, we found that we could free a pin on the microcontroller if we eliminated a redundant second trigger for the ultrasonic sensors and had one trigger that activated both sensors at once. Our goal is to find out how we should repurpose these two pins on the microcontroller.

We've decided to repurpose both pins as outputs from the microcontroller to the Pi. The first will be used to tell the Pi when the microcontroller is ready to accept a new input from the Pi, and it will also be used to record the approximate runtime of the code in the microcontroller's main loop. The second will be used to tell the Pi when an object is within a certain distance from the sensors. The output will be 1 if something is within range, and 0 else.

# 2023-04-16 - Working software demo

We need to have a user interface that makes it easier for us to test and debug our integrated design. The interface should explain how to use manual control mode, and the user should be able to toggle printing, runtime data collection, whether the design boots in demo mode (shows the camera view on the screen) or not, whether the design boots in manual control mode or not, and which state the FSM (auto mode only) is initialized to through the command line.

We've implemented all of the features described above, along with a means of manually generating the SIGUSR1 and SIGUSR2 signals to partially simulate an input to the Pi from the microcontroller. With this, we should be able to demonstrate full functionality of the fetching subsystem and collect data for validation, even if we are unable to successfully integrate the components of the design.

NOTE: Regarding the partial SIGUSR1 and SIGUSR2 simulation. In the final design, the microcontroller can generate interrupts completely asynchronously. The simulation of these signals via manual input fails to account for this by only raising the signals when certain condition is met within the predefined context of the fetching subsystem's code. Therefore, extra measures may have to be taken to properly handle these signals in the finalized design.


# Example of how to format images and links in *.md files
![](insert_image_here.png)
[insert-link-name-here](https://insert-link-here.com)
