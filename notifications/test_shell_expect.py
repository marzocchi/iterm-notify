from unittest import TestCase, skipUnless
import tempfile
from os import environ
import os
import pexpect

works_for_me = skipUnless(os.environ.get('WORKS_FOR_ME', False),
                          'Skip tests that I can\'t figure out how to make work on CI')


def _cleanup_shell_output(b) -> str:
    return str(b).replace(r"\\", "")


class TestInteractiveShell(TestCase):
    def setUp(self) -> None:
        self.project_dir = os.getcwd()

        self.id_file = tempfile.NamedTemporaryFile('w', suffix='-iterm-notify-id')
        self.id_file.write("FOO_ID\n")
        self.id_file.flush()

        self.home = tempfile.mkdtemp()

        self.env = environ.copy()
        self.env.update({
            'ITERM_NOTIFY_IDENTITY_FILE': self.id_file.name,
            'TERM': 'xterm-256color',
            'HOME': self.home,
        })


class TestZsh(TestInteractiveShell):
    def setUp(self) -> None:
        super().setUp()

        zsh_init = [
            'PS1=""',
            "source {project_dir}/init.sh".format(project_dir=self.project_dir)
        ]

        with open("{home}/.zshrc".format(home=self.home), "w") as f:
            f.write(";\n".join(zsh_init))

    @works_for_me
    def test_zsh_with_successful_command(self):
        child = pexpect.spawn("zsh --login", env=self.env, timeout=3, encoding='UTF-8')

        child.sendline("ls -l | head -n 1")
        child.sendeof()

        # consume some lines
        child.readline()
        child.readline()
        self.assertIn("Custom=id=FOO_ID:before-command,", _cleanup_shell_output(child.readline()))
        self.assertIn("Custom=id=FOO_ID:after-command,MA==", _cleanup_shell_output(child.readline()))

    @works_for_me
    def test_zsh_with_failed_command(self):
        child = pexpect.spawn("zsh --login", env=self.env, timeout=3, encoding='UTF-8')

        child.sendline("does-not-exits")
        child.sendeof()

        # consume some lines
        child.readline()
        child.readline()
        self.assertIn("Custom=id=FOO_ID:before-command,", _cleanup_shell_output(child.readline()))
        self.assertIn("Custom=id=FOO_ID:after-command,MTI3", _cleanup_shell_output(child.readline()))


class TestFish(TestInteractiveShell):
    def setUp(self) -> None:
        super().setUp()

        os.mkdir("{home}/.config".format(home=self.home))
        os.mkdir("{home}/.config/fish".format(home=self.home))

        fish_init = [
            "set fish_greeting",
            "function fish_prompt",
            "  echo '>'",
            "end",
            "source {project_dir}/init.fish".format(project_dir=self.project_dir)
        ]

        with open("{home}/.config/fish/config.fish".format(home=self.home), "w") as f:
            f.write(";\n".join(fish_init))

    @works_for_me
    def test_fish_with_successful_command(self):
        child = pexpect.spawn('fish --login', env=self.env, timeout=3, encoding='UTF-8')

        child.sendline("ls -l | head -n 1")
        child.sendeof()

        # consume this line
        child.readline()
        self.assertIn("Custom=id=FOO_ID:before-command,", _cleanup_shell_output(child.readline()))
        self.assertIn("Custom=id=FOO_ID:after-command,MA==", _cleanup_shell_output(child.readline()))

    @works_for_me
    def test_fish_with_failed_command(self):
        child = pexpect.spawn('fish --login', env=self.env, timeout=3, encoding='UTF-8')

        child.sendline("does-not-exits")
        child.sendline("exit")

        # consume this line
        child.readline()
        self.assertIn("Custom=id=FOO_ID:before-command,", _cleanup_shell_output(child.readline()))
        self.assertIn("Custom=id=FOO_ID:after-command,MTI3", _cleanup_shell_output(child.readline()))
