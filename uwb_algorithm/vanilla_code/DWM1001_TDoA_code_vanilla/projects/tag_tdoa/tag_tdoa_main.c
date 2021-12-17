/*! ----------------------------------------------------------------------------
*  @file    anch_master_main.c
*  @brief   
*
*           Notes at the end of this file, expand on the inline comments.
* 
* @attention
*
* Copyright 2015 (c) Decawave Ltd, Dublin, Ireland.
*
* All rights reserved.
*
* @author unitn
*/

#include "FreeRTOS.h"
#include "deca_device_api.h"
#include "deca_regs.h"
#include "port_platform.h"
#include "task.h"
#include <stdio.h>
#include <string.h>

#include "anch_conf.h"

#define APP_NAME "TAG"
#define TAG_ID 4
  // per ora uso tag fissi

// ********************************************************* DEF TDOA *********************************************************
static uint8 tag_blink[] = {0x41, 0x88, TAG_ID, 0, 0x10, 0, 0}; //blinco

#define CODE_INIT 3
#define RESP_DLY 1000 // 65536000 sono in uwb tick ~1ms
#define UUS_TO_DWT_TIME 65536

#define RX_INIT_LEN 10 //conta 1,2,3,4,...22 elementi
static uint8 rx_buffer[RX_INIT_LEN];

static uint32 status_reg = 0;
static uint64 ts_init;

//SLEEP
static uint64 get_rx_timestamp_u64(void);
static uint8 msg_number = 0;
static uint32 frame_len;

int tag_tdoa_run(void) {

  //----------------------------------- START RX -------------------------------------
  dwt_rxenable(DWT_START_RX_IMMEDIATE);
  while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_ERR))) {};

  // ---------------------------- ARRIVA BROADCAST ----------------------------------
  if (status_reg & SYS_STATUS_RXFCG) {

    dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);

    frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;

	if(frame_len == 6){

	  dwt_readrxdata(rx_buffer, frame_len, 0);

	  if (rx_buffer[CODE_INIT] == INIT_TDOA_MSG) {

		if (rx_buffer[NUM_TAG_IDX] == TAG_ID) {

		  ts_init = get_rx_timestamp_u64();

          /*** NEL CASO NON SI VUOLE RISPOSTA IMMEDIATA SETTO IL TEMPO DI DELAY DI RISPOSTA DEL BLINK ****/
          uint32 resp_time = (ts_init + (RESP_DLY * UUS_TO_DWT_TIME)) >> 8;
          dwt_setdelayedtrxtime(resp_time);

          tag_blink[3] = msg_number;
          dwt_writetxdata(sizeof(tag_blink), tag_blink, 0);
          dwt_writetxfctrl(sizeof(tag_blink), 0, 1);

          dwt_starttx(DWT_START_TX_DELAYED); // se uso il delay
		  while (!(dwt_read32bitreg(SYS_STATUS_ID) & SYS_STATUS_TXFRS)) {};

		  dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_TXFRS);

		  msg_number++;

		} //IF tag_id
		else {
		  dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
		  dwt_rxreset();
		}
	  } // IF INIT
	  else {
		dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
		dwt_rxreset();
	  }
	}
	else {
	  dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
	  dwt_rxreset();
	} // IF RX something
  }
  else {
	dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
	dwt_rxreset();
  }
}

/*! ------------------------------------------------------------------------------------------------------------------
 * @fn get_rx_timestamp_u64()
 *
 * @brief Get the RX time-stamp in a 64-bit variable.
 *        /!\ This function assumes that length of time-stamps is 40 bits, for both TX and RX!
 *
 * @param  none
 *
 * @return  64-bit value of the read time-stamp.
 */
static uint64 get_rx_timestamp_u64(void) {
  uint8 ts_tab[5];
  uint64 ts = 0;
  int i;
  dwt_readrxtimestamp(ts_tab);
  for (i = 4; i >= 0; i--) {
    ts <<= 8;
    ts |= ts_tab[i];
  }
  return ts;
}

void tag_tdoa_task_function(void *pvParameter) {

  UNUSED_PARAMETER(pvParameter);
  dwt_setleds(DWT_LEDS_ENABLE);
  while (true) {

    tag_tdoa_run();

  }
}

/*****************************************************************************************************************************************************
* NOTES:
*
* 1. The frames used here are Decawave specific ranging frames, complying with the IEEE 802.15.4 standard data frame encoding. The frames are the
*    following:
*     - a poll message sent by the initiator to trigger the ranging exchange.
*     - a response message sent by the responder to complete the exchange and provide all information needed by the initiator to compute the
*       time-of-flight (distance) estimate.
*    The first 10 bytes of those frame are common and are composed of the following fields:
*     - byte 0/1: frame control (0x8841 to indicate a data frame using 16-bit addressing).
*     - byte 2: sequence number, incremented for each new frame.
*     - byte 3/4: PAN ID (0xDECA).
*     - byte 5/6: destination address, see NOTE 2 below.
*     - byte 7/8: source address, see NOTE 2 below.
*     - byte 9: function code (specific values to indicate which message it is in the ranging process).
*    The remaining bytes are specific to each message as follows:
*    Poll message:
*     - no more data
*    Response message:
*     - byte 10 -> 13: poll message reception timestamp.
*     - byte 14 -> 17: response message transmission timestamp.
*    All messages end with a 2-byte checksum automatically set by DW1000.
* 2. Source and destination addresses are hard coded constants in this example to keep it simple but for a real product every device should have a
*    unique ID. Here, 16-bit addressing is used to keep the messages as short as possible but, in an actual application, this should be done only
*    after an exchange of specific messages used to define those short addresses for each device participating to the ranging exchange.
* 3. dwt_writetxdata() takes the full size of the message as a parameter but only copies (size - 2) bytes as the check-sum at the end of the frame is
*    automatically appended by the DW1000. This means that our variable could be two bytes shorter without losing any data (but the sizeof would not
*    work anymore then as we would still have to indicate the full length of the frame to dwt_writetxdata()).
* 4. We use polled mode of operation here to keep the example as simple as possible but all status events can be used to generate interrupts. Please
*    refer to DW1000 User Manual for more details on "interrupts". It is also to be noted that STATUS register is 5 bytes long but, as the event we
*    use are all in the first bytes of the register, we can use the simple dwt_read32bitreg() API call to access it instead of reading the whole 5
*    bytes.
* 5. The high order byte of each 40-bit time-stamps is discarded here. This is acceptable as, on each device, those time-stamps are not separated by
*    more than 2**32 device time units (which is around 67 ms) which means that the calculation of the round-trip delays can be handled by a 32-bit
*    subtraction.
* 6. The user is referred to DecaRanging ARM application (distributed with EVK1000 product) for additional practical example of usage, and to the
*     DW1000 API Guide for more details on the DW1000 driver functions.
* 7. The use of the carrier integrator value to correct the TOF calculation, was added Feb 2017 for v1.3 of this example.  This significantly
*     improves the result of the SS-TWR where the remote responder unit's clock is a number of PPM offset from the local inmitiator unit's clock.
*     As stated in NOTE 2 a fixed offset in range will be seen unless the antenna delsy is calibratred and set correctly.
*
****************************************************************************************************************************************************/