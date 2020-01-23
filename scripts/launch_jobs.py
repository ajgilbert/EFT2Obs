from jobs import Jobs
import argparse
import os

job_mgr = Jobs()
parser = argparse.ArgumentParser()

parser.add_argument('--gridpack', default='.')
parser.add_argument('-j', '--jobs', default=1, type=int, help="Number of jobs")
parser.add_argument('-e', '--events', default=5000, type=int, help="Number of events per job")
parser.add_argument('-s', '--initial-seed', type=int, default=1, help="Initial random number seed")
parser.add_argument('-p', '--plugins', type=str, default='', help="Comma separated list of rivet plugins to run")
parser.add_argument('-o', '--outdir', type=str, default='.', help="Output directory for yoda files")
parser.add_argument('--env', type=str, default=None, help="Additional environment variables for job [VAR1=X,VAR2=Y]")

job_mgr.attach_job_args(parser)
args = parser.parse_args()
job_mgr.set_args(args)

iwd = os.environ['PWD']
gp_full = os.path.abspath(args.gridpack)
run_script = os.path.abspath('run_gridpack.sh')

outdir = os.path.abspath(args.outdir)

for i in xrange(args.initial_seed, args.initial_seed + args.jobs):
    cmd = []

    if args.env is not None:
        for X in args.env.split(','):
            cmd.append('export %s' % X)

    cmd.append('bash %s/scripts/run_gridpack.sh %s %i %i %s' % (iwd, gp_full, args.events, i, args.plugins))
    cmd.append('cp Rivet_%i.yoda %s/Rivet_%i.yoda' % (i, outdir, i))
    cmd.append('rm Rivet_%i.yoda' % i)
    job_mgr.job_queue.append('; '.join(cmd))

job_mgr.flush_queue()
