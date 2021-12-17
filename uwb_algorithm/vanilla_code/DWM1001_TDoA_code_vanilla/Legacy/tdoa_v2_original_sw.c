/*
 * tdoa_v2.c
 *
 *  Created on: Jul 25, 2019
 *      Author: marco.armellini
 */

#pragma GCC optimize("00")

#include "debug_lcd.h"
#include "deca_device_api.h"
#include "deca_regs.h"
#include "deca_spi.h"
#include "port.h"
#include <string.h>
#include <inttypes.h>

extern TIM_HandleTypeDef htim6;


/* ---------------------------------------
 * ANCH_MASTER
 *
 * ANCH_SLAVE_3_V3
 * ANCH_SLAVE_4_V3
 * ANCH_SLAVE_5_V3
 * ANCH_SLAVE_7_V3
 * ANCH_SLAVE_8_V3
 *
 * TWR_CALIBRATION_MASTER
 * TWR_CALIBRATION_SLAVE
 *
 * 16725 antenna5, 16725 antenna7, 16686 antenna4
 *
 * TOF 895  -> 420cm antenna 5 + 150 rxdelay
 * TOF 901  -> 423cm antenna 7 + correzione da riflessione (530)
 * TOF 1270 -> 596cm antenna 4 + 485 rxdelay
 *
 * ------------------------------------- */

// ============================================================================
/*TEST SU SYNC --> VERSIONE 2 FUNZIONANTE --> AGGIUSTARE ANTENNA DELAY! */
// ============================================================================
#define ANCH_MASTER
// ============================================================================
// ============================================================================

static dwt_config_t config = {
    2,               /* Channel number. */
    DWT_PRF_64M,     /* Pulse repetition frequency. */
    DWT_PLEN_512,   /* Preamble length. Used in TX only. */
    DWT_PAC16,       /* Preamble acquisition chunk size. Used in RX only. */
    9,               /* TX preamble code. Used in TX only. */
    9,               /* RX preamble code. Used in RX only. */
    1,               /* 0 to use standard SFD, 1 to use non-standard SFD. */
    DWT_BR_850K,     /* Data rate. */
    DWT_PHRMODE_STD, /* PHY header mode. */
    (513   + 64 - 16) /* SFD timeout (preamble length + 1 + SFD length - PAC size). Used in RX only. */
};

static dwt_config_t config3 = {
    2,               /* Channel number. */
    DWT_PRF_64M,     /* Pulse repetition frequency. */
    DWT_PLEN_256,   /* Preamble length. Used in TX only. */
    DWT_PAC16,       /* Preamble acquisition chunk size. Used in RX only. */
    9,               /* TX preamble code. Used in TX only. */
    9,               /* RX preamble code. Used in RX only. */
    1,               /* 0 to use standard SFD, 1 to use non-standard SFD. */
    DWT_BR_6M8,     /* Data rate. */
    DWT_PHRMODE_STD, /* PHY header mode. */
    (257 + 64 - 16) /* SFD timeout (preamble length + 1 + SFD length - PAC size). Used in RX only. */
};

static dwt_config_t config2 = {
    2,               /* Channel number. */
    DWT_PRF_64M,     /* Pulse repetition frequency. */
    DWT_PLEN_1024,   /* Preamble length. Used in TX only. */
    DWT_PAC32,       /* Preamble acquisition chunk size. Used in RX only. */
    9,               /* TX preamble code. Used in TX only. */
    9,               /* RX preamble code. Used in RX only. */
    1,               /* 0 to use standard SFD, 1 to use non-standard SFD. */
    DWT_BR_110K,     /* Data rate. */
    DWT_PHRMODE_STD, /* PHY header mode. */
    (1025 + 64 - 32) /* SFD timeout (preamble length + 1 + SFD length - PAC size). Used in RX only. */
};

#ifdef ANCH_MASTER

/*Nella versione 2 non codifico il time_tx usato per dwt_txdeleyed calcolato a 32 bit->
 * uso 3 messaggi 2 blink (1 con delay) e prendo il timestamp dei due blink->
 * sono pi� preciso e codifico la differenza in un messaggio finale
 * considero 10cm di distanza -> 333,56ps -> 21 dtu*/


#define APP_NAME "TX_MASTER"

#define TX_ANT_DLY 16436
#define RX_ANT_DLY 16436
#define RNG_DELAY_MS 200

// ********************************************************* TWR-INITIALIZATION *****************************************************************

static uint8 msg_init_twr[] = {0xC5, 0 , 'T', 'W', 'R', 0, 0};

#define ANCH_ID		1
#define NUM_ANCH    5  //slave only

static uint8 anch_idx;    // anch4 = 0 | anch5 = 1 | anch7 = 2 | anch8 = 3

// ************************************************************ TWR-CORRECTION ******************************************************************
static uint8 tx_poll_msg[]  = {0x41, 0x88, 0, 0xCA, 0xDE, 'W', 'A', 'V', 'E', 0x21, 0, 0};
static uint8 rx_resp_msg[]  = {0x41, 0x88, 0, 0xCA, 0xDE, 'V', 'E', 'W', 'A', 0x10, 0x02, 0, 0, 0, 0};
static uint8 tx_final_msg[] = {0x41, 0x88, 0, 0xCA, 0xDE, 'W', 'A', 'V', 'E', 0x23, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};

#define TWR_CYCLE 10
#define ALL_MSG_COMMON_LEN 10


#define ALL_MSG_SN_IDX				 2
#define FINAL_MSG_POLL_TX_TS_IDX 	10
#define FINAL_MSG_RESP_RX_TS_IDX 	14
#define FINAL_MSG_FINAL_TX_TS_IDX 	18
#define FINAL_MSG_TS_LEN			 4

static uint8 frame_seq_nb = 0;
#define RX_BUF_LEN 20
static uint8 rx_buffer[RX_BUF_LEN];

static uint32 status_reg = 0;

#define UUS_TO_DWT_TIME 65536

#define POLL_TX_TO_RESP_RX_DLY_UUS 300
#define RESP_RX_TO_FINAL_TX_DLY_UUS 3100
#define RESP_RX_TIMEOUT_UUS 2700
#define PRE_TIMEOUT 8

typedef signed long long int64;
typedef unsigned long long uint64;
static uint64 poll_tx_ts;
static uint64 resp_rx_ts;
static uint64 final_tx_ts;

// ------------------------------------------------------------ DEF ANCH SYNC ---------------------------------------------------------------------------------

static uint8 tx_init_blink[] = {0x41, 0x88, 0, 0xCA, 0xDE, 'S', 'Y', 'N', 'C', 0x19, 0, 0};
static uint8 tx_final_blink[]= {0x41, 0x88, 0, 0xCA, 0xDE, 'S', 'Y', 'N', 'C', 0x6, 0, 0 };
static uint8 tx_final_ts[]	 = {0x41, 0x88, 0, 0xCA, 0xDE, 'S', 'Y', 'N', 'C', 0x23, 0, 0, 0, 0, 0, 0};  //differenza in 32 bit

#define FINAL_MSG_TS_LEN 	4
#define BLINK_FRAME_SN_IDX 	2
#define TS_INT_IDX 			10
#define ALL_MSG_SN_IDX 		2

#define SYNC_CYCLE			50
#define TX_DELAY_MS 		100 					//sleep finale
#define DELAY_UUS 			20000  					//per fisare timestamp fisso un delay per decidere quando trasmettere
#define UUS_TO_DWT_TIME 	65536 					// fattore di conversione UUS in tempo DW1000

typedef unsigned long long uint64;
static uint64 final_tx_ts;        			//delay tx finale
static uint64 blink1_tx_ts;
static uint64 blink2_tx_ts;
static uint32 final_tx_time;

static void msg_set_idx_sync(uint8 *ts_field, uint8 ts);

// __________________________________________________________ DEF TDOA __________________________________________________________

static uint8 broadcast_blink[] = {0x41, 0x88, 0, 0xFF, 0, 0}; 	 //0xFFFF-> broadcast

#define TAG_IDX 		3
#define TAG_BLINK 		0x10
#define TDOA_CYCLE 		10000

#define RX_BUF_TAG 		6   						 //conta 1,2,3,4,...22 elementi
static uint8 tag_buffer[RX_BUF_TAG];

static uint64 ts_init_tdoa; 		// timestamp del msg di init del master
static uint64 tag_ts;				// timestamp in rx del blink del tag
static uint64 total_time;			// TEMPO TOTALE TRA INIT MSG E RISPOSTA DEL TAG


//_____________________ MSG_TDOA_MATLAB_DATA _________________________

#define TEST_LEN		4
#define TEST_IDX		0
#define TEST			0xC5
#define IDX_MSG_DIST	7
#define ANCH_IDX		1
#define ANCH4			0
#define ANCH5			1
#define ANCH7			2
#define ANCH8			3
#define ANCH3			4
#define LEN				3

typedef struct
{
  uint32 anch3;
  uint32 anch4;
  uint32 anch5;
  uint32 anch7;
  uint32 anch8;
} time_stamp_Anch_t;


// considero una distanza di 2 metri -> 6.6712819039630409915115342894984e-9 sec/15.65e-12 = 426 DWT_TIME
// #define DWT_TIME_UNITS		gi� definito nella libreria decawave
static double TDOA_TIME_A3;
static double TDOA_TIME_A4;
static double TDOA_TIME_A5;
static double TDOA_TIME_A7;
static double TDOA_TIME_A8;

static double distance_A3;
static double distance_A4;
static double distance_A5;
static double distance_A7;
static double distance_A8;

#define SPEED_OF_LIGHT 299702547

#define TEST_BUF 		14   						 //conta 1,2,3,4,...22 elementi
static uint8 test_buffer[TEST_BUF];
static void test_msg_get(const uint8 *ts_field, uint32 *ts);

//_________________________________________________________

// __________________________________________________________ TS FUNCTION __________________________________________________________

static uint64 get_tx_timestamp_u64(void);
static void msg_set_ts(uint8 *ts_field, uint64 ts);
static uint64 get_rx_timestamp_u64(void);
//static void tag_TIMESTAMP(uint64 *ts_tag);


int dw_main(void)
{

	lcd_display_str(APP_NAME);
	uart_display_str(APP_NAME);

	reset_DW1000(); /* Target specific drive of RSTn line into DW1000 low for a period. */
	port_set_dw1000_slowrate();
	if (dwt_initialise(DWT_LOADUCODE) == DWT_ERROR)
	{
		lcd_display_str("INIT FAILED");
		while (1)
		{ };
	}
	port_set_dw1000_fastrate();
	dwt_configure(&config);

	dwt_setrxantennadelay(RX_ANT_DLY);
	dwt_settxantennadelay(TX_ANT_DLY);
	dwt_setleds(DWT_LEDS_ENABLE);

	//TWR ranging si autogestisce nel caso di non risposta delle ancore ->
//	dwt_setrxaftertxdelay(POLL_TX_TO_RESP_RX_DLY_UUS);
//	dwt_setrxtimeout(RESP_RX_TIMEOUT_UUS);
//	dwt_setpreambledetecttimeout(PRE_TIMEOUT);


	//-------------------- TS_COLLECT --------------------------
	time_stamp_Anch_t TimeStamp_Anch;
	//----------------------------------------------------------

	while(1)
	{
		//		__________________________________________________________TWR_ANCH_SELECTION_____________________________________________________________________
		anch_idx = 0;
		while(anch_idx < NUM_ANCH)
		{
			HAL_TIM_Base_Init(&htim6);
			if(HAL_TIM_IC_Start_IT(&htim6, TIM_CHANNEL_1) != HAL_OK)
			{
				/* Starting Error */
				Error_Handler();
			}

			int init_ok;

			msg_init_twr[ANCH_ID] = anch_idx;
			dwt_writetxdata(sizeof(msg_init_twr), msg_init_twr, 0); /* Zero offset in TX buffer. */
			dwt_writetxfctrl(sizeof(msg_init_twr), 0, 0); /* Zero offset in TX buffer, ranging. */
			init_ok = dwt_starttx(DWT_START_TX_IMMEDIATE);

			if(init_ok == DWT_SUCCESS)
			{
				Sleep(100);
				int twr_cycle = 0;

				while(twr_cycle < TWR_CYCLE)
				{

					//	___________________________________________________________________TWR-CORRECTION__________________________________________________________________________________
					tx_poll_msg[ALL_MSG_SN_IDX] = frame_seq_nb;
					dwt_writetxdata(sizeof(tx_poll_msg), tx_poll_msg, 0); /* Zero offset in TX buffer. */
					dwt_writetxfctrl(sizeof(tx_poll_msg), 0, 1); /* Zero offset in TX buffer, ranging. */
					dwt_starttx(DWT_START_TX_IMMEDIATE | DWT_RESPONSE_EXPECTED);

					while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR)))
					{ };
					frame_seq_nb++;

					if (status_reg & SYS_STATUS_RXFCG)
					{
						uint32 frame_len;
						dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG | SYS_STATUS_TXFRS);

						frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFLEN_MASK;
						if (frame_len <= RX_BUF_LEN)
						{
							dwt_readrxdata(rx_buffer, frame_len, 0);
						}

						rx_buffer[ALL_MSG_SN_IDX] = 0;
						if (memcmp(rx_buffer, rx_resp_msg, ALL_MSG_COMMON_LEN) == 0)
						{
							uint32 final_tx_time;
							int ret;

							poll_tx_ts = get_tx_timestamp_u64();
							resp_rx_ts = get_rx_timestamp_u64();

							final_tx_time = (resp_rx_ts + (RESP_RX_TO_FINAL_TX_DLY_UUS * UUS_TO_DWT_TIME)) >> 8;
							dwt_setdelayedtrxtime(final_tx_time);

							final_tx_ts = (((uint64)(final_tx_time & 0xFFFFFFFEUL)) << 8) + TX_ANT_DLY;

							msg_set_ts(&tx_final_msg[FINAL_MSG_POLL_TX_TS_IDX], poll_tx_ts);
							msg_set_ts(&tx_final_msg[FINAL_MSG_RESP_RX_TS_IDX], resp_rx_ts);
							msg_set_ts(&tx_final_msg[FINAL_MSG_FINAL_TX_TS_IDX], final_tx_ts);

							tx_final_msg[ALL_MSG_SN_IDX] = frame_seq_nb;
							dwt_writetxdata(sizeof(tx_final_msg), tx_final_msg, 0); /* Zero offset in TX buffer. */
							dwt_writetxfctrl(sizeof(tx_final_msg), 0, 1); /* Zero offset in TX buffer, ranging. */
							ret = dwt_starttx(DWT_START_TX_DELAYED);

							if (ret == DWT_SUCCESS)
							{
								while (!(dwt_read32bitreg(SYS_STATUS_ID) & SYS_STATUS_TXFRS))
								{ };
								dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_TXFRS);
								frame_seq_nb++;

								twr_cycle++;

							}
						}
					}
					else
					{
						dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
						dwt_rxreset();
					}
					Sleep(RNG_DELAY_MS);
				}

			}
			else // se non spedito correttamente msg ad ancora
			{
				dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
				dwt_rxreset();
				continue;
			}
			anch_idx++;
			Sleep(10);
		}
		uint32 time_cnt = TIM6->CNT; // 1tick = 1ms (pre-scaler 72000)
			//	________________________________________________________________________________________________________________________________________________________________

			//	___________________________________________________________________ SYNC-PART ________________________________________________________________________

//		int sync_cycle = 0;
//		while(sync_cycle < SYNC_CYCLE)
//		{
//			final_tx_time = 0;
//
//			dwt_writetxdata(sizeof(tx_init_blink), tx_init_blink, 0);
//			dwt_writetxfctrl(sizeof(tx_init_blink), 0, 1);
//
//			int ret1;
//			ret1 = dwt_starttx(DWT_START_TX_IMMEDIATE);
//			if(ret1 == DWT_SUCCESS)
//			{
//				//se ho spedito correttamente
//				while (!(dwt_read32bitreg(SYS_STATUS_ID) & SYS_STATUS_TXFRS))
//				{ };
//				dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_TXFRS);
//
//				// --------------------------- TIMESTAMP INIT -------------------------------
//				blink1_tx_ts = get_tx_timestamp_u64();
//				// --------------------------------------------------------------------------
//
//				//---------------------------------------------------------------------------------------------------------
//				final_tx_time = (blink1_tx_ts + (DELAY_UUS * UUS_TO_DWT_TIME)) >> 8;  					//delay per fissare trasmissione msg con delta_timestamp
//				dwt_setdelayedtrxtime(final_tx_time);                									//set tx delayed
//
//				final_tx_ts = (((uint64)((final_tx_time) & 0xFFFFFFFEUL)) << 8) + TX_ANT_DLY;
//
//				// --------------------------------- SECONDO BLINK RITARDATO -----------------------------------------------
//
//				dwt_writetxdata(sizeof(tx_final_blink), tx_final_blink, 0);
//				dwt_writetxfctrl(sizeof(tx_final_blink), 0, 1);
//
//				int ret2;
//				ret2 = dwt_starttx(DWT_START_TX_DELAYED);  												//inizia a tx al delay prestabilito: final_tx_time
//
//				if(ret2 == DWT_SUCCESS)
//				{
//					//se ho spedito correttamente
//					while (!(dwt_read32bitreg(SYS_STATUS_ID) & SYS_STATUS_TXFRS))
//					{ };
//					dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_TXFRS);
//
//
//					// --------------------------- TIMESTAMP FINAL -------------------------------
//					blink2_tx_ts = get_tx_timestamp_u64();
//					// ---------------------------------------------------------------------------
//
//					//-------------------------------CALCOLO DELTA TIMESTAMP --------------------------------------------------------------------------
//
//					uint32 delta_ts;
//					delta_ts = blink2_tx_ts - blink1_tx_ts;
//					msg_set_ts(&tx_final_ts[TS_INT_IDX], delta_ts);    			//NB. funzione aggiunge zeri in automatico->in watchexpr il programma non li mostra ma ci sono!!!
//					msg_set_idx_sync(&tx_final_ts[ALL_MSG_SN_IDX], sync_cycle);
//
//					dwt_writetxdata(sizeof(tx_final_ts), tx_final_ts, 0); 		        /* Zero offset in TX buffer. */
//					dwt_writetxfctrl(sizeof(tx_final_ts), 0, 1); 			        	/* Zero offset in TX buffer, ranging. */
//
//					int ret3;
//					ret3 = dwt_starttx(DWT_START_TX_IMMEDIATE);  			        	//inizia a tx al delay prestabilito: final_tx_time
//
//					if(ret3 == DWT_SUCCESS)
//					{
//						while (!(dwt_read32bitreg(SYS_STATUS_ID) & SYS_STATUS_TXFRS))
//						{ };
//						dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_TXFRS);
//
//						sync_cycle++;
//						HAL_Delay(10);
//						//char output[32] = "";
//						//sprintf(output,"DELTA_TS: %d", delta_ts);
//						//lcd_display_str(output);
//					}
//					else
//					{					//in caso di errore reset
//						dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
//						dwt_rxreset();
//					}
//				}
//				else
//				{				//in caso di errore reset
//					dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
//					dwt_rxreset();
//				}
//			}
//			else
//			{			//in caso di errore reset
//				dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
//				dwt_rxreset();
//			}
//
//		}

		//	__________________________________________________________ TDOA-PART __________________________________________________________

		/*prendo il timestamp della tx del master e in rx dello slave, poi aspetto il blink del tag e prendo il timestamp, noto il tempo di volo tra le due ancore
		 * calcolo TDOA */
		int i = 0;
		while(i < TDOA_CYCLE)
		{
			uint32 time_cnt = 0;
			//========================== START TIME COUNTER ===============================
//			HAL_TIM_Base_Init(&htim6);
//			if(HAL_TIM_IC_Start_IT(&htim6, TIM_CHANNEL_1) != HAL_OK)
//			{
//				/* Starting Error */
//				Error_Handler();
//			}

			dwt_writetxdata(sizeof(broadcast_blink), broadcast_blink, 0);
			dwt_writetxfctrl(sizeof(broadcast_blink), 0, 1);
			dwt_starttx(DWT_START_TX_IMMEDIATE);// | DWT_RESPONSE_EXPECTED);
			dwt_rxenable(DWT_START_RX_IMMEDIATE);

			// --------------------------- RX TAG BLINK ----------------------------------

			while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_ERR)))
			{ };

			if (status_reg & SYS_STATUS_RXFCG)
			{
				uint32 frame_len;
				dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG | SYS_STATUS_TXFRS);

				frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFLEN_MASK;

				if (frame_len <= RX_BUF_TAG)
				{
					dwt_readrxdata(tag_buffer, frame_len, 0);
				}

				if (tag_buffer[TAG_IDX] == TAG_BLINK)
				{
					//--------------- TIMESTAMP TAG BLINK ------------------------
					tag_ts = get_rx_timestamp_u64();
					//------------------------------------------------------------

					//---------------- TIMESTAMP INIT MASTER ---------------------
					ts_init_tdoa = get_tx_timestamp_u64();
					//------------------------------------------------------------

					total_time = tag_ts - ts_init_tdoa;

					//char output[32] = "";
					//sprintf(output,"TS_TAG: %d", total_time);
					//lcd_display_str(output);

					//_____________________________________ MSG_TDOA_MATLAB_DATA ____________________________________________
					int anch_count = 0;
					while(anch_count < NUM_ANCH)
					{
						dwt_rxenable(DWT_START_RX_IMMEDIATE);
						while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_ERR)))
						{ };

						if (status_reg & SYS_STATUS_RXFCG)
						{
							uint32 frame_len;
							dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG | SYS_STATUS_TXFRS);
							frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFLEN_MASK;

							if (frame_len <= TEST_BUF)
							{
								dwt_readrxdata(test_buffer, frame_len, 0);
							}

							if (test_buffer[TEST_IDX] == TEST)
							{

								//***************** COLLECT ANCH TimeStamp **********************

								if(test_buffer[ANCH_IDX] == ANCH3)
								{
									test_msg_get(&test_buffer[IDX_MSG_DIST], &TimeStamp_Anch.anch3);

									int64 TDOA_DWT_TIME_A3 = total_time - (uint64)TimeStamp_Anch.anch3;
									TDOA_TIME_A3 = TDOA_DWT_TIME_A3 * DWT_TIME_UNITS;

									anch_count++;
								}

								if(test_buffer[ANCH_IDX] == ANCH4)
								{
									test_msg_get(&test_buffer[IDX_MSG_DIST], &TimeStamp_Anch.anch4);

									int64 TDOA_DWT_TIME_A4 = total_time - (uint64)TimeStamp_Anch.anch4;
									TDOA_TIME_A4 = TDOA_DWT_TIME_A4 * DWT_TIME_UNITS;

									anch_count++;
								}

								if(test_buffer[ANCH_IDX] == ANCH5)
								{
									test_msg_get(&test_buffer[IDX_MSG_DIST], &TimeStamp_Anch.anch5);

									int64 TDOA_DWT_TIME_A5 = total_time - (uint64)TimeStamp_Anch.anch5;
									TDOA_TIME_A5 = TDOA_DWT_TIME_A5 * DWT_TIME_UNITS;

									anch_count++;
								}

								if(test_buffer[ANCH_IDX] == ANCH7)
								{
									test_msg_get(&test_buffer[IDX_MSG_DIST], &TimeStamp_Anch.anch7);

									int64 TDOA_DWT_TIME_A7 = total_time - (uint64)TimeStamp_Anch.anch7;
									TDOA_TIME_A7 = TDOA_DWT_TIME_A7 * DWT_TIME_UNITS;

									anch_count++;
								}

								if(test_buffer[ANCH_IDX] == ANCH8)
								{
									test_msg_get(&test_buffer[IDX_MSG_DIST], &TimeStamp_Anch.anch8);

									int64 TDOA_DWT_TIME_A8 = total_time - (uint64)TimeStamp_Anch.anch8;
									TDOA_TIME_A8 = TDOA_DWT_TIME_A8 * DWT_TIME_UNITS;

									anch_count++;
								}
								//	************************************************************
							}
							else
							{
								dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
								dwt_rxreset();
							}
						}
						else
						{
							dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
							dwt_rxreset();
						}
					}

					distance_A3 = TDOA_TIME_A3 * SPEED_OF_LIGHT;
					distance_A4 = TDOA_TIME_A4 * SPEED_OF_LIGHT;
					distance_A5 = TDOA_TIME_A5 * SPEED_OF_LIGHT;
					distance_A7 = TDOA_TIME_A7 * SPEED_OF_LIGHT;
					distance_A8 = TDOA_TIME_A8 * SPEED_OF_LIGHT;

					char output[64] = "";
					char output_LCD[32] = "";
					//MATLAB
					uint32 timestamp[6] = {(uint32)total_time, TimeStamp_Anch.anch3, TimeStamp_Anch.anch4, TimeStamp_Anch.anch5, TimeStamp_Anch.anch7, TimeStamp_Anch.anch8};
					sprintf(output,"%lu %lu %lu %lu %lu %lu", (uint32)total_time, TimeStamp_Anch.anch3, TimeStamp_Anch.anch4, TimeStamp_Anch.anch5, TimeStamp_Anch.anch7, TimeStamp_Anch.anch8);
					uart_display_str(output);

					sprintf(output_LCD,"TS: %d", total_time);
					lcd_display_str(output_LCD);
//					HAL_Delay(50);

					//DEBUG
//					sprintf(output,"[%d] delta4: %f | delta5: %f", i, distance_A4, distance_A5);
//					uart_display_str(output);
//					sprintf(output,"[%d] delta7: %f | delta8: %f | delta3: %f", i, distance_A7, distance_A8, distance_A3);
//					uart_display_str(output);


//					if(HAL_TIM_IC_Stop_IT(&htim6, TIM_CHANNEL_1) != HAL_OK)
//					{
//						/* Starting Error */
//						Error_Handler();
//					}
//
//
//					uint32 time_cnt = TIM6->CNT; // 1tick = 2us (pre-scaler 144)
					//========================== STOP TIME COUNTER ===============================
				}
			}
			else
			{
				dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
				dwt_rxreset();
				char output[32] = "";
				sprintf(output,"error_tag");
				uart_display_str(output);
			}

			i++;
		}
		Sleep(10);  //safe wait a caso in realt� col tempo che fa i conti e butta i dati le ancore saranno gi� in ascolto
	}
}

static uint64 get_tx_timestamp_u64(void)
{
	uint8 ts_tab[5];
	uint64 ts = 0;
	int i;
	dwt_readtxtimestamp(ts_tab); // dwt_readfromdevice(TX_TIME_ID, TX_TIME_TX_STAMP_OFFSET, TX_TIME_TX_STAMP_LEN, ts_tab) ; //;
	for (i = 4; i >= 0; i--)
	{
		ts <<= 8;
		ts |= ts_tab[i];
	}
	return ts;
}

static uint64 get_rx_timestamp_u64(void)
{
    uint8 ts_tab[5];
    uint64 ts = 0;
    int i;
    dwt_readrxtimestamp(ts_tab);
    for (i = 4; i >= 0; i--)
    {
        ts <<= 8;
        ts |= ts_tab[i];
    }
    return ts;
}

//static void tag_TIMESTAMP(uint64 *ts_tag)
//{
//    uint8 ts_tab[5];
//    int i;
//    dwt_readrxtimestamp(ts_tab);
//    for (i = 4; i >= 0; i--)
//    {
//    	*ts_tag <<= 8;
//    	*ts_tag |= ts_tab[i];
//    }
//}

static void msg_set_ts(uint8 *ts_field, uint64 ts)
{
	int i;
	for (i = 0; i < FINAL_MSG_TS_LEN; i++)
	{
		ts_field[i] = (uint8) ts;
		ts >>= 8;
	}
}

static void msg_set_idx_sync(uint8 *ts_field, uint8 ts)
{
	int i;
	for (i = 0; i < 1; i++)
	{
		ts_field[i] = (uint8) ts;
		ts >>= 8;
	}
}

//_____________________ MSG_TEST _________________________
static void test_msg_get(const uint8 *ts_field, uint32 *ts)
{
    int i;
    *ts = 0;
    for (i = 0; i < TEST_LEN; i++)
    {
        *ts += ts_field[i] << (i * 8);
    }
}
//_________________________________________________________
#endif


#ifdef ANCH_SLAVE_4_V3

#define APP_NAME "RX_SYNC_A4"

//#pragma GCC optimize ("00")

#define ANCH4_ID	0

//	***************************************************************** TWR-CORRECTION **************************************************************************************

#define RX_BUF_TWR 	7		   						 //conta 1,2,3,4,...22 elementi
static uint8 twr_buffer[RX_BUF_TWR];

#define ANCH_CODE	1

#define TX_ANT_DLY 16436
#define RX_ANT_DLY 16436
//#define POSITION 5960 //in mm

static uint8 rx_poll_msg[] = {0x41, 0x88, 0, 0xCA, 0xDE, 'W', 'A', 'V', 'E', 0x21, 0, 0};
static uint8 tx_resp_msg[] = {0x41, 0x88, 0, 0xCA, 0xDE, 'V', 'E', 'W', 'A', 0x10, 0x02, 0, 0, 0, 0};
static uint8 rx_final_msg[] = {0x41, 0x88, 0, 0xCA, 0xDE, 'W', 'A', 'V', 'E', 0x23, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};

#define TWR_CYCLE 					10
#define ALL_MSG_SN_IDX 				2
#define FINAL_MSG_POLL_TX_TS_IDX 	10
#define FINAL_MSG_RESP_RX_TS_IDX 	14
#define FINAL_MSG_FINAL_TX_TS_IDX 	18
#define FINAL_MSG_TS_LEN 			4

static uint8 frame_seq_nb = 0;
#define RX_BUF_LEN 24
static uint8 rx_buffer[RX_BUF_LEN];
static uint32 status_reg = 0;

#define UUS_TO_DWT_TIME 				65536
#define POLL_RX_TO_RESP_TX_DLY_UUS 2750
#define RESP_TX_TO_FINAL_RX_DLY_UUS 500
#define FINAL_RX_TIMEOUT_UUS 3300
#define PRE_TIMEOUT 8

typedef signed long long int64;
typedef unsigned long long uint64;
static uint64 poll_rx_ts;
static uint64 resp_tx_ts;
static uint64 final_rx_ts;

#define SPEED_OF_LIGHT 299702547

//static double tof;
//static double distance;

static void final_msg_get_ts(const uint8 *ts_field, uint32 *ts);
static uint64 get_tx_timestamp_u64(void);

// ------------------------------------------------------------ DEF SYNC TIMESTAMP ---------------------------------------------------------------------------------
//#define CORR_DLY   370      //370->5, 0->4, ->7

#define START_BLINK 0x19
#define FINAL_BLINK 0x6
#define FINAL_MSG   0x23


#define ALL_MSG_COMMON_LEN 		  	 5
#define SYNC_CYCLE_IDX				 2
#define CODE_IDX 					 9
#define FINAL_MSG_POLL_TX_TS_IDX  	 10

#define FINAL_MSG_TS_LEN 		  	 4


#define SYNC_BUF_LEN 12   						 //conta 1,2,3,4,...22 elementi
static uint8 sync_buffer[SYNC_BUF_LEN];

static uint64 sync_poll_rx_ts;
static uint64 sync_final_rx_ts;
static double corr_factor[50];
static double total;

static uint64 get_rx_timestamp_u64(void);
static void get_ts(const uint8 *ts_field, uint32 *ts);
static void get_msg_idx(const uint8 *ts_field, uint8 *ts);

// ---------------------------------------------------------- DEF INIT ---------------------------------------------------------------------------------------
#define INIT_TDOA_MSG   0xFF
#define CODE_INIT  3

// ---------------------------------------------------------- DEF TDOA ---------------------------------------------------------------------------------------

#define UUS_TO_DWT_TIME		65536 		//1 uus = 512 / 499.2 �s and 1 �s = 499.2 * 128 dtu | UWB microsecond (uus) to device time unit (dtu, around 15.65 ps) conversion factor�

#define TAG_IDX				3
#define TAG_BLINK			0x10



#define BUF_INIT_TDOA 		6   					 //conta 1,2,3,4,...22 elementi
static uint8 tdoa_init_buffer[BUF_INIT_TDOA];

#define RX_BUF_TAG 			6 						 //conta 1,2,3,4,...22 elementi
static uint8 tag_buffer[RX_BUF_TAG];

static uint64 rx_init_ts;
static uint64 rx_init_ts_corr;
static uint64 ts;
static uint64 ts_corretto;
static uint64 total_ts;

static double dly_corr_factor;         // fattore di correzzione in dtu del delay pre-impostato in modo che sia in synch con il conteggio del master
static double tof_media;
static double tof_tot;
static int64 CORR_DLY;

//___________________ MSG_RESP_TDOA______________________
static uint8 tdoa_resp[] = {0xC5, 0, 0, 'T', 'E', 'S', 'T', 0, 0, 0, 0, 0, 0};

#define IDX_MSG_DIST  	7
#define TEST_LEN		4
#define ANCH_IDX		1
#define TAG_IDX			3
#define TOF				1010    //POSIZIONE (2.12, 4.24)

#define TIME_SLOT	383386580   //in UWB tick ~ 6ms

static void test_msg_set(uint8 *ts_field, uint64 ts);
static void msg_set_idx(uint8 *ts_field, uint8 ts);
//___________________________________________________


int dw_main(void)
{
	lcd_display_str(APP_NAME);
	reset_DW1000(); /* Target specific drive of RSTn line into DW1000 low for a period. */
	port_set_dw1000_slowrate();
	if (dwt_initialise(DWT_LOADUCODE) == DWT_ERROR)
	{
		lcd_display_str("INIT FAILED");
		while (1)
		{ };
	}
	port_set_dw1000_fastrate();
	dwt_configure(&config);


	dwt_setrxantennadelay(RX_ANT_DLY);    //non vanno..conpensati da sync?
	dwt_settxantennadelay(TX_ANT_DLY);


	dwt_setleds(DWT_LEDS_ENABLE);


	while (1)
	{
		//applicazione stai in ascolta di msg init (ogni parte prevede un msg di inizializzazione)
		dwt_setrxtimeout(0);

		dwt_rxenable(DWT_START_RX_IMMEDIATE);
		while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR)))
		{ };

		// ************************ RX_QUALSIASICOSA *****************************

		if (status_reg & SYS_STATUS_RXFCG)
		{
			uint32 frame_len;
			dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);
			frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;

			switch(frame_len)
			{
			//	 _____________________________________________________________________TWR_INIT____________________________________________________________________________________
			case(RX_BUF_TWR):   //lung 7+ check codice ancora

				dwt_readrxdata(twr_buffer, frame_len, 0);

				if (twr_buffer[ANCH_CODE] == ANCH4_ID)
				{
					//	___________________________________________________________________TWR-CORRECTION__________________________________________________________________________________

					int twr_cycle = 0;  //ciclo una volta sola il controllo del twr
					tof_tot = 0;

					while(twr_cycle < TWR_CYCLE)
					{
						dwt_setrxtimeout(0);
						dwt_rxenable(DWT_START_RX_IMMEDIATE);

						while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR)))
						{ };
						if (status_reg & SYS_STATUS_RXFCG)
						{
							uint32 frame_len;
							dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);

							frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;
							if (frame_len <= RX_BUFFER_LEN)
							{
								dwt_readrxdata(rx_buffer, frame_len, 0);
							}
							rx_buffer[ALL_MSG_SN_IDX] = 0;
							if (memcmp(rx_buffer, rx_poll_msg, ALL_MSG_COMMON_LEN) == 0)
							{
								uint32 resp_tx_time;
								int ret;

								poll_rx_ts = get_rx_timestamp_u64();

								resp_tx_time = (poll_rx_ts + (POLL_RX_TO_RESP_TX_DLY_UUS * UUS_TO_DWT_TIME)) >> 8;
								dwt_setdelayedtrxtime(resp_tx_time);

								dwt_setrxaftertxdelay(RESP_TX_TO_FINAL_RX_DLY_UUS);
								dwt_setrxtimeout(FINAL_RX_TIMEOUT_UUS);

								tx_resp_msg[ALL_MSG_SN_IDX] = frame_seq_nb;
								dwt_writetxdata(sizeof(tx_resp_msg), tx_resp_msg, 0); /* Zero offset in TX buffer. */
								dwt_writetxfctrl(sizeof(tx_resp_msg), 0, 1); /* Zero offset in TX buffer, ranging. */
								ret = dwt_starttx(DWT_START_TX_DELAYED | DWT_RESPONSE_EXPECTED);
								if (ret == DWT_ERROR)
								{
									continue;
								}

								while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR)))
								{ };

								frame_seq_nb++;

								if (status_reg & SYS_STATUS_RXFCG)
								{
									dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG | SYS_STATUS_TXFRS);

									frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFLEN_MASK;
									if (frame_len <= RX_BUF_LEN)
									{
										dwt_readrxdata(rx_buffer, frame_len, 0);
									}

									rx_buffer[ALL_MSG_SN_IDX] = 0;
									if (memcmp(rx_buffer, rx_final_msg, ALL_MSG_COMMON_LEN) == 0)
									{
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
										//							tof = tof_dtu * DWT_TIME_UNITS;
										//							distance = tof * SPEED_OF_LIGHT;
										tof_tot = tof_tot + tof_dtu;
										twr_cycle++;
									}
								}
								else
								{
									dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
									dwt_rxreset();
								}
							}
						}
						else
						{
							dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
							dwt_rxreset();
						}

					}

					tof_media = tof_tot/10;
					CORR_DLY  = (int64)(TOF - tof_media);
					twr_cycle = 0;
				}
				else
				{
					Sleep(500); //se hai ricevuto un pacchetto di ranging e non � il tuo dormitela e poi rimettiti in rx
					continue;
				}

				break;

			//	__________________________________________________SYNC-PART ____________________________________________________________
			case(SYNC_BUF_LEN):    //lung 12, il sync si fa in parallelo perch� il master invia solo pacchetti

				total = 0;
				dwt_readrxdata(sync_buffer, frame_len, 0);

				// ---------------------------- CHECK BLINK_CODE ----------------------------------
				if (sync_buffer[CODE_IDX] == START_BLINK)
				{
					sync_poll_rx_ts = get_rx_timestamp_u64();  //primo timestamp

					dwt_rxenable(DWT_START_RX_IMMEDIATE);
					while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_ERR)))
					{ };

					// ---------------------------- ARRIVA SECONDO BLINK ----------------------------------
					if (status_reg & SYS_STATUS_RXFCG)
					{
						uint32 frame_len;
						dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);

						frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;
						if (frame_len <= SYNC_BUF_LEN)
						{
							dwt_readrxdata(sync_buffer, frame_len, 0);
						}
						// ---------------------------- CHECK BLINK_CODE ----------------------------------
						if (sync_buffer[CODE_IDX] == FINAL_BLINK)
						{
							sync_final_rx_ts = get_rx_timestamp_u64();  	//final timestamp

							dwt_rxenable(DWT_START_RX_IMMEDIATE);
							while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_ERR)))
							{ };

							// ----------------------------ARRIVA MSG FINALE ----------------------------------
							if (status_reg & SYS_STATUS_RXFCG)
							{
								uint32 frame_len;
								dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);

								frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;
								if (frame_len <= RX_BUFFER_LEN)
								{
									dwt_readrxdata(rx_buffer, frame_len, 0);
								}
								// ---------------------------- CHECK FINAL_CODE ----------------------------------
								if (rx_buffer[CODE_IDX] == FINAL_MSG)
								{
									//estraggo dato da ANCH_INITIATOR
									uint8 sync_count = 0;
									uint32 timer_master;
									uint64 timer_anch=0;
									int64  delta;

									get_ts(&rx_buffer[FINAL_MSG_POLL_TX_TS_IDX], &timer_master);
									get_msg_idx(&rx_buffer[SYNC_CYCLE_IDX], &sync_count);
									timer_anch 	= (uint64)(sync_final_rx_ts - sync_poll_rx_ts );

									delta = (int64)(timer_master - timer_anch);
									corr_factor[sync_count] = (double)timer_anch/(uint64)timer_master;

									if(sync_count == 49)
									{
										int j;

										for(j = 0; j < 50; j++)
										{
											total = total + corr_factor[j];
										}
										dly_corr_factor = total/50;
									}
								}
								else
								{
									dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
									dwt_rxreset();
								}
							}
							else
							{
								dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
								dwt_rxreset();
							}
						}
						else
						{
							dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
							dwt_rxreset();
						}
					}
					else
					{
						dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
						dwt_rxreset();
					}
				}
				else
				{
					dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
					dwt_rxreset();
					continue;
				}

				break;

				//***************************************************** TDOA ***************************************************************
			case(BUF_INIT_TDOA):

									dwt_readrxdata(tdoa_init_buffer, frame_len, 0);

			if (tdoa_init_buffer[CODE_INIT] == INIT_TDOA_MSG)
			{
				rx_init_ts = get_rx_timestamp_u64();
				rx_init_ts_corr = (uint64)(rx_init_ts - (uint64)TOF + CORR_DLY);

				dwt_rxenable(DWT_START_RX_IMMEDIATE);
				while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_ERR)))
				{ };

				// ---------------------------- TAG BLINK ----------------------------------
				if (status_reg & SYS_STATUS_RXFCG)
				{
					uint32 frame_len;
					dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);
					frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;

					if (frame_len <= RX_BUF_TAG)
					{
						dwt_readrxdata(tag_buffer, frame_len, 0);
					}

					if (tag_buffer[TAG_IDX] == TAG_BLINK)
					{
						uint8 tag_ID;

						ts = get_rx_timestamp_u64();
						ts_corretto = (uint64)(ts - CORR_DLY);


						get_msg_idx(&tag_buffer[1], &tag_ID);

						total_ts = (uint64)(ts_corretto - rx_init_ts_corr);

						char output[32] = "";
						sprintf(output,"%d", total_ts);
						lcd_display_str(output);

						Sleep(5);

						test_msg_set(&tdoa_resp[IDX_MSG_DIST], total_ts);
						msg_set_idx(&tdoa_resp[ANCH_IDX], ANCH4_ID);
						msg_set_idx(&tdoa_resp[TAG_IDX], tag_ID);

						dwt_writetxdata(sizeof(tdoa_resp), tdoa_resp, 0);
						dwt_writetxfctrl(sizeof(tdoa_resp), 0, 0);


						dwt_starttx(DWT_START_TX_IMMEDIATE);

						while (!(dwt_read32bitreg(SYS_STATUS_ID) & SYS_STATUS_TXFRS))
						{ };
						dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_TXFRS);
						//*************************************************************************************************

					}
					else
					{
						dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
						dwt_rxreset();
					}
				}
				else
				{
					dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
					dwt_rxreset();
				}
			}
			else
			{
				dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
				dwt_rxreset();
			}

			break;

			//se ricevo msg che non centra
			default: continue;

			} //SWITCH

			//			break;  //ogni volta che esco da switch rivai in rx mode e checca quello che arriva
		} //IF RX (LISTEN)

	} // while(1)

} //MAIN


static uint64 get_rx_timestamp_u64(void)
{
	uint8 ts_tab[5];
	uint64 ts = 0;
	int i;
	dwt_readrxtimestamp(ts_tab);
	for (i = 4; i >= 0; i--)
	{
		ts <<= 8;
		ts |= ts_tab[i];
	}
	return ts;
}

static void get_ts(const uint8 *ts_field, uint32 *ts)
{
	int i;
	*ts = 0;
	for (i = 0; i < FINAL_MSG_TS_LEN; i++)
	{
		*ts += ts_field[i] << (i * 8);
	}
}

static void get_msg_idx(const uint8 *ts_field, uint8 *ts)
{
	int i;
	*ts = 0;
	for (i = 0; i < 1; i++)
	{
		*ts += ts_field[i] << (i * 8);
	}
}

static uint64 get_tx_timestamp_u64(void)
{
	uint8 ts_tab[5];
	uint64 ts = 0;
	int i;
	dwt_readtxtimestamp(ts_tab);
	for (i = 4; i >= 0; i--)
	{
		ts <<= 8;
		ts |= ts_tab[i];
	}
	return ts;
}

static void final_msg_get_ts(const uint8 *ts_field, uint32 *ts)
{
	int i;
	*ts = 0;
	for (i = 0; i < FINAL_MSG_TS_LEN; i++)
	{
		*ts += ts_field[i] << (i * 8);
	}
}


//___________________ MSG_RESP_TDOA__________________
static void test_msg_set(uint8 *ts_field, uint64 ts)
{
	int i;
	for (i = 0; i < TEST_LEN; i++)
	{
		ts_field[i] = (uint8) ts;
		ts >>= 8;
	}
}

static void msg_set_idx(uint8 *ts_field, uint8 ts)
{
	int i;
	for (i = 0; i < 1; i++)
	{
		ts_field[i] = (uint8) ts;
		ts >>= 8;
	}
}
//____________________________________________________
#endif



#ifdef ANCH_SLAVE_5_V3

#define APP_NAME "RX_SYNC_A5"

//#pragma GCC optimize ("00")

#define ANCH5_ID	1

//	***************************************************************** TWR-CORRECTION **************************************************************************************

#define RX_BUF_TWR 	7		   						 //conta 1,2,3,4,...22 elementi
static uint8 twr_buffer[RX_BUF_TWR];

#define ANCH_CODE	1

#define TX_ANT_DLY 16436
#define RX_ANT_DLY 16436
//#define POSITION 5960 //in mm

static uint8 rx_poll_msg[] = {0x41, 0x88, 0, 0xCA, 0xDE, 'W', 'A', 'V', 'E', 0x21, 0, 0};
static uint8 tx_resp_msg[] = {0x41, 0x88, 0, 0xCA, 0xDE, 'V', 'E', 'W', 'A', 0x10, 0x02, 0, 0, 0, 0};
static uint8 rx_final_msg[] = {0x41, 0x88, 0, 0xCA, 0xDE, 'W', 'A', 'V', 'E', 0x23, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};

#define TWR_CYCLE 					10
#define ALL_MSG_SN_IDX 				2
#define FINAL_MSG_POLL_TX_TS_IDX 	10
#define FINAL_MSG_RESP_RX_TS_IDX 	14
#define FINAL_MSG_FINAL_TX_TS_IDX 	18
#define FINAL_MSG_TS_LEN 			4

static uint8 frame_seq_nb = 0;
#define RX_BUF_LEN 24
static uint8 rx_buffer[RX_BUF_LEN];
static uint32 status_reg = 0;

#define UUS_TO_DWT_TIME 				65536
#define POLL_RX_TO_RESP_TX_DLY_UUS 		2750
#define RESP_TX_TO_FINAL_RX_DLY_UUS 	500
#define FINAL_RX_TIMEOUT_UUS 			3300
#define PRE_TIMEOUT 					8

typedef signed long long int64;
typedef unsigned long long uint64;
static uint64 poll_rx_ts;
static uint64 resp_tx_ts;
static uint64 final_rx_ts;

#define SPEED_OF_LIGHT 299702547

//static double tof;
//static double distance;

static void final_msg_get_ts(const uint8 *ts_field, uint32 *ts);
static uint64 get_tx_timestamp_u64(void);

// ------------------------------------------------------------ DEF SYNC TIMESTAMP ---------------------------------------------------------------------------------
//#define CORR_DLY   370      //370->5, 0->4, ->7

#define START_BLINK 0x19
#define FINAL_BLINK 0x6
#define FINAL_MSG   0x23

#define SYNC_CYCLE 					 30
#define ALL_MSG_COMMON_LEN 		  	 5
#define SYNC_CYCLE_IDX				 2
#define CODE_IDX 					 9
#define FINAL_MSG_POLL_TX_TS_IDX  	 10

#define FINAL_MSG_TS_LEN 		  	 4


#define SYNC_BUF_LEN 12   						 //conta 1,2,3,4,...22 elementi
static uint8 sync_buffer[SYNC_BUF_LEN];

static uint64 sync_poll_rx_ts;
static uint64 sync_final_rx_ts;
static double corr_factor[50];
static double total;

static uint64 get_rx_timestamp_u64(void);
static void get_ts(const uint8 *ts_field, uint32 *ts);
static void get_msg_idx(const uint8 *ts_field, uint8 *ts);

// ---------------------------------------------------------- DEF INIT ---------------------------------------------------------------------------------------
#define INIT_TDOA_MSG   0xFF
#define CODE_INIT  3

// ---------------------------------------------------------- DEF TDOA ---------------------------------------------------------------------------------------

#define UUS_TO_DWT_TIME		65536 		//1 uus = 512 / 499.2 �s and 1 �s = 499.2 * 128 dtu | UWB microsecond (uus) to device time unit (dtu, around 15.65 ps) conversion factor�

#define TAG_IDX				3
#define TAG_BLINK			0x10



#define BUF_INIT_TDOA 		6   					 //conta 1,2,3,4,...22 elementi
static uint8 tdoa_init_buffer[BUF_INIT_TDOA];

#define RX_BUF_TAG 			6 						 //conta 1,2,3,4,...22 elementi
static uint8 tag_buffer[RX_BUF_TAG];

static uint64 rx_init_ts;
static uint64 rx_init_ts_corr;
static uint64 ts;
static uint64 ts_corretto;
static uint64 total_ts;

static double dly_corr_factor;         // fattore di correzzione in dtu del delay pre-impostato in modo che sia in synch con il conteggio del master
static double tof_media;
static double tof_tot;
static int64 CORR_DLY;

//___________________ MSG_RESP_TDOA______________________
static uint8 tdoa_resp[] = {0xC5, 0, 0, 'T', 'E', 'S', 'T', 0, 0, 0, 0, 0, 0};

#define IDX_MSG_DIST  	7
#define TEST_LEN		4
#define ANCH_IDX		1
#define TAG_IDX			3
#define TOF				1010 //POSIZIONE (-2.12, 4.24)

#define TIME_SLOT	383386580   //in UWB tick ~ 6ms

static void test_msg_set(uint8 *ts_field, uint64 ts);
static void msg_set_idx(uint8 *ts_field, uint8 ts);
//___________________________________________________


int dw_main(void)
{
	lcd_display_str(APP_NAME);
	reset_DW1000(); /* Target specific drive of RSTn line into DW1000 low for a period. */
	port_set_dw1000_slowrate();
	if (dwt_initialise(DWT_LOADUCODE) == DWT_ERROR)
	{
		lcd_display_str("INIT FAILED");
		while (1)
		{ };
	}
	port_set_dw1000_fastrate();
	dwt_configure(&config);

	dwt_setrxantennadelay(RX_ANT_DLY);    //non vanno..conpensati da sync?
	dwt_settxantennadelay(TX_ANT_DLY);


	dwt_setleds(DWT_LEDS_ENABLE);

	while (1)
	{
		//applicazione stai in ascolta di msg init (ogni parte prevede un msg di inizializzazione)
		dwt_setrxtimeout(0);

		dwt_rxenable(DWT_START_RX_IMMEDIATE);
		while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR)))
		{ };

		// ************************ RX_QUALSIASICOSA *****************************

		if (status_reg & SYS_STATUS_RXFCG)
		{
			uint32 frame_len;
			dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);
			frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;

			switch(frame_len)
			{
			//	 _____________________________________________________________________TWR_INIT____________________________________________________________________________________
			case(RX_BUF_TWR):   //lung 7+ check codice ancora

				dwt_readrxdata(twr_buffer, frame_len, 0);

				if (twr_buffer[ANCH_CODE] == ANCH5_ID)
				{
					//	___________________________________________________________________TWR-CORRECTION__________________________________________________________________________________

					int twr_cycle = 0;  //ciclo una volta sola il controllo del twr
					tof_tot = 0;

					while(twr_cycle < TWR_CYCLE)
					{
						dwt_setrxtimeout(0);
						dwt_rxenable(DWT_START_RX_IMMEDIATE);

						while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR)))
						{ };
						if (status_reg & SYS_STATUS_RXFCG)
						{
							uint32 frame_len;
							dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);

							frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;
							if (frame_len <= RX_BUFFER_LEN)
							{
								dwt_readrxdata(rx_buffer, frame_len, 0);
							}
							rx_buffer[ALL_MSG_SN_IDX] = 0;
							if (memcmp(rx_buffer, rx_poll_msg, ALL_MSG_COMMON_LEN) == 0)
							{
								uint32 resp_tx_time;
								int ret;

								poll_rx_ts = get_rx_timestamp_u64();

								resp_tx_time = (poll_rx_ts + (POLL_RX_TO_RESP_TX_DLY_UUS * UUS_TO_DWT_TIME)) >> 8;
								dwt_setdelayedtrxtime(resp_tx_time);

								dwt_setrxaftertxdelay(RESP_TX_TO_FINAL_RX_DLY_UUS);
								dwt_setrxtimeout(FINAL_RX_TIMEOUT_UUS);

								tx_resp_msg[ALL_MSG_SN_IDX] = frame_seq_nb;
								dwt_writetxdata(sizeof(tx_resp_msg), tx_resp_msg, 0); /* Zero offset in TX buffer. */
								dwt_writetxfctrl(sizeof(tx_resp_msg), 0, 1); /* Zero offset in TX buffer, ranging. */
								ret = dwt_starttx(DWT_START_TX_DELAYED | DWT_RESPONSE_EXPECTED);
								if (ret == DWT_ERROR)
								{
									continue;
								}

								while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR)))
								{ };

								frame_seq_nb++;

								if (status_reg & SYS_STATUS_RXFCG)
								{
									dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG | SYS_STATUS_TXFRS);

									frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFLEN_MASK;
									if (frame_len <= RX_BUF_LEN)
									{
										dwt_readrxdata(rx_buffer, frame_len, 0);
									}

									rx_buffer[ALL_MSG_SN_IDX] = 0;
									if (memcmp(rx_buffer, rx_final_msg, ALL_MSG_COMMON_LEN) == 0)
									{
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
										//tof = tof_dtu * DWT_TIME_UNITS;
										//distance = tof * SPEED_OF_LIGHT;
										tof_tot = tof_tot + tof_dtu;
										twr_cycle++;
									}
								}
								else
								{
									dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
									dwt_rxreset();
								}
							}
						}
						else
						{
							dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
							dwt_rxreset();
						}

					}

					tof_media = tof_tot/10;
					CORR_DLY  = (int64)(TOF - tof_media);
					twr_cycle = 0;
				}
				else
				{
					Sleep(500); //se hai ricevuto un pacchetto di ranging e non � il tuo dormitela e poi rimettiti in rx
					continue;
				}

				break;

			//	__________________________________________________SYNC-PART ____________________________________________________________
			case(SYNC_BUF_LEN):    //lung 12, il sync si fa in parallelo perch� il master invia solo pacchetti

				total = 0;
				dwt_readrxdata(sync_buffer, frame_len, 0);

				// ---------------------------- CHECK BLINK_CODE ----------------------------------
				if (sync_buffer[CODE_IDX] == START_BLINK)
				{
					sync_poll_rx_ts = get_rx_timestamp_u64();  //primo timestamp

					dwt_rxenable(DWT_START_RX_IMMEDIATE);
					while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_ERR)))
					{ };

					// ---------------------------- ARRIVA SECONDO BLINK ----------------------------------
					if (status_reg & SYS_STATUS_RXFCG)
					{
						uint32 frame_len;
						dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);

						frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;
						if (frame_len <= SYNC_BUF_LEN)
						{
							dwt_readrxdata(sync_buffer, frame_len, 0);
						}
						// ---------------------------- CHECK BLINK_CODE ----------------------------------
						if (sync_buffer[CODE_IDX] == FINAL_BLINK)
						{
							sync_final_rx_ts = get_rx_timestamp_u64();  	//final timestamp

							dwt_rxenable(DWT_START_RX_IMMEDIATE);
							while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_ERR)))
							{ };

							// ----------------------------ARRIVA MSG FINALE ----------------------------------
							if (status_reg & SYS_STATUS_RXFCG)
							{
								uint32 frame_len;
								dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);

								frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;
								if (frame_len <= RX_BUFFER_LEN)
								{
									dwt_readrxdata(rx_buffer, frame_len, 0);
								}
								// ---------------------------- CHECK FINAL_CODE ----------------------------------
								if (rx_buffer[CODE_IDX] == FINAL_MSG)
								{
									//estraggo dato da ANCH_INITIATOR
									uint8 sync_count = 0;
									uint32 timer_master;
									uint64 timer_anch=0;
									int64  delta;

									get_ts(&rx_buffer[FINAL_MSG_POLL_TX_TS_IDX], &timer_master);
									get_msg_idx(&rx_buffer[SYNC_CYCLE_IDX], &sync_count);
									timer_anch 	= (uint64)(sync_final_rx_ts - sync_poll_rx_ts);

									delta = (int64)(timer_master - timer_anch);
									corr_factor[sync_count] = (double)((uint64)timer_master/timer_anch);

									if(sync_count == 49)
									{
										int j;

										for(j = 0; j < 50; j++)
										{
											total = total + corr_factor[j];
										}
										dly_corr_factor = total/50;
									}
								}
								else
								{
									dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
									dwt_rxreset();
								}
							}
							else
							{
								dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
								dwt_rxreset();
							}
						}
						else
						{
							dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
							dwt_rxreset();
						}
					}
					else
					{
						dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
						dwt_rxreset();
					}
				}
				else
				{
					dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
					dwt_rxreset();
					continue;
				}

				break;

			//***************************************************** TDOA ***************************************************************
			case(BUF_INIT_TDOA):

				dwt_readrxdata(tdoa_init_buffer, frame_len, 0);

				if (tdoa_init_buffer[CODE_INIT] == INIT_TDOA_MSG)
				{
					rx_init_ts = get_rx_timestamp_u64();
					rx_init_ts_corr = (uint64)(rx_init_ts - (uint64)TOF + CORR_DLY);


					dwt_rxenable(DWT_START_RX_IMMEDIATE);
					while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_ERR)))
					{ };

					// ---------------------------- TAG BLINK ----------------------------------
					if (status_reg & SYS_STATUS_RXFCG)
					{
						uint32 frame_len;
						dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);
						frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;

						if (frame_len <= RX_BUF_TAG)
						{
							dwt_readrxdata(tag_buffer, frame_len, 0);
						}

						if (tag_buffer[TAG_IDX] == TAG_BLINK)
						{
							uint8 tag_ID;

							ts = get_rx_timestamp_u64();
							ts_corretto = (uint64)(ts - CORR_DLY);

							get_msg_idx(&tag_buffer[1], &tag_ID);

							total_ts = (uint64)(ts_corretto - rx_init_ts_corr);

							char output[32] = "";
							sprintf(output,"%d", total_ts);
							lcd_display_str(output);

							// ________________ TEST-DISTANZA ________________

//							uint32 tx_delay;
//							tx_delay = (uint32)(ts_corretto) + TIME_SLOT;
//							dwt_setdelayedtrxtime(tx_delay);

							Sleep(10);

							test_msg_set(&tdoa_resp[IDX_MSG_DIST], total_ts);
							msg_set_idx(&tdoa_resp[ANCH_IDX], ANCH5_ID);
							msg_set_idx(&tdoa_resp[TAG_IDX], tag_ID);

							dwt_writetxdata(sizeof(tdoa_resp), tdoa_resp, 0);
							dwt_writetxfctrl(sizeof(tdoa_resp), 0, 0);


							dwt_starttx(DWT_START_TX_IMMEDIATE);
							while (!(dwt_read32bitreg(SYS_STATUS_ID) & SYS_STATUS_TXFRS))
							{ };
							dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_TXFRS);

							//*************************************************************************************************

						}
						else
						{
							dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
							dwt_rxreset();
						}
					}
					else
					{
						dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
						dwt_rxreset();
					}
				}
				else
				{
					dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
					dwt_rxreset();
				}

				break;

			//se ricevo msg che non centra
			default: continue;

			} //SWITCH

//			break;  //ogni volta che esco da switch rivai in rx mode e checca quello che arriva
		} //IF RX (LISTEN)

	} // while(1)

} //MAIN


static uint64 get_rx_timestamp_u64(void)
{
	uint8 ts_tab[5];
	uint64 ts = 0;
	int i;
	dwt_readrxtimestamp(ts_tab);
	for (i = 4; i >= 0; i--)
	{
		ts <<= 8;
		ts |= ts_tab[i];
	}
	return ts;
}

static void get_ts(const uint8 *ts_field, uint32 *ts)
{
	int i;
	*ts = 0;
	for (i = 0; i < FINAL_MSG_TS_LEN; i++)
	{
		*ts += ts_field[i] << (i * 8);
	}
}

static void get_msg_idx(const uint8 *ts_field, uint8 *ts)
{
	int i;
	*ts = 0;
	for (i = 0; i < 1; i++)
	{
		*ts += ts_field[i] << (i * 8);
	}
}

static uint64 get_tx_timestamp_u64(void)
{
	uint8 ts_tab[5];
	uint64 ts = 0;
	int i;
	dwt_readtxtimestamp(ts_tab);
	for (i = 4; i >= 0; i--)
	{
		ts <<= 8;
		ts |= ts_tab[i];
	}
	return ts;
}

static void final_msg_get_ts(const uint8 *ts_field, uint32 *ts)
{
	int i;
	*ts = 0;
	for (i = 0; i < FINAL_MSG_TS_LEN; i++)
	{
		*ts += ts_field[i] << (i * 8);
	}
}


//___________________ MSG_RESP_TDOA__________________
static void test_msg_set(uint8 *ts_field, uint64 ts)
{
	int i;
	for (i = 0; i < TEST_LEN; i++)
	{
		ts_field[i] = (uint8) ts;
		ts >>= 8;
	}
}

static void msg_set_idx(uint8 *ts_field, uint8 ts)
{
	int i;
	for (i = 0; i < 1; i++)
	{
		ts_field[i] = (uint8) ts;
		ts >>= 8;
	}
}
//____________________________________________________
#endif


#ifdef ANCH_SLAVE_7_V3

#define APP_NAME "RX_SYNC_A7"

//#pragma GCC optimize ("00")

#define ANCH7_ID	2

// versione anch 7 in posizione senza riflessioni -> (2.12 5.35) (messa sul tavolo rimane leggermente sfalsata su z)
//	***************************************************************** TWR-CORRECTION **************************************************************************************

#define RX_BUF_TWR 	7		   						 //conta 1,2,3,4,...22 elementi
static uint8 twr_buffer[RX_BUF_TWR];

#define ANCH_CODE	1

#define TX_ANT_DLY 16436
#define RX_ANT_DLY 16436


static uint8 rx_poll_msg[] = {0x41, 0x88, 0, 0xCA, 0xDE, 'W', 'A', 'V', 'E', 0x21, 0, 0};
static uint8 tx_resp_msg[] = {0x41, 0x88, 0, 0xCA, 0xDE, 'V', 'E', 'W', 'A', 0x10, 0x02, 0, 0, 0, 0};
static uint8 rx_final_msg[] = {0x41, 0x88, 0, 0xCA, 0xDE, 'W', 'A', 'V', 'E', 0x23, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};

#define TWR_CYCLE 					10
#define ALL_MSG_SN_IDX 				2
#define FINAL_MSG_POLL_TX_TS_IDX 	10
#define FINAL_MSG_RESP_RX_TS_IDX 	14
#define FINAL_MSG_FINAL_TX_TS_IDX 	18
#define FINAL_MSG_TS_LEN 			4

static uint8 frame_seq_nb = 0;
#define RX_BUF_LEN 24
static uint8 rx_buffer[RX_BUF_LEN];
static uint32 status_reg = 0;

#define UUS_TO_DWT_TIME 				65536
#define POLL_RX_TO_RESP_TX_DLY_UUS 		2750
#define RESP_TX_TO_FINAL_RX_DLY_UUS 	500
#define FINAL_RX_TIMEOUT_UUS 			3300
#define PRE_TIMEOUT 					8

typedef signed long long int64;
typedef unsigned long long uint64;
static uint64 poll_rx_ts;
static uint64 resp_tx_ts;
static uint64 final_rx_ts;

#define SPEED_OF_LIGHT 299702547

//static double tof;
//static double distance;

static void final_msg_get_ts(const uint8 *ts_field, uint32 *ts);
static uint64 get_tx_timestamp_u64(void);

// ------------------------------------------------------------ DEF SYNC TIMESTAMP ---------------------------------------------------------------------------------
//#define CORR_DLY   370      //370->5, 0->4, ->7

#define START_BLINK 0x19
#define FINAL_BLINK 0x6
#define FINAL_MSG   0x23

#define SYNC_CYCLE 					 30
#define ALL_MSG_COMMON_LEN 		  	 5
#define SYNC_CYCLE_IDX				 2
#define CODE_IDX 					 9
#define FINAL_MSG_POLL_TX_TS_IDX  	 10

#define FINAL_MSG_TS_LEN 		  	 4


#define SYNC_BUF_LEN 12   						 //conta 1,2,3,4,...22 elementi
static uint8 sync_buffer[SYNC_BUF_LEN];

static uint64 sync_poll_rx_ts;
static uint64 sync_final_rx_ts;
static double corr_factor[50];
static double total;

static uint64 get_rx_timestamp_u64(void);
static void get_ts(const uint8 *ts_field, uint32 *ts);
static void get_msg_idx(const uint8 *ts_field, uint8 *ts);

// ---------------------------------------------------------- DEF INIT ---------------------------------------------------------------------------------------
#define INIT_TDOA_MSG   0xFF
#define CODE_INIT  3

// ---------------------------------------------------------- DEF TDOA ---------------------------------------------------------------------------------------

#define UUS_TO_DWT_TIME		65536 		//1 uus = 512 / 499.2 �s and 1 �s = 499.2 * 128 dtu | UWB microsecond (uus) to device time unit (dtu, around 15.65 ps) conversion factor�

#define TAG_IDX				3
#define TAG_BLINK			0x10



#define BUF_INIT_TDOA 		6   					 //conta 1,2,3,4,...22 elementi
static uint8 tdoa_init_buffer[BUF_INIT_TDOA];

#define RX_BUF_TAG 			6 						 //conta 1,2,3,4,...22 elementi
static uint8 tag_buffer[RX_BUF_TAG];

static uint64 rx_init_ts;
static uint64 rx_init_ts_corr;
static uint64 ts;
static uint64 ts_corretto;
static uint64 total_ts;

static double dly_corr_factor;         // fattore di correzzione in dtu del delay pre-impostato in modo che sia in synch con il conteggio del master
static double tof_media;
static double tof_tot;
static int64 CORR_DLY;

//___________________ MSG_RESP_TDOA______________________
static uint8 tdoa_resp[] = {0xC5, 0, 0, 'T', 'E', 'S', 'T', 0, 0, 0, 0, 0, 0};

#define IDX_MSG_DIST  	7
#define TEST_LEN		4
#define ANCH_IDX		1
#define TAG_IDX			3
#define TOF				639 //POSIZIONE (-2.12, 2.12)

#define TIME_SLOT	383386580   //in UWB tick ~ 6ms

static void test_msg_set(uint8 *ts_field, uint64 ts);
static void msg_set_idx(uint8 *ts_field, uint8 ts);
//___________________________________________________


int dw_main(void)
{
	lcd_display_str(APP_NAME);
	reset_DW1000(); /* Target specific drive of RSTn line into DW1000 low for a period. */
	port_set_dw1000_slowrate();
	if (dwt_initialise(DWT_LOADUCODE) == DWT_ERROR)
	{
		lcd_display_str("INIT FAILED");
		while (1)
		{ };
	}
	port_set_dw1000_fastrate();
	dwt_configure(&config);

	dwt_setrxantennadelay(RX_ANT_DLY);    //non vanno..conpensati da sync?
	dwt_settxantennadelay(TX_ANT_DLY);



	dwt_setleds(DWT_LEDS_ENABLE);

	while (1)
	{
		//applicazione stai in ascolta di msg init (ogni parte prevede un msg di inizializzazione)
		dwt_setrxtimeout(0);

		dwt_rxenable(DWT_START_RX_IMMEDIATE);
		while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR)))
		{ };

		// ************************ RX_QUALSIASICOSA *****************************

		if (status_reg & SYS_STATUS_RXFCG)
		{
			uint32 frame_len;
			dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);
			frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;

			switch(frame_len)
			{
			//	 _____________________________________________________________________TWR_INIT____________________________________________________________________________________
			case(RX_BUF_TWR):   //lung 7+ check codice ancora

				dwt_readrxdata(twr_buffer, frame_len, 0);

				if (twr_buffer[ANCH_CODE] == ANCH7_ID)
				{
					//	___________________________________________________________________TWR-CORRECTION__________________________________________________________________________________

					int twr_cycle = 0;  //ciclo una volta sola il controllo del twr
					tof_tot = 0;

					while(twr_cycle < TWR_CYCLE)
					{
						dwt_setrxtimeout(0);
						dwt_rxenable(DWT_START_RX_IMMEDIATE);

						while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR)))
						{ };
						if (status_reg & SYS_STATUS_RXFCG)
						{
							uint32 frame_len;
							dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);

							frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;
							if (frame_len <= RX_BUFFER_LEN)
							{
								dwt_readrxdata(rx_buffer, frame_len, 0);
							}
							rx_buffer[ALL_MSG_SN_IDX] = 0;
							if (memcmp(rx_buffer, rx_poll_msg, ALL_MSG_COMMON_LEN) == 0)
							{
								uint32 resp_tx_time;
								int ret;

								poll_rx_ts = get_rx_timestamp_u64();

								resp_tx_time = (poll_rx_ts + (POLL_RX_TO_RESP_TX_DLY_UUS * UUS_TO_DWT_TIME)) >> 8;
								dwt_setdelayedtrxtime(resp_tx_time);

								dwt_setrxaftertxdelay(RESP_TX_TO_FINAL_RX_DLY_UUS);
								dwt_setrxtimeout(FINAL_RX_TIMEOUT_UUS);

								tx_resp_msg[ALL_MSG_SN_IDX] = frame_seq_nb;
								dwt_writetxdata(sizeof(tx_resp_msg), tx_resp_msg, 0); /* Zero offset in TX buffer. */
								dwt_writetxfctrl(sizeof(tx_resp_msg), 0, 1); /* Zero offset in TX buffer, ranging. */
								ret = dwt_starttx(DWT_START_TX_DELAYED | DWT_RESPONSE_EXPECTED);
								if (ret == DWT_ERROR)
								{
									continue;
								}

								while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR)))
								{ };

								frame_seq_nb++;

								if (status_reg & SYS_STATUS_RXFCG)
								{
									dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG | SYS_STATUS_TXFRS);

									frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFLEN_MASK;
									if (frame_len <= RX_BUF_LEN)
									{
										dwt_readrxdata(rx_buffer, frame_len, 0);
									}

									rx_buffer[ALL_MSG_SN_IDX] = 0;
									if (memcmp(rx_buffer, rx_final_msg, ALL_MSG_COMMON_LEN) == 0)
									{
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
										//tof = tof_dtu * DWT_TIME_UNITS;
										//distance = tof * SPEED_OF_LIGHT;
										tof_tot = tof_tot + tof_dtu;
										twr_cycle++;
									}
								}
								else
								{
									dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
									dwt_rxreset();
								}
							}
						}
						else
						{
							dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
							dwt_rxreset();
						}

					}

					tof_media = tof_tot/10;
					CORR_DLY  = (int64)(TOF - (abs)(tof_media));
					twr_cycle = 0;
				}
				else
				{
					Sleep(500); //se hai ricevuto un pacchetto di ranging e non � il tuo dormitela e poi rimettiti in rx
					continue;
				}

				break;

			//	__________________________________________________SYNC-PART ____________________________________________________________
			case(SYNC_BUF_LEN):    //lung 12, il sync si fa in parallelo perch� il master invia solo pacchetti

				total = 0;
				dwt_readrxdata(sync_buffer, frame_len, 0);

				// ---------------------------- CHECK BLINK_CODE ----------------------------------
				if (sync_buffer[CODE_IDX] == START_BLINK)
				{
					sync_poll_rx_ts = get_rx_timestamp_u64();  //primo timestamp

					dwt_rxenable(DWT_START_RX_IMMEDIATE);
					while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_ERR)))
					{ };

					// ---------------------------- ARRIVA SECONDO BLINK ----------------------------------
					if (status_reg & SYS_STATUS_RXFCG)
					{
						uint32 frame_len;
						dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);

						frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;
						if (frame_len <= SYNC_BUF_LEN)
						{
							dwt_readrxdata(sync_buffer, frame_len, 0);
						}
						// ---------------------------- CHECK BLINK_CODE ----------------------------------
						if (sync_buffer[CODE_IDX] == FINAL_BLINK)
						{
							sync_final_rx_ts = get_rx_timestamp_u64();  	//final timestamp

							dwt_rxenable(DWT_START_RX_IMMEDIATE);
							while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_ERR)))
							{ };

							// ----------------------------ARRIVA MSG FINALE ----------------------------------
							if (status_reg & SYS_STATUS_RXFCG)
							{
								uint32 frame_len;
								dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);

								frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;
								if (frame_len <= RX_BUFFER_LEN)
								{
									dwt_readrxdata(rx_buffer, frame_len, 0);
								}
								// ---------------------------- CHECK FINAL_CODE ----------------------------------
								if (rx_buffer[CODE_IDX] == FINAL_MSG)
								{
									//estraggo dato da ANCH_INITIATOR
									uint8 sync_count = 0;
									uint32 timer_master;
									uint64 timer_anch=0;
									int64  delta;

									get_ts(&rx_buffer[FINAL_MSG_POLL_TX_TS_IDX], &timer_master);
									get_msg_idx(&rx_buffer[SYNC_CYCLE_IDX], &sync_count);
									timer_anch 	= (uint64)(sync_final_rx_ts - sync_poll_rx_ts);

									delta = (int64)(timer_master - timer_anch);
									corr_factor[sync_count] = (double)timer_anch/(uint64)timer_master;

									if(sync_count == 49)
									{
										int j;

										for(j = 0; j < 50; j++)
										{
											total = total + corr_factor[j];
										}
										dly_corr_factor = total/50;
									}
								}
								else
								{
									dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
									dwt_rxreset();
								}
							}
							else
							{
								dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
								dwt_rxreset();
							}
						}
						else
						{
							dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
							dwt_rxreset();
						}
					}
					else
					{
						dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
						dwt_rxreset();
					}
				}
				else
				{
					dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
					dwt_rxreset();
					continue;
				}

				break;

			//***************************************************** TDOA ***************************************************************
			case(BUF_INIT_TDOA):

				dwt_readrxdata(tdoa_init_buffer, frame_len, 0);

				if (tdoa_init_buffer[CODE_INIT] == INIT_TDOA_MSG)
				{
					rx_init_ts = get_rx_timestamp_u64();
					rx_init_ts_corr = (uint64)(rx_init_ts - (uint64)TOF + CORR_DLY);

					// - TOF perch� lo slave prende il valore del registro in ritardo di TOF

					//while()   //fin tanto che non arrivano tutti i tag..intanto vedo se va con un tag

					dwt_rxenable(DWT_START_RX_IMMEDIATE);
					while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_ERR)))
					{ };

					// ---------------------------- TAG BLINK ----------------------------------
					if (status_reg & SYS_STATUS_RXFCG)
					{
						uint32 frame_len;
						dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);
						frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;

						if (frame_len <= RX_BUF_TAG)
						{
							dwt_readrxdata(tag_buffer, frame_len, 0);
						}

						if (tag_buffer[TAG_IDX] == TAG_BLINK)
						{
							uint8 tag_ID;

							ts = get_rx_timestamp_u64();
							ts_corretto = (uint64)(ts - CORR_DLY);

							get_msg_idx(&tag_buffer[1], &tag_ID);

							total_ts = (uint64)(ts_corretto - rx_init_ts_corr);


							char output[32] = "";
							sprintf(output,"%d", total_ts);
							lcd_display_str(output);

							// ________________ TEST-DISTANZA ________________

//							uint32 tx_delay;
//							tx_delay = (uint32)(ts_corretto) + TIME_SLOT;
//							dwt_setdelayedtrxtime(tx_delay);

							Sleep(15);

							test_msg_set(&tdoa_resp[IDX_MSG_DIST], total_ts);
							msg_set_idx(&tdoa_resp[ANCH_IDX], ANCH7_ID);
							msg_set_idx(&tdoa_resp[TAG_IDX], tag_ID);

							dwt_writetxdata(sizeof(tdoa_resp), tdoa_resp, 0);
							dwt_writetxfctrl(sizeof(tdoa_resp), 0, 0);


							dwt_starttx(DWT_START_TX_IMMEDIATE);
							while (!(dwt_read32bitreg(SYS_STATUS_ID) & SYS_STATUS_TXFRS))
							{ };
							dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_TXFRS);

							//*************************************************************************************************

						}
						else
						{
							dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
							dwt_rxreset();
						}
					}
					else
					{
						dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
						dwt_rxreset();
					}
				}
				else
				{
					dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
					dwt_rxreset();
				}

				break;

			//se ricevo msg che non centra
			default: continue;

			} //SWITCH

//			break;  //ogni volta che esco da switch rivai in rx mode e checca quello che arriva
		} //IF RX (LISTEN)

	} // while(1)

} //MAIN


static uint64 get_rx_timestamp_u64(void)
{
	uint8 ts_tab[5];
	uint64 ts = 0;
	int i;
	dwt_readrxtimestamp(ts_tab);
	for (i = 4; i >= 0; i--)
	{
		ts <<= 8;
		ts |= ts_tab[i];
	}
	return ts;
}

static void get_ts(const uint8 *ts_field, uint32 *ts)
{
	int i;
	*ts = 0;
	for (i = 0; i < FINAL_MSG_TS_LEN; i++)
	{
		*ts += ts_field[i] << (i * 8);
	}
}

static void get_msg_idx(const uint8 *ts_field, uint8 *ts)
{
	int i;
	*ts = 0;
	for (i = 0; i < 1; i++)
	{
		*ts += ts_field[i] << (i * 8);
	}
}

static uint64 get_tx_timestamp_u64(void)
{
	uint8 ts_tab[5];
	uint64 ts = 0;
	int i;
	dwt_readtxtimestamp(ts_tab);
	for (i = 4; i >= 0; i--)
	{
		ts <<= 8;
		ts |= ts_tab[i];
	}
	return ts;
}

static void final_msg_get_ts(const uint8 *ts_field, uint32 *ts)
{
	int i;
	*ts = 0;
	for (i = 0; i < FINAL_MSG_TS_LEN; i++)
	{
		*ts += ts_field[i] << (i * 8);
	}
}


//___________________ MSG_RESP_TDOA__________________
static void test_msg_set(uint8 *ts_field, uint64 ts)
{
	int i;
	for (i = 0; i < TEST_LEN; i++)
	{
		ts_field[i] = (uint8) ts;
		ts >>= 8;
	}
}

static void msg_set_idx(uint8 *ts_field, uint8 ts)
{
	int i;
	for (i = 0; i < 1; i++)
	{
		ts_field[i] = (uint8) ts;
		ts >>= 8;
	}
}
//____________________________________________________
#endif



#ifdef ANCH_SLAVE_8_V3
// POSITION: (0, 2.10)
#define APP_NAME "RX_SYNC_A8"

//#pragma GCC optimize ("00")

#define ANCH8_ID	3

//	***************************************************************** TWR-CORRECTION **************************************************************************************

#define RX_BUF_TWR 	7		   						 //conta 1,2,3,4,...22 elementi
static uint8 twr_buffer[RX_BUF_TWR];

#define ANCH_CODE	1

#define TX_ANT_DLY 16436
#define RX_ANT_DLY 16436
//#define POSITION 5960 //in mm

static uint8 rx_poll_msg[] = {0x41, 0x88, 0, 0xCA, 0xDE, 'W', 'A', 'V', 'E', 0x21, 0, 0};
static uint8 tx_resp_msg[] = {0x41, 0x88, 0, 0xCA, 0xDE, 'V', 'E', 'W', 'A', 0x10, 0x02, 0, 0, 0, 0};
static uint8 rx_final_msg[] = {0x41, 0x88, 0, 0xCA, 0xDE, 'W', 'A', 'V', 'E', 0x23, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};

#define TWR_CYCLE 					10
#define ALL_MSG_SN_IDX 				2
#define FINAL_MSG_POLL_TX_TS_IDX 	10
#define FINAL_MSG_RESP_RX_TS_IDX 	14
#define FINAL_MSG_FINAL_TX_TS_IDX 	18
#define FINAL_MSG_TS_LEN 			4

static uint8 frame_seq_nb = 0;
#define RX_BUF_LEN 24
static uint8 rx_buffer[RX_BUF_LEN];
static uint32 status_reg = 0;

#define UUS_TO_DWT_TIME 				65536
#define POLL_RX_TO_RESP_TX_DLY_UUS 		2750
#define RESP_TX_TO_FINAL_RX_DLY_UUS 	500
#define FINAL_RX_TIMEOUT_UUS 			3300
#define PRE_TIMEOUT 					8

typedef signed long long int64;
typedef unsigned long long uint64;
static uint64 poll_rx_ts;
static uint64 resp_tx_ts;
static uint64 final_rx_ts;

#define SPEED_OF_LIGHT 299702547

//static double tof;
//static double distance;

static void final_msg_get_ts(const uint8 *ts_field, uint32 *ts);
static uint64 get_tx_timestamp_u64(void);

// ------------------------------------------------------------ DEF SYNC TIMESTAMP ---------------------------------------------------------------------------------
//#define CORR_DLY   370      //370->5, 0->4, ->7

#define START_BLINK 0x19
#define FINAL_BLINK 0x6
#define FINAL_MSG   0x23

#define SYNC_CYCLE 					 30
#define ALL_MSG_COMMON_LEN 		  	 5
#define SYNC_CYCLE_IDX				 2
#define CODE_IDX 					 9
#define FINAL_MSG_POLL_TX_TS_IDX  	 10

#define FINAL_MSG_TS_LEN 		  	 4


#define SYNC_BUF_LEN 12   						 //conta 1,2,3,4,...22 elementi
static uint8 sync_buffer[SYNC_BUF_LEN];

static uint64 sync_poll_rx_ts;
static uint64 sync_final_rx_ts;
static double corr_factor[50];
static double total;

static uint64 get_rx_timestamp_u64(void);
static void get_ts(const uint8 *ts_field, uint32 *ts);
static void get_msg_idx(const uint8 *ts_field, uint8 *ts);

// ---------------------------------------------------------- DEF INIT ---------------------------------------------------------------------------------------
#define INIT_TDOA_MSG   0xFF
#define CODE_INIT  3

// ---------------------------------------------------------- DEF TDOA ---------------------------------------------------------------------------------------

#define UUS_TO_DWT_TIME		65536 		//1 uus = 512 / 499.2 �s and 1 �s = 499.2 * 128 dtu | UWB microsecond (uus) to device time unit (dtu, around 15.65 ps) conversion factor�

#define TAG_IDX				3
#define TAG_BLINK			0x10



#define BUF_INIT_TDOA 		6   					 //conta 1,2,3,4,...22 elementi
static uint8 tdoa_init_buffer[BUF_INIT_TDOA];

#define RX_BUF_TAG 			6 						 //conta 1,2,3,4,...22 elementi
static uint8 tag_buffer[RX_BUF_TAG];

static uint64 rx_init_ts;
static uint64 rx_init_ts_corr;
static uint64 ts;
static uint64 ts_corretto;
static uint64 total_ts;

static double dly_corr_factor;         // fattore di correzzione in dtu del delay pre-impostato in modo che sia in synch con il conteggio del master
static double DLY;
static double tof_media;
static double tof_tot;
static int64 CORR_DLY;

//___________________ MSG_RESP_TDOA______________________
static uint8 tdoa_resp[] = {0xC5, 0, 0, 'T', 'E', 'S', 'T', 0, 0, 0, 0, 0, 0};

#define IDX_MSG_DIST  	7
#define TEST_LEN		4
#define ANCH_IDX		1
#define TAG_IDX			3
#define TOF				452     //POSIZIONE (-2.12, 0)

#define TIME_SLOT	383386580   //in UWB tick ~ 6ms

static void test_msg_set(uint8 *ts_field, uint64 ts);
static void msg_set_idx(uint8 *ts_field, uint8 ts);
//___________________________________________________


int dw_main(void)
{
	lcd_display_str(APP_NAME);
	reset_DW1000(); /* Target specific drive of RSTn line into DW1000 low for a period. */
	port_set_dw1000_slowrate();
	if (dwt_initialise(DWT_LOADUCODE) == DWT_ERROR)
	{
		lcd_display_str("INIT FAILED");
		while (1)
		{ };
	}
	port_set_dw1000_fastrate();
	dwt_configure(&config);

	dwt_setrxantennadelay(RX_ANT_DLY);    //non vanno..conpensati da sync?
	dwt_settxantennadelay(TX_ANT_DLY);

	dwt_setleds(DWT_LEDS_ENABLE);

	total = 0; //sync

	while (1)
	{
		//applicazione stai in ascolta di msg init (ogni parte prevede un msg di inizializzazione)
		dwt_setrxtimeout(0);

		dwt_rxenable(DWT_START_RX_IMMEDIATE);
		while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR)))
		{ };

		// ************************ RX_QUALSIASICOSA *****************************

		if (status_reg & SYS_STATUS_RXFCG)
		{
			uint32 frame_len;
			dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);
			frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;

			switch(frame_len)
			{
			//	 _____________________________________________________________________TWR_INIT____________________________________________________________________________________
			case(RX_BUF_TWR):   //lung 7+ check codice ancora

				dwt_readrxdata(twr_buffer, frame_len, 0);

				if (twr_buffer[ANCH_CODE] == ANCH8_ID)
				{
					//	___________________________________________________________________TWR-CORRECTION__________________________________________________________________________________

					int twr_cycle = 0;  //ciclo una volta sola il controllo del twr
					tof_tot = 0;

					while(twr_cycle < TWR_CYCLE)
					{
						dwt_setrxtimeout(0);
						dwt_rxenable(DWT_START_RX_IMMEDIATE);

						while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR)))
						{ };
						if (status_reg & SYS_STATUS_RXFCG)
						{
							uint32 frame_len;
							dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);

							frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;
							if (frame_len <= RX_BUFFER_LEN)
							{
								dwt_readrxdata(rx_buffer, frame_len, 0);
							}
							rx_buffer[ALL_MSG_SN_IDX] = 0;
							if (memcmp(rx_buffer, rx_poll_msg, ALL_MSG_COMMON_LEN) == 0)
							{
								uint32 resp_tx_time;
								int ret;

								poll_rx_ts = get_rx_timestamp_u64();

								resp_tx_time = (poll_rx_ts + (POLL_RX_TO_RESP_TX_DLY_UUS * UUS_TO_DWT_TIME)) >> 8;
								dwt_setdelayedtrxtime(resp_tx_time);

								dwt_setrxaftertxdelay(RESP_TX_TO_FINAL_RX_DLY_UUS);
								dwt_setrxtimeout(FINAL_RX_TIMEOUT_UUS);

								tx_resp_msg[ALL_MSG_SN_IDX] = frame_seq_nb;
								dwt_writetxdata(sizeof(tx_resp_msg), tx_resp_msg, 0); /* Zero offset in TX buffer. */
								dwt_writetxfctrl(sizeof(tx_resp_msg), 0, 1); /* Zero offset in TX buffer, ranging. */
								ret = dwt_starttx(DWT_START_TX_DELAYED | DWT_RESPONSE_EXPECTED);
								if (ret == DWT_ERROR)
								{
									continue;
								}

								while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR)))
								{ };

								frame_seq_nb++;

								if (status_reg & SYS_STATUS_RXFCG)
								{
									dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG | SYS_STATUS_TXFRS);

									frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFLEN_MASK;
									if (frame_len <= RX_BUF_LEN)
									{
										dwt_readrxdata(rx_buffer, frame_len, 0);
									}

									rx_buffer[ALL_MSG_SN_IDX] = 0;
									if (memcmp(rx_buffer, rx_final_msg, ALL_MSG_COMMON_LEN) == 0)
									{
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
										//tof = tof_dtu * DWT_TIME_UNITS;
										//distance = tof * SPEED_OF_LIGHT;
										tof_tot = tof_tot + tof_dtu;
										twr_cycle++;
									}
								}
								else
								{
									dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
									dwt_rxreset();
								}
							}
						}
						else
						{
							dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
							dwt_rxreset();
						}

					}

					tof_media = tof_tot/10;
					CORR_DLY  = (int64)(TOF - (abs)(tof_media));
					twr_cycle = 0;
				}
				else
				{
					Sleep(500); //se hai ricevuto un pacchetto di ranging e non � il tuo dormitela e poi rimettiti in rx
					continue;
				}

				break;

			//	__________________________________________________SYNC-PART ____________________________________________________________
			case(SYNC_BUF_LEN):    //lung 12, il sync si fa in parallelo perch� il master invia solo pacchetti

				dwt_readrxdata(sync_buffer, frame_len, 0);

				// ---------------------------- CHECK BLINK_CODE ----------------------------------
				if (sync_buffer[CODE_IDX] == START_BLINK)
				{
					sync_poll_rx_ts = get_rx_timestamp_u64();  //primo timestamp

					dwt_rxenable(DWT_START_RX_IMMEDIATE);
					while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_ERR)))
					{ };

					// ---------------------------- ARRIVA SECONDO BLINK ----------------------------------
					if (status_reg & SYS_STATUS_RXFCG)
					{
						uint32 frame_len;
						dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);

						frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;
						if (frame_len <= SYNC_BUF_LEN)
						{
							dwt_readrxdata(sync_buffer, frame_len, 0);
						}
						// ---------------------------- CHECK BLINK_CODE ----------------------------------
						if (sync_buffer[CODE_IDX] == FINAL_BLINK)
						{
							sync_final_rx_ts = get_rx_timestamp_u64();  	//final timestamp

							dwt_rxenable(DWT_START_RX_IMMEDIATE);
							while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_ERR)))
							{ };

							// ----------------------------ARRIVA MSG FINALE ----------------------------------
							if (status_reg & SYS_STATUS_RXFCG)
							{
								uint32 frame_len;
								dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);

								frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;
								if (frame_len <= RX_BUFFER_LEN)
								{
									dwt_readrxdata(rx_buffer, frame_len, 0);
								}
								// ---------------------------- CHECK FINAL_CODE ----------------------------------
								if (rx_buffer[CODE_IDX] == FINAL_MSG)
								{
									//estraggo dato da ANCH_INITIATOR
									uint8 sync_count = 0;
									uint32 timer_master;
									uint64 timer_anch=0;


									get_ts(&rx_buffer[FINAL_MSG_POLL_TX_TS_IDX], &timer_master);
									get_msg_idx(&rx_buffer[SYNC_CYCLE_IDX], &sync_count);
									timer_anch 	= (uint64)(sync_final_rx_ts - sync_poll_rx_ts);

									corr_factor[sync_count] = (double)((uint64)timer_master/timer_anch);

									if(sync_count == 49)
									{
										int j;

										for(j = 0; j < 50; j++)
										{
											total = total + corr_factor[j];
										}
										dly_corr_factor = total/50;
										total= 0;
									}
								}
								else
								{
									dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
									dwt_rxreset();
								}
							}
							else
							{
								dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
								dwt_rxreset();
							}
						}
						else
						{
							dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
							dwt_rxreset();
						}
					}
					else
					{
						dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
						dwt_rxreset();
					}
				}
				else
				{
					dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
					dwt_rxreset();
					continue;
				}

				break;

			//***************************************************** TDOA ***************************************************************
			case(BUF_INIT_TDOA):

				dwt_readrxdata(tdoa_init_buffer, frame_len, 0);

				if (tdoa_init_buffer[CODE_INIT] == INIT_TDOA_MSG)
				{
					rx_init_ts = get_rx_timestamp_u64();
					rx_init_ts_corr = (uint64)(rx_init_ts - (uint64)TOF + CORR_DLY);
//					rx_init_ts_corr = (uint64)(rx_init_ts - (uint64)TOF);

					dwt_rxenable(DWT_START_RX_IMMEDIATE);
					while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_ERR)))
					{ };

					// ---------------------------- TAG BLINK ----------------------------------
					if (status_reg & SYS_STATUS_RXFCG)
					{
						uint32 frame_len;
						dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);
						frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;

						if (frame_len <= RX_BUF_TAG)
						{
							dwt_readrxdata(tag_buffer, frame_len, 0);
						}

						if (tag_buffer[TAG_IDX] == TAG_BLINK)
						{
							uint8 tag_ID;

							ts = get_rx_timestamp_u64();
							ts_corretto = (uint64)(ts - CORR_DLY);

							get_msg_idx(&tag_buffer[1], &tag_ID);

							total_ts = (uint64)(ts_corretto - rx_init_ts_corr);

							char output[32] = "";
							sprintf(output,"%d", total_ts);
							lcd_display_str(output);

							// ________________ TEST-DISTANZA ________________

//							uint32 tx_delay;
//							tx_delay = (uint32)(ts_corretto) + TIME_SLOT;
//							dwt_setdelayedtrxtime(tx_delay);

							Sleep(20);

							test_msg_set(&tdoa_resp[IDX_MSG_DIST], total_ts);
							msg_set_idx(&tdoa_resp[ANCH_IDX], ANCH8_ID);
							msg_set_idx(&tdoa_resp[TAG_IDX], tag_ID);

							dwt_writetxdata(sizeof(tdoa_resp), tdoa_resp, 0);
							dwt_writetxfctrl(sizeof(tdoa_resp), 0, 0);


							dwt_starttx(DWT_START_TX_IMMEDIATE);
							while (!(dwt_read32bitreg(SYS_STATUS_ID) & SYS_STATUS_TXFRS))
							{ };
							dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_TXFRS);

							//*************************************************************************************************

						}
						else
						{
							dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
							dwt_rxreset();
						}
					}
					else
					{
						dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
						dwt_rxreset();
					}
				}
				else
				{
					dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
					dwt_rxreset();
				}

				break;

			//se ricevo msg che non centra
			default: continue;

			} //SWITCH

//			break;  //ogni volta che esco da switch rivai in rx mode e checca quello che arriva
		} //IF RX (LISTEN)

	} // while(1)

} //MAIN


static uint64 get_rx_timestamp_u64(void)
{
	uint8 ts_tab[5];
	uint64 ts = 0;
	int i;
	dwt_readrxtimestamp(ts_tab);
	for (i = 4; i >= 0; i--)
	{
		ts <<= 8;
		ts |= ts_tab[i];
	}
	return ts;
}

static void get_ts(const uint8 *ts_field, uint32 *ts)
{
	int i;
	*ts = 0;
	for (i = 0; i < FINAL_MSG_TS_LEN; i++)
	{
		*ts += ts_field[i] << (i * 8);
	}
}

static void get_msg_idx(const uint8 *ts_field, uint8 *ts)
{
	int i;
	*ts = 0;
	for (i = 0; i < 1; i++)
	{
		*ts += ts_field[i] << (i * 8);
	}
}

static uint64 get_tx_timestamp_u64(void)
{
	uint8 ts_tab[5];
	uint64 ts = 0;
	int i;
	dwt_readtxtimestamp(ts_tab);
	for (i = 4; i >= 0; i--)
	{
		ts <<= 8;
		ts |= ts_tab[i];
	}
	return ts;
}

static void final_msg_get_ts(const uint8 *ts_field, uint32 *ts)
{
	int i;
	*ts = 0;
	for (i = 0; i < FINAL_MSG_TS_LEN; i++)
	{
		*ts += ts_field[i] << (i * 8);
	}
}


//___________________ MSG_RESP_TDOA__________________
static void test_msg_set(uint8 *ts_field, uint64 ts)
{
	int i;
	for (i = 0; i < TEST_LEN; i++)
	{
		ts_field[i] = (uint8) ts;
		ts >>= 8;
	}
}

static void msg_set_idx(uint8 *ts_field, uint8 ts)
{
	int i;
	for (i = 0; i < 1; i++)
	{
		ts_field[i] = (uint8) ts;
		ts >>= 8;
	}
}
//____________________________________________________
#endif

#ifdef ANCH_SLAVE_3_V3

#define APP_NAME "RX_SYNC_A3"

//#pragma GCC optimize ("00")

#define ANCH3_ID	4

//	***************************************************************** TWR-CORRECTION **************************************************************************************

#define RX_BUF_TWR 	7		   						 //conta 1,2,3,4,...22 elementi
static uint8 twr_buffer[RX_BUF_TWR];

#define ANCH_CODE	1

#define TX_ANT_DLY 16436
#define RX_ANT_DLY 16436


static uint8 rx_poll_msg[] = {0x41, 0x88, 0, 0xCA, 0xDE, 'W', 'A', 'V', 'E', 0x21, 0, 0};
static uint8 tx_resp_msg[] = {0x41, 0x88, 0, 0xCA, 0xDE, 'V', 'E', 'W', 'A', 0x10, 0x02, 0, 0, 0, 0};
static uint8 rx_final_msg[] = {0x41, 0x88, 0, 0xCA, 0xDE, 'W', 'A', 'V', 'E', 0x23, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};

#define TWR_CYCLE 					10
#define ALL_MSG_SN_IDX 				2
#define FINAL_MSG_POLL_TX_TS_IDX 	10
#define FINAL_MSG_RESP_RX_TS_IDX 	14
#define FINAL_MSG_FINAL_TX_TS_IDX 	18
#define FINAL_MSG_TS_LEN 			4

static uint8 frame_seq_nb = 0;
#define RX_BUF_LEN 24
static uint8 rx_buffer[RX_BUF_LEN];
static uint32 status_reg = 0;

#define UUS_TO_DWT_TIME 				65536
#define POLL_RX_TO_RESP_TX_DLY_UUS 		2750
#define RESP_TX_TO_FINAL_RX_DLY_UUS 	500
#define FINAL_RX_TIMEOUT_UUS 			3300
#define PRE_TIMEOUT 					8

typedef signed long long int64;
typedef unsigned long long uint64;
static uint64 poll_rx_ts;
static uint64 resp_tx_ts;
static uint64 final_rx_ts;

#define SPEED_OF_LIGHT 299702547

//static double tof;
//static double distance;

static void final_msg_get_ts(const uint8 *ts_field, uint32 *ts);
static uint64 get_tx_timestamp_u64(void);

// ------------------------------------------------------------ DEF SYNC TIMESTAMP ---------------------------------------------------------------------------------
//#define CORR_DLY   370      //370->5, 0->4, ->7

#define START_BLINK 0x19
#define FINAL_BLINK 0x6
#define FINAL_MSG   0x23


#define ALL_MSG_COMMON_LEN 		  	 5
#define SYNC_CYCLE_IDX				 2
#define CODE_IDX 					 9
#define FINAL_MSG_POLL_TX_TS_IDX  	 10

#define FINAL_MSG_TS_LEN 		  	 4


#define SYNC_BUF_LEN 12   						 //conta 1,2,3,4,...22 elementi
static uint8 sync_buffer[SYNC_BUF_LEN];

static uint64 sync_poll_rx_ts;
static uint64 sync_final_rx_ts;
static double corr_factor[50];
static double total;

static uint64 get_rx_timestamp_u64(void);
static void get_ts(const uint8 *ts_field, uint32 *ts);
static void get_msg_idx(const uint8 *ts_field, uint8 *ts);

// ---------------------------------------------------------- DEF INIT ---------------------------------------------------------------------------------------
#define INIT_TDOA_MSG   0xFF
#define CODE_INIT  3

// ---------------------------------------------------------- DEF TDOA ---------------------------------------------------------------------------------------

#define UUS_TO_DWT_TIME		65536 		//1 uus = 512 / 499.2 �s and 1 �s = 499.2 * 128 dtu | UWB microsecond (uus) to device time unit (dtu, around 15.65 ps) conversion factor�

#define TAG_IDX				3
#define TAG_BLINK			0x10



#define BUF_INIT_TDOA 		6   					 //conta 1,2,3,4,...22 elementi
static uint8 tdoa_init_buffer[BUF_INIT_TDOA];

#define RX_BUF_TAG 			6 						 //conta 1,2,3,4,...22 elementi
static uint8 tag_buffer[RX_BUF_TAG];

static uint64 rx_init_ts;
static uint64 rx_init_ts_corr;
static uint64 ts;
static uint64 ts_corretto;
static uint64 total_ts;

static double dly_corr_factor;         // fattore di correzzione in dtu del delay pre-impostato in modo che sia in synch con il conteggio del master
static double tof_media;
static double tof_tot;
static int64 CORR_DLY;

//___________________ MSG_RESP_TDOA______________________
static uint8 tdoa_resp[] = {0xC5, 0, 0, 'T', 'E', 'S', 'T', 0, 0, 0, 0, 0, 0};

#define IDX_MSG_DIST  	7
#define TEST_LEN		4
#define ANCH_IDX		1
#define TAG_IDX			3
#define TOF				452    //POSIZIONE (2.12, 0)

#define TIME_SLOT	383386580   //in UWB tick ~ 6ms

static void test_msg_set(uint8 *ts_field, uint64 ts);
static void msg_set_idx(uint8 *ts_field, uint8 ts);
//___________________________________________________


int dw_main(void)
{
	lcd_display_str(APP_NAME);
	reset_DW1000(); /* Target specific drive of RSTn line into DW1000 low for a period. */
	port_set_dw1000_slowrate();
	if (dwt_initialise(DWT_LOADUCODE) == DWT_ERROR)
	{
		lcd_display_str("INIT FAILED");
		while (1)
		{ };
	}
	port_set_dw1000_fastrate();
	dwt_configure(&config);

	dwt_setrxantennadelay(RX_ANT_DLY);    //non vanno..conpensati da sync?
	dwt_settxantennadelay(TX_ANT_DLY);


	dwt_setleds(DWT_LEDS_ENABLE);


	while (1)
	{
		//applicazione stai in ascolta di msg init (ogni parte prevede un msg di inizializzazione)
		dwt_setrxtimeout(0);

		dwt_rxenable(DWT_START_RX_IMMEDIATE);
		while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR)))
		{ };

		// ************************ RX_QUALSIASICOSA *****************************

		if (status_reg & SYS_STATUS_RXFCG)
		{
			uint32 frame_len;
			dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);
			frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;

			switch(frame_len)
			{
			//	 _____________________________________________________________________TWR_INIT____________________________________________________________________________________
			case(RX_BUF_TWR):   //lung 7+ check codice ancora

				dwt_readrxdata(twr_buffer, frame_len, 0);

				if (twr_buffer[ANCH_CODE] == ANCH3_ID)
				{
					//	___________________________________________________________________TWR-CORRECTION__________________________________________________________________________________

					int twr_cycle = 0;  //ciclo una volta sola il controllo del twr
					tof_tot = 0;

					while(twr_cycle < TWR_CYCLE)
					{
						dwt_setrxtimeout(0);
						dwt_rxenable(DWT_START_RX_IMMEDIATE);

						while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR)))
						{ };
						if (status_reg & SYS_STATUS_RXFCG)
						{
							uint32 frame_len;
							dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);

							frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;
							if (frame_len <= RX_BUFFER_LEN)
							{
								dwt_readrxdata(rx_buffer, frame_len, 0);
							}
							rx_buffer[ALL_MSG_SN_IDX] = 0;
							if (memcmp(rx_buffer, rx_poll_msg, ALL_MSG_COMMON_LEN) == 0)
							{
								uint32 resp_tx_time;
								int ret;

								poll_rx_ts = get_rx_timestamp_u64();

								resp_tx_time = (poll_rx_ts + (POLL_RX_TO_RESP_TX_DLY_UUS * UUS_TO_DWT_TIME)) >> 8;
								dwt_setdelayedtrxtime(resp_tx_time);

								dwt_setrxaftertxdelay(RESP_TX_TO_FINAL_RX_DLY_UUS);
								dwt_setrxtimeout(FINAL_RX_TIMEOUT_UUS);

								tx_resp_msg[ALL_MSG_SN_IDX] = frame_seq_nb;
								dwt_writetxdata(sizeof(tx_resp_msg), tx_resp_msg, 0); /* Zero offset in TX buffer. */
								dwt_writetxfctrl(sizeof(tx_resp_msg), 0, 1); /* Zero offset in TX buffer, ranging. */
								ret = dwt_starttx(DWT_START_TX_DELAYED | DWT_RESPONSE_EXPECTED);
								if (ret == DWT_ERROR)
								{
									continue;
								}

								while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR)))
								{ };

								frame_seq_nb++;

								if (status_reg & SYS_STATUS_RXFCG)
								{
									dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG | SYS_STATUS_TXFRS);

									frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFLEN_MASK;
									if (frame_len <= RX_BUF_LEN)
									{
										dwt_readrxdata(rx_buffer, frame_len, 0);
									}

									rx_buffer[ALL_MSG_SN_IDX] = 0;
									if (memcmp(rx_buffer, rx_final_msg, ALL_MSG_COMMON_LEN) == 0)
									{
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
										//							tof = tof_dtu * DWT_TIME_UNITS;
										//							distance = tof * SPEED_OF_LIGHT;
										tof_tot = tof_tot + tof_dtu;
										twr_cycle++;
									}
								}
								else
								{
									dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
									dwt_rxreset();
								}
							}
						}
						else
						{
							dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
							dwt_rxreset();
						}

					}

					tof_media = tof_tot/10;
					CORR_DLY  = (int64)(TOF - tof_media);
					twr_cycle = 0;
				}
				else
				{
					Sleep(500); //se hai ricevuto un pacchetto di ranging e non � il tuo dormitela e poi rimettiti in rx
					continue;
				}

				break;

			//	__________________________________________________SYNC-PART ____________________________________________________________
			case(SYNC_BUF_LEN):    //lung 12, il sync si fa in parallelo perch� il master invia solo pacchetti

				total = 0;
				dwt_readrxdata(sync_buffer, frame_len, 0);

				// ---------------------------- CHECK BLINK_CODE ----------------------------------
				if (sync_buffer[CODE_IDX] == START_BLINK)
				{
					sync_poll_rx_ts = get_rx_timestamp_u64();  //primo timestamp

					dwt_rxenable(DWT_START_RX_IMMEDIATE);
					while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_ERR)))
					{ };

					// ---------------------------- ARRIVA SECONDO BLINK ----------------------------------
					if (status_reg & SYS_STATUS_RXFCG)
					{
						uint32 frame_len;
						dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);

						frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;
						if (frame_len <= SYNC_BUF_LEN)
						{
							dwt_readrxdata(sync_buffer, frame_len, 0);
						}
						// ---------------------------- CHECK BLINK_CODE ----------------------------------
						if (sync_buffer[CODE_IDX] == FINAL_BLINK)
						{
							sync_final_rx_ts = get_rx_timestamp_u64();  	//final timestamp

							dwt_rxenable(DWT_START_RX_IMMEDIATE);
							while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_ERR)))
							{ };

							// ----------------------------ARRIVA MSG FINALE ----------------------------------
							if (status_reg & SYS_STATUS_RXFCG)
							{
								uint32 frame_len;
								dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);

								frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;
								if (frame_len <= RX_BUFFER_LEN)
								{
									dwt_readrxdata(rx_buffer, frame_len, 0);
								}
								// ---------------------------- CHECK FINAL_CODE ----------------------------------
								if (rx_buffer[CODE_IDX] == FINAL_MSG)
								{
									//estraggo dato da ANCH_INITIATOR
									uint8 sync_count = 0;
									uint32 timer_master;
									uint64 timer_anch=0;
									int64  delta;

									get_ts(&rx_buffer[FINAL_MSG_POLL_TX_TS_IDX], &timer_master);
									get_msg_idx(&rx_buffer[SYNC_CYCLE_IDX], &sync_count);
									timer_anch 	= (uint64)(sync_final_rx_ts - sync_poll_rx_ts );

									delta = (int64)(timer_master - timer_anch);
									corr_factor[sync_count] = (double)timer_anch/(uint64)timer_master;

									if(sync_count == 49)
									{
										int j;

										for(j = 0; j < 50; j++)
										{
											total = total + corr_factor[j];
										}
										dly_corr_factor = total/50;
									}
								}
								else
								{
									dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
									dwt_rxreset();
								}
							}
							else
							{
								dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
								dwt_rxreset();
							}
						}
						else
						{
							dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
							dwt_rxreset();
						}
					}
					else
					{
						dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
						dwt_rxreset();
					}
				}
				else
				{
					dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
					dwt_rxreset();
					continue;
				}

				break;

				//***************************************************** TDOA ***************************************************************
			case(BUF_INIT_TDOA):

									dwt_readrxdata(tdoa_init_buffer, frame_len, 0);

			if (tdoa_init_buffer[CODE_INIT] == INIT_TDOA_MSG)
			{
				rx_init_ts = get_rx_timestamp_u64();
				rx_init_ts_corr = (uint64)(rx_init_ts - (uint64)TOF + CORR_DLY);

				dwt_rxenable(DWT_START_RX_IMMEDIATE);
				while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_ERR)))
				{ };

				// ---------------------------- TAG BLINK ----------------------------------
				if (status_reg & SYS_STATUS_RXFCG)
				{
					uint32 frame_len;
					dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);
					frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;

					if (frame_len <= RX_BUF_TAG)
					{
						dwt_readrxdata(tag_buffer, frame_len, 0);
					}

					if (tag_buffer[TAG_IDX] == TAG_BLINK)
					{
						uint8 tag_ID;

						ts = get_rx_timestamp_u64();
						ts_corretto = (uint64)(ts - CORR_DLY);


						get_msg_idx(&tag_buffer[1], &tag_ID);

						total_ts = (uint64)(ts_corretto - rx_init_ts_corr);

						char output[32] = "";
						sprintf(output,"%d", total_ts);
						lcd_display_str(output);

						Sleep(25);

						test_msg_set(&tdoa_resp[IDX_MSG_DIST], total_ts);
						msg_set_idx(&tdoa_resp[ANCH_IDX], ANCH3_ID);
						msg_set_idx(&tdoa_resp[TAG_IDX], tag_ID);

						dwt_writetxdata(sizeof(tdoa_resp), tdoa_resp, 0);
						dwt_writetxfctrl(sizeof(tdoa_resp), 0, 0);


						dwt_starttx(DWT_START_TX_IMMEDIATE);

						while (!(dwt_read32bitreg(SYS_STATUS_ID) & SYS_STATUS_TXFRS))
						{ };
						dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_TXFRS);
						//*************************************************************************************************

					}
					else
					{
						dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
						dwt_rxreset();
					}
				}
				else
				{
					dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
					dwt_rxreset();
				}
			}
			else
			{
				dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
				dwt_rxreset();
			}

			break;

			//se ricevo msg che non centra
			default: continue;

			} //SWITCH

			//			break;  //ogni volta che esco da switch rivai in rx mode e checca quello che arriva
		} //IF RX (LISTEN)

	} // while(1)

} //MAIN


static uint64 get_rx_timestamp_u64(void)
{
	uint8 ts_tab[5];
	uint64 ts = 0;
	int i;
	dwt_readrxtimestamp(ts_tab);
	for (i = 4; i >= 0; i--)
	{
		ts <<= 8;
		ts |= ts_tab[i];
	}
	return ts;
}

static void get_ts(const uint8 *ts_field, uint32 *ts)
{
	int i;
	*ts = 0;
	for (i = 0; i < FINAL_MSG_TS_LEN; i++)
	{
		*ts += ts_field[i] << (i * 8);
	}
}

static void get_msg_idx(const uint8 *ts_field, uint8 *ts)
{
	int i;
	*ts = 0;
	for (i = 0; i < 1; i++)
	{
		*ts += ts_field[i] << (i * 8);
	}
}

static uint64 get_tx_timestamp_u64(void)
{
	uint8 ts_tab[5];
	uint64 ts = 0;
	int i;
	dwt_readtxtimestamp(ts_tab);
	for (i = 4; i >= 0; i--)
	{
		ts <<= 8;
		ts |= ts_tab[i];
	}
	return ts;
}

static void final_msg_get_ts(const uint8 *ts_field, uint32 *ts)
{
	int i;
	*ts = 0;
	for (i = 0; i < FINAL_MSG_TS_LEN; i++)
	{
		*ts += ts_field[i] << (i * 8);
	}
}


//___________________ MSG_RESP_TDOA__________________
static void test_msg_set(uint8 *ts_field, uint64 ts)
{
	int i;
	for (i = 0; i < TEST_LEN; i++)
	{
		ts_field[i] = (uint8) ts;
		ts >>= 8;
	}
}

static void msg_set_idx(uint8 *ts_field, uint8 ts)
{
	int i;
	for (i = 0; i < 1; i++)
	{
		ts_field[i] = (uint8) ts;
		ts >>= 8;
	}
}
//____________________________________________________
#endif



#ifdef ANCH_SLAVE_7_V3_RIF

#define APP_NAME "RX_SYNC_A7"

//#pragma GCC optimize ("00")

#define ANCH7_ID	2

//	***************************************************************** TWR-CORRECTION **************************************************************************************

#define RX_BUF_TWR 	7		   						 //conta 1,2,3,4,...22 elementi
static uint8 twr_buffer[RX_BUF_TWR];

#define ANCH_CODE	1

#define TX_ANT_DLY 16436
#define RX_ANT_DLY 16436
//#define POSITION 5960 //in mm

static uint8 rx_poll_msg[] = {0x41, 0x88, 0, 0xCA, 0xDE, 'W', 'A', 'V', 'E', 0x21, 0, 0};
static uint8 tx_resp_msg[] = {0x41, 0x88, 0, 0xCA, 0xDE, 'V', 'E', 'W', 'A', 0x10, 0x02, 0, 0, 0, 0};
static uint8 rx_final_msg[] = {0x41, 0x88, 0, 0xCA, 0xDE, 'W', 'A', 'V', 'E', 0x23, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};

#define TWR_CYCLE 					10
#define ALL_MSG_SN_IDX 				2
#define FINAL_MSG_POLL_TX_TS_IDX 	10
#define FINAL_MSG_RESP_RX_TS_IDX 	14
#define FINAL_MSG_FINAL_TX_TS_IDX 	18
#define FINAL_MSG_TS_LEN 			4

static uint8 frame_seq_nb = 0;
#define RX_BUF_LEN 24
static uint8 rx_buffer[RX_BUF_LEN];
static uint32 status_reg = 0;

#define UUS_TO_DWT_TIME 				65536
#define POLL_RX_TO_RESP_TX_DLY_UUS 		2750
#define RESP_TX_TO_FINAL_RX_DLY_UUS 	500
#define FINAL_RX_TIMEOUT_UUS 			3300
#define PRE_TIMEOUT 					8

typedef signed long long int64;
typedef unsigned long long uint64;
static uint64 poll_rx_ts;
static uint64 resp_tx_ts;
static uint64 final_rx_ts;

#define SPEED_OF_LIGHT 299702547

//static double tof;
//static double distance;

static void final_msg_get_ts(const uint8 *ts_field, uint32 *ts);
static uint64 get_tx_timestamp_u64(void);

// ------------------------------------------------------------ DEF SYNC TIMESTAMP ---------------------------------------------------------------------------------
//#define CORR_DLY   370      //370->5, 0->4, ->7

#define START_BLINK 0x19
#define FINAL_BLINK 0x6
#define FINAL_MSG   0x23


#define ALL_MSG_COMMON_LEN 		  	 5
#define SYNC_CYCLE_IDX				 2
#define CODE_IDX 					 9
#define FINAL_MSG_POLL_TX_TS_IDX  	 10

#define FINAL_MSG_TS_LEN 		  	 4


#define SYNC_BUF_LEN 12   						 //conta 1,2,3,4,...22 elementi
static uint8 sync_buffer[SYNC_BUF_LEN];

static uint64 sync_poll_rx_ts;
static uint64 sync_final_rx_ts;
static double corr_factor[50];
static double total;

static uint64 get_rx_timestamp_u64(void);
static void get_ts(const uint8 *ts_field, uint32 *ts);
static void get_msg_idx(const uint8 *ts_field, uint8 *ts);

// ---------------------------------------------------------- DEF INIT ---------------------------------------------------------------------------------------
#define INIT_TDOA_MSG   0xFF
#define CODE_INIT  3

// ---------------------------------------------------------- DEF TDOA ---------------------------------------------------------------------------------------

#define UUS_TO_DWT_TIME		65536 		//1 uus = 512 / 499.2 �s and 1 �s = 499.2 * 128 dtu | UWB microsecond (uus) to device time unit (dtu, around 15.65 ps) conversion factor�

#define TAG_IDX				3
#define TAG_BLINK			0x10



#define BUF_INIT_TDOA 		6   					 //conta 1,2,3,4,...22 elementi
static uint8 tdoa_init_buffer[BUF_INIT_TDOA];

#define RX_BUF_TAG 			6 						 //conta 1,2,3,4,...22 elementi
static uint8 tag_buffer[RX_BUF_TAG];

static uint64 rx_init_ts;
static uint64 rx_init_ts_corr;
static uint64 ts;
static uint64 ts_corretto;
static uint64 total_ts;

static double dly_corr_factor;         // fattore di correzzione in dtu del delay pre-impostato in modo che sia in synch con il conteggio del master
static double tof_media;
static double tof_tot;
static int64 CORR_DLY;

//___________________ MSG_RESP_TDOA______________________
static uint8 tdoa_resp[] = {0xC5, 0, 0, 'T', 'E', 'S', 'T', 0, 0, 0, 0, 0, 0};

#define IDX_MSG_DIST  	7
#define TEST_LEN		4
#define ANCH_IDX		1
#define TAG_IDX			3
#define TOF				901     //895(5)/901(7)/1270(4)
#define CORR_EMPIRICA 	120

#define TIME_SLOT	1150159740   //in UWB tick ~ 18 ms

static void test_msg_set(uint8 *ts_field, uint64 ts);
static void msg_set_idx(uint8 *ts_field, uint8 ts);
//___________________________________________________


int dw_main(void)
{
	lcd_display_str(APP_NAME);
	reset_DW1000(); /* Target specific drive of RSTn line into DW1000 low for a period. */
	port_set_dw1000_slowrate();
	if (dwt_initialise(DWT_LOADUCODE) == DWT_ERROR)
	{
		lcd_display_str("INIT FAILED");
		while (1)
		{ };
	}
	port_set_dw1000_fastrate();
	dwt_configure(&config);


	dwt_setrxantennadelay(RX_ANT_DLY);    //non vanno..conpensati da sync?
	dwt_settxantennadelay(TX_ANT_DLY);
	dwt_setleds(DWT_LEDS_ENABLE);

	while (1)
	{
		//applicazione stai in ascolta di msg init (ogni parte prevede un msg di inizializzazione)
		dwt_setrxtimeout(0);

		dwt_rxenable(DWT_START_RX_IMMEDIATE);
		while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR)))
		{ };

		// ************************ RX_QUALSIASICOSA *****************************

		if (status_reg & SYS_STATUS_RXFCG)
		{
			uint32 frame_len;
			dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);
			frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;

			switch(frame_len)
			{
			//	 _____________________________________________________________________TWR_INIT____________________________________________________________________________________
			case(RX_BUF_TWR):   //lung 7+ check codice ancora

				dwt_readrxdata(twr_buffer, frame_len, 0);

				if (twr_buffer[ANCH_CODE] == ANCH7_ID)
				{
					//	___________________________________________________________________TWR-CORRECTION__________________________________________________________________________________

					int twr_cycle = 0;  //ciclo una volta sola il controllo del twr
					tof_tot = 0;

					while(twr_cycle < TWR_CYCLE)
					{
						dwt_setrxtimeout(0);
						dwt_rxenable(DWT_START_RX_IMMEDIATE);

						while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR)))
						{ };
						if (status_reg & SYS_STATUS_RXFCG)
						{
							uint32 frame_len;
							dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);

							frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;
							if (frame_len <= RX_BUFFER_LEN)
							{
								dwt_readrxdata(rx_buffer, frame_len, 0);
							}
							rx_buffer[ALL_MSG_SN_IDX] = 0;
							if (memcmp(rx_buffer, rx_poll_msg, ALL_MSG_COMMON_LEN) == 0)
							{
								uint32 resp_tx_time;
								int ret;

								poll_rx_ts = get_rx_timestamp_u64();

								resp_tx_time = (poll_rx_ts + (POLL_RX_TO_RESP_TX_DLY_UUS * UUS_TO_DWT_TIME)) >> 8;
								dwt_setdelayedtrxtime(resp_tx_time);

								dwt_setrxaftertxdelay(RESP_TX_TO_FINAL_RX_DLY_UUS);
								dwt_setrxtimeout(FINAL_RX_TIMEOUT_UUS);

								tx_resp_msg[ALL_MSG_SN_IDX] = frame_seq_nb;
								dwt_writetxdata(sizeof(tx_resp_msg), tx_resp_msg, 0); /* Zero offset in TX buffer. */
								dwt_writetxfctrl(sizeof(tx_resp_msg), 0, 1); /* Zero offset in TX buffer, ranging. */
								ret = dwt_starttx(DWT_START_TX_DELAYED | DWT_RESPONSE_EXPECTED);
								if (ret == DWT_ERROR)
								{
									continue;
								}

								while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR)))
								{ };

								frame_seq_nb++;

								if (status_reg & SYS_STATUS_RXFCG)
								{
									dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG | SYS_STATUS_TXFRS);

									frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFLEN_MASK;
									if (frame_len <= RX_BUF_LEN)
									{
										dwt_readrxdata(rx_buffer, frame_len, 0);
									}

									rx_buffer[ALL_MSG_SN_IDX] = 0;
									if (memcmp(rx_buffer, rx_final_msg, ALL_MSG_COMMON_LEN) == 0)
									{
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
										//							tof = tof_dtu * DWT_TIME_UNITS;
										//							distance = tof * SPEED_OF_LIGHT;
										tof_tot = tof_tot + tof_dtu;
										twr_cycle++;
									}
								}
								else
								{
									dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
									dwt_rxreset();
								}
							}
						}
						else
						{
							dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
							dwt_rxreset();
						}

					}

					CORR_DLY = tof_tot/10;
					twr_cycle = 0;
				}
				else
				{
					Sleep(500); //se hai ricevuto un pacchetto di ranging e non � il tuo dormitela e poi rimettiti in rx
					continue;
				}

				break;

			//	__________________________________________________SYNC-PART ____________________________________________________________
			case(SYNC_BUF_LEN):    //lung 12, il sync si fa in parallelo perch� il master invia solo pacchetti

				total = 0;
				dwt_readrxdata(sync_buffer, frame_len, 0);

				// ---------------------------- CHECK BLINK_CODE ----------------------------------
				if (sync_buffer[CODE_IDX] == START_BLINK)
				{
					sync_poll_rx_ts = get_rx_timestamp_u64();  //primo timestamp

					dwt_rxenable(DWT_START_RX_IMMEDIATE);
					while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_ERR)))
					{ };

					// ---------------------------- ARRIVA SECONDO BLINK ----------------------------------
					if (status_reg & SYS_STATUS_RXFCG)
					{
						uint32 frame_len;
						dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);

						frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;
						if (frame_len <= SYNC_BUF_LEN)
						{
							dwt_readrxdata(sync_buffer, frame_len, 0);
						}
						// ---------------------------- CHECK BLINK_CODE ----------------------------------
						if (sync_buffer[CODE_IDX] == FINAL_BLINK)
						{
							sync_final_rx_ts = get_rx_timestamp_u64();  	//final timestamp

							dwt_rxenable(DWT_START_RX_IMMEDIATE);
							while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_ERR)))
							{ };

							// ----------------------------ARRIVA MSG FINALE ----------------------------------
							if (status_reg & SYS_STATUS_RXFCG)
							{
								uint32 frame_len;
								dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);

								frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;
								if (frame_len <= RX_BUFFER_LEN)
								{
									dwt_readrxdata(rx_buffer, frame_len, 0);
								}
								// ---------------------------- CHECK FINAL_CODE ----------------------------------
								if (rx_buffer[CODE_IDX] == FINAL_MSG)
								{
									//estraggo dato da ANCH_INITIATOR
									uint8 sync_count = 0;
									uint32 timer_master;
									uint64 timer_anch=0;
									int64  delta;

									get_ts(&rx_buffer[FINAL_MSG_POLL_TX_TS_IDX], &timer_master);
									get_msg_idx(&rx_buffer[SYNC_CYCLE_IDX], &sync_count);
									timer_anch 	= (uint64)(sync_final_rx_ts - sync_poll_rx_ts);

									delta = (int64)(timer_master - timer_anch);
									corr_factor[sync_count] = (double)timer_anch/(uint64)timer_master;

									if(sync_count == 49)
									{
										int j;

										for(j = 0; j < 50; j++)
										{
											total = total + corr_factor[j];
										}
										dly_corr_factor = total/50;
									}
								}
								else
								{
									dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
									dwt_rxreset();
								}
							}
							else
							{
								dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
								dwt_rxreset();
							}
						}
						else
						{
							dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
							dwt_rxreset();
						}
					}
					else
					{
						dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
						dwt_rxreset();
					}
				}
				else
				{
					dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
					dwt_rxreset();
					continue;
				}

				break;

			//***************************************************** TDOA ***************************************************************
			case(BUF_INIT_TDOA):

				dwt_readrxdata(tdoa_init_buffer, frame_len, 0);

				if (tdoa_init_buffer[CODE_INIT] == INIT_TDOA_MSG)
				{
					rx_init_ts = get_rx_timestamp_u64();
					rx_init_ts_corr = (uint64)((uint64)(rx_init_ts - (uint64)(CORR_DLY)) * dly_corr_factor);   //per rx il timestamp dal master passa tof (li faccio partire insieme e aggiungo la correzzione del delay)
					// - TOF perch� lo slave prende il valore del registro in ritardo di TOF

					//while()   //fin tanto che non arrivano tutti i tag..intanto vedo se va con un tag

					dwt_rxenable(DWT_START_RX_IMMEDIATE);
					while (!((status_reg = dwt_read32bitreg(SYS_STATUS_ID)) & (SYS_STATUS_RXFCG | SYS_STATUS_ALL_RX_ERR)))
					{ };

					// ---------------------------- TAG BLINK ----------------------------------
					if (status_reg & SYS_STATUS_RXFCG)
					{
						uint32 frame_len;
						dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);
						frame_len = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;

						if (frame_len <= RX_BUF_TAG)
						{
							dwt_readrxdata(tag_buffer, frame_len, 0);
						}

						if (tag_buffer[TAG_IDX] == TAG_BLINK)
						{
							uint8 tag_ID;

							ts = get_rx_timestamp_u64();
							ts_corretto = (uint64)(ts * dly_corr_factor); // + TOF + (uint64)(CORR_DLY));

							get_msg_idx(&tag_buffer[1], &tag_ID);

							total_ts = (uint64)(ts_corretto - rx_init_ts_corr + (uint64)(CORR_EMPIRICA));
//							total_ts = ts -  rx_init_ts;
							char output[32] = "";
							sprintf(output,"%d", total_ts);
							lcd_display_str(output);

							// ________________ TEST-DISTANZA ________________

//							uint32 tx_delay;
//							tx_delay = (uint32)(ts_corretto) + TIME_SLOT;
//							dwt_setdelayedtrxtime(tx_delay);

							Sleep(30);

							test_msg_set(&tdoa_resp[IDX_MSG_DIST], total_ts);
							msg_set_idx(&tdoa_resp[ANCH_IDX], ANCH7_ID);
							msg_set_idx(&tdoa_resp[TAG_IDX], tag_ID);

							dwt_writetxdata(sizeof(tdoa_resp), tdoa_resp, 0);
							dwt_writetxfctrl(sizeof(tdoa_resp), 0, 0);


							dwt_starttx(DWT_START_TX_IMMEDIATE);

							while (!(dwt_read32bitreg(SYS_STATUS_ID) & SYS_STATUS_TXFRS))
							{ };
							dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_TXFRS);
							//*************************************************************************************************

						}
						else
						{
							dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
							dwt_rxreset();
						}
					}
					else
					{
						dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
						dwt_rxreset();
					}
				}
				else
				{
					dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_TO | SYS_STATUS_ALL_RX_ERR);
					dwt_rxreset();
				}

				break;

			//se ricevo msg che non centra
			default: continue;

			} //SWITCH

//			break;  //ogni volta che esco da switch rivai in rx mode e checca quello che arriva
		} //IF RX (LISTEN)

	} // while(1)

} //MAIN


static uint64 get_rx_timestamp_u64(void)
{
	uint8 ts_tab[5];
	uint64 ts = 0;
	int i;
	dwt_readrxtimestamp(ts_tab);
	for (i = 4; i >= 0; i--)
	{
		ts <<= 8;
		ts |= ts_tab[i];
	}
	return ts;
}

static void get_ts(const uint8 *ts_field, uint32 *ts)
{
	int i;
	*ts = 0;
	for (i = 0; i < FINAL_MSG_TS_LEN; i++)
	{
		*ts += ts_field[i] << (i * 8);
	}
}

static void get_msg_idx(const uint8 *ts_field, uint8 *ts)
{
	int i;
	*ts = 0;
	for (i = 0; i < 1; i++)
	{
		*ts += ts_field[i] << (i * 8);
	}
}

static uint64 get_tx_timestamp_u64(void)
{
	uint8 ts_tab[5];
	uint64 ts = 0;
	int i;
	dwt_readtxtimestamp(ts_tab);
	for (i = 4; i >= 0; i--)
	{
		ts <<= 8;
		ts |= ts_tab[i];
	}
	return ts;
}

static void final_msg_get_ts(const uint8 *ts_field, uint32 *ts)
{
	int i;
	*ts = 0;
	for (i = 0; i < FINAL_MSG_TS_LEN; i++)
	{
		*ts += ts_field[i] << (i * 8);
	}
}


//___________________ MSG_RESP_TDOA__________________
static void test_msg_set(uint8 *ts_field, uint64 ts)
{
	int i;
	for (i = 0; i < TEST_LEN; i++)
	{
		ts_field[i] = (uint8) ts;
		ts >>= 8;
	}
}

static void msg_set_idx(uint8 *ts_field, uint8 ts)
{
	int i;
	for (i = 0; i < 1; i++)
	{
		ts_field[i] = (uint8) ts;
		ts >>= 8;
	}
}
//____________________________________________________
#endif
