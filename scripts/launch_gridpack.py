from jobs import Jobs
import argparse
import os

job_mgr = Jobs()
parser = argparse.ArgumentParser()

parser.add_argument('-c', '--cores', default=1, type=int, help="Number of cores")
parser.add_argument('task', type=str, help="Directory to run")

job_mgr.attach_job_args(parser)
(args, unknown) = parser.parse_known_args()
job_mgr.set_args(args)

iwd = os.environ['PWD']
cmd = 'cd %s; ./scripts/make_gridpack.sh %s 1 %i' % (iwd, args.task, args.cores)
job_mgr.job_queue.append(cmd)
job_mgr.flush_queue()
