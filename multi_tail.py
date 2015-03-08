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
'''
Implement multi-file tail
'''

interval = 1.0

def _fstat(filename):
    st_results = os.stat(filename)
    return (st_results[6], st_results[8])

class LogFileReader(Thread):
    def __init__(self, queue, fname, stats, seek_begin=False, poll_time=10):
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
                    process(line)
            
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
                sentence = json.dumps(msg, sort_keys=True, indent=4,separators=(',',':'))
                self.que.put(sentence)
            else:
                self.que.put('INVALID LINE:' + line)       
        except ValueError:
            self.que.put('INVALID LINE:' + line)

        
class OutputAppender(Thread):
    def __init__(self, out = sys.stdout, maxsize=2000):
        Thread.__init__(self)
        self.out = sys.stdout
        self.max_size = maxsize
        self.queues = []
        self.output_queue = []

    def run(self):
        while True:
            while len(self.output_queue) < self.max_size:
                for queue in self.queues:
                    try:
                        sentence = queue.get_nowait()
                        self.output_queue.append(sentence) 
                        queue.task_done()
                    except Empty:
                        pass
                for queue in self.queues:
                    try:
                        sentence = queue.get(True, interval/(2 *len(self.queues)))
                        self.output_queue.append(sentence) 
                        queue.task_done()
                    except Empty:
                        pass
                messages = sorted(self.output_queue)
                for m in messages:
                    print(m)
                del self.output_queue
                self.output_queue = []

def multi_tail(root_dir, max_size=20000, interval=1.0):
    
    filenames = [ ]
    for f in listdir(root_dir):
         if isfile(join(root_dir,f)):
             if f.split(".")[-1] == 'log':
                 filenames.append(f)
                 
    last_stats = dict((fn, _fstat(fn)) for fn in filenames)
    last_fn = None
    last_print = 0
    
    writer = OutputAppender(max_size/(len(filenames) + 1))
    for fn in filenames:
        queue = Queue(max_size/(len(filenames) + 1))
        writer.queues.append(queue)
        reader = LogFileReader(queue, fn, last_stats[fn])
        reader.start()
    writer.start()

if '__main__' == __name__:
    from optparse import OptionParser
    op = OptionParser()
    op.add_option('-D', '--directory', help='/path/to/dir',
        type='str', default='.')
    op.add_option('-T', '--interval', help='check interval, in milliseconds', type='int',
        default=1000)
    opts, args = op.parse_args()
    try:
        multi_tail(root_dir=opts.directory, max_size=2000, interval=opts.interval/1000)
    except KeyboardInterrupt:
        pass

