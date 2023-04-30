#include <Servo.h>

#define MIN_DIST_CM 5
#define MAX_DIST_CM 50 

//required initialization for pincer motors
Servo servo1;
Servo servo2;

#define ECHO0 PIN_PB0
#define TRIG  PIN_PB1
// #define ECHO1 PIN_PB2
#define ECHO1 PIN_PD1
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
// #define RMOTORS_IN1  PIN_PD1 // PD1
#define RMOTORS_IN1  PIN_PD7

#define PI_INT       PIN_PD2 // PD2
#define CTRL_ACK     PIN_PD3 // PD3
// #define CTRL_ACK     PIN_PD1

#define CTRL         PIN_PD4 // PD4
#define PINCER_ON    PIN_PD5 // PD5
#define PINCER_DIR   PIN_PD6 // PD6
// #define Prox_Data    PIN_PD7 // PD7
// #define Prox_Data    PIN_PD1
// #define Prox_Data    PIN_PD3
#define Prox_Data    PIN_PB2

//variables for random functions
int counter = 0;
int openCnt = 0;
int proxCounter = 0;
int lCount = 0;
int hCount = 0;

unsigned int dist_vector[20] = {0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0};
// unsigned int dist_vector[10] = {0,0,0,0,0,0,0,0,0,0};
int vec_index = 0;
unsigned int mini = 2000;
unsigned int maxi = 0;
int secCode = 0;
int left0 = 0;
int left1 = 0;
int right0 = 0;
int right1 = 0;

int wait_INT = 0;
int startUP = 0;

/* The input from the pi formatted as follows:
       0           1            2            3            4           5         6
 (LMOTORS_IN0)(LMOTORS_IN1)(RMOTORS_IN0)(RMOTORS_IN1)(PINCERS_ON)(PINCERS_DIR)(CTRL)
*/
uint8_t pi_input[7] = {0,0,0,0,0,0,0};
uint8_t checkCode[2] = {0,0};

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
  // checkCode[0] = digitalRead(PINCER_ON  );
  // checkCode[1] = digitalRead(PINCER_DIR );
  // if((checkCode[0] == 0) && (checkCode[1] == 1)){
  //   secCode = 1;
  //   return;
  // }
  
  pi_input[0] = digitalRead(LMOTORS_IN0);
  pi_input[1] = digitalRead(LMOTORS_IN1); // 00: stop, 01: forward, 10: stop, 11: back
  pi_input[2] = digitalRead(RMOTORS_IN0);
  pi_input[3] = digitalRead(RMOTORS_IN1); // 00: stop, 01: forward, 10: stop, 11: back
  pi_input[4] = digitalRead(PINCER_ON  );
  pi_input[5] = digitalRead(PINCER_DIR ); // 00: stop, 01: stop,    10: open, 11: close
  pi_input[6] = digitalRead(CTRL       );

  if(pi_input[1] == 1){
    if(pi_input[0] == 1){
      left0 = 0;
      left1 = 170;
    }
    else{
      left0 = 170;
      left1 = 0;
    }
  }
  if(pi_input[3] == 1){
    if(pi_input[2] == 1){
      right0 = 0;
      right1 = 170;
    }
    else{
      right0 = 170;
      right1 = 0;
    }
  }

  if(wait_INT == 0){
    wait_INT = 2;
  }
  startUP = 1;
  // digitalWrite(CTRL_ACK, 0);
  // delayMicroseconds(2);
  // digitalWrite(CTRL_ACK, HIGH);
  // delayMicroseconds(10);
  // digitalWrite(CTRL_ACK, 0);
}

void setup() {
  pinMode(ECHO0, INPUT); // pin 8
  pinMode(TRIG, OUTPUT); // pin 9
  // pinMode(ECHO1, INPUT); // pin 10

  pinMode(LMOTORS_IN0,INPUT); // pin 11
  pinMode(LMOTORS_IN1,INPUT); // pin 12
  pinMode(LMOTORS_OUT0,OUTPUT); // left motor out 0
  pinMode(LMOTORS_OUT1,OUTPUT); // left motor out 1
  pinMode(RMOTORS_OUT0,OUTPUT); // right motor out 0
  pinMode(RMOTORS_OUT1,OUTPUT); // right motor out 1
  servo1.attach(PINCER_OUT0); // left pincer
  servo2.attach(PINCER_OUT1); // right pincer

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
  digitalWrite(Prox_Data, 0);
  digitalWrite(CTRL_ACK, 0);

  Serial.begin(9600); // Starts the serial communication
}

//MICROCONTROLLER LOOP
void loop() {
  //possible code for detection with ultra sensors
  // sensor_data();

  // if(startUP==1){
  // if(wait_INT > 0){
  //   wait_INT = 2;
  //   digitalWrite(Prox_Data, HIGH);
  //   delayMicroseconds(5);
  //   digitalWrite(Prox_Data, 0);
  // }

  /* Auto control mode. The inputs from the pi and the sensors are data (not instructions)
     used by the microcontroller to decide how to control the motors. */
  if (pi_input[6] == 0){
    // Pincer controls
    if (pi_input[4] == 1){
      //make sure pincers are on
      if(!(servo1.attached())){
        servo1.attach(PINCER_OUT0);
        servo2.attach(PINCER_OUT1);
      }
      //fetching ball so open pincers
      if(pi_input[5] == 0){
        int curA = servo2.read();
        if(curA != 35){
          servo1.write(145);
          servo2.write(35);
          // delay(100);
        }
      }
      //acquiring ball so close pincers
      else if (pi_input[5]==1){      
        servo1.writeMicroseconds(2500);
        servo2.write(10);
        // delay(100);
        //make all the wheels brake
        analogWrite(LMOTORS_OUT0, 170);
        analogWrite(LMOTORS_OUT1, 170);
        analogWrite(RMOTORS_OUT0, 170);
        analogWrite(RMOTORS_OUT1, 170);
        servo1.detach();
        servo2.detach();
        pi_input[4] = 0;
        pi_input[5] = 0;
      }
    } 
    else {
      // make sure pincers are off
      if (servo1.attached()){
        servo1.detach();
        servo2.detach();
      }
    }
    //right motor control
    if (pi_input[3]==1) {
      analogWrite(RMOTORS_OUT0,right0);
      analogWrite(RMOTORS_OUT1,right1);
    } else {
      analogWrite(RMOTORS_OUT0,0);
      analogWrite(RMOTORS_OUT1,0);
    }
    //left motor control
    if (pi_input[1]==1) {
      analogWrite(LMOTORS_OUT0,left0);
      analogWrite(LMOTORS_OUT1,left1);
    } else {
      analogWrite(LMOTORS_OUT0,0);
      analogWrite(LMOTORS_OUT1,0);
    }
  }

  /* Manual control mode. The sensor input isn't used, and the microcontroller interprets the
     pi input as instructions to be interpreted and relayed to the control subsystem. */
  else{
    //pincer control
    if (pi_input[4] == 1){
      //make sure pincers are on
      if(!(servo1.attached())){
        servo1.attach(PINCER_OUT0);
        servo2.attach(PINCER_OUT1);
      }
      //acquiring ball so open pincers
      if(pi_input[5]==0){
        int curA = servo2.read();
        if(curA != 35){
          servo1.write(145);
          servo2.write(35);
          // delay(100);
        }
      }
      //caught ball so close pincers
      else if (pi_input[5]==1){      
        servo1.writeMicroseconds(2500);
        servo2.write(10);
        // delay(100);
        //make all the wheels brake
        analogWrite(LMOTORS_OUT0, 170);
        analogWrite(LMOTORS_OUT1, 170);
        analogWrite(RMOTORS_OUT0, 170);
        analogWrite(RMOTORS_OUT1, 170);
        servo1.detach();
        servo2.detach();
        pi_input[4] = 0;
        pi_input[5] = 0;
      }
    }
    //right motor control
    if (pi_input[3]==1) {
      analogWrite(RMOTORS_OUT0,right0);
      analogWrite(RMOTORS_OUT1,right1);
    } else {
      analogWrite(RMOTORS_OUT0,0);
      analogWrite(RMOTORS_OUT1,0);
    }
    //left motor control
    if (pi_input[1]==1) {
      analogWrite(LMOTORS_OUT0,left0);
      analogWrite(LMOTORS_OUT1,left1);
    } else {
      analogWrite(LMOTORS_OUT0,0);
      analogWrite(LMOTORS_OUT1,0);
    }

  }
  if(wait_INT == 2){
    // delay(1000);
    digitalWrite(CTRL_ACK, HIGH);
    delayMicroseconds(5);
    digitalWrite(CTRL_ACK, 0);
    delay(50);
  }

}
