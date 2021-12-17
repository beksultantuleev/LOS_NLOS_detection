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

#define APP_NAME "ANCH_MASTER v0.1"

extern uint8_t NUM_ANCH;

// ********************************************************* TWR-INITIALIZATION *****************************************************************

static uint8 msg_init_twr[] = {0xC5, 0, 0, 0};
static uint8 anch_idx;

// ************************************************************ TWR-CORRECTION ******************************************************************

/* Frames used in the ranging process. See NOTE 1,2 below. */
static uint8 tx_poll_msg[] = {0x41, 0x88, 0, 0xCA, 0xDE, 'W', 'A', 'V', 'E', 0x21, 0, 0};
static uint8 rx_resp_msg[] = {0x41, 0x88, 0, 0xCA, 0xDE, 'V', 'E', 'W', 'A', 0x10, 0x02, 0, 0, 0, 0};
static uint8 tx_final_msg[] = {0x41, 0x88, 0, 0xCA, 0xDE, 'W', 'A', 'V', 'E', 0x23, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};

/* Frame sequence number, incremented after each transmission. */
static uint8 frame_seq_nb = 0;

/* Buffer to store received response message.
* Its size is adjusted to longest frame that this example code is supposed to handle. */
#define RX_BUF_LEN 20
static uint8 rx_buffer[RX_BUF_LEN];

/* Hold copy of status register state here for reference so that it can be examined at a debug breakpoint. */
static uint32 status_reg = 0;

/* Time-stamps of frames transmission/reception, expressed in device time units.
 * As they are 40-bit wide, we need to define a 64-bit int type to handle them. */
typedef signed long long int64;
typedef unsigned long long uint64;
static uint64 poll_tx_ts;
static uint64 resp_rx_ts;
static uint64 final_tx_ts;

// *************************************************************** DEF ANCH SYNC *********************************************************************

static uint8 tx_init_blink[] = {0x41, 0x88, 0, 0xCA, 0xDE, 'S', 'Y', 'N', 'C', 0x19, 0, 0};
static uint8 tx_final_blink[] = {0x41, 0x88, 0, 0xCA, 0xDE, 'S', 'Y', 'N', 'C', 0x6, 0, 0};
static uint8 tx_final_ts[] = {0x41, 0x88, 0, 0xCA, 0xDE, 'S', 'Y', 'N', 'C', 0x23, 0, 0, 0, 0, 0, 0}; //differenza in 32 bit

#define FINAL_MSG_TS_LEN 4
#define BLINK_FRAME_SN_IDX 2
#define TS_INT_IDX 10
#define ALL_MSG_SN_IDX 2

//#define SYNC_CYCLE 10
#define TX_DELAY_MS 100       //sleep finale
#define DELAY_UUS 10000       //per fisare timestamp fisso un delay per decidere quando trasmettere
#define UUS_TO_DWT_TIME 65536 // fattore di conversione UUS in tempo DW1000

typedef unsigned long long uint64;
static uint64 final_tx_ts; //delay tx finale
static uint64 blink1_tx_ts;
static uint64 blink2_tx_ts;
static uint32 final_tx_time;

static void msg_set_idx_sync(uint8 *ts_field, uint8 ts);

// ********************************************************* DEF TDOA *********************************************************

static uint8 broadcast_blink[] = {0x41, 0x88, 0, 0xFF, 0, 0}; //0xFFFF-> broadcast

#define TDOA_CYCLE 10000
#define TAG_NUM 10
#define RX_TAG_BUF_LEN 7 //conta 1,2,3,4,...22 elementi
static uint8 tag_buffer[RX_TAG_BUF_LEN];

static uint64 ts_init_tdoa; // timestamp del msg di init del master
static uint64 tag_ts;       // timestamp in rx del blink del tag
static uint64 total_time;   // TEMPO TOTALE TRA INIT MSG E RISPOSTA DEL TAG
static char buffer[30] = {""};

//_____________________ MSG_TDOA_MATLAB_DATA _________________________
// ste cose andranno eliminate quando non si riceverà più il dato su UWB

typedef struct
{
  uint32 anch1;
  uint32 anch2;
  uint32 anch3;
  uint32 anch4;
  uint32 anch5;
  uint32 anch6;
  uint32 anch7;
} time_stamp_Anch_t;

#define TEST_BUF_LEN 14 //conta 1,2,3,4,...22 elementi
static uint8 test_buffer[TEST_BUF_LEN];
static void test_msg_get(const uint8 *ts_field, uint32 *ts);

time_stamp_Anch_t TimeStamp_Anch;

// __________________________________________________________ TS FUNCTION __________________________________________________________

static uint64 get_tx_timestamp_u64(void);
static void msg_set_ts(uint8 *ts_field, uint64 ts);
static uint64 get_rx_timestamp_u64(void);
static void get_msg_idx(const uint8 *ts_field, uint8 *ts);

/*Transactions Counters */
static volatile int tx_count = 0; // Successful transmit counter
static volatile int rx_count = 0; // Successful receive counter

int anch_master_run(void) {

  //  ============================================================== TWR_ANCH ==============================================================
  anch_idx = 1;

  while (anch_idx < NUM_ANCH) {

    int init_ok;

    msg_init_twr[ANCH_IDX] = anch_idx;

    dwt_writetxdata(sizeof(msg_init_twr), msg_init_twr, 0); /* Zero offset in TX buffer. */
    dwt_writetxfctrl(sizeof(msg_init_twr), 0, 0);           /* Zero offset in TX buffer, ranging. */

    init_ok = dwt_starttx(DWT_START_TX_IMMEDIATE);

    if (init_ok == DWT_SUCCESS) {

      vTaskDelay(100);

      int twr_cycle = 0;

      while (twr_cycle < NUM_TWR_CYCLE) {

        /* Write frame data to DW1000 and prepare transmission. See NOTE below. */
        tx_poll_msg[ALL_MSG_SN_IDX] = frame_seq_nb;
        dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_TXFRS);
        dwt_writetxdata(sizeof(tx_poll_msg), tx_poll_msg, 0); /* Zero offset in TX buffer. */
        dwt_writetxfctrl(sizeof(tx_poll_msg), 0, 1);          /* Zero offset in TX buffer, ranging. */

        dwt_starttx(DWT_START_TX_IMMEDIATE | DWT_RESPONSE_EXPECTED);
        /* We assume that the transmission is achieved correctly, poll for reception of a frame or error/timeout. See NOTE below. */
        while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR))) {
        };

#if 0 // include if required to help debug timeouts.
          int temp = 0;		
          if(status_reg & SYS_STATUS_RXFCG )
          temp =1;
          else if(status_reg & SYS_STATUS_ALL_RX_TO )
          temp =2;
          if(status_reg & SYS_STATUS_ALL_RX_ERR )
          temp =3;
#endif

        /* Increment frame sequence number after transmission of the poll message (modulo 256). */
        frame_seq_nb++;

        if (status_reg & SYS_STATUS_RXFCG) {
          uint32 frame_len;
          /* Clear good RX frame event and TX frame sent in the DW1000 status register. */
          dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG | SYS_STATUS_TXFRS);
          /* A frame has been received, read it into the local buffer. */
          frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFLEN_MASK;
          if (frame_len <= RX_BUF_LEN) {
            dwt_readrxdata(rx_buffer, frame_len, 0);
          }

          rx_buffer[ALL_MSG_SN_IDX] = 0;

          if (memcmp(rx_buffer, rx_resp_msg, ALL_MSG_COMMON_LEN) == 0) {

            uint32 final_tx_time;
            int ret;

            /* Retrieve poll transmission and response reception timestamp. */
            poll_tx_ts = get_tx_timestamp_u64();
            resp_rx_ts = get_rx_timestamp_u64();

            /* Compute final message transmission time. See NOTE below. */
            final_tx_time = (resp_rx_ts + (RESP_RX_TO_FINAL_TX_DLY_UUS * UUS_TO_DWT_TIME)) >> 8;
            dwt_setdelayedtrxtime(final_tx_time);

            final_tx_ts = (((uint64)(final_tx_time & 0xFFFFFFFEUL)) << 8) + TX_ANT_DLY;

            msg_set_ts(&tx_final_msg[FINAL_MSG_POLL_TX_TS_IDX], poll_tx_ts);
            msg_set_ts(&tx_final_msg[FINAL_MSG_RESP_RX_TS_IDX], resp_rx_ts);
            msg_set_ts(&tx_final_msg[FINAL_MSG_FINAL_TX_TS_IDX], final_tx_ts);

            tx_final_msg[ALL_MSG_SN_IDX] = frame_seq_nb;

            dwt_writetxdata(sizeof(tx_final_msg), tx_final_msg, 0); /* Zero offset in TX buffer. */
            dwt_writetxfctrl(sizeof(tx_final_msg), 0, 1);           /* Zero offset in TX buffer, ranging. */

            ret = dwt_starttx(DWT_START_TX_DELAYED);

            if (ret == DWT_SUCCESS) {

              while (!(dwt_read32bitreg(SYS_STATUS_ID) & SYS_STATUS_TXFRS)) {};

              dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_TXFRS);

              frame_seq_nb++;

              twr_cycle++;

            } // if DWT_SUCCESS

          } // if RX_BUFF

        } else {
          dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
          dwt_rxreset();
        }

        vTaskDelay(100);

      }// end TWR-CORRECTION


	  // TODO: QUA CI SAREBBE DA METTERE LA STORIA CHE IL MASTER RICEVE IL DATO DALLA ANCORA PRIMA DI ANDARE AVANTI

    }// end if init

    else {// se non spedito correttamente msg ad ancora

      dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
      dwt_rxreset();

      continue;
    }

    //__________________ SYNC - PART________________________

    int sync_cycle = 0;

    while (sync_cycle < SYNC_CYCLE) {

      final_tx_time = 0;
      tx_init_blink[2] = anch_idx;

      dwt_writetxdata(sizeof(tx_init_blink), tx_init_blink, 0);
      dwt_writetxfctrl(sizeof(tx_init_blink), 0, 1);

      int ret1 = dwt_starttx(DWT_START_TX_IMMEDIATE);

      if (ret1 == DWT_SUCCESS) {
        //se ho spedito correttamente
        while (!(dwt_read32bitreg(SYS_STATUS_ID) & SYS_STATUS_TXFRS)) {};

        dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_TXFRS);

        // --------------------------- TIMESTAMP INIT -------------------------------
        blink1_tx_ts = get_tx_timestamp_u64();
        // --------------------------------------------------------------------------

        //---------------------------------------------------------------------------------------------------------
        final_tx_time = (blink1_tx_ts + (DELAY_UUS * UUS_TO_DWT_TIME)) >> 8; //delay per fissare trasmissione msg con delta_timestamp
        dwt_setdelayedtrxtime(final_tx_time);                                //set tx delayed

        final_tx_ts = (((uint64)((final_tx_time)&0xFFFFFFFEUL)) << 8) + TX_ANT_DLY;

        // --------------------------------- SECONDO BLINK RITARDATO -----------------------------------------------

        dwt_writetxdata(sizeof(tx_final_blink), tx_final_blink, 0);
        dwt_writetxfctrl(sizeof(tx_final_blink), 0, 1);

        int ret2 = dwt_starttx(DWT_START_TX_DELAYED); //inizia a tx al delay prestabilito: final_tx_time

        if (ret2 == DWT_SUCCESS) {
          //se ho spedito correttamente
          while (!(dwt_read32bitreg(SYS_STATUS_ID) & SYS_STATUS_TXFRS)) {};
          dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_TXFRS);

          // --------------------------- TIMESTAMP FINAL -------------------------------
          blink2_tx_ts = get_tx_timestamp_u64();
          // ---------------------------------------------------------------------------

          //-------------------------------CALCOLO DELTA TIMESTAMP --------------------------------------------------------------------------

          uint32 delta_ts;
          delta_ts = blink2_tx_ts - blink1_tx_ts;
          msg_set_ts(&tx_final_ts[TS_INT_IDX], delta_ts); //NB. funzione aggiunge zeri in automatico->in watchexpr il programma non li mostra ma ci sono!!!
          msg_set_idx_sync(&tx_final_ts[ALL_MSG_SN_IDX], sync_cycle);

          dwt_writetxdata(sizeof(tx_final_ts), tx_final_ts, 0); /* Zero offset in TX buffer. */
          dwt_writetxfctrl(sizeof(tx_final_ts), 0, 1);          /* Zero offset in TX buffer, ranging. */

          int ret3 = dwt_starttx(DWT_START_TX_IMMEDIATE); //inizia a tx al delay prestabilito: final_tx_time

          if (ret3 == DWT_SUCCESS) {

            while (!(dwt_read32bitreg(SYS_STATUS_ID) & SYS_STATUS_TXFRS)) {};
            dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_TXFRS);
 
            sync_cycle++;
            vTaskDelay(5);

          } else { //in caso di errore reset
            dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
            dwt_rxreset();
          }
        } else { //in caso di errore reset
          dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
          dwt_rxreset();
        }
      } else { //in caso di errore reset
        dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
        dwt_rxreset();
      }
    }

    anch_idx++;

    vTaskDelay(100);
  } //while anch_idx

  vTaskDelay(1000);
  // ============================================================== TDOA-PART ==============================================================

  int i = 0;
  int tag_nr;
	
	while(1){

	tag_nr = 1;

    while (tag_nr <= TAG_NUM) {

      broadcast_blink[NUM_TAG_IDX] = tag_nr;

      dwt_writetxdata(sizeof(broadcast_blink), broadcast_blink, 0);
      dwt_writetxfctrl(sizeof(broadcast_blink), 0, 1);
      dwt_starttx(DWT_START_TX_IMMEDIATE);

      while (!(dwt_read32bitreg(SYS_STATUS_ID) & SYS_STATUS_TXFRS)) {};

	  dwt_setrxtimeout(6010); 
      dwt_rxenable(DWT_START_RX_IMMEDIATE);
      // --------------------------- RX TAG BLINK ----------------------------------
      while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_ERR | SYS_STATUS_ALL_RX_TO))) {};

      if (status_reg & SYS_STATUS_RXFCG) {

        uint32 frame_len;

        dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG | SYS_STATUS_TXFRS);

        frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFLEN_MASK;

        if (frame_len <= RX_TAG_BUF_LEN) {

          dwt_readrxdata(tag_buffer, frame_len, 0);

        }
        //my modification
        dwt_rxdiag_t diag;
        dwt_readdiagnostics(&diag);
        //<<

        if (tag_buffer[TAG_IDX] == TAG_BLINK) {

          //--------------- TIMESTAMP TAG BLINK ------------------------
          tag_ts = get_rx_timestamp_u64();
          //------------------------------------------------------------

          //---------------- TIMESTAMP INIT MASTER ---------------------
          ts_init_tdoa = get_tx_timestamp_u64();
          //------------------------------------------------------------

          uint8 tag_ID;
          uint8 msg_num;

          tag_ID = tag_buffer[2];
          msg_num = tag_buffer[3];

          total_time = tag_ts - ts_init_tdoa;

          //sprintf(buffer,"%lu %lu %lu\r\n", tag_ID, msg_num, total_time);
          //printf(buffer);

          //my code
          //my modification
          uint16 C = diag.maxGrowthCIR;
          uint32 N = diag.rxPreamCount;
          float F1 = diag.firstPathAmp1;
          float F2 = diag.firstPathAmp2;
          float F3 = diag.firstPathAmp3;
          float A = 121.74;//113.77;121.74

          float RX_level = 10 * log10((C * pow(2, 17)) / (N*N)) - A;
          float FP_POWER = 10 * log10((F1*F1 + F2*F2 + F3*F3)/(N*N)) - A;

          sprintf(buffer, "[%lu, %lu, %lu, %f, %f]\r\n", tag_ID, msg_num, total_time, RX_level, RX_level-FP_POWER);
          printf(buffer);
          //<<<



        }

      } else {

        dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
        dwt_rxreset();
      }

      tag_nr++;

      vTaskDelay(5);

    }
	 // end tag cycle 

    vTaskDelay(10); //aspetta che tutti mandino il dato
  }
}

static uint64 get_tx_timestamp_u64(void) {
  uint8 ts_tab[5];
  uint64 ts = 0;
  int i;
  dwt_readtxtimestamp(ts_tab);
  for (i = 4; i >= 0; i--) {
    ts <<= 8;
    ts |= ts_tab[i];
  }
  return ts;
}

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

static void msg_set_ts(uint8 *ts_field, uint64 ts) {
  int i;
  for (i = 0; i < FINAL_MSG_TS_LEN; i++) {
    ts_field[i] = (uint8)ts;
    ts >>= 8;
  }
}

static void msg_set_idx_sync(uint8 *ts_field, uint8 ts) {
  int i;
  for (i = 0; i < 1; i++) {
    ts_field[i] = (uint8)ts;
    ts >>= 8;
  }
}

static void get_msg_idx(const uint8 *ts_field, uint8 *ts) {
  int i;
  *ts = 0;
  for (i = 0; i < 1; i++) {
    *ts += ts_field[i] << (i * 8);
  }
}

//_____________________ MSG_TEST _________________________
static void test_msg_get(const uint8 *ts_field, uint32 *ts) {
  int i;
  *ts = 0;
  for (i = 0; i < TEST_LEN; i++) {
    *ts += ts_field[i] << (i * 8);
  }
}

/**@brief SS TWR Initiator task entry function.
*
* @param[in] pvParameter   Pointer that will be used as the parameter for the task.
*/
void anch_master_task_function(void *pvParameter) {
  UNUSED_PARAMETER(pvParameter);

  //dwt_setrxtimeout(RESP_RX_TIMEOUT_UUS);

  dwt_setleds(DWT_LEDS_ENABLE);

  while (true) {
    anch_master_run();
    /* Delay a task for a given number of ticks */
    vTaskDelay(30);
    /* Tasks must be implemented to never return... */
  }
}