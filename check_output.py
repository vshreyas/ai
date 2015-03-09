import fileinput
import time
from datetime import datetime
import dateutil
from dateutil.tz import *
from _datetime import timedelta

if '__main__' == __name__:
    filenames = [ ]
    for f in listdir(root_dir):
         if isfile(join(root_dir,f)):
             if f.split(".")[-1] == 'log':
                 filenames.append(f)
    last_timestamp = dict()
    counter = {f:0 for f in filenames}
    errors = []
    max_lag = 0
    window_start = datetime.fromtimestamp(0)
    for line in fileinput.input():
        msg = json.loads(line)
        if 'note' in msg and 'at' in msg:
            ts = msg['at']
            time_received = dateutil.parser.parse(ts, tzinfos=tzd)
            time_logged = datetime.now()
            
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
    
    print("Maximum observed lag time, seconds: " + max_lag)
    print("Out of order messages")
    for msg in errors:
        print(msg)
            