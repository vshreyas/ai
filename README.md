Programming Languages Used

---------------------------------------------
Python 3.2

Key Assumptions

---------------------------------------------

1. Timestamps are in the format specified in the example, and use one of 30 well known timezone abbreviations

2.  Last-modified date is updated correctly for each file

3.  UTF-8 encoding is used


Requirements

---------------------------------------------

Python installation
python-dateutils


Setup

----------------------------------------------
Install Python
pip3 install dateutils

Running the program

----------------------------------------------
<progname> -h gives help instructions
<progname> [-D  /path/to/directory [–T xxx [-B]]]








Design and architecture

----------------------------------------------
Multi-threading was used to promote concurrent reading of log files with fairness. Turnaround time  for each message may be slightly higher than the specified interval T. 

High level description:

Files are polled periodically to detect changes by a set of reader threads, which write to their individual buffers(FIFO queues). A writer thread assimilates the contents of these buffers in a round robin fashion, sorts them by the timestamp value and writes to output. Locking is used to control access to shared queues.

Pseudo code:

1.Program scans directory for log files and adds them to the list of files to monitor
It collects initial stats for last modified date and file size for each of these files

2.Main process then launches threads to monitor each file for changes. 

Each LogReader thread keeps the following variables:

- Last position read to in each file
- Queue object shared with output thread
- 

and runs the following code:

2.1.  Iterate and enqueue the last line(default) or all the lines(-B option) of the file that are available at the beginning.
2.2  Scan the file for changes 
2.3 If a text message has been appended, read it from the file, parse it to JSON with error handling, enqueue the augmented message in the queue for that file. If queue is full, 
2.4  Sleep for a period of T/2*(n+1) to prevent stalling of CPU and OS
2.5 Go back to step 2.2

3. Main process also launches output thread in parallel. This thread runs the following procedure:

3.1 Iterate over all input queues issuing a non-blocking call to 
3.2 








Testing Platform

-----------------------------------------------

Processor: Intel Core i3-2370 CPU @2.4GHz

Installed RAM: 6GB

Working memory at time of execution (limit set in environment): 1MB

Operating System: Ubuntu 12.0.4(Linux kernel 3.2.0-29-generic)





Design

------------------------------------------------
The basic blocks of the design consist of: (highlight and explain the buffer design)
Common Functions :
_fstat(filename)
getKey(json_msg)

Classname :
 
LogFileReader 
The purpose of this class is to perform line flush from the logfiles as and when additional  lines are added to the logfiles or when the logfile is regenerated.
Functions
__init__(self, queue, fname, stats, seek_begin, poll_time=10)
run(self)
check_file_for_changes(self)
get_latest_message(self, pos)
process(self, line)
OutputAppender
This class is intended to read lines from the buffer(s) and write out.
Functions :
__init__(self, out = sys.stdout, maxsize=2000)
run(self)
multi_tail(root_dir, max_size=20000, interval=1.0, seek_begin=False)





ai
==
