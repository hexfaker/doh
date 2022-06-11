from doh.commands.kernel.install import install


def test_install(context):
    install(context=context, lang="python")
