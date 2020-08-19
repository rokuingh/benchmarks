#!/usr/bin/python
# coding: utf-8

import os, re
from subprocess import check_call, check_output
from shutil import copy2
from time import localtime, strftime
from math import floor
from threading import Thread

# from: https://stackoverflow.com/questions/2829329/catch-a-threads-exception-in-the-caller-thread-in-python
class PropagatingThread(Thread):
    def run(self):
        self.exc = None
        try:
            if hasattr(self, '_Thread__target'):
                # Thread uses name mangling prior to Python 3.
                self.ret = self._Thread__target(*self._Thread__args, **self._Thread__kwargs)
            else:
                self.ret = self._target(*self._args, **self._kwargs)
        except BaseException as e:
            self.exc = e

    def join(self):
        super(PropagatingThread, self).join()
        if self.exc:
            raise self.exc
        return self.ret

def generate_id(ROOTDIR):
    import os, re

    RUNDIR = os.path.join(ROOTDIR, "runs")

    if not os.path.isdir(RUNDIR):
        try:
            os.makedirs(RUNDIR)
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    dirnums = []
    for path in os.listdir(RUNDIR):
        directory = os.path.join(RUNDIR, path)
        if os.path.isdir(directory):
            head, tail = os.path.split(directory)
            dirnums.append(int(tail))

    EXECDIR = os.path.join(RUNDIR, str(max(dirnums or [0]) + 1))

    if not os.path.isdir(EXECDIR):
        try:
            os.makedirs(EXECDIR)
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    return EXECDIR

# source: http://code.activestate.com/recipes/81330/
def multiple_replace(dict, text):
  # Create a regular expression  from the dictionary keys
  regex = re.compile("(%s)" % "|".join(map(re.escape, dict.keys())))

  # For each match, look-up corresponding value in dictionary
  return regex.sub(lambda mo: dict[mo.string[mo.start():mo.end()]], text) 

def setup(config, n, runs, testcase, platform):
    try:
        RUNDIR = config.RUNDIR
        SRCDIR = config.SRCDIR
        procs = config.procs
        if (n > procs[-1]): raise ValueError("--n cannot be greater than "+str(procs[-1])+". Please adjust the 'procs' values in the configuration file for your platform.")

        # import testcase specific platform parameters
        args = config.testcase_args[testcase]
        GRID1 = args["GRID1"]
        GRID2 = args["GRID2"]

        EXECDIR = generate_id(RUNDIR)

        # run all cases in procs that are not larger than input
        for pnum in procs:
            if pnum <= n:
                # calculate the number of nodes required for this batch submission
                nnum = floor((pnum+36-1)/36)
    
                # build the qsub file
                replacements = {"%n%" : str(pnum),
                                "%nn%" : str(nnum)}

                with open(os.path.join(SRCDIR, "runProfile.pbs")) as text:
                    new_text = multiple_replace(replacements, text.read())
                with open(os.path.join(EXECDIR, "runProfile"+str(pnum)+".pbs"), "w") as result:
                    result.write(new_text)

                for ind in range(1,runs+1):
                    # create a separate directory to run each executable nrun times to  give
                    PROCRUNDIR = os.path.join(EXECDIR,str(pnum)+"-"+str(ind))
                    if not os.path.isdir(PROCRUNDIR):
                        try:
                            os.makedirs(PROCRUNDIR)
                        except OSError as exc: # Guard against race condition
                            if exc.errno != errno.EEXIST:
                                raise
                    # copy config files and executable to execution directory
                    copy2(os.path.join(SRCDIR,testcase,"MOAB_eval_"+testcase), os.path.join(PROCRUNDIR,"MOAB_eval"))

    except:
        raise RuntimeError ("Error setting up execution directory.")

    return EXECDIR

def call_script(*args, **kwargs):
    check_call(args)

def test(config, clickargs):

    n = clickargs["n"]
    testcase = clickargs["testcase"]
    branch = clickargs["branch"]
    esmfmkfile = clickargs["esmfmkfile"]
    platform = clickargs["platform"]
    runs = clickargs["runs"]
    gnu10 = clickargs["gnu10"]

    try:
        print ("\nSubmit the test runs (<15 minutes):", strftime("%a, %d %b %Y %H:%M:%S", localtime()))

        SRCDIR = config.SRCDIR
        procs = config.procs
        # import testcase specific platform parameters
        args = config.testcase_args[testcase]
        GRID1 = args["GRID1"]
        GRID2 = args["GRID2"]

        # set up the execution directory
        EXECDIR = setup(config, n, runs, testcase, platform)
        
        # call from EXECDIR to avoid polluting the source directory with output files 
        os.chdir(EXECDIR)

        job_threads = []
        for pnum in procs:
            if pnum <= n:
                print 
                run_command = [os.path.join(EXECDIR, "runProfile"+str(pnum)+".pbs"), str(pnum), str(runs), EXECDIR, platform, GRID1, GRID2]
                if platform == "Cheyenne":
                    run_command = ["qsub", "-W block=true"] + run_command
                else:
                    run_command = ["bash"] + run_command

                job_threads.append(PropagatingThread(target=call_script, args=run_command))
        
        for job in job_threads:
            job.start()

        for job in job_threads:
            job.join()

        print ("All jobs completed successfully.", strftime("%a, %d %b %Y %H:%M:%S", localtime()))
    
    except:
        raise RuntimeError("Error submitting the tests.")

    return EXECDIR
