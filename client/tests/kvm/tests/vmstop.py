import logging, time, os
from autotest_lib.client.common_lib import error
from autotest_lib.client.bin import utils
import kvm_subprocess, kvm_test_utils, kvm_utils


def run_vmstop(test, params, env):
    """
    KVM guest stop test:
    1) Log into a guest
    2) Copy a file into guest
    3) Stop guest
    4) Check the status through monitor
    5) Check the session
    6) Migrat the vm to a file twice and compare them.

    @param test: kvm test object
    @param params: Dictionary with the test parameters
    @param env: Dictionary with test environment.
    """
    vm = kvm_test_utils.get_living_vm(env, params.get("main_vm"))
    timeout = float(params.get("login_timeout", 240))
    session = kvm_test_utils.wait_for_login(vm, 0, timeout, 0, 2)

    save_path = params.get("save_path", "/tmp")
    clean_save = params.get("clean_save") == "yes"
    save1 = os.path.join(save_path, "save1")
    save2 = os.path.join(save_path, "save2")

    guest_path = params.get("guest_path", "/tmp")
    file_size = params.get("file_size", "1000")
    bg = None

    try:
        utils.run("dd if=/dev/zero of=/tmp/file bs=1M count=%s" % file_size)
        # Transfer file from host to guest, we didn't expect the finish of
        # transfer, we just let it to be a kind of stress in guest.
        bg = kvm_test_utils.BackgroundTest(vm.copy_files_to,
                                           ("/tmp/file", guest_path,
                                            0, 60))
        logging.info("Start the background transfer")
        bg.start()

        # wait for the transfer start
        time.sleep(5)
        logging.info("Stop the VM")
        vm.monitor.cmd("stop")

        # check with monitor
        logging.info("Check the status through monitor")
        if "paused" not in vm.monitor.info("status"):
            raise error.TestFail("Guest did not pause after sending stop")

        # check through session
        logging.info("Check the session")
        if session.is_responsive():
            raise error.TestFail("Session still alive after sending stop")

        # Check with the migration file
        logging.info("Save and check the state files")
        for p in [save1, save2]:
            vm.save_to_file(p)
            time.sleep(1)
            if not os.path.isfile(p):
                raise error.TestFail("VM failed to save state file %s" % p)

        # Fail if we see deltas
        md5_save1 = utils.hash_file(save1)
        md5_save2 = utils.hash_file(save2)
        if md5_save1 != md5_save2:
            raise error.TestFail("The produced state files differ")

    finally:
        if clean_save:
            logging.debug("Clean the state files")
            if os.path.isfile(save1):
                os.remove(save1)
            if os.path.isfile(save2):
                os.remove(save2)
        if bg:
            bg.join()
        vm.monitor.cmd("cont")
        session.close()
