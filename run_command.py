#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys, os, re
import getopt

scriptName = os.path.basename(os.path.abspath(sys.argv[0])).replace('.pyc', '.py')

# If this script is called via a symbolic link:
# this returns the symbolic link's directory:
# scriptDir = os.path.dirname(os.path.abspath(sys.argv[0]))
# this returns the symbolic link's target's directory:
scriptDir = os.path.dirname(os.path.realpath(sys.argv[0]))

sys.path.append(scriptDir)

from logging_wrappers import reportError

if sys.version_info[0] == 3:  # for python3
    xrange = range
else:
    xrange = xrange

#-----------------------------------------------------

# Cannot execute nohup'ed commands.

# commands.getstatusoutput() has been made obsolete by the subprocess module.
# Use run_command() further down.
# def run_local_command(command):
#     status, output = subprocess.getstatusoutput(command)
#     return status, output


import subprocess
from subprocess import Popen, call, PIPE

# For before Python 3.5

# Output can only go to files.
'''
def run_command(cmd, stdin=None, stdout=None, stderr=None):
    returncode = subprocess.call(cmd, stdin=stdin, stdout=stdout, stderr=stderr, shell=True)
    return returncode, ""
Call:  run_command("ls file1", stdout=fd_stdout, stderr=fd_stderr)
'''

# Send captured output to screen and pipe.

# def execute_generator(cmd):
#     import shlex
#     popen = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, universal_newlines=True)
#     for stdout_line in iter(popen.stdout.readline, ""):
#         yield stdout_line 
#     popen.stdout.close()
#     return_code = popen.wait()
#     if return_code:
#         raise subprocess.CalledProcessError(return_code, cmd)

def run_command(cmd, realtime_output=False, silent=False):
    if realtime_output == True:
        output = ''
        for output_line in read_command_output(cmd):
            output_line_string = output_line.decode('UTF-8')
            output_line_string_stripped = output_line_string.rstrip()
            output += output_line_string
            # output += output_line_string
            # print(output_line_string_stripped)
            sys.stdout.write(output_line_string_stripped + '\n\r')
            # sys.stdout.write(str(output_line))
        error = ''
        return 0, output, error

    # import shlex
    # process = subprocess.Popen(shlex.split(cmd), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    # process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

    if re.search('^I:', cmd):
        import string
        rest_of_cmd = string.split(cmd, ':', 1)[1]  # just 1 split
        process = subprocess.Popen(rest_of_cmd, shell=True)
    else:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    # print(56, output)
    # print(57, error)
    output = output.decode() # convert from bytes to strings
    error  = error.decode() # convert from bytes to strings

    # for line in execute_generator(cmd):
    #     print(line)

    # # Always show any current cmd output before errors.
    # output = bytes(output).decode('UTF-8')
    # if str(output) != 'None' and str(output) != '':
    #    print(str(output))

    # This decode gets rid of 'u' when outputting strings:
    # if error != None:
    #     error  = bytes(error).decode('UTF-8')
    #
    # but it also causes the following error when executing direct commands, e.g., ls:
    # ERROR: Command cannot be executed: ls.  Exception e = 'ascii' codec can't decode byte 0xc2 in position 2733: ordinal not in range(128)

    if error != None and error != '' and error != b'':
        return 1, output, reportError('subprocess() error running command: ' + str(cmd) + " .  Error: " + str(error), mode='return_msg_only')
    else:
        return 0, output, error

def read_command_output(command):
    process = subprocess.Popen(command, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT, shell=True)
    return iter(process.stdout.readline, b"")




# Interactive command execution:

# Does not work for the ci command   :-( .

def run_interactive_command(cmd):
    fw = open("tmpout", "wb")
    fr = open("tmpout", "r")
    p = Popen(cmd, stdin = PIPE, stdout = fw, stderr = fw, bufsize = 1)
    p.stdin.write("1\n")
    out = fr.read()
    p.stdin.write("5\n")
    out = fr.read()
    fw.close()
    fr.close()
    return 0, ''


'''
# This interactive version does not work.

import fcntl

def setNonBlocking(fd):
    """
    Set the file description of the given file descriptor to non-blocking.
    """
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    flags = flags | os.O_NONBLOCK
    fcntl.fcntl(fd, fcntl.F_SETFL, flags)

def run_interactive_command(cmd):
   p = Popen(cmd, stdin = PIPE, stdout = PIPE, stderr = PIPE, bufsize = 1)
   setNonBlocking(p.stdout)
   setNonBlocking(p.stderr)

   p.stdin.write("1\n")
   while True:
       try:
           out1 = p.stdout.read()
       except IOError:
           continue
       else:
           break
   out1 = p.stdout.read()
   p.stdin.write("5\n")
   while True:
       try:
           out2 = p.stdout.read()
       except IOError:
           continue
       else:
           break
'''

def run_interactive_command(cmd):
    cmd = cmd.split()
    code = os.spawnvpe(os.P_WAIT, cmd[0], cmd, os.environ)
    if code == 127:
        sys.stderr.write('{0}: command not found\n'.format(cmd[0]))
    return code


# For Python 3.5
'''
def run_command(cmd, out=None, err=None):
    # log.debug("run command entered: " + str(cmd))
    # proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    # error handling
    results = ''
    if err != '':
       results += 'Errors:\n' + err
    if out != '':
       # results += 'Output:\n' + out
       results += out
    # log.debug("proc.returncode = %s" % str(proc.returncode))
    if proc.returncode == 0:
        # log.debug("run command succeeds: " + str(cmd))
        return proc.returncode, results
    elif proc.returncode == 28:
        log.warning("run command: time out!")
        log.warn(err)
        # Return back a zero; treat a warning like success.
        return 0, results
    else:
        # Let the caller decide what to do about errors.
        # log.error("run command error: " + str(err) )
        return proc.returncode, results

    # log.debug("run command: Returning." + str(cmd))
    return proc.returncode, results
'''

#===================================================

# Example main code

if __name__ == '__main__':
    # global debug_flag

    # Set a global debug flag based on an environment variable, or use logging.DEBUG below, or both.
    debug_flag = debug_option(__file__ + "," + srcLineNum())

    logging_setup(logMsgPrefix='run_command', logfilename=scriptName + '.log', loglevel=logging.ERROR)

    if len(sys.argv) < 2:
        usage()

    try:
        opts, args = getopt.getopt(sys.argv[1:], "", ["list=", "of=", "debug", "unit_test="])
    except:
        print("ERROR: Unrecognized runstring option.")
        usage()

    list_option = ''
    of_option = 'full'

    for opt, arg in opts:
        if opt == "--list":
            list_option = arg
        elif opt == "--of":
            of_option = arg
        elif opt == "--debug":
            setLoggingLevel(logging.DEBUG)
            debug_flag = True
        # elif opt == "--unit_test":
        else:
            print("ERROR: Runstring options.")
            usage()

    # If you have non-hyphenated options in the runstring such as filenames, you can get them from the runstring like this:
    # file1 = args[0]
    # file2 = args[1]

    # Run examples of how to call above functions.

    rc, results = run_local_command("ls file_does_not_exist")
    if rc != 0:
        print("ERROR: " + os.path.basename(__file__) + ", Line: " + srcLineNum() + ", rc: " + str(rc) + ", results: " + results)
        test_func()

    sys.exit(0)




