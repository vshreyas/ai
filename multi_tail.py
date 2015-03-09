#!/usr/bin/env python
import time
import json 
from os import listdir
from os.path import isfile, join
import os
import sys
from threading import Thread
from queue import Queue
from queue import Empty
import dateutil.parser as dp
import cgi
from _datetime import datetime
from datetime import datetime
import dateutil
from dateutil.tz import *
'''
Implement multi-file tail
'''

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

def _fstat(filename):
    st_results = os.stat(filename)
    return (st_results[6], st_results[8])

def parse_date(timestr):
    return dp.parse(timestr, tzinfos=tzd)

def getKey(json_msg):
    if 'at' in json_msg:
        return parse_date(json_msg['at'])
    return parse_date(json_msg['timestamp'])

class LogFileReader(Thread):
    def __init__(self, queue, fname, stats, seek_begin, poll_time=10):
        Thread.__init__(self)
        self.que = queue
        self.filename = fname
        self.stats = stats
        self.seek_begin = seek_begin
        self.poll_wait = poll_time
    
    def run(self):
        if(self.seek_begin):
            with open(self.filename, 'r') as fh:
                while True:
                    line = fh.readline()
                    if not line:
                        break
                    self.process(line)
        else:
            with open(self.filename, 'rb') as fh:
                offs = -100
                while True:
                    fh.seek(offs, 2)
                    lines = fh.readlines()
                    if len(lines)>1:
                        last = lines[-1]
                        break
                    offs *= 2      # Read last line.
                self.process(last.decode("utf-8"))
            
        while 1:
        # print last_stats
            changed = False
            if self.check_file_for_changes():
                changed = True
            if not changed:
                time.sleep(self.poll_wait)

    def check_file_for_changes(self):
        changed = False
        #Find the size of the file and move to  the end
        tup = _fstat(self.filename)
        # print tup
        if self.stats != tup:
            changed = True
            self.get_latest_message(self.stats[0])
            self.stats = tup
        return changed
    
    def get_latest_message(self, pos):
        with open(self.filename, 'r') as fh:
            fh.seek(pos)
            while True:
                line = fh.readline()
                if not line:
                    break
                self.process(line)
                    
    def process(self, line):
        try:
            msg = json.loads(line)
            if 'note' in msg and 'at' in msg:
                msg['input'] = self.filename
                self.que.put(msg)
            else:
                self.que.put({'# INVALID LINE':cgi.escape(line), 'timestamp': datetime.now().strftime("%b %d %Y %H:%M:%S")+ datetime.now(tzlocal()).tzname()})       
        except ValueError:
            self.que.put({'# INVALID LINE':cgi.escape(line), 'timestamp': datetime.now().strftime("%b %d %Y %H:%M:%S") + datetime.now(tzlocal()).tzname()})
            print(datetime.now().strftime("%b %d %Y %H:%M:%S %Z"))

        
class OutputAppender(Thread):
    def __init__(self, out = sys.stdout, maxsize=2000, interval=1.0):
        Thread.__init__(self)
        self.out = sys.stdout
        self.max_size = maxsize
        self.queues = []
        self.output_queue = []
        self.interval = interval

    def run(self):
        while True:
            while len(self.output_queue) < self.max_size:
                for queue in self.queues:
                    try:
                        msg = queue.get(True, self.interval/(2 *len(self.queues)))
                        self.output_queue.append(msg) 
                        queue.task_done()
                    except Empty:
                        pass
                self.output_queue.sort(key=getKey)
                for m in self.output_queue:
                    self.out.write(json.dumps(m, sort_keys=True, indent=4,separators=(',',':')))
                    self.out.write('\n')
                del self.output_queue
                self.output_queue = []

def multi_tail(root_dir, max_size=20000, interval=1.0, seek_begin=False):
    
    filenames = [ ]
    for f in listdir(root_dir):
         if isfile(join(root_dir,f)):
             if f.split(".")[-1] == 'log':
                 filenames.append(f)
                 
    last_stats = dict((fn, _fstat(fn)) for fn in filenames)
    last_fn = None
    last_print = 0
    
    writer = OutputAppender(max_size/(len(filenames) + 1), interval)
    for fn in filenames:
        queue = Queue(max_size/(len(filenames) + 1))
        writer.queues.append(queue)
        reader = LogFileReader(queue, fn, last_stats[fn],seek_begin)
        reader.start()
    writer.start()

if '__main__' == __name__:
    from optparse import OptionParser
    op = OptionParser()
    op.add_option('-D', '--directory', help='/path/to/dir',
        type='str', default='.')
    op.add_option('-T', '--interval', help='check interval, in milliseconds', 
        type='int', default=1000)
    op.add_option('-B', '--seek_begin', help='start at beginning of file',
        action='store_true', dest='seek_begin')
    opts, args = op.parse_args()
    try:
        multi_tail(root_dir=opts.directory, max_size=2000, interval=opts.interval/1000, seek_begin=opts.seek_begin)
    except KeyboardInterrupt:
        pass

