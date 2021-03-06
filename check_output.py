import fileinput
import time
from datetime import datetime
import dateutil
from dateutil.tz import *
from _datetime import timedelta
from os import listdir
from os.path import isfile, join
import os
from posix import getcwd
import json 
import dateutil.parser as dp

tz_str = '''-12 Y
-11 X NUT SST
-10 W CKT HAST HST TAHT TKT
-9 V AKST GAMT GIT HADT HNY
-8 U AKDT CIST HAY HNP PST PT
-7 T HAP HNR MST PDT
-6 S CST EAST GALT HAR HNC MDT
-5 R CDT COT EASST ECT EST ET HAC HNE PET
-4 Q AST BOT CLT COST EDT FKT GYT HAE HNA PYT
-3 P ADT ART BRT CLST FKST GFT HAA PMST PYST SRT UYT WGT
-2 O BRST FNT PMDT UYST WGST
-1 N AZOT CVT EGT
0 Z EGST GMT UTC WET WT
1 A CET DFT WAT WEDT WEST
2 B CAT CEDT CEST EET SAST WAST
3 C EAT EEDT EEST IDT MSK
4 D AMT AZT GET GST KUYT MSD MUT RET SAMT SCT
5 E AMST AQTT AZST HMT MAWT MVT PKT TFT TJT TMT UZT YEKT
6 F ALMT BIOT BTT IOT KGT NOVT OMST YEKST
7 G CXT DAVT HOVT ICT KRAT NOVST OMSST THA WIB
8 H ACT AWST BDT BNT CAST HKT IRKT KRAST MYT PHT SGT ULAT WITA WST
9 I AWDT IRKST JST KST PWT TLT WDT WIT YAKT
10 K AEST ChST PGT VLAT YAKST YAPT
11 L AEDT LHDT MAGT NCT PONT SBT VLAST VUT
12 M ANAST ANAT FJT GILT MAGST MHT NZST PETST PETT TVT WFT
13 FJST NZDT
11.5 NFT
10.5 ACDT LHST
9.5 ACST
6.5 CCT MMT
5.75 NPT
5.5 SLT
4.5 AFT IRDT
3.5 IRST
-2.5 HAT NDT
-3.5 HNT NST NT
-4.5 HLV VET
-9.5 MART MIT'''

tzd = {}
for tz_descr in map(str.split, tz_str.split('\n')):
    tz_offset = int(float(tz_descr[0]) * 3600)
    for tz_code in tz_descr[1:]:
        tzd[tz_code] = tz_offset

if '__main__' == __name__:
    filenames = [ ]
    for f in listdir(getcwd()):
         if isfile(join(getcwd(),f)):
             if f.split(".")[-1] == 'log':
                 filenames.append(f)
    last_timestamp = dict()
    counter = {f:0 for f in filenames}
    errors = []
    max_lag = 0
    window_start = datetime.now(tzlocal()) + timedelta(days=-100)
    linebuffer = ''
    for line in fileinput.input():
        if line != '\n':
            linebuffer += line
        else:
            if linebuffer.strip():
                continue
            print(linebuffer)
            msg = json.loads(linebuffer)
            if 'note' in msg and 'at' in msg:
                ts = msg['at']
                time_received = dp.parse(ts, tzinfos=tzd)
                time_logged = datetime.now(tzlocal())
                
                if ((time_received - window_start)/timedelta(seconds=1) > 100):
                    window_start = time_received
                    avg = 0.0
                    for key in counter:
                        avg += counter[key]/len(counter.keys())
                    for key in counter:
                        if(avg - counter[key]< 10):
                             print("File " + key + " got starved")  
                    for key in counter:
                        counter[key] = 0
                delta = time_logged - time_received
                if(delta/timedelta(seconds=1) > max_lag):
                    max_lag = delta.seconds
                if msg['input'] in last_timestamp:
                    if(last_timestamp[msg['input']] > time_received):
                        errors.append(msg)
                        last_timestamp[msg['input']] = time_received
                else:
                    last_timestamp[msg['input']] = time_received
                counter[msg['input']] = counter[msg['input']] + 1    
        linebuffer = ''
    print("Maximum observed lag time, seconds: " + str(max_lag))
    print("Out of order messages")
    for msg in errors:
        print(msg)
            