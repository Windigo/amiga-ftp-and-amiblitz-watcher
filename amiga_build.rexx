/*
 * AmiBlitz3 Auto-Build Script voor Amiga
 * =======================================
 *
 * Dit AREXX script wordt aangeroepen door de Mac file watcher.
 * Het compileert je AmiBlitz3 project en start het programma.
 *
 * Installatie:
 *   1. Kopieer dit script naar je Amiga (via FTP)
 *   2. Zet het in SYS:WBStartup of start het vanuit een shell:
 *      RX amiga_build.rexx
 *
 * Gebruik:
 *   Het script luistert op TCP poort 9999 naar signalen van de Mac.
 *   Als er een bestand is gewijzigd, compileert het en start het.
 */

OPTIONS RESULTS

/* Configuratie - pas aan voor jouw situatie */
PROJECT_DIR = "DH0:Projects/MyBlitzProject/"
MAIN_FILE = "main.bb2"
COMPILER = "Amiblitz3:Amiblitz3"
SIGNAL_PORT = 9999

SAY "AmiBlitz3 Auto-Build gestart"
SAY "Project: "PROJECT_DIR
SAY "Wacht op signaal van Mac op poort "SIGNAL_PORT"..."


/* Eenvoudige TCP listener */
DO FOREVER
    /* Wacht een paar seconden */
    CALL Wait 5

    /* Kijk of er een nieuw bestand is in de project folder */
    FILE_COUNT = 0
    FILES = SHOWDIR(PROJECT_DIR, "F")
    IF FILES <> "" THEN DO
        FILE_COUNT = WORDS(FILES)
    END

    /* Als we een signaal bestand zien, compileer dan */
    SIGNAL_FILE = PROJECT_DIR || ".build_signal"
    IF OPEN("signal", SIGNAL_FILE, "R") THEN DO
        CALL CLOSE("signal")
        CALL DELETE(SIGNAL_FILE)

        SAY "Signaal ontvangen! Start compilatie..."

        /* Compileer met AmiBlitz3 */
        ADDRESS COMMAND
        COMPILE_CMD = COMPILER || " " || PROJECT_DIR || MAIN_FILE
        SAY "Compileer: "COMPILE_CMD
        'RUN 'COMPILE_CMD

        /* Wacht tot compilatie klaar is */
        CALL Wait 3

        /* Start het programma */
        PROGRAM = PROJECT_DIR || "MyProgram"
        SAY "Start programma: "PROGRAM
        'RUN 'PROGRAM
    END
END

EXIT 0


/*
 * Hulpfunctie: wacht aantal seconden
 */
WAIT:
    PARSE ARG seconds
    ADDRESS COMMAND 'WAIT 'seconds
    RETURN


/*
 * Hulpfunctie: toon directory inhoud
 */
SHOWDIR:
    PARSE ARG path, type
    ADDRESS COMMAND 'LIST "'path'" 'type' TO TMP:dirlist.tmp'
    IF OPEN("dirlist", "TMP:dirlist.tmp", "R") THEN DO
        CONTENT = READLN("dirlist")
        CALL CLOSE("dirlist")
        ADDRESS COMMAND 'DELETE TMP:dirlist.tmp QUIET'
        RETURN CONTENT
    END
    RETURN ""
