#!/usr/bin/bash
python3 multi_tail.py | python3 check_output.py &
for i in `seq 1 200`;do echo { \"content\": { \"key$i\": \"value1\"}, \"at\": \"`date`\", \"note\": \"hello robert\" }>>test1.log;sleep 1;done &
for i in `seq 1 200`;do echo { \"content\": { \"key$i\": \"value1\"}, \"at\": \"`date`\", \"note\": \"hello robert\" }>>test1.log;sleep 2;done &
