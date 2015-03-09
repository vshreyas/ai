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

Install Python3
pip3 install dateutils

Running the program
----------------------------------------------

python3 <progname> -h gives help instructions
python3 <progname> [-D  /path/to/directory [–T xxx [-B]]]

Testing the program and verifying output
-------------------------------------------

python3 <progname> [options] | python3 check_ouput.py

Test cases have been provided as test1.sh, test2.sh.....

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
- Name of file
and runs the following code:
2.1.  Iterate and enqueue the last line(default) or all the lines(-B option) of the file that are available at the beginning.
2.2  Scan the file for changes 
2.3 If a text message has been appended, read it from the file, parse it to JSON with error handling, enqueue the augmented message in the queue for that file. If queue is full, 
2.4  Sleep for a period of T/2*(n+1) to prevent stalling of CPU and OS
2.5 Go back to step 2.2

3. Main process also launches output thread in parallel. This thread runs the following procedure:

3.1 Iterate over all input queues issuing a blocking call to pop the 1st element, with a timeout value of  T/2*(n+1). Accumulate the results in a sorted list holding the output, using the sort merge algorithm
3.2  Print the sorted output and flush output queue.

Modules
------------------------------------------------

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
Testing Platform
-----------------------------------------------

Processor: Intel Core i3-2370 CPU @2.4GHz

Installed RAM: 6GB

Working memory at time of execution (limit set in environment): 100MB

Operating System: Ubuntu 12.0.4(Linux kernel 3.2.0-29-generic)

Test cases
-----------------------------------------------

Options are assumed to be default unless otherwise mentioned
1. Single empty log file
2. Single log file test.log containing a JSON message with input,at
3. Single log file test.log containing an unformatted string
4. Single log file test.log containing a JSON message without input,at
5. Single log file test.log containing 5 JSON messages with input,at and different timestamps, -B option
6. Single log file with generator process(Bash script) that appends a JSON message every 1 second
7. Two log files test1.log,  test2.log containing 5 JSON messages with input,at and different timestamps, -B option
8.  Two log files test1.log,  test2.log with generator process(Bash script) that appends a JSON message every 1 second
9.  Two log files test1.log,  test2.log with generator processes(Bash script) that append a JSON message every 1 second and 2 seconds respectively
10. Two log files test1.log,  test2.log with generator process(Bash script) that appends a JSON message every 1 second. Log file 2 is rotated after 10 seconds(renamed original to test2.log.2015-01-01 and new file test2.log created)
11. Two log files test1.log,  test2.log with generator process(Bash script) that appends a JSON message every 1 second. Option -T 500(max wait time 500 milliseconds)
12. Two log files test1.log,  test2.log with generator process(Bash script) that appends a JSON message every 1 second. Option -T 1500(max wait time 1500 milliseconds)
13. Performance test with 10 log files and processes to append to them


Test criteria
-----------------------------------

1. Check output sorted by timestamp for intervals of T millisecond(using check_sorted.py). Number of out of order messages reported
2. Check ordering within output for messages from a single file with the same timestamp
3. Measure fairness using number of messages logged from each file in a time interval of 100 seconds
4. Measure worst case turnaround time for a message by checking the difference between timestamp and time it was emitted for each message


