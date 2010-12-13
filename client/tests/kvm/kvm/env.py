import UserDict

import kvm_utils

class KvmEnv(UserDict.IterableUserDict):
    """A wrapper to the 'env' object used by KVM tests

    It behaves like a dictionary, but may implement
    additional common operations used by KVM tests.
    """
    def __init__(self, d):
        UserDict.IterableUserDict.__init__(self, d)
