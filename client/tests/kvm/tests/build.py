import kvm.installer

def run_build(test, params, env):
    """
    Installs KVM using the selected install mode. Most install methods will
    take kvm source code, build it and install it to a given location.

    @param test: kvm test object.
    @param params: Dictionary with test parameters.
    @param env: Test environment.
    """
    srcdir = params.get("srcdir", test.srcdir)
    params["srcdir"] = srcdir

    try:
        installer = kvm.installer.make_installer(params)
        installer.set_install_params(test, params)
        installer.install()
        env.register_installer(installer)
    except Exception,e:
        # if the build/install fails, don't allow other tests
        # to get a installer.
        msg = "KVM install failed: %s" % (e)
        env.register_installer(kvm.installer.FailedInstaller(msg))
        raise
