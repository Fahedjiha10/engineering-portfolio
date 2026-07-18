/*
This code was automatically generated using the Riverside-Irvine State machine Builder tool
Version 2.9 --- 2/18/2025 20:49:11 PST
*/

#include "rims.h"

/*Define user variables and functions for this state machine here.*/
unsigned char cnt ;
unsigned char SM1_Clk;
void TimerISR() {
   SM1_Clk = 1;
}

enum SM1_States { SM1_WAIT, SM1_FILTER_GLITCH, SM1_MOTION } SM1_State;

TickFct_State_machine_1() {
   switch(SM1_State) { // Transitions
      case -1:
         SM1_State = SM1_WAIT;
         break;
         case SM1_WAIT: 
         if (!A0) {
            SM1_State = SM1_WAIT;
         }
         else if (A0) {
            SM1_State = SM1_FILTER_GLITCH;
         }
         break;
      case SM1_FILTER_GLITCH: 
         if (!A0 && cnt <=120) {
            SM1_State = SM1_WAIT;
         }
         else if (A0 && cnt >=150) {
            SM1_State = SM1_MOTION;
         }
         break;
      case SM1_MOTION: 
         if (A0) {
            SM1_State = SM1_MOTION;
         }
         else if (!A0) {
            SM1_State = SM1_WAIT;
         }
         break;
      default:
         SM1_State = SM1_WAIT;
   } // Transitions

   switch(SM1_State) { // State actions
      case SM1_WAIT:
         B0=0;
         break;
      case SM1_FILTER_GLITCH:
         cnt++ ;
         break;
      case SM1_MOTION:
         B0=1;
         break;
      default: // ADD default behaviour below
      break;
   } // State actions

}

int main() {

   const unsigned int periodState_machine_1 = 120;
   TimerSet(periodState_machine_1);
   TimerOn();
   
   SM1_State = -1; // Initial state
   B = 0; // Init outputs

   while(1) {
      TickFct_State_machine_1();
      while(!SM1_Clk);
      SM1_Clk = 0;
   } // while (1)
} // Main