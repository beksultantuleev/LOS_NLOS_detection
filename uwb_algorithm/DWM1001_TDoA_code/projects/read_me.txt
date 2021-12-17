
	=========================================================================================================================================

									NB: SYNC CYCLE!!!

	=========================================================================================================================================
	|																	|
	| con le dwm10001 il timer fa schifo e tutte le ancore contano abbastanza a caso:							|
	|																	|
	|	- drift tra due ancore su 5ms di oltre 3000tick (accettabile < 100) nonostante la correzzione iniziale in TWR.			|
	|	  Questo significa che siccome il twr avviene con conteggi di timestap brevi, non basta a 					|
	|	  per correggere i timer. (errore = ANT_DELAY + drift). Con le dwm1001 il drift iniziale non è trascurabile ed è di molto	|
	|	  più incisivo del fattore antenna delay-> introduco un sync per sincronizzarsi ad una stessa timebase -> faccio contare 	|
	|	  per un tempo noto e lungo ~10ms le ancore rispetto all'ancora master e gurda quanto sbarellano.				|
	|																	|
 	|																	|				
	|	  																|
	|	  																|	
	|																	|
	| con le EVB1000 invece una volta calibrato il delay d'antenna il conteggio era molto preciso per cui il sync non serviva! 		|
	|																	|
	=========================================================================================================================================


	    APPUNTI: osservare dopo quanto essere corrette e syncronizzate le ancore iniano a driftare con errori in media superiori 100 tick