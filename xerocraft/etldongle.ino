
// The tokens, ids, and passwords for ETL are kept on an Arduino Micro as strings in this
// program (they are currently blank so that the code can be checked in). To use ETL, 
// run the ETL command and then plug in the Arduino Micro which will act as a keyboard and
// "type" the token/id/pw info. 

#include <Keyboard.h>

void slow_print(char* s) {
  for (int i=0; i<strlen(s); i++) {
    Keyboard.print(s[i]);
    delay(20); 
  }
  Keyboard.print("\n");
  delay(500);
}

void setup() {
}

void loop() {
  delay(1000);
  Keyboard.begin();

  slow_print("xerocraft.etlfetchers.square xerocraft.etlfetchers.twocheckout xerocraft.etlfetchers.wepay");
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

