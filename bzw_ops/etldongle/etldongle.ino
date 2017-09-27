
// The tokens, ids, and passwords for ETL are kept on an Arduino Micro as strings in this
// program (they are currently blank so that the code can be checked in). To use ETL, 
// run the ETL command and then plug in the Arduino Micro which will act as a keyboard and
// "type" the token/id/pw info. 

#include <Keyboard.h>

void slow_print(char* s) {
  for (int i=0; i<strlen(s); i++) {
    Keyboard.print(s[i]);
    delay(40);
  }
  Keyboard.print("\n");
  delay(800);
}

void setup() {
}

void loop() {
  delay(1000);
  Keyboard.begin();
  delay(1000);

  for (int i=0; i<10; i++) {
    Keyboard.print(" ");
    delay(100);
    Keyboard.print("\b");
    delay(100);
  }

  slow_print("");
  slow_print("");

  slow_print("");
  slow_print("");

  slow_print("");
  slow_print("");

  slow_print("");
  slow_print("");

  slow_print("");
  slow_print("");

  Keyboard.end();
  while(true) delay(100);
}
