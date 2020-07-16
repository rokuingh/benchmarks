#!/usr/bin/python
# coding: utf-8
#

import sys, os, re
from subprocess import check_call
from time import localtime, strftime

# source: http://code.activestate.com/recipes/81330/
def multiple_replace(dict, text):
  # Create a regular expression  from the dictionary keys
  regex = re.compile("(%s)" % "|".join(map(re.escape, dict.keys())))

  # For each match, look-up corresponding value in dictionary
  return regex.sub(lambda mo: dict[mo.string[mo.start():mo.end()]], text) 

def build_esmf(RUNDIR, SRCDIR, testcase, platform, branch, esmfmkfile, gnu10):
    # # 1.2 initialize: build and install ESMF
    ESMFMKFILE=""
    if (esmfmkfile != ""):
        try:
            # verify validity of ESMFMKFILE before accepting
            accept = False
            with open(esmfmkfile) as esmfmkf:
                for line in esmfmkf:
                    if "ESMF environment variables pointing to 3rd party software" in line: accept = True
            if accept:
                print ("\nSkip ESMF build, esmf.mk provided.")
                ESMFMKFILE = esmfmkfile
            else:
                print ("\nSorry, there is something wrong with the provided esmf.mk, please check it and resubmit: ", esmfmkfile)
                raise EnvironmentError
        except EnvironmentError as err:
            raise
    else:
        try:
            print ("\nBuild and install ESMF (<30 minutes):", strftime("%a, %d %b %Y %H:%M:%S", localtime()))

            # call from RUNDIR to avoid polluting execution dir with output files 
            BUILDDIR = os.path.join(RUNDIR, testcase)
            if not os.path.isdir(BUILDDIR):
                try:
                    os.makedirs(BUILDDIR)
                except OSError as exc: # Guard against race condition
                    if exc.errno != errno.EEXIST:
                        raise
            os.chdir(BUILDDIR)

            # checkout ESMF
            esmfgitrepo = "https://github.com/esmf-org/esmf.git"
            ESMFDIR = os.path.join(BUILDDIR, "esmf")
            if not os.path.isdir(ESMFDIR):
                try:
                    check_call(["git", "clone", esmfgitrepo])
                except OSError as exc: # Guard against race condition
                    if exc.errno != errno.EEXIST:
                        raise
            
            os.chdir(ESMFDIR)
            check_call(["git", "checkout", branch])

            # build the pbs script
            replacements = {"%testcase%" : testcase,
                            "%esmfdir%" : ESMFDIR,
                            "%branch%" : branch,
                            "%platform%" : platform,
                            "%gnu10%" : str(gnu10)}

            # write the pbs script
            pbscript = os.path.join(BUILDDIR, "buildESMF-"+testcase+".pbs")
            with open(os.path.join(SRCDIR, "buildESMF.pbs")) as text:
                new_text = multiple_replace(replacements, text.read())
            with open(pbscript, "w") as result:
                result.write(new_text)

            # set up the pbs script for submission to qsub on cheyenne or bash otherwise
            if platform == "Cheyenne":
                run_command = ["qsub", "-W block=true"] + [pbscript]
            else:  
                run_command = ["bash"] + [pbscript]

            check_call(run_command)

            # buildESMF.pbs writes location of esmf.mk to $ESMFDIR/esmfmkfile.out
            with open (os.path.join(ESMFDIR, "esmfmkfile.out"), "r") as esmfmkfileobj:
                ESMFMKFILE = esmfmkfileobj.read().replace("\n","")
            print ("ESMF build and installation success.", strftime("%a, %d %b %Y %H:%M:%S", localtime()))
        except:
            raise RuntimeError("Error building ESMF installation.")

    return ESMFMKFILE


def build_test(ESMFMKFILE, RUNDIR, SRCDIR, testcase, platform):
    # # 1.2 initialize: build the test executable
    try:
        print ("Build test executable")
        test_command = ["bash", os.path.join(SRCDIR, "buildTest.bash"), ESMFMKFILE, RUNDIR, SRCDIR, testcase, platform]
        check_call(test_command)
    except:
        raise RuntimeError("Error building test executable.")

