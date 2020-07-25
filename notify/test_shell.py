from os import environ
from subprocess import run
from tempfile import NamedTemporaryFile
from unittest import TestCase


class TestShellScripts(TestCase):
    pass


def create_test_func(shell_name: str, init_file: str, command: str, expected: str, input_text=None):
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
                "source {}; iterm-notify {}".format(init_file, command)
            ],
            input=input_text,
            capture_output=True,
            env=env
        )

        out = result.stdout.decode('UTF-8')

        self.assertEqual(0, result.returncode)
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
        'call': 'send title',
        'expect': 'notify,bWVzc2FnZQ==,dGl0bGU=',
        'input': b'message',
    },
    {
        'name': 'notify-with-inline-message',
        'call': 'send title message',
        'expect': 'notify,bWVzc2FnZQ==,dGl0bGU=',
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
                    test['input'] if 'input' in test else None))
