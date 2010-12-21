import logging, time, os, shutil, glob, ConfigParser
from autotest_lib.client.common_lib import error
import kvm_subprocess, kvm_test_utils, kvm_utils, kvm_preprocessing


def run_unittest(test, params, env):
    """
    KVM RHEL-6 style unit test:
    1) Resume a stopped VM
    2) Wait for VM to terminate
    3) If qemu exited with code = 0, the unittest passed. Otherwise, it failed
    4) Collect all logs generated

    @param test: kvm test object
    @param params: Dictionary with the test parameters
    @param env: Dictionary with test environment
    """
    unittest_dir = os.path.join(test.bindir, 'unittests')
    if not os.path.isdir(unittest_dir):
        raise error.TestError("No unittest dir %s available (did you run the "
                              "build test first?)" % unittest_dir)
    os.chdir(unittest_dir)
    unittest_list = glob.glob('*.flat')
    if not unittest_list:
        raise error.TestError("No unittest files available (did you run the "
                              "build test first?)")
    logging.debug('Flat file list: %s', unittest_list)

    unittest_cfg = os.path.join(unittest_dir, 'unittests.cfg')
    parser = ConfigParser.ConfigParser()
    parser.read(unittest_cfg)
    test_list = parser.sections()

    if not test_list:
        raise error.TestError("No tests listed on config file %s" %
                              unittest_cfg)
    logging.debug('Unit test list: %s' % test_list)

    if params.get('test_list', None):
        test_list = kvm_utils.get_sub_dict_names(params, 'test_list')
        logging.info('Original test list overriden by user')
        logging.info('User defined unit test list: %s' % test_list)

    nfail = 0
    tests_failed = []

    timeout = int(params.get('unittest_timeout', 600))

    extra_params_original = params['extra_params']

    for t in test_list:
        logging.info('Running %s', t)

        file = None
        if parser.has_option(t, 'file'):
            file = parser.get(t, 'file')

        if file is None:
            nfail += 1
            tests_failed.append(t)
            logging.error('Unittest config file %s has section %s but no '
                          'mandatory option file' % (unittest_cfg, t))
            continue

        if file not in unittest_list:
            nfail += 1
            tests_failed.append(t)
            logging.error('Unittest file %s referenced in config file %s but '
                          'was not find under the unittest dir' %
                          (file, unittest_cfg))
            continue

        smp = None
        if parser.has_option(t, 'smp'):
            smp = int(parser.get(t, 'smp'))
            params['smp'] = smp

        extra_params = None
        if parser.has_option(t, 'extra_params'):
            extra_params = parser.get(t, 'extra_params')
            params['extra_params'] += ' %s' % extra_params

        vm_name = params.get("main_vm")
        params['kernel'] = os.path.join(unittest_dir, file)
        testlog_path = os.path.join(test.debugdir, "%s.log" % t)

        try:
            try:
                vm_name = params.get('main_vm')
                kvm_preprocessing.preprocess_vm(test, params, env, vm_name)
                vm = env.get_vm(vm_name)
                vm.create()
                vm.monitor.cmd("cont")
                logging.info("Waiting for unittest %s to complete, timeout %s, "
                             "output in %s", t, timeout,
                             vm.get_testlog_filename())
                if not kvm_utils.wait_for(vm.is_dead, timeout):
                    raise error.TestFail("Timeout elapsed (%ss)" % timeout)
                # Check qemu's exit status
                status = vm.process.get_status()
                if status != 0:
                    nfail += 1
                    tests_failed.append(t)
                    logging.error("Unit test %s failed", t)
            except Exception, e:
                nfail += 1
                tests_failed.append(t)
                logging.error('Exception happened during %s: %s', t, str(e))
        finally:
            try:
                shutil.copy(vm.get_testlog_filename(), testlog_path)
                logging.info("Unit test log collected and available under %s",
                             testlog_path)
            except NameError, IOError:
                logging.error("Not possible to collect logs")

        # Restore the extra params so other tests can run normally
        params['extra_params'] = extra_params_original

    if nfail != 0:
        raise error.TestFail("Unit tests failed: %s" % " ".join(tests_failed))
