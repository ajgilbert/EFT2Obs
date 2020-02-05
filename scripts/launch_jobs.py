from jobs import Jobs
import argparse
import os

job_mgr = Jobs()
parser = argparse.ArgumentParser()

parser.add_argument('-j', '--jobs', default=1, type=int, help="Number of jobs")
parser.add_argument('-s', '--initial-seed', type=int, default=1, help="Initial random number seed")
parser.add_argument('--env', type=str, default=None, help="Additional environment variables for job [VAR1=X,VAR2=Y]")

job_mgr.attach_job_args(parser)
(args, unknown) = parser.parse_known_args()
job_mgr.set_args(args)

iwd = os.environ['PWD']

for i in xrange(args.initial_seed, args.initial_seed + args.jobs):
    cmd = []

    if args.env is not None:
        for X in args.env.split(','):
            cmd.append('export %s' % X)

    gp_cmd = 'python %s/scripts/run_gridpack.py --launch-dir %s --seed %i' % (iwd, iwd, i)
    if len(unknown) > 0:
        gp_cmd += ' %s' % (' '.join(unknown))
    cmd.append(gp_cmd)
    job_mgr.job_queue.append('; '.join(cmd))

job_mgr.flush_queue()
