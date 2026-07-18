/*
This code was automatically generated using the Riverside-Irvine State machine Builder tool
Version 2.9 --- 3/4/2025 21:38:27 PST
*/

#include "rims.h"

/*This code will be shared between state machines.*/
unsigned char TimerFlag = 0;
void TimerISR() {
   TimerFlag = 1;
}


enum SM1_States { SM1_LED_OFF, SM1_LED_ON } SM1_State;

TickFct_State_machine_1() {
   /*VARIABLES MUST BE DECLARED STATIC*/
/*e.g., static int x = 0;*/
/*Define user variables for this state machine here. No functions; make them global.*/
   switch(SM1_State) { // Transitions
      case -1:
         SM1_State = SM1_LED_OFF;
         break;
      case SM1_LED_OFF:
         if (1) {
            SM1_State = SM1_LED_ON;
         }
         break;
      case SM1_LED_ON:
         if (1) {
            SM1_State = SM1_LED_OFF;
         }
         break;
      default:
         SM1_State = SM1_LED_OFF;
      } // Transitions

   switch(SM1_State) { // State actions
      case SM1_LED_OFF:
         B0=0;
         break;
      case SM1_LED_ON:
         B0=1;
         break;
      default: // ADD default behaviour below
         break;
   } // State actions
}

enum SM2_States { SM2_T0, SM2_T1, SM2_T2 } SM2_State;

TickFct_State_machine_2() {
   /*VARIABLES MUST BE DECLARED STATIC*/
/*e.g., static int x = 0;*/
/*Define user variables for this state machine here. No functions; make them global.*/
   switch(SM2_State) { // Transitions
      case -1:
         SM2_State = SM2_T0;
         break;
      case SM2_T0:
         if (1) {
            SM2_State = SM2_T1;
         }
         break;
      case SM2_T1:
         if (1) {
            SM2_State = SM2_T2;
         }
         break;
      case SM2_T2:
         if (1) {
            SM2_State = SM2_T0;
         }
         break;
      default:
         SM2_State = SM2_T0;
      } // Transitions

   switch(SM2_State) { // State actions
      case SM2_T0:
         B5=1;
         B6=0;
         B7=0;
         break;
      case SM2_T1:
         B5=0;
         B6=1;
         B7=0;
         break;
      case SM2_T2:
         B5=0;
         B6=0;
         B7=1;
         break;
      default: // ADD default behaviour below
         break;
   } // State actions
}
int main() {
   B = 0; //Init outputs
   TimerSet(500);
   TimerOn();
   SM1_State = -1;
   SM2_State = -1;
   while(1) {
      TickFct_State_machine_1();
      TickFct_State_machine_2();
      while (!TimerFlag);
      TimerFlag = 0;
   }
}