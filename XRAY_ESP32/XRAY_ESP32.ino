#include <SpeedyStepper.h>

const int YAW_MOTOR_STEP_PIN = 19;
const int YAW_MOTOR_DIRECTION_PIN = 18;
const int YAW_MOTOR_ENABLE = 5;

const int FILAMENT_CURRENT_PIN = 4;

String content = "";
char character;
int action_i;
String action;
String value;

float filament_current;

SpeedyStepper yaw;
long yaw_angle;

float get_filament_current() {
  float loop_total = 0.0;
  int analog;
  int i;

  float start_time = micros();

  for (i=0; i<=1000; i++) {
    analog = analogRead(FILAMENT_CURRENT_PIN);
    loop_total += analog;
    
    if ((micros() - start_time) > 10000) {
      break;
    }
  }
  
  float avg_reading = loop_total / i;
  //return (0.00795412 * avg_reading) - 15.24036691;
  return avg_reading;
}

void setup() {
  Serial.begin(1000000);
  
  yaw.connectToPins(YAW_MOTOR_STEP_PIN, YAW_MOTOR_DIRECTION_PIN);
  
  pinMode(YAW_MOTOR_ENABLE, OUTPUT);
  digitalWrite(YAW_MOTOR_ENABLE, HIGH);
  yaw.setSpeedInStepsPerSecond(5000*16);
  yaw.setAccelerationInStepsPerSecondPerSecond(100*16);
}

void loop() {
  filament_current = get_filament_current();
  
  if (Serial.available()) {
    character = Serial.read();

    if (character == '?') {
      Serial.println(filament_current);
    } else if (character == ';') {
      if (content == "STEPPER_ON") {
        Serial.println("Stepper motor enabled");
        digitalWrite(YAW_MOTOR_ENABLE, LOW);
      } else if (content == "STEPPER_OFF") {
        Serial.println("Stepper motor disabled");
        digitalWrite(YAW_MOTOR_ENABLE, HIGH);
      } else {
        action_i = content.indexOf(':');

        if (action_i != -1) {
          action = content.substring(0, action_i);
          value = content.substring(action_i + 1);

          if (action == "STEPPER_MOVE") {
            Serial.print("STEPPER MOVE TO ");
            Serial.println(value);
            yaw.moveToPositionInSteps(value.toInt());
          }
        }
      }
      content = "";
    } else {
      content.concat(character);
    }
  }
}
