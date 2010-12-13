import UserDict
import cPickle

import kvm_utils

class KvmEnv(UserDict.IterableUserDict):
    """A wrapper to the 'env' object used by KVM tests

    It behaves like a dictionary, but may implement
    additional common operations used by KVM tests.
    """
    def __init__(self, d):
        UserDict.IterableUserDict.__init__(self, d)

def dump_env(obj, filename):
    """
    Dump KVM test environment to a file.

    @param filename: Path to a file where the environment will be dumped to.
    """
    file = open(filename, "w")
    cPickle.dump(obj, file)
    file.close()
