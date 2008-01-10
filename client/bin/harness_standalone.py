"""The standalone harness interface

The default interface as required for the standalone reboot helper.
"""

__author__ = """Copyright Andy Whitcroft 2007"""

from autotest_utils import *
import os, harness, shutil

class harness_standalone(harness.harness):
	"""The standalone server harness

	Properties:
		job
			The job object for this job
	"""

	def __init__(self, job):
		"""
			job
				The job object for this job
		"""
		self.autodir = os.path.abspath(os.environ['AUTODIR'])
		self.setup(job)

		src = job.control_get()
		dest = os.path.join(self.autodir, 'control')
		if os.path.abspath(src) != os.path.abspath(dest):
			shutil.copyfile(src, dest)
			job.control_set(dest)

		print 'Symlinking init scripts'
		rc = os.path.join(self.autodir, 'tools/autotest')
		# see if system supports event.d versus inittab
		if os.path.exists('/etc/event.d'):
			# NB: assuming current runlevel is default
			initdefault = system_output('runlevel').split()[1]
		else:
			initdefault = system_output('grep :initdefault: /etc/inittab')
			initdefault = initdefault.split(':')[1]

		try:
			system('ln -sf %s /etc/init.d/autotest' % rc)
			system('ln -sf %s /etc/rc%s.d/S99autotest' % \
							(rc, initdefault))
		except:
			print "WARNING: linking init scripts failed"
