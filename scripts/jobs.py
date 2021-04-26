import os
import json
import stat
import copy
import glob
from math import ceil
from functools import partial
from multiprocessing import Pool

JOB_PREFIX = """#!/bin/bash
set -o pipefail
pushd %(PWD)s
source env.sh
popd
"""


CONDOR_TEMPLATE = """executable = %(EXE)s
arguments = $(ProcId)
output                = %(TASKDIR)s%(TASK)s.$(ClusterId).$(ProcId).out
error                 = %(TASKDIR)s%(TASK)s.$(ClusterId).$(ProcId).err
log                   = %(TASKDIR)s%(TASK)s.$(ClusterId).log

# Send the job to Held state on failure.
on_exit_hold = (ExitBySignal == True) || (ExitCode != 0)

# Periodically retry the jobs every 10 minutes, up to a maximum of 5 retries.
periodic_release =  (NumJobStarts < 3) && ((CurrentTime - EnteredCurrentStatus) > 600)

%(EXTRA)s
queue %(NUMBER)s

"""

SLURM_PREFIX_TEMPLATE = """#! /bin/bash
#SBATCH --get-user-env
#SBATCH -e %(LOG)s_%%j.err

echo SLURM_JOB_ID: $SLURM_JOB_ID
echo HOSTNAME: $HOSTNAME
mkdir -p /scratch/$USER/${SLURM_JOB_ID}
export TMPDIR=/scratch/$USER/${SLURM_JOB_ID}
set -o pipefail
pushd %(PWD)s
source env.sh
popd
"""

SLURM_POSTFIX = """
rmdir /scratch/$USER/${SLURM_JOB_ID}
"""


ERROR_CAPTURE = """
function error_exit
{
    mv %s %s.$1
    exit $1
}

trap 'error_exit $?' ERR
"""


def run_command(dry_run, command):
    if not dry_run:
        print '>> ' + command
        return os.system(command)
    else:
        print '[DRY-RUN]: ' + command


class Jobs:
    description = 'Simple job submission system'

    def __init__(self):
        self.job_queue = []
        self.args = None
        self.job_mode = 'interactive'
        self.parallel = 1
        self.merge = 1
        self.task_name = 'combine_task'
        self.dry_run = False
        self.bopts = ''  # batch submission options
        self.tracking = False
        self.task_dir = ''

    def attach_job_args(self, group):
        group.add_argument('--job-mode', default=self.job_mode, choices=[
                           'interactive', 'script', 'lxbatch', 'condor', 'ts','slurm'], help='Task execution mode')
        group.add_argument('--task-name', default=self.task_name,
                           help='Task name, used for job script and log filenames for batch system tasks')
        group.add_argument('--dir', default=self.task_dir,
                           help='Area for creating the job scripts')
        group.add_argument('--parallel', type=int, default=self.parallel,
                           help='Number of jobs to run in parallel [only affects interactive job-mode]')
        group.add_argument('--merge', type=int, default=self.merge,
                           help='Number of jobs to run in a single script [only affects batch submission]')
        group.add_argument('--dry-run', action='store_true',
                           help='Print commands to the screen but do not run them')
        group.add_argument('--cwd', type=int, default=1,
                           help='Switch to the submission directory within the job')
        group.add_argument('--sub-opts', default=self.bopts,
                           help='Options for batch submission')
        group.add_argument('--memory', type=int,
                           help='Request memory for job [MB]')
        group.add_argument('--tracking', nargs='?', default=False, const='short',
                           help='Track job status (if applicable)')

    def set_args(self, args):
        self.args = args
        self.job_mode = self.args.job_mode
        self.task_name = self.args.task_name
        self.parallel = self.args.parallel
        self.merge = self.args.merge
        self.dry_run = self.args.dry_run
        self.bopts = self.args.sub_opts
        self.memory = self.args.memory
        self.tracking = self.args.tracking
        self.task_dir = self.args.dir
        # if self.dry_run:
        #     self.tracking = False

    def file_len(self, fname):
        with open(fname) as f:
            for i, l in enumerate(f):
                pass
            return i + 1

    def add_filelist_split_jobs(self, prog, cfg, files_per_job, output_cfgs):
        if 'filelist' in cfg:
            filelist = cfg['filelist']
            nfiles = self.file_len(filelist)
        elif 'filelists' in cfg:
            nfiles = 0
            for f in cfg['filelists']:
                nfiles += self.file_len(f)
        if files_per_job <= 0:
            njobs = 1
        else:
            njobs = int(ceil(float(nfiles)/float(files_per_job)))
        for n in xrange(njobs):
            final_cfg = copy.deepcopy(cfg)
            for item in output_cfgs:
                filename, extension = os.path.splitext(cfg[item])
                final_cfg[item] = filename + ('_%i' % n) + extension
            final_cfg['file_offset'] = n
            final_cfg['file_step'] = njobs
            cmd = """%s '%s'""" % (prog, json.dumps(final_cfg))
            self.job_queue.append(cmd)
            # print cmd

    def create_job_script(self, commands, script_filename, do_log=False, is_slurm=False):
        fname = script_filename
        logname = script_filename.replace('.sh', '.log')
        if is_slurm:
            DO_JOB_PREFIX = SLURM_PREFIX_TEMPLATE
            DO_JOB_PREFIX = DO_JOB_PREFIX % ({
              'LOG' : script_filename.replace('.sh',''),
              'PWD' : (os.environ['PWD'] if self.args.cwd else '${INITIALDIR}')
            })
        else :
            DO_JOB_PREFIX = JOB_PREFIX
            DO_JOB_PREFIX = DO_JOB_PREFIX % ({
              'PWD' : (os.environ['PWD'] if self.args.cwd else '${INITIALDIR}')
            })

        with open(fname, "w") as text_file:
            text_file.write(DO_JOB_PREFIX)
            if self.tracking:
                full_path = os.path.abspath(script_filename)
                text_file.write('mv %s %s\n' % (
                        full_path.replace('.sh', '.status.submitted'),
                        full_path.replace('.sh', '.status.running')
                    ))
                text_file.write(ERROR_CAPTURE % (
                        full_path.replace('.sh', '.status.running'),
                        full_path.replace('.sh', '.status.error')
                    ))
            for i, command in enumerate(commands):
                tee = 'tee' if i == 0 else 'tee -a'
                log_part = '\n'
                if do_log: log_part = ' 2>&1 | %s ' % tee + logname + log_part
                text_file.write(command + log_part)
            if self.tracking:
                full_path = os.path.abspath(script_filename)
                text_file.write('mv %s %s\n' % (
                        full_path.replace('.sh', '.status.running'),
                        full_path.replace('.sh', '.status.done')
                    ))
            if is_slurm:
                text_file.write(SLURM_POSTFIX)
        st = os.stat(fname)
        os.chmod(fname, st.st_mode | stat.S_IEXEC)
        print 'Created job script: %s' % script_filename
        if self.tracking and not self.dry_run:
            trackname = script_filename.replace('.sh', '.status.created')
            open(trackname, 'a').close()

    def read_job_status(self, script_filename):
        full_path = os.path.abspath(script_filename)
        status_files = glob.glob(full_path.replace('.sh', '.status.*'))
        statuses = []
        for status_f in status_files:
            pos = status_f.rfind('status')
            status = (status_f[pos:]).split('.')[1:]
            statuses.append(status)
        # print statuses
        return statuses

    def flush_queue(self):
        if self.job_mode == 'interactive':
            pool = Pool(processes=self.parallel)
            result = pool.map(
                partial(run_command, self.dry_run), self.job_queue)
        script_list = []
        status_result = {}
        njobs = 0
        if self.job_mode in ['script', 'lxbatch', 'ts', 'slurm']:
            for i, j in enumerate(range(0, len(self.job_queue), self.merge)):
                njobs += 1
                script_name = 'job_%s_%i.sh' % (self.task_name, i)
                if self.task_dir is not '':
                    script_name = os.path.join(self.task_dir, script_name)
                status = 'unknown'
                if self.tracking:
                    statuses = self.read_job_status(script_name)
                    if len(statuses) == 0:
                        status = 'new'
                    elif len(statuses) == 1:
                        status = statuses[0][0]
                    else:
                        status = 'confused'
                    if status not in status_result:
                       status_result[status] = []
                    status_result[status].append(script_name)
                    if len(statuses) > 0:
                        # print '%s appears to already be in progress, skipping...' % script_name
                        continue

                # each job is given a slice from the list of combine commands of length 'merge'
                # we also keep track of the files that were created in case submission to a
                # batch system was also requested
                self.create_job_script(
                    self.job_queue[j:j + self.merge], script_name, self.job_mode in ['script', 'ts'],self.job_mode in ['slurm'])
                script_list.append(script_name)
        if self.job_mode == 'lxbatch':
            for script in script_list:
                full_script = os.path.abspath(script)
                logname = full_script.replace('.sh', '_%J.log')
                if self.tracking and not self.dry_run:
                    os.rename(full_script.replace('.sh', '.status.created'), full_script.replace('.sh', '.status.submitted'))
                run_command(self.dry_run, 'bsub -o %s %s %s' % (logname, self.bopts, full_script))
        if self.job_mode == 'slurm':
            for script in script_list:
                full_script = os.path.abspath(script)
                logname = full_script.replace('.sh', '_%A.log')
                if self.tracking and not self.dry_run:
                    os.rename(full_script.replace('.sh', '.status.created'), full_script.replace('.sh', '.status.submitted'))
                run_command(self.dry_run, 'sbatch -o %s %s %s' % (logname, self.bopts, full_script))
        if self.job_mode == 'ts':
            for script in script_list:
                full_script = os.path.abspath(script)
                if self.tracking and not self.dry_run:
                    os.rename(full_script.replace('.sh', '.status.created'), full_script.replace('.sh', '.status.submitted'))
                run_command(self.dry_run, 'ts bash -c "eval %s"' % (full_script))
        if self.job_mode == 'condor':
            outscriptname = 'condor_%s.sh' % self.task_name
            subfilename = 'condor_%s.sub' % self.task_name
            if self.task_dir is not '':
                outscriptname = os.path.join(self.task_dir, outscriptname)
                subfilename = os.path.join(self.task_dir, subfilename)
            print '>> condor job script will be %s' % outscriptname
            outscript = open(outscriptname, "w")
            DO_JOB_PREFIX = JOB_PREFIX % ({
              'PWD': (os.environ['PWD'] if self.args.cwd else '${INITIALDIR}')
            })
            outscript.write(DO_JOB_PREFIX)
            jobs = 0
            for i, j in enumerate(range(0, len(self.job_queue), self.merge)):
                outscript.write('\nif [ $1 -eq %i ]; then\n' % jobs)
                jobs += 1
                for line in self.job_queue[j:j + self.merge]:
                    newline = line
                    outscript.write('  ' + newline + '\n')
                outscript.write('fi')
            outscript.close()
            subfile = open(subfilename, "w")
            condor_settings = CONDOR_TEMPLATE % {
              'EXE': outscriptname,
              'TASK': self.task_name,
              'TASKDIR': os.path.join(self.task_dir, ''),
              'EXTRA': self.bopts.decode('string_escape'),
              'NUMBER': jobs
            }
            subfile.write(condor_settings)
            subfile.close()
            run_command(self.dry_run, 'condor_submit %s' % (subfilename))

        if self.job_mode in ['lxbatch', 'ts'] and self.tracking:
            print '>> Status summary: %s' % self.task_name
            for status in status_result:
                counter = '[%i/%i]' % (len(status_result[status]), njobs)
                print '%20s %10s' % (status, counter)
                if self.tracking == 'long':
                    for f in status_result[status]:
                        print ' '*20 + '%s' % f



        del self.job_queue[:]
