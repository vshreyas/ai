#!/usr/bin/env python
import time
import json 
from os import listdir
from os.path import isfile, join
import os
import sys
from threading import Thread
from queue import Queue

'''
Implement multi-file tail
'''

# 
# fn = 'test.log'
# for sentence in watch(fn):
#     print(json.dumps(sentence, sort_keys=True, indent=4,separators=(',',':')));

interval = 1

def _fstat(filename):
    st_results = os.stat(filename)
    return (st_results[6], st_results[8])

class LogFileReader(Thread):
    def __init__(self, queue, fname, stats, seek_begin=False):
        Thread.__init__(self)
        self.que = queue
        self.filename = fname
        self.stats = stats
        self.seek_begin = seek_begin
    
    def run(self):
        while 1:
        # print last_stats
            changed = False
            if self.check_file_for_changes():
                changed = True
            if not changed:
                time.sleep(interval)

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
                try:
                    msg = json.loads(line)
                    if 'note' in msg and 'at' in msg:
                        msg['input'] = self.filename
                        self.que.put(msg)
                    else:
                        self.que.put(line)       
                except ValueError:
                    self.que.put(line)

class OutputAppender(Thread):
    def __init__(self, out = sys.stdout):
        Thread.__init__(self)
        self.out = sys.stdout
        self.queues = []
    
    def run(self):
        while True:
            for queue in self.queues:
                msg = queue.get()
                sentence = json.dumps(msg, sort_keys=True, indent=4,separators=(',',':'))
                queue.task_done()
                self.out.write(sentence);
            


def multi_tail(root_dir, max_size=20000, interval=1):
    S = lambda st_size_st_mtime: (max(0, st_size_st_mtime[0] - 124), st_size_st_mtime[1])
    filenames = [ f for f in listdir(root_dir) if isfile(join(root_dir,f)) ]
    last_stats = dict((fn, S(_fstat(fn))) for fn in filenames)
    last_fn = None
    last_print = 0  
    
    writer = OutputAppender()
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
    op.add_option('--interval', help='check interval, in seconds', type='int',
        default=1)
    opts, args = op.parse_args()
    try:
        multi_tail(root_dir=opts.directory, max_size=2000, interval=opts.interval)
    except KeyboardInterrupt:
        pass

