# tgrep.py
# Author:       Colin Woodbury
# Contact:      colingw@gmail.com
# Start date:   02/17/2011 
# End date:     02/21/2011 
# Description:  A customized version of grep that
#               works specifically to locate and store
#               entries in Reddit's large .log files.
# updated:      03/13/2011

import sys
import re

class TgrepError(Exception):
    """Base class for errors in tgrep."""
    def __init__(self, message = ""):
        self.message = message

    def f7u12(self):
        "Rage at the user for doing something stupid."
        if self.message: #if a message was given, print it
            print("Specifics: {0}".format(self.message))

class ArgumentError(TgrepError):
    """Exception raised for errors concerning
    arguments passed on the command line.
    """
    def __init__(self, message = ""):
        super(ArgumentError, self).__init__(message)

    def f7u12(self):
        print("Improper arguments passed on the command line.")
        super().f7u12()
        print("Args given --> {0}".format(sys.argv[1:]))

class DataError(TgrepError):
    """Exception raised for errors concerning
    data in the file or issues with the data set
    requested by the user.
    """
    def __init__(self, message = ""):
        super(DataError, self).__init__(message)

    def f7u12(self):
        print("Error in the data / data set requested on command line.")
        super().f7u12()

def get_args():
    """Safely gets the arguments passed on the
    command line and handles all associated errors.
    Valid arguments are returned as a tuple 
    in the form: (filename, time)
    """
    try:
        # Test for the presence/overpresence of command-line args.
        argQuant = len(sys.argv)
        if argQuant == 1 or argQuant > 3:    
            raise ArgumentError("Argument quantity incorrect.")
        else:
            # Check formatting. Were we given a time and a file?
            file = defaultFile #global
            time = 0
            fileSolved = timeSolved = False
            for arg in sys.argv[1:]:
                if is_file(arg):
                    if fileSolved:
                        raise ArgumentError("Two files given.")
                    else:
                        file = arg
                        fileSolved = True
                elif get_time(arg): #arg was formatted like a time
                    if not is_valid_time(arg):
                        raise ArgumentError("Non-existant time given.")
                    else:  # A proper time was given.
                        if timeSolved:
                            raise ArgumentError("Two times given.")
                        else:
                            time = arg
                            timeSolved = True
            # Final check for bogus arguments
            if not timeSolved:
                if not fileSolved:
                    raise ArgumentError("No file or time given.")
                else:
                    raise ArgumentError("Bad/No time given.")
    except ArgumentError as error:
        # Rage at the user, then quit.
        error.f7u12() 
        sys.exit(2)
    return (file, time)
        
def is_file(line):
    """Confirms if the file argument passed
    on the command line is, in fact, a file.
    """
    match = re.match(r"^(\w+)[.](\w+)$", line)
    if match:  # The string was formatted like a file.
        result = True
    else:
        result = False
    return result
    
def get_time(line):
    """Given a string, scans it using a regex,
    and parses a time of the format
    xx:xx or xx:xx:xx .
    """
    regex = r"\b([01]?\d|2[0-3]):([0-5]\d)(:[0-5]\d)?\b"
    match = re.search(regex, line)
    if match: 
        time = match.group()
    else:
        time = None
    return time

def is_valid_time(time):
    """Checks whether a string formatted
    like a time is in fact a real time.
    """
    validTime = True  # Assume success.
    if "-" in time:  # A time range was given.
        index = time.index("-")
        if not is_valid_time(time[0:index]) or not \
                is_valid_time(time[index+1:]):
            validTime = False
    elif time == "":
        validTime = False
    else:
        time = zero_check(time)
        tokens = time.split(":")
        # Check the hours.
        if tokens[0] > "23":
            validTime = False
        else:
            #Check the minutes and seconds.
            for each in tokens[1:]:
                if len(each) != 2:
                    validTime = False
                elif each > "59":
                    validTime = False
    return validTime
        
def confirm_time(time):
    """Given the time argument taken from
    the command line, parses it to determine 
    what range of times the user wants to search.
    """
    if "-" not in time:  # We were not given a range.
        start = zero_check(time)
        end = start
    else:  # We were given a range. Split.
        pos = time.index("-")
        start = zero_check(time[0:pos])
        end = zero_check(time[pos+1:])
    # Add seconds, if necessary.
    if len(start) == 5: #format: xx:xx
        start += ":00"
    if len(end) == 5: 
        end += ":59"
    return (start, end)

def zero_check(time):
    """To make later processing easier, adds
    a 0 to certain times. e.g. 6:32 -> 06:32
    """
    size = len(time)
    if size == 4 or size == 7:
        time = "0" + time
    return time

def begin_file_oper(filename, start, end):
    """Manages all operations on the file."""
    try:
        with open(filename) as file:
            firstLine = file.readline()
            if firstLine == "":
                raise ArgumentError("Empty file given.")
            elif not get_time(firstLine):
                raise ArgumentError("File with garbage data given.")
            else:
                lastLine = get_last_line(file)
                # Parse out the times, they'll be used a few times.
                firstTime = get_time(firstLine)
                lastTime = get_time(lastLine)
                # Check if the given times could exist in the file.
                confirm_data_set(file, start, end, firstTime, lastTime)
                # Find the tell() position of the first instance of 'start'.
                pos = get_lower_bound(file, start, firstTime, lastTime)
                # Read and print all matches.
                if include_roll_over(start, end, firstTime, lastTime):
                    main_output(file, start, end, pos, lastLine)
                else:
                    main_output(file, start, end, pos)
    except (ArgumentError, DataError) as error:
        error.f7u12() #fffffffuuuuuuuuuuuu
        sys.exit(2)

def get_last_line(file):
    """Retrieves the last line of the file."""
    # Set the cursor at the end and get the line.
    file.seek(0, 2)      
    pos = file.tell() 
    lastLine = get_full_line(file, pos-1)  # Explodes without offset.
    return lastLine

def get_full_line(file, pos):
    """Given a file and a cursor position,
    uses lseek to find the start of the line
    and returns it.
    """
    lseek(file, pos)
    fullLine = file.readline()
    return fullLine

def lseek(file, pos):
    """Sets the cursor at the start of the line containing 'pos'"""
    global lseekCalls
    lseekCalls += 1
    found = False
    jumpDist = 15  # Distance (bytes) to jump back by each time.
    # Check for initial newline. 
    if newline_check(file, pos, jumpDist) != -1:
        # Jump back a bit to avoid problems.
        pos -= jumpDist
    while not found:
        # Jump back and check for file bounds.
        pos -= jumpDist
        if pos < 0:  # Prevent running off the start of the file.
            file.seek(0)
            found = True
        else:  # Seek n' read.
            # Add a buffer in case original pos was the 
            # start of the line.
            index = newline_check(file, pos, jumpDist + 1)
            if index != -1:  # Newline present.
                pos += index + 1  # Byte right after the newline.
                file.seek(pos)
                found = True 

def newline_check(file, pos, buff):
    """Reads 'buff' bytes from 'pos' onward in 'file'
    and checks if the line contains a newline character.
    Returns the distance from 'pos' that the newline was found.
    """
    file.seek(pos)
    line = read(file, buff)
    file.seek(pos)  # Bring the cursor back.
    index = line.rfind("\n")
    return index

def read(file, bytes):
    """A filter for file.read() to record its use."""
    global readCalls
    readCalls += 1
    line = file.read(bytes)
    return line

def confirm_data_set(file, start, end, firstTime, lastTime):
    """Determines if the file given and 
    the times indicated will make a valid
    data set.
    """
    # There were more conditions here earlier, but later
    # methods/logic revelations rendered them useless.
    if start == firstTime and end == lastTime:
        line = "Time range given encompasses entire data set. Revise."
        raise DataError(line)
            
def get_lower_bound(file, start, firstTime, lastTime):
    """Uses a binary search on the file to find
    the tell() position of the first line to be read.
    """
    # Target time is at the start of the file?
    if start == firstTime:
        pos = 0
    else:
        # Find any instance of 'start' in the file.
        pos = circular_bin_search(file, start, firstTime, lastTime)
        # Find the earliest instance of the time at 'pos'.
        pos = first_instance(file, start, pos)
    return pos

def circular_bin_search(file, time, firstTime, lastTime):
    """Searches for any time that matches 'time'
    using a circular bin search.
    If the exact value isn't found, the method provides
    the closest value to the one being looked for.
    """
    # Set initial times and file positions.
    file.seek(0, 2)
    upper = file.tell()
    upperTime = lastTime
    lower = 0
    lowerTime = firstTime
    mid = 0
    lastMid = 0  # Holds the last mid value calculated.
    recordPos = 0
    recordDiff = to_seconds("99:99:99")
    pos = -1  # The return value. Assume failure.
    found = False
    timeSecs = to_seconds(time)  # The given 'time' in seconds.
    while not found:
        lastMid = mid
        lseek(file, (upper + lower) // 2)
        mid = file.tell()
        midLine = file.readline()
        midTime = get_time(midLine)
        currDiff = abs(timeSecs - to_seconds(midTime))
        # Deal with the diff records.
        if currDiff < recordDiff:
            recordDiff = currDiff
            recordPos = mid
        # Standard binary search logic.
        if time == midTime:
            pos = mid
            found = True #gtfo
        elif time > lowerTime and time < midTime:
            upper = mid
            upperTime = midTime
        elif time > midTime and time < upperTime:
            lower = mid
            lowerTime = midTime
        else: 
            # Standard binary search logic fails. 
            # Find what side the "day break" is on.
            # 'time' is always on the side of daybreak.
            if lowerTime > midTime:  # Day break on the left.
                upper = mid
                upperTime = midTime
            else:  # Day break on the right.
                lower = mid
                lowerTime = midTime
        if lastMid == mid:
            # The mid didn't change. If our time doesn't exist in the set,
            # then the current 'pos' is a good starting place to look
            # for the closest value.
            pos = recordPos
            found = True
    return pos

def to_seconds(time):
    """Converts a time in the format xx:xx:xx to its 
    value in seconds.
    """
    return (int(time[0:2]) * 3600) + (int(time[3:5]) * 60) + int(time[6:])

def first_instance(file, start, pos):
    """At 'pos' is a line that contains a time
    equal to start. Is this line the earliest instance
    of that time?
    """
    file.seek(pos)
    while 1:
        # Get the line before the current line. 
        lseek(file, pos - 5)  # Arbitrary jump back distance. Must be > 1.
        currPos = file.tell()
        currLine = file.readline()
        currTime = get_time(currLine)
        if currTime != start:  # First instance found.
            break
        pos = currPos
    return pos

def include_roll_over(start, end, firstTime, lastTime):
    """Checks to see if the there was a value that
    slipped over the 24-hour mark, and if it
    deserves to be included in the output.
    """
    result = False  # Assume no.
    lastSecs = to_seconds(lastTime)
    if lastSecs > to_seconds(firstTime):
        # There was a roll-over. Does the user need it?
        startSecs = to_seconds(start)
        if lastSecs > startSecs:
            endSecs = to_seconds(end)
            if lastSecs <= endSecs:
                result = True
            elif endSecs < startSecs:  # Deal with the day break.
                if lastSecs < (endSecs + to_seconds("24:00:00")):
                    result = True
    return result

def main_output(file, start, end, pos, lastLine=""):
    """Outputs all lines that have times between
    'start' and 'end'.
    """
    entered = False  # Entered the home stretch?
    file.seek(pos)
    line = file.readline()
    while line:
        # Position 7 to 15 is where the time appears in the log line.
        if not entered and line[7:15] == end:
            entered = True
        elif entered and line[7:15] != end:
            # We've moved past the last value to be read.
            break  # Done!
        print(line, end="")
        line = file.readline()
    if lastLine:  # Possible roll-over.
        print(lastLine, end="")
        
#Some globals.
readCalls = 0  #total number of calls to read()
lseekCalls = 0 #total number of calls to lseek()
defaultFile = "/logs/haproxy.log"

if __name__ == "__main__":
    args = get_args()
    times = confirm_time(args[1])
    begin_file_oper(args[0], times[0], times[1])
    # Test output.
    #print("Calls to lseek():", lseekCalls)
    #print("Calls to read():", readCalls)

