import logging, time, re, random
from autotest_lib.client.common_lib import error
import kvm_subprocess, kvm_test_utils, kvm_utils


def run_iofuzz(test, params, env):
    """
    KVM iofuzz test:
    1) Log into a guest
    2) Enumerate all IO port ranges through /proc/ioports
    3) On each port of the range:
        * Read it
        * Write 0 to it
        * Write a random value to a random port on a random order

    If the guest SSH session hangs, the test detects the hang and the guest
    is then rebooted. The test fails if we detect the qemu process to terminate
    while executing the process.

    @param test: kvm test object
    @param params: Dictionary with the test parameters
    @param env: Dictionary with test environment.
    """
    def outb(session, port, data):
        """
        Write data to a given port.

        @param session: SSH session stablished to a VM
        @param port: Port where we'll write the data
        @param data: Integer value that will be written on the port. This
                value will be converted to octal before its written.
        """
        logging.debug("outb(0x%x, 0x%x)", port, data)
        outb_cmd = ("echo -e '\\%s' | dd of=/dev/port seek=%d bs=1 count=1" %
                    (oct(data), port))
        try:
            session.cmd(outb_cmd)
        except kvm_subprocess.ShellError, e:
            logging.debug(e)


    def inb(session, port):
        """
        Read from a given port.

        @param session: SSH session stablished to a VM
        @param port: Port where we'll read data
        """
        logging.debug("inb(0x%x)", port)
        inb_cmd = "dd if=/dev/port seek=%d of=/dev/null bs=1 count=1" % port
        try:
            session.cmd(inb_cmd)
        except kvm_subprocess.ShellError, e:
            logging.debug(e)


    def fuzz(session, inst_list):
        """
        Executes a series of read/write/randwrite instructions.

        If the guest SSH session hangs, an attempt to relogin will be made.
        If it fails, the guest will be reset. If during the process the VM
        process abnormally ends, the test fails.

        @param inst_list: List of instructions that will be executed.
        @raise error.TestFail: If the VM process dies in the middle of the
                fuzzing procedure.
        """
        for (op, operand) in inst_list:
            if op == "read":
                inb(session, operand[0])
            elif op =="write":
                outb(session, operand[0], operand[1])
            else:
                raise error.TestError("Unknown command %s" % op)

            if not session.is_responsive():
                logging.debug("Session is not responsive")
                if vm.process.is_alive():
                    logging.debug("VM is alive, try to re-login")
                    try:
                        session = kvm_test_utils.wait_for_login(vm, 0, 10, 0, 2)
                    except:
                        logging.debug("Could not re-login, reboot the guest")
                        session = kvm_test_utils.reboot(vm, session,
                                                        method = "system_reset")
                else:
                    raise error.TestFail("VM has quit abnormally during %s",
                                         (op, operand))


    login_timeout = float(params.get("login_timeout", 240))
    vm = kvm_test_utils.get_living_vm(env, params.get("main_vm"))
    session = kvm_test_utils.wait_for_login(vm, 0, login_timeout, 0, 2)

    try:
        ports = {}
        r = random.SystemRandom()

        logging.info("Enumerate guest devices through /proc/ioports")
        ioports = session.cmd_output("cat /proc/ioports")
        logging.debug(ioports)
        devices = re.findall("(\w+)-(\w+)\ : (.*)", ioports)

        skip_devices = params.get("skip_devices","")
        fuzz_count = int(params.get("fuzz_count", 10))

        for (beg, end, name) in devices:
            ports[(int(beg, base=16), int(end, base=16))] = name.strip()

        for (beg, end) in ports.keys():
            name = ports[(beg, end)]
            if name in skip_devices:
                logging.info("Skipping device %s", name)
                continue

            logging.info("Fuzzing %s, port range 0x%x-0x%x", name, beg, end)
            inst = []

            # Read all ports of the range
            for port in range(beg, end + 1):
                inst.append(("read", [port]))

            # Write 0 to all ports of the range
            for port in range(beg, end + 1):
                inst.append(("write", [port, 0]))

            # Write random values to random ports of the range
            for seq in range(fuzz_count * (end - beg + 1)):
                inst.append(("write",
                             [r.randint(beg, end), r.randint(0,255)]))

            fuzz(session, inst)

    finally:
        session.close()
