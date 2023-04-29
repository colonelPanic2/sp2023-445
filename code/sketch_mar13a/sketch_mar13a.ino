#include <Servo.h>

#define MIN_DIST_CM 5
#define MAX_DIST_CM 50 

//required initialization for pincer motors
Servo servo1;
Servo servo2;

#define ECHO0 PIN_PB0
#define TRIG  PIN_PB1
#define ECHO1 PIN_PB2
// PB3-PB5 are for MOSI, MISO, and SCK

#define LMOTORS_IN0  PIN_PB6 // XTAL1/PB6
#define LMOTORS_IN1  PIN_PB7 // XTAL2/PB7
#define LMOTORS_OUT0 PIN_PC0 // PC0
#define LMOTORS_OUT1 PIN_PC1 // PC1
#define RMOTORS_OUT0 PIN_PC2 // PC2
#define RMOTORS_OUT1 PIN_PC3 // PC3
#define PINCER_OUT0  PIN_PC4 // PC4
#define PINCER_OUT1  PIN_PC5 // PC5
// PC6 is reset - used only for programming the mega
#define RMOTORS_IN0  PIN_PD0 // PD0
#define RMOTORS_IN1  PIN_PD1 // PD1
#define PI_INT       PIN_PD2 // PD2
#define CTRL_ACK     PIN_PD3 // PD3
#define CTRL         PIN_PD4 // PD4
#define PINCER_ON    PIN_PD5 // PD5
#define PINCER_DIR   PIN_PD6 // PD6
#define Prox_Data    PIN_PD7 // PD7

//variables for random functions
long duration;
int distance;
int midCheck;
int counter = 0;

/* The input from the pi formatted as follows:
       0           1            2            3            4           5         6
 (LMOTORS_IN0)(LMOTORS_IN1)(RMOTORS_IN0)(RMOTORS_IN1)(PINCERS_ON)(PINCERS_DIR)(CTRL)
*/
uint8_t pi_input[7] = {0,0,0,0,0,0,0};

unsigned int sensor_distances[2] = {65535,65535}; 

//read inputs from sensors
void sensor_data() {
  // sequence to activate ultrasonic sensors
  digitalWrite(TRIG,LOW);
  delayMicroseconds(2) ;
  digitalWrite(TRIG,HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG,LOW);

  // pulseIn gets the travel time of the sound wave (to the surface and back)
  sensor_distances[0] = pulseIn(ECHO0,HIGH)/58.2; // 29.1(cm/us)*2 = 58.2
  // sensor_distances[1] = pulseIn(ECHO1,HIGH)/58.2;
  //distracne might be: distance = duration * 0.034 / 2;

}

//read Pi inputs
void read_pi() {
  pi_input[0] = digitalRead(LMOTORS_IN0);
  pi_input[1] = digitalRead(LMOTORS_IN1); // 00: stop, 01: forward, 10: stop, 11: back
  pi_input[2] = digitalRead(RMOTORS_IN0);
  pi_input[3] = digitalRead(RMOTORS_IN1); // 00: stop, 01: forward, 10: stop, 11: back
  pi_input[4] = digitalRead(PINCER_ON  );
  pi_input[5] = digitalRead(PINCER_DIR ); // 00: stop, 01: stop,    10: open, 11: close
  pi_input[6] = digitalRead(CTRL       );
  if(pi_input[6]==0){
    check_left();
    delay(100);
    check_right();
  }
  
  // digitalWrite(CTRL_ACK, HIGH);
  // delayMicroseconds(5);
  // digitalWrite(CTRL_ACK, 0);
}

//function used to see how left wheel should move
void check_left() {
  // make motors brake if pi[0] = 0 and pi[1] = 0
  if((pi_input[0] == 0) && (pi_input[1] == 0)){
    digitalWrite(LMOTORS_OUT0, HIGH);
    digitalWrite(LMOTORS_OUT1, HIGH);
  }
  // make motors move forward if pi[0] = 0 and pi[1] = 1
  else if((pi_input[0] == 0) && (pi_input[1] == 1)){
    digitalWrite(LMOTORS_OUT0, HIGH);
    digitalWrite(LMOTORS_OUT1, 0);
  }
  // make motors coast if pi[0] = 1 and pi[1] = 0
  else if((pi_input[0] == 1) && (pi_input[1] == 0)){
    digitalWrite(LMOTORS_OUT0, 0);
    digitalWrite(LMOTORS_OUT1, 0);
  }
  // make motors reverse if pi[0] = 1 and pi[1] = 1
  else{
    digitalWrite(LMOTORS_OUT0, 0);
    digitalWrite(LMOTORS_OUT1, HIGH);
  }
}
//function used to see how right wheel should move
void check_right() {
  // make motors brake if pi[0] = 0 and pi[1] = 0
  if((pi_input[2] == 0) && (pi_input[3] == 0)){
    digitalWrite(RMOTORS_OUT0, HIGH);
    digitalWrite(RMOTORS_OUT1, HIGH);
  }
  // make motors move forward if pi[0] = 0 and pi[1] = 1
  else if((pi_input[2] == 0) && (pi_input[3] == 1)){
    digitalWrite(RMOTORS_OUT0, HIGH);
    digitalWrite(RMOTORS_OUT1, 0);
  }
  // make motors coast if pi[0] = 1 and pi[1] = 0
  else if((pi_input[2] == 1) && (pi_input[3] == 0)){
    digitalWrite(RMOTORS_OUT0, 0);
    digitalWrite(RMOTORS_OUT1, 0);
  }
  // make motors reverse if pi[0] = 1 and pi[1] = 1
  else{
    digitalWrite(RMOTORS_OUT0, 0);
    digitalWrite(RMOTORS_OUT1, HIGH);
  }
}


void setup() {
  pinMode(ECHO0, INPUT); // pin 8
  pinMode(TRIG, OUTPUT); // pin 9
  pinMode(ECHO0, INPUT); // pin 10

  pinMode(LMOTORS_IN0,INPUT); // pin 11
  pinMode(LMOTORS_IN1,INPUT); // pin 12
  pinMode(LMOTORS_OUT0,OUTPUT); // left motor out 0
  pinMode(LMOTORS_OUT1,OUTPUT); // left motor out 1
  pinMode(RMOTORS_OUT0,OUTPUT); // right motor out 0
  pinMode(RMOTORS_OUT1,OUTPUT); // right motor out 1
  servo1.attach(PINCER_OUT0); // left pincer
  servo2.attach(PINCER_OUT1); // right pincer
  // servo1.writeMicroseconds(2500);
  // servo2.write(10);

  // don't need pinMode for reset pin      
  pinMode(RMOTORS_IN0,INPUT);
  pinMode(RMOTORS_IN1,INPUT);
  // pinMode(PI_INT, INPUT);
  pinMode(PI_INT,INPUT_PULLUP); // pin 2
  attachInterrupt(digitalPinToInterrupt(PI_INT),read_pi,RISING);
  // attachInterrupt(digitalPinToInterrupt(PI_INT),read_pi,CHANGE);
  pinMode(CTRL_ACK,OUTPUT); // pin 3
  pinMode(CTRL,INPUT); // pin 4
  pinMode(PINCER_ON,INPUT); // pin 5  
  pinMode(PINCER_DIR,INPUT); // pin 6 
  pinMode(Prox_Data,OUTPUT); // pin 7

  Serial.begin(9600); // Starts the serial communication
}

//MICROCONTROLLER LOOP
void loop() {
  // read_pi();
  // if(counter<4){
  //   counter++;
  // }
  // else{
  //   sensor_data();
  //   counter = 0;
  // }
  // if(sensor_distances[0]<=15){
  //   digitalWrite(Prox_Data, HIGH);
  // }
  // else{
  //   digitalWrite(Prox_Data, 0);
  // }
  digitalWrite(Prox_Data, HIGH);
  delayMicroseconds(5);
  digitalWrite(Prox_Data, 0);
  /* Auto control mode. The inputs from the pi and the sensors are data (not instructions)
     used by the microcontroller to decide how to control the motors. */
  if (pi_input[6] == 0){
    // Pincer H-bridge controls
    if (pi_input[4] == 1){
      //make sure pincers are on
      if(!(servo1.attached())){
        servo1.attach(PINCER_OUT0);
        servo2.attach(PINCER_OUT1);
      }
      /* If acquiring the ball, then close the pincers. 
         If fetching the ball, then open the pincers. */
      if(!pi_input[5]){
        int curA = servo2.read();
        if(curA != 35){
          servo1.write(145);
          servo2.write(35);
          delay(100);
        }

        // check_left();
        // delay(100);
        // check_right();
      }
      // else if ((pi_input[5]==1) && (sensor_distances[0]>15)){
      else if (pi_input[5]==1){
        // sensor_data();
        // while(sensor_distances[0]<=15){
        //   sensor_data();
        // }        
        servo1.writeMicroseconds(2500);
        servo2.write(10);
        delay(100);
        //make all the wheels brake
        digitalWrite(LMOTORS_OUT0, HIGH);
        digitalWrite(LMOTORS_OUT1, HIGH);
        digitalWrite(RMOTORS_OUT0, HIGH);
        digitalWrite(RMOTORS_OUT1, HIGH);
        servo1.detach();
        servo2.detach();
        pi_input[4] = 0;
        pi_input[5] = 0;
      }
      //if we want to close the pincers, keep driving till ball is within range to catch
      // else{
      //   check_left();
      //   check_right();
      // }
    } 
    else {
      // make sure pincers are off
      if (servo1.attached()){
        servo1.detach();
        servo2.detach();
      }

    }
  }

  /* Manual control mode. The sensor input isn't used, and the microcontroller interprets the
     pi input as instructions to be interpreted and relayed to the control subsystem. */
  else if (pi_input[6] == 1) {
    // if (pi_input[3]==1) {
    //   check_right();
    // } else {
    //   digitalWrite(RMOTORS_OUT0,0);
    //   digitalWrite(RMOTORS_OUT1,0);
    // }
    // // Left motors control translation
    // if (pi_input[1]==1) {
    //   check_left();
    // } else {
    //   digitalWrite(LMOTORS_OUT0,0);
    //   digitalWrite(LMOTORS_OUT1,0);
    // }
    // // Right motors control translation
    // // if (pi_input[3]==1) {
    // //   check_right();
    // // } else {
    // //   digitalWrite(RMOTORS_OUT0,0);
    // //   digitalWrite(RMOTORS_OUT1,0);
    // // }
    // // Pincer motors control translation
    // // NOTE: The direction for the pincer motors might be reversed
    // if (pi_input[4]==1) {

    //   if(!(servo1.attached())){
    //     servo1.attach(PINCER_OUT0);
    //     servo2.attach(PINCER_OUT1);
    //   }
    //   /* If acquiring the ball, then close the pincers. 
    //      If fetching the ball, then open the pincers. */
    //   if(!pi_input[5]){
    //     int curA = servo2.read();
    //     if(curA != 35){
    //       servo1.write(145);
    //       servo2.write(35);
    //       // delay(100);
    //     }
    //   }
    //   // else if ((pi_input[5]==1) && (sensor_distances[0]>15)){
    //   else if (pi_input[5]==1){      
    //     servo1.writeMicroseconds(2500);
    //     servo2.write(10);
    //     digitalWrite(LMOTORS_OUT0, HIGH);
    //     digitalWrite(LMOTORS_OUT1, HIGH);
    //     digitalWrite(RMOTORS_OUT0, HIGH);
    //     digitalWrite(RMOTORS_OUT1, HIGH);
    //     // servo1.detach();
    //     // servo2.detach();
    //   }
    // } 
    // // else {
    // //     servo1.detach();
    // //     servo2.detach();
    // // }
    if (pi_input[1]==1) {
      digitalWrite(LMOTORS_OUT0,!pi_input[0]);
      digitalWrite(LMOTORS_OUT1, pi_input[0]);
    } else {
      digitalWrite(LMOTORS_OUT0,LOW);
      digitalWrite(LMOTORS_OUT1,LOW);
    }
    // Right motors control translation
    if (pi_input[3]==1) {
      digitalWrite(RMOTORS_OUT0,!pi_input[2]);
      digitalWrite(RMOTORS_OUT1, pi_input[2]);
    } else {
      digitalWrite(RMOTORS_OUT0,LOW);
      digitalWrite(RMOTORS_OUT1,LOW);
    }
    // Pincer motors control translation
    // NOTE: The direction for the pincer motors might be reversed
    // if (pi_input[4]==1) {
    //   digitalWrite(PINCER_OUT0, !pi_input[5]);
    //   digitalWrite(PINCER_OUT1, pi_input[5]);
    // } else {
    //   digitalWrite(PINCER_OUT0, LOW);
    //   digitalWrite(PINCER_OUT1, LOW);
    // }
  }
  delay(100);
  digitalWrite(CTRL_ACK, HIGH);
  delayMicroseconds(5);
  digitalWrite(CTRL_ACK, 0);
}