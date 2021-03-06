#!/usr/bin/python
"""
Program to help setup kvm test environment

@copyright: Red Hat 2010
"""

import os, sys, optparse, logging, shutil
import common, kvm_utils
from autotest_lib.client.common_lib import logging_manager
from autotest_lib.client.bin import utils, os_dep


def check_iso(url, destination, hash):
    """
    Verifies if ISO that can be find on url is on destination with right hash.

    This function will verify the SHA1 hash of the ISO image. If the file
    turns out to be missing or corrupted, let the user know we can download it.

    @param url: URL where the ISO file can be found.
    @param destination: Directory in local disk where we'd like the iso to be.
    @param hash: SHA1 hash for the ISO image.
    """
    logging.info("Verifying iso %s", os.path.basename(url))
    if not destination:
        os.makedirs(destination)
    iso_path = os.path.join(destination, os.path.basename(url))
    if not os.path.isfile(iso_path) or (
                            utils.hash_file(iso_path, method="sha1") != hash):
        logging.warning("%s not found or corrupted", iso_path)
        logging.warning("Would you like to download it? (y/n)")
        iso_download = raw_input()
        if iso_download == 'y':
            utils.unmap_url_cache(destination, url, hash, method="sha1")
        else:
            logging.warning("Missing file %s. Please download it", iso_path)
    else:
        logging.debug("%s present, with proper checksum", iso_path)


if __name__ == "__main__":
    logging_manager.configure_logging(kvm_utils.KvmLoggingConfig(),
                                      verbose=True)
    logging.info("KVM test config helper")

    logging.info("1 - Verifying directories (check if the directory structure "
                 "expected by the default test config is there)")
    base_dir = "/tmp/kvm_autotest_root"
    sub_dir_list = ["images", "isos", "steps_data"]
    for sub_dir in sub_dir_list:
        sub_dir_path = os.path.join(base_dir, sub_dir)
        if not os.path.isdir(sub_dir_path):
            logging.debug("Creating %s", sub_dir_path)
            os.makedirs(sub_dir_path)
        else:
            logging.debug("Dir %s exists, not creating" %
                          sub_dir_path)
    logging.info("Do you want to setup NFS mounts for some of those "
                 "dirs? (y/n)")
    setup_nfs = raw_input()
    if setup_nfs == 'y':
        logging.info("Exiting the script so you can setup the NFS mounts. "
                     "When you are done, re-run this script.")
        sys.exit(0)

    logging.info("2 - Creating config files from samples (copy the default "
                 "config samples to actual config files)")
    kvm_test_dir = os.path.dirname(sys.modules[__name__].__file__)
    kvm_test_dir = os.path.abspath(kvm_test_dir)
    config_file_list = ["build.cfg", "cdkeys.cfg", "tests_base.cfg",
                        "tests.cfg", "unittests.cfg"]
    for config_file in config_file_list:
        src_file = os.path.join(kvm_test_dir, "%s.sample" % config_file)
        dst_file = os.path.join(kvm_test_dir, config_file)
        if not os.path.isfile(dst_file):
            logging.debug("Creating config file %s from sample", dst_file)
            shutil.copyfile(src_file, dst_file)
        else:
            logging.debug("Config file %s exists, not touching" % dst_file)

    logging.info("3 - Verifying iso (make sure we have the OS ISO needed for "
                 "the default test set)")

    iso_name = "Fedora-14-x86_64-DVD.iso"
    fedora_dir = "pub/fedora/linux/releases/14/Fedora/x86_64/iso"
    url = os.path.join("http://download.fedoraproject.org/", fedora_dir,
                       iso_name)
    hash = "38a4078011bac74493db7ecc53c9d9fbc96dbbd5"
    destination = os.path.join(base_dir, 'isos', 'linux')
    check_iso(url, destination, hash)

    logging.info("4 - Verifying winutils.iso (make sure we have the utility "
                 "ISO needed for Windows testing)")

    logging.info("In order to run the KVM autotests in Windows guests, we "
                 "provide you an ISO that this script can download")

    url = "http://people.redhat.com/mrodrigu/kvm/winutils.iso"
    hash = "02930224756510e383c44c49bffb760e35d6f892"
    destination = os.path.join(base_dir, 'isos', 'windows')
    check_iso(url, destination, hash)

    logging.info("5 - Checking if qemu is installed (certify qemu and qemu-kvm "
                 "are in the place the default config expects)")
    qemu_default_paths = ['/usr/bin/qemu-kvm', '/usr/bin/qemu-img']
    for qemu_path in qemu_default_paths:
        if not os.path.isfile(qemu_path):
            logging.warning("No %s found. You might need to install qemu-kvm.",
                            qemu_path)
        else:
            logging.debug("%s present", qemu_path)

    logging.info("6 - Checking for the KVM module (make sure kvm is loaded "
                 "to accelerate qemu-kvm)")
    if not utils.module_is_loaded("kvm"):
        logging.warning("KVM module is not loaded. You might want to load it")
    else:
        logging.debug("KVM module loaded")

    logging.info("7 - Verify needed packages to get started")
    logging.info("Please take a look at the online documentation "
                 "http://www.linux-kvm.org/page/KVM-Autotest/Client_Install "
                 "(session 'Install Prerequisite packages')")

    client_dir = os.path.abspath(os.path.join(kvm_test_dir, "..", ".."))
    autotest_bin = os.path.join(client_dir, 'bin', 'autotest')
    control_file = os.path.join(kvm_test_dir, 'control')
    logging.info("When you are done fixing eventual warnings found, "
                 "you can run the kvm test using the command line AS ROOT:")
    logging.info("%s --verbose %s", autotest_bin, control_file)
    logging.info("You can also edit the test config files (see output of "
                 "step 2 for a list)")
