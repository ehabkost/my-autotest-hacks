import kvm.installer

def run_build(test, params, env):
    """
    Installs KVM using the selected install mode. Most install methods will
    take kvm source code, build it and install it to a given location.

    @param test: kvm test object.
    @param params: Dictionary with test parameters.
    @param env: Test environment.
    """
    install_mode = params.get("mode")
    srcdir = params.get("srcdir", test.srcdir)
    params["srcdir"] = srcdir

    installer = kvm.installer.make_installer(install_mode, test, params)
    installer.install()
