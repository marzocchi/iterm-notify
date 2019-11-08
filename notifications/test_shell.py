from unittest import TestCase
from subprocess import run
from tempfile import NamedTemporaryFile
from os import environ


class TestShellScripts(TestCase):
    pass


def create_test_func(shell_name: str, init: str, command: str, expected: str, input_text=None):
    def f(self):
        tmp = NamedTemporaryFile('w', suffix='-iterm-notify-id')
        tmp.write("FOO_ID\n")
        tmp.flush()

        env = environ.copy()
        env['ITERM_NOTIFY_IDENTITY_FILE'] = tmp.name

        result = run(
            [
                shell_name,
                '-c',
                "source {}; iterm-notify {}".format(init, command)
            ],
            input=input_text,
            capture_output=True,
            env=env
        )

        err = result.stderr.decode('UTF-8')
        out = result.stdout.decode('UTF-8')

        self.assertEqual('', err)
        self.assertIn("Custom=id=FOO_ID:", out)
        self.assertIn(expected, out)

    return f


tests = [
    {
        'name': 'before-command',
        'call': 'before-command "ls -l"',
        'expect': 'before-command,bHMgLWw=',
    },
    {
        'name': 'after-command',
        'call': 'after-command 0',
        'expect': 'after-command,MA==',
    },
    {
        'name': 'notify',
        'call': 'send title 1',
        'expect': 'notify,bWVzc2FnZQ==,dGl0bGU=,MQ==',
        'input': b'message',
    },
    {
        'name': 'config-set',
        'call': 'config-set FOO BAR',
        'expect': 'set-FOO,QkFS',
    }
]

shells = {
    "zsh": "init.sh",
    "bash": "init.sh",
    "fish": "init.fish"
}

for shell in shells:
    init = shells[shell]
    for test in tests:
        setattr(TestShellScripts,
                "test_{shell}_{command}".format(shell=shell, command=test['name']),
                create_test_func(
                    shell,
                    init,
                    test['call'],
                    test['expect'],
                    test['input'] if 'input' in test else None
                )
                )
