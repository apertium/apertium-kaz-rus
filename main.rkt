#lang racket

; Racket interface for apertium-kaz-rus
;
; REQUIRES: apertiumpp package.
; https://taruen.github.io/apertiumpp/apertiumpp/ gives info on how to install
; it.

(provide kaz-rus
         kaz-rus-from-pretransfer-to-biltrans
         kaz-rus-from-t1x-to-postgen)

(require pkg/lib
         rackunit
         rash
         apertiumpp/streamparser)

(define (symbol-append s1 s2)
  (string->symbol (string-append (symbol->string s1) (symbol->string s2))))

(define A-KAZ-RUS './)
(define A-KAZ-RUS-BIL (symbol-append A-KAZ-RUS 'kaz-rus.autobil.bin))
(define A-KAZ-RUS-T1X (symbol-append A-KAZ-RUS 'apertium-kaz-rus.kaz-rus.t1x))
(define A-KAZ-RUS-T1X-BIN (symbol-append A-KAZ-RUS 'kaz-rus.t1x.bin))
(define A-KAZ-RUS-T2X (symbol-append A-KAZ-RUS 'apertium-kaz-rus.kaz-rus.t2x))
(define A-KAZ-RUS-T2X-BIN (symbol-append A-KAZ-RUS 'kaz-rus.t2x.bin))
(define A-KAZ-RUS-T3X (symbol-append A-KAZ-RUS 'apertium-kaz-rus.kaz-rus.t3x))
(define A-KAZ-RUS-T3X-BIN (symbol-append A-KAZ-RUS 'kaz-rus.t3x.bin))
(define A-KAZ-RUS-T4X (symbol-append A-KAZ-RUS 'apertium-kaz-rus.kaz-rus.t4x))
(define A-KAZ-RUS-T4X-BIN (symbol-append A-KAZ-RUS 'kaz-rus.t4x.bin))
(define A-KAZ-RUS-GEN (symbol-append A-KAZ-RUS 'kaz-rus.autogen.bin))
(define A-KAZ-RUS-PGEN (symbol-append A-KAZ-RUS 'kaz-rus.autopgen.bin))

(define (kaz-rus s)
  (parameterize ([current-directory (pkg-directory "apertium-kaz-rus")])
    (rash
     "echo (values s) | apertium -d . kaz-rus")))

(define (kaz-rus-from-pretransfer-to-biltrans s)
  (parameterize ([current-directory (pkg-directory "apertium-kaz-rus")])
    (rash
     "echo (values s) | apertium-pretransfer | "
     "lt-proc -b (values A-KAZ-RUS-BIL)")))

(define (kaz-rus-from-t1x-to-postgen s)
  (parameterize ([current-directory (pkg-directory "apertium-kaz-rus")])
    (rash
     "echo (values s) | "
     "apertium-transfer -b (values A-KAZ-RUS-T1X) (values A-KAZ-RUS-T1X-BIN) | "
     "apertium-interchunk (values A-KAZ-RUS-T2X) (values A-KAZ-RUS-T2X-BIN) | "
     "apertium-interchunk (values A-KAZ-RUS-T3X) (values A-KAZ-RUS-T3X-BIN) | "
     "apertium-postchunk (values A-KAZ-RUS-T4X) (values A-KAZ-RUS-T4X-BIN) | "      
     "lt-proc -g (values A-KAZ-RUS-GEN) | "
     "lt-proc -p (values A-KAZ-RUS-PGEN)"))) 