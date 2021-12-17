/*! ----------------------------------------------------------------------------
*  @file    anch_generic_main.c
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

#define APP_NAME "ANCH_GENERIC v0.2"

extern uint8_t ANCH_ID;
extern double TOF;

//#define POSITION 5960 //in mm

/* Hold copy of status register state here for reference so that it can be examined at a debug breakpoint. */
static uint32 status_reg = 0;

/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * TWR defines and variables
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * */

#define TWR_BUF_LEN 4 //conta 1,2,3,4,...22 elementi
static uint8 twr_buffer[TWR_BUF_LEN];

static uint8 rx_poll_msg[] = {0x41, 0x88, 0, 0xCA, 0xDE, 'W', 'A', 'V', 'E', 0x21, 0, 0};
static uint8 tx_resp_msg[] = {0x41, 0x88, 0, 0xCA, 0xDE, 'V', 'E', 'W', 'A', 0x10, 0x02, 0, 0, 0, 0};
static uint8 rx_final_msg[] = {0x41, 0x88, 0, 0xCA, 0xDE, 'W', 'A', 'V', 'E', 0x23, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};

/* Frame sequence number, incremented after each transmission. */
static uint8 frame_seq_nb = 0;

/* Buffer to store received response message.
 * Its size is adjusted to longest frame that this example code is supposed to handle. */
#define RX_BUF_LEN 24
static uint8 rx_buffer[RX_BUF_LEN];

/* Time-stamps of frames transmission/reception, expressed in device time units.
 * As they are 40-bit wide, we need to define a 64-bit int type to handle them. */
typedef signed long long int64;
typedef unsigned long long uint64;
static uint64 poll_rx_ts;
static uint64 resp_tx_ts;
static uint64 final_rx_ts;

static void final_msg_get_ts(const uint8 *ts_field, uint32 *ts);
static uint64 get_tx_timestamp_u64(void);

// ------------------------------------------------------------ DEF SYNC TIMESTAMP ---------------------------------------------------------------------------------
#define START_BLINK 0x19
#define FINAL_BLINK 0x6
#define FINAL_MSG 0x23

#define ALL_MSG_COMMON_LEN 5
#define SYNC_CYCLE_IDX 2
#define CODE_IDX 9
#define FINAL_MSG_POLL_TX_TS_IDX 10

#define FINAL_MSG_TS_LEN 4

#define SYNC_BUF_LEN 12 //conta 1,2,3,4,...22 elementi
static uint8 sync_buffer[SYNC_BUF_LEN];

static uint64 sync_poll_rx_ts;
static uint64 sync_final_rx_ts;
static double corr_factor[50];
static double total;

static uint64 get_rx_timestamp_u64(void);
static void get_ts(const uint8 *ts_field, uint32 *ts);
static void get_msg_idx(const uint8 *ts_field, uint8 *ts);

/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SYNC defines and variables
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * */

#define SYNC_BUF_LEN 12 //conta 1,2,3,4,...22 elementi
static uint8 sync_buffer[SYNC_BUF_LEN];

static uint64 sync_poll_rx_ts;
static uint64 sync_final_rx_ts;
static double corr_factor[50];
static double total;

static uint64 get_rx_timestamp_u64(void);
static void get_ts(const uint8 *ts_field, uint32 *ts);
static void get_msg_idx(const uint8 *ts_field, uint8 *ts);

// ************************************************************* init message here:
#define BUF_INIT_TDOA 6 //conta 1,2,3,4,...22 elementi
static uint8 tdoa_init_buffer[BUF_INIT_TDOA];

// ************************************************************* tdoa part here:
#define RX_BUF_TAG 7 //conta 1,2,3,4,...22 elementi
static uint8 tag_buffer[RX_BUF_TAG];

static uint64 rx_init_ts;
static uint64 rx_init_ts_corr;
static uint64 ts;
static uint64 ts_corretto;
static uint64 total_ts;

static double dly_corr_factor; // fattore di correzzione in dtu del delay pre-impostato in modo che sia in synch con il conteggio del master
static double tof_media;
static double tof_tot;
static int32_t corr_dly;
static char buffer[30] = {""};

//TDoA TAG-INFO
uint8_t tag_ID;
uint8 msg_num;

// ___________________ MSG_RESP_TDOA ______________________
static uint8 tdoa_resp[] = {0xC5, 0, 0, 'T', 'E', 'S', 'T', 0, 0, 0, 0, 0, 0};

//#define TOF           1010 //POSIZIONE (2.12, 4.24)

//#define TIME_SLOT     383386580 //in UWB tick ~ 6ms

static void test_msg_set(uint8 *ts_field, uint64 ts);
static void msg_set_idx(uint8 *ts_field, uint8 ts);
// ________________________________________________________

int anch_generic_run(void) {

  //applicazione stai in ascolta di msg init (ogni parte prevede un msg di inizializzazione)
  dwt_setrxtimeout(0);
  dwt_rxenable(DWT_START_RX_IMMEDIATE);

  while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR))) {};

  if (status_reg & SYS_STATUS_RXFCG) {

    uint32 frame_len;

    dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);

    frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;

    switch (frame_len) {
    //***************************************************** TWR-SYNC *******************************************************
    case (TWR_BUF_LEN):

      dwt_readrxdata(twr_buffer, frame_len, 0);

      if (twr_buffer[ANCH_IDX] == ANCH_ID) {

        int twr_cycle = 0; //ciclo una volta sola il controllo del twr
        tof_tot = 0;

        while (twr_cycle < NUM_TWR_CYCLE) {

          dwt_setrxtimeout(0);
          dwt_rxenable(DWT_START_RX_IMMEDIATE);

          while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR))) {};

          if (status_reg & SYS_STATUS_RXFCG) {

            uint32 frame_len;
            dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);

            frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;

            if (frame_len <= RX_BUFFER_LEN) {

              dwt_readrxdata(rx_buffer, frame_len, 0);

            }

            rx_buffer[ALL_MSG_SN_IDX] = 0;

            if (memcmp(rx_buffer, rx_poll_msg, ALL_MSG_COMMON_LEN) == 0) {

              uint32 resp_tx_time;
              int ret;

              poll_rx_ts = get_rx_timestamp_u64();

              resp_tx_time = (poll_rx_ts + (POLL_RX_TO_RESP_TX_DLY_UUS * UUS_TO_DWT_TIME)) >> 8;

              dwt_setdelayedtrxtime(resp_tx_time);
              dwt_setrxaftertxdelay(RESP_TX_TO_FINAL_RX_DLY_UUS);
              dwt_setrxtimeout(FINAL_RX_TIMEOUT_UUS);

              tx_resp_msg[ALL_MSG_SN_IDX] = frame_seq_nb;

              dwt_writetxdata(sizeof(tx_resp_msg), tx_resp_msg, 0); /* Zero offset in TX buffer. */
              dwt_writetxfctrl(sizeof(tx_resp_msg), 0, 1);          /* Zero offset in TX buffer, ranging. */

              ret = dwt_starttx(DWT_START_TX_DELAYED | DWT_RESPONSE_EXPECTED);

              if (ret == DWT_ERROR) {
                continue;
              }

              while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR))) {};

              frame_seq_nb++;

              if (status_reg & SYS_STATUS_RXFCG) {

                dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG | SYS_STATUS_TXFRS);

                frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFLEN_MASK;

                if (frame_len <= RX_BUF_LEN) {

                  dwt_readrxdata(rx_buffer, frame_len, 0);

                }

                rx_buffer[ALL_MSG_SN_IDX] = 0;

                if (memcmp(rx_buffer, rx_final_msg, ALL_MSG_COMMON_LEN) == 0) {

                  uint32 poll_tx_ts, resp_rx_ts, final_tx_ts;
                  uint32 poll_rx_ts_32, resp_tx_ts_32, final_rx_ts_32;
                  double Ra, Rb, Da, Db;
                  int64 tof_dtu;

                  resp_tx_ts = get_tx_timestamp_u64();
                  final_rx_ts = get_rx_timestamp_u64();

                  final_msg_get_ts(&rx_buffer[FINAL_MSG_POLL_TX_TS_IDX], &poll_tx_ts);
                  final_msg_get_ts(&rx_buffer[FINAL_MSG_RESP_RX_TS_IDX], &resp_rx_ts);
                  final_msg_get_ts(&rx_buffer[FINAL_MSG_FINAL_TX_TS_IDX], &final_tx_ts);

                  poll_rx_ts_32 = (uint32)poll_rx_ts;
                  resp_tx_ts_32 = (uint32)resp_tx_ts;
                  final_rx_ts_32 = (uint32)final_rx_ts;
                  Ra = (double)(resp_rx_ts - poll_tx_ts);
                  Rb = (double)(final_rx_ts_32 - resp_tx_ts_32);
                  Da = (double)(final_tx_ts - resp_rx_ts);
                  Db = (double)(resp_tx_ts_32 - poll_rx_ts_32);
                  tof_dtu = (int64)((Ra * Rb - Da * Db) / (Ra + Rb + Da + Db));

                  tof_tot = tof_tot + tof_dtu;

                  twr_cycle++;

                }
              } else {

                dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
                dwt_rxreset();

              }
            }

          } else {

            dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
            dwt_rxreset();

          }
        }

        tof_media = tof_tot / 10;
        corr_dly = (int32_t)(TOF - tof_media);

        printf("%d \r\n", corr_dly);

		twr_cycle = 0;

      } else {

        return 0;
      }

      break;

      //	__________________________________________________SYNC-PART ____________________________________________________________
    case (SYNC_BUF_LEN): //lung 12, il sync si fa in parallelo perch? il master invia solo pacchetti

      dwt_readrxdata(sync_buffer, frame_len, 0);

      // ---------------------------- CHECK BLINK_CODE ----------------------------------
      if (sync_buffer[CODE_IDX] == START_BLINK) {

        sync_poll_rx_ts = get_rx_timestamp_u64(); //primo timestamp

        if (sync_buffer[2] == ANCH_ID) {

          dwt_rxenable(DWT_START_RX_IMMEDIATE);

          while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_ERR))) {};

          // ---------------------------- ARRIVA SECONDO BLINK ----------------------------------
          if (status_reg & SYS_STATUS_RXFCG) {

            uint32 frame_len;
            dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);

            frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;

            if (frame_len <= SYNC_BUF_LEN) {

              dwt_readrxdata(sync_buffer, frame_len, 0);

            }
            // ---------------------------- CHECK BLINK_CODE ----------------------------------
            if (sync_buffer[CODE_IDX] == FINAL_BLINK) {

              sync_final_rx_ts = get_rx_timestamp_u64(); //final timestamp

              dwt_rxenable(DWT_START_RX_IMMEDIATE);

              while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_ERR))) {};

              // ----------------------------ARRIVA MSG FINALE ----------------------------------
              if (status_reg & SYS_STATUS_RXFCG) {

                uint32 frame_len;
                dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);

                frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;

                if (frame_len <= RX_BUFFER_LEN) {

                  dwt_readrxdata(rx_buffer, frame_len, 0);

                }

                // ---------------------------- CHECK FINAL_CODE ----------------------------------
                if (rx_buffer[CODE_IDX] == FINAL_MSG) {

                  //estraggo dato da ANCH_INITIATOR
                  uint8 sync_count = 0;
                  uint32 timer_master;
                  uint64 timer_anch = 0;
                  int64 delta;

                  get_ts(&rx_buffer[FINAL_MSG_POLL_TX_TS_IDX], &timer_master);
                  get_msg_idx(&rx_buffer[SYNC_CYCLE_IDX], &sync_count);

                  timer_anch = (uint64)(sync_final_rx_ts - sync_poll_rx_ts);

                  delta = (int64)(timer_master - timer_anch);
                  corr_factor[sync_count] = (double)timer_anch / (uint64)timer_master;

                  if (sync_count == SYNC_CYCLE - 1) {

                    int j, cycles = 0;

					total = 0;
					dly_corr_factor = 0;

                    for (j = 0; j < SYNC_CYCLE; j++) {

					  if(corr_factor[j] < 1.00001 && corr_factor[j] >= 0.99999){

						total = total + corr_factor[j];

						//printf("%d -- %.17g\r\n", j, corr_factor[j]);

						cycles++;
					  }

                    }

					if (total != 0) {

					  dly_corr_factor = total / cycles;

					} else {

					  dly_corr_factor = 1;

					}

                    printf("%.17g\r\n", dly_corr_factor);

                  }
                } else {
                  dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
                  dwt_rxreset();
                }
              } else {
                dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
                dwt_rxreset();
              }
            } else {
              dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
              dwt_rxreset();
            }
          } else {
            dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
            dwt_rxreset();
          }
        } else {
          dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
          dwt_rxreset();
          return 0;
        }
      } else {
        dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
        dwt_rxreset();
        return 0;
      }

      break;

    //***************************************************** TDOA *******************************************************
    case (BUF_INIT_TDOA):

      dwt_readrxdata(tdoa_init_buffer, frame_len, 0);

      if (tdoa_init_buffer[INIT_IDX] == INIT_TDOA_MSG) {
        rx_init_ts = get_rx_timestamp_u64();
        rx_init_ts_corr = (uint64)((rx_init_ts - (uint64)TOF + corr_dly) / dly_corr_factor);
        //

        dwt_setrxtimeout(1010);
        dwt_rxenable(DWT_START_RX_IMMEDIATE);
        while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_ERR | SYS_STATUS_ALL_RX_TO))) {
        };

        // ---------------------------- TAG BLINK ----------------------------------
        if (status_reg & SYS_STATUS_RXFCG) {
          uint32 frame_len;
          dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);
          frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;

          if (frame_len <= RX_BUF_TAG) {
            dwt_readrxdata(tag_buffer, frame_len, 0);
          }

          if (tag_buffer[TAG_IDX] == TAG_BLINK_MSG) {

            ts = get_rx_timestamp_u64();
            ts_corretto = (uint64)((ts - corr_dly) / dly_corr_factor);

            tag_ID = tag_buffer[2];
            msg_num = tag_buffer[3];

            total_ts = (uint64)(ts_corretto - rx_init_ts_corr);

            sprintf(buffer, "%lu %lu %lu\r\n", tag_ID, msg_num, total_ts);
            printf(buffer);

          } else {
            dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
            dwt_rxreset();
          }
        } else {
          dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
          dwt_rxreset();
        }
      } else {
        dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
        dwt_rxreset();
      }
      break;

    //se ricevo msg che non centra
    default:
      return 0; //check il return nel task! forse non  uguale al continue che usava Marco!
    }           //SWITCH
  }             //IF RX (LISTEN)
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

static void get_ts(const uint8 *ts_field, uint32 *ts) {
  int i;
  *ts = 0;
  for (i = 0; i < FINAL_MSG_TS_LEN; i++) {
    *ts += ts_field[i] << (i * 8);
  }
}

static void get_msg_idx(const uint8 *ts_field, uint8 *ts) {
  int i;
  *ts = 0;
  for (i = 0; i < 1; i++) {
    *ts += ts_field[i] << (i * 8);
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

static void final_msg_get_ts(const uint8 *ts_field, uint32 *ts) {
  int i;
  *ts = 0;
  for (i = 0; i < FINAL_MSG_TS_LEN; i++) {
    *ts += ts_field[i] << (i * 8);
  }
}

//___________________ MSG_RESP_TDOA__________________
static void test_msg_set(uint8 *ts_field, uint64 ts) {
  int i;
  for (i = 0; i < TEST_LEN; i++) {
    ts_field[i] = (uint8)ts;
    ts >>= 8;
  }
}

static void msg_set_idx(uint8 *ts_field, uint8 ts) {
  int i;
  for (i = 0; i < 1; i++) {
    ts_field[i] = (uint8)ts;
    ts >>= 8;
  }
}

/**@brief SS TWR Initiator task entry function.
*
* @param[in] pvParameter   Pointer that will be used as the parameter for the task.
*/
void anch_generic_task_function(void *pvParameter) {
  UNUSED_PARAMETER(pvParameter);

  //dwt_setrxtimeout(RESP_RX_TIMEOUT_UUS);

  dwt_setleds(DWT_LEDS_ENABLE);

  while (true) {
    anch_generic_run();
    /* Delay a task for a given number of ticks */
    // vTaskDelay(RNG_DELAY_MS);       // FIXME: non ci vuole in realt
    //    vTaskDelay(10);
    /* Tasks must be implemented to never return... */
  }
}