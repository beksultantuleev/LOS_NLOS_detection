/*
 * configurations words and things for anchors
 * 
 */

#ifndef __ANCH_CONF_H
#define __ANCH_CONF_H


//#define NUM_ANCH      5      // num of slave only


// change this for different anchors ID (only generic anchors !)
// ANCH_ID = 0,1,2,3,4
//#define ANCH_ID       ANCH3


//-----------------dw1000----------------------------

static dwt_config_t config = {
    5,                /* Channel number. */
    DWT_PRF_64M,      /* Pulse repetition frequency. */
    DWT_PLEN_128,     /* Preamble length. Used in TX only. */
    DWT_PAC8,         /* Preamble acquisition chunk size. Used in RX only. */
    10,               /* TX preamble code. Used in TX only. */
    10,               /* RX preamble code. Used in RX only. */
    0,                /* 0 to use standard SFD, 1 to use non-standard SFD. */
    DWT_BR_6M8,       /* Data rate. */
    DWT_PHRMODE_STD,  /* PHY header mode. */
    (129 + 8 - 8)     /* SFD timeout (preamble length + 1 + SFD length - PAC size). Used in RX only. */
};

//static dwt_config_t config = {
//    2,               /* Channel number. */
//    DWT_PRF_64M,     /* Pulse repetition frequency. */
//    DWT_PLEN_512,    /* Preamble length. Used in TX only. */
//    DWT_PAC16,       /* Preamble acquisition chunk size. Used in RX only. */
//    9,               /* TX preamble code. Used in TX only. */
//    9,               /* RX preamble code. Used in RX only. */
//    1,               /* 0 to use standard SFD, 1 to use non-standard SFD. */
//    DWT_BR_850K,     /* Data rate. */
//    DWT_PHRMODE_STD, /* PHY header mode. */
//    (513 + 64 - 16)  /* SFD timeout (preamble length + 1 + SFD length - PAC size). Used in RX only. */
//};


/* Preamble timeout, in multiple of PAC size. See NOTE x below. */
// probabilmente mai utilizzato
#define PRE_TIMEOUT 1000

/* Delay between frames, in UWB microseconds. See NOTE x below. */
//probabilmente mai utilizzato
#define POLL_TX_TO_RESP_RX_DLY_UUS 100 

/*Should be accurately calculated during calibration*/
#define TX_ANT_DLY 16456
#define RX_ANT_DLY 16456	

//--------------dw1000---end---------------

/* UWB microsecond (uus) to device time unit (dtu, around 15.65 ps) conversion factor.
* 1 uus = 512 / 499.2 �s and 1 �s = 499.2 * 128 dtu. */
#define UUS_TO_DWT_TIME 65536

/* Speed of light in air, in metres per second. */
#define SPEED_OF_LIGHT 299702547 


/* Inter-ranging delay period, in milliseconds. */
//usato solo in ancora master !
#define RNG_DELAY_MS 50       

//	***************************************************************** TWR-CORRECTION PARAMETERS **************************************************************************************

#define NUM_TWR_CYCLE 10

/* Length of the common part of the message (up to and including the function code, see NOTE below). */
#define ALL_MSG_COMMON_LEN 10
/* Indexes to access some of the fields in the frames defined above. */
#define ALL_MSG_SN_IDX              2
#define FINAL_MSG_POLL_TX_TS_IDX    10
#define FINAL_MSG_RESP_RX_TS_IDX    14
#define FINAL_MSG_FINAL_TX_TS_IDX   18
#define FINAL_MSG_TS_LEN            4
/*
 * 2. The messages here are similar to those used in the DecaRanging ARM application (shipped with EVK1000 kit). They comply with the IEEE
 *    802.15.4 standard MAC data frame encoding and they are following the ISO/IEC:24730-62:2013 standard. The messages used are:
 *     - a poll message sent by the initiator to trigger the ranging exchange.
 *     - a response message sent by the responder allowing the initiator to go on with the process
 *     - a final message sent by the initiator to complete the exchange and provide all information needed by the responder to compute the
 *       time-of-flight (distance) estimate.
 *    The first 10 bytes of those frame are common and are composed of the following fields:
 *     - byte 0/1: frame control (0x8841 to indicate a data frame using 16-bit addressing).
 *     - byte 2: sequence number, incremented for each new frame.
 *     - byte 3/4: PAN ID (0xDECA).
 *     - byte 5/6: destination address, see NOTE 3 below.
 *     - byte 7/8: source address, see NOTE 3 below.
 *     - byte 9: function code (specific values to indicate which message it is in the ranging process).
 *    The remaining bytes are specific to each message as follows:
 *    Poll message:
 *     - no more data
 *    Response message:
 *     - byte 10: activity code (0x02 to tell the initiator to go on with the ranging exchange).
 *     - byte 11/12: activity parameter, not used here for activity code 0x02.
 *    Final message:
 *     - byte 10 -> 13: poll message transmission timestamp.
 *     - byte 14 -> 17: response message reception timestamp.
 *     - byte 18 -> 21: final message transmission timestamp.
 *    All messages end with a 2-byte checksum automatically set by DW1000.
 *
 * 3. Source and destination addresses are hard coded constants in this example to keep it simple but for a real product every device should have a
 *    unique ID. Here, 16-bit addressing is used to keep the messages as short as possible but, in an actual application, this should be done only
 *    after an exchange of specific messages used to define those short addresses for each device participating to the ranging exchange.
 */

// Not enough time to write the data so TX timeout extended for nRF operation.
// Might be able to get away with 800 uSec but would have to test
// See note 6 at the end of this file
// generic anchor delay, beware of timing !
#define POLL_RX_TO_RESP_TX_DLY_UUS 1100  //1100

// master anchor delay
#define RESP_RX_TO_FINAL_TX_DLY_UUS 1100 //1100

/* This is the delay from the end of the frame transmission to the enable of the receiver, as programmed for the DW1000's wait for response feature. */
#define RESP_TX_TO_FINAL_RX_DLY_UUS 500 //500

/* Receive final timeout. See NOTE 5 below. */
#define FINAL_RX_TIMEOUT_UUS 3300



/*
 *SYNC
 */
#define SYNC_CYCLE 10

#define START_BLINK   0x19
#define FINAL_BLINK   0x6
#define FINAL_MSG     0x23

#define TAG_BLINK   0x10

#define ALL_MSG_COMMON_LEN        5
#define SYNC_CYCLE_IDX            2
#define CODE_IDX                  9

#define FINAL_MSG_TS_LEN          4

// ***************************************************************** DEF INIT MSG *****************************************************************
#define INIT_IDX        3
#define INIT_TDOA_MSG   0xFF

// ***************************************************************** DEF TDOA PHASE *****************************************************************
#define TAG_IDX         4
#define NUM_TAG_IDX     2
#define TAG_BLINK_MSG   0x10

// ***************************************************************** DEF MATLAB PHASE *****************************************************************
#define TEST_LEN      4
#define TEST_IDX      0
#define TEST_MSG      0xC5
#define MSG_DIST_IDX  7
#define ANCH_IDX      1      // idx ancora nel frame rx


#endif