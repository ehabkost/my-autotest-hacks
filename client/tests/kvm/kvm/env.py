import UserDict
import cPickle, logging

import kvm_utils

class KvmEnv(UserDict.IterableUserDict):
    """A wrapper to the 'env' object used by KVM tests

    It behaves like a dictionary, but may implement
    additional common operations used by KVM tests.
    """
    def __init__(self, d, filename=None):
        UserDict.IterableUserDict.__init__(self, d)
        self._filename = filename

    def _dump(self, filename):
        """
        Dump KVM test environment to a file.

        @param filename: Path to a file where the environment will be dumped to.
        """
        file = open(filename, "w")
        cPickle.dump(self.data, file)
        file.close()

    def save(self):
        return self._dump(self._filename)

    def get_all_vms(self):
        """
        Return a list of all VM objects on a given environment.
        """
        vms = []
        for obj in self.values():
            if kvm_utils.is_vm(obj):
                vms.append(obj)
        return vms

    def get_vm(self, name):
        """
        Return a VM object by its name.

        @param name: VM name.
        """
        return self.get("vm__%s" % name)

    def register_vm(self, name, vm):
        """
        Register a given VM in a given env.

        @param name: VM name.
        @param vm: VM object.
        """
        self.data["vm__%s" % name] = vm

    def unregister_vm(self, name):
        """
        Remove a given VM from a given env.

        @param name: VM name.
        """
        del self.data["vm__%s" % name]

    def register_installer(self, installer):
        """Register a installer that was just run

        The installer will be available for other tests, so that
        information about the installed KVM modules and qemu-kvm can be used by
        them.
        """
        self['last_installer'] = installer

    def previous_installer(self):
        """Return the last installer that was registered
        """
        return self.get('last_installer')


def _load_env(filename, version):
    """
    Load KVM test environment from an env file.
    If the version recorded in the file is lower than version, return an empty
    env.  If some other error occurs during unpickling, return an empty env.

    @param filename: Path to an env file.
    """
    default = {"version": version}
    try:
        file = open(filename, "r")
        env = cPickle.load(file)
        file.close()
        if env.get("version", 0) < version:
            logging.warn("Incompatible env file found. Not using it.")
            return default
        return env
    # Almost any exception can be raised during unpickling, so let's catch
    # them all
    except Exception, e:
        logging.warn(e)
        return default

def load(filename, version):
    return KvmEnv(_load_env(filename, version), filename)

