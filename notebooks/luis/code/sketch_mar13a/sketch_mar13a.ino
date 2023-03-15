#define ECHO0        14 // PB0
#define TRIG1        15 // PB1
#define ECHO1        16 // PB2
/*
#define MOSI 17 // PB3
#define MISO 18 // PB4
#define SCK 19  // PB5
*/
#define LMOTORS_IN0   9 // XTAL1/PB6
#define LMOTORS_IN1  10 // XTAL2/PB7
#define LMOTORS_OUT0 23 // PC0
#define LMOTORS_OUT1 24 // PC1
#define RMOTORS_OUT0 25 // PC2
#define RMOTORS_OUT1 26 // PC3
#define PINCER_OUT0  27 // PC4
#define PINCER_OUT1  28 // PC5
//#define RST 1 // !RESET/PC6
#define RMOTORS_IN0   2 // PD0
#define RMOTORS_IN1   3 // PD1
#define PI_INT        4 // PD2
#define SENSOR_INT    5 // PD3
#define CTRL          6 // PD4
#define PINCER_ON    11 // PD5
#define PINCER_DIR   12 // PD6
#define TRIG0        13 // PD7

/* The input from the pi formatted as follows:
       0           1            2            3            4           5         6
 (LMOTORS_IN0)(LMOTORS_IN1)(RMOTORS_IN0)(RMOTORS_IN1)(PINCERS_ON)(PINCERS_DIR)(CTRL)
*/
uint8_t pi_input[7] = {0,0,0,0,0,0,0};
// The actual processed sensor inputs should always be >=0, so they will only be 
// negative when an input hasn't been read from the sensors
int sensor_input[2] = {-100,-100}; 

void read_pi() {
  pi_input[0] = digitalRead(LMOTORS_IN0);
  pi_input[1] = digitalRead(LMOTORS_IN1); // 00: stop, 01: forward, 10: stop, 11: back
  pi_input[2] = digitalRead(RMOTORS_IN0);
  pi_input[3] = digitalRead(RMOTORS_IN1); // 00: stop, 01: forward, 10: stop, 11: back
  pi_input[4] = digitalRead(PINCER_ON  );
  pi_input[5] = digitalRead(PINCER_DIR ); // 00: stop, 01: stop,    10: open, 11: close
  pi_input[6] = digitalRead(CTRL       );
}
void read_sensors() {
  return;
}

void setup() {
  // put your setup code here, to run once:
  pinmode(ECHO0,INPUT);
  pinmode(TRIG1,OUTPUT);
  pinmode(ECHO1,INPUT);
  /*pinmode(MOSI,);
  pinmode(MISO,);
  pinmode(SCK,);*/
  pinmode(LMOTORS_IN0,INPUT);
  pinmode(LMOTORS_IN1,INPUT);
  pinmode(LMOTORS_OUT0,OUTPUT);
  pinmode(LMOTORS_OUT1,OUTPUT);
  pinmode(RMOTORS_OUT0,OUTPUT);
  pinmode(RMOTORS_OUT1,OUTPUT);
  pinmode(PINCER_OUT0,OUTPUT);
  pinmode(PINCER_OUT1,OUTPUT);
  //pinmode(RST,);        
  pinmode(RMOTORS_IN0,INPUT); 
  pinmode(RMOTORS_IN1,INPUT); 
  pinmode(PI_INT,INPUT);
  attachInterrupt(digitalPinToInterrupt(PI_INT),read_pi,CHANGE);
  pinmode(SENSOR_INT,INPUT);
  attachInterrupt(digitalPinToInterrupt(SENSOR_INT),read_sensors,RISING);
  pinmode(CTRL,INPUT);   
  pinmode(PINCER_ON,INPUT);  
  pinmode(PINCER_DIR,INPUT); 
  pinmode(TRIG0,OUTPUT);
}

/* NOTE: Interrupt logic may interfere with the microcontroller's decision
  process if interrupts occur at intervals shorter than the runtime of the 
  decision process. This isn't expected to be an issue in manual mode, as
  no human should be able to press and release a key within the amount of 
  time necessary for the manual control code to execute. */
void loop() {
  // put your main code here, to run repeatedly:
  //delay(100);

  /* Auto control mode. The inputs from the pi and the sensors are data (not instructions)
     used by the microcontroller to decide how to control the motors. */
  if (pi_input[6]==0) {
    // NOTE: Continue working from here.
    digitalWrite(LMOTORS_OUT0,HIGH)
  }
  /* Manual control mode. The sensor input isn't used, and the microcontroller interprets the
     pi input as instructions to be interpreted and relayed to the control subsystem. */
  else {
    // Left motors control translation
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
    if (pi_input[4]==1) {
      digitalWrite(PINCER_ON, !pi_input[5]);
      digitalWrite(PINCER_DIR, pi_input[5]);
    } else {
      digitalWrite(PINCER_ON, LOW);
      digitalWrite(PINCER_DIR,LOW);
    }

  }
}
