import asyncio
import os
from typing import ClassVar, Literal

from anthropic.types.beta import BetaToolBash20241022Param

from .base import BaseAnthropicTool, CLIResult, ToolError, ToolResult


class _BashSession:
    """A session of a bash shell."""

    _started: bool
    _process: asyncio.subprocess.Process

    command: str = "/bin/bash"
    _output_delay: float = 0.2  # seconds
    _timeout: float = 120.0  # seconds
    _sentinel: str = "<<exit>>"

    def __init__(self):
        self._started = False
        self._timed_out = False

    async def start(self):
        if self._started:
            return

        # Launch an interactive bash process we can reuse across calls
        self._process = await asyncio.create_subprocess_exec(
            self.command,
            preexec_fn=os.setsid,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        self._started = True

    def stop(self):
        """Terminate the bash shell."""
        if not self._started:
            raise ToolError("Session has not started.")
        if self._process.returncode is not None:
            return
        self._process.terminate()

    async def run(self, command: str):
        """Execute a command in the bash shell."""
        if not self._started:
            raise ToolError("Session has not started.")
        if self._process.returncode is not None:
            return ToolResult(
                system="tool must be restarted",
                error=f"bash has exited with returncode {self._process.returncode}",
            )
        if self._timed_out:
            raise ToolError(
                f"timed out: bash has not returned in {self._timeout} seconds and must be restarted",
            )

        # we know these are not None because we created the process with PIPEs
        assert self._process.stdin
        assert self._process.stdout
        assert self._process.stderr

        # To avoid contaminating STDIN for programs like `python -`, write the
        # command to a temporary script and source it in the current shell.
        # This preserves shell state (e.g., `cd`) across runs and prevents
        # subsequent bytes from being read by child processes.
        import tempfile
        import pathlib

        tmp_file = tempfile.NamedTemporaryFile(
            mode="w", delete=False, prefix="oi_bash_", suffix=".sh"
        )
        try:
            tmp_file.write(command)
            tmp_file.flush()
            tmp_path = pathlib.Path(tmp_file.name)
        finally:
            tmp_file.close()

        # Use POSIX-compliant dot (.) to source the file so that state persists
        # within the session. Then print a sentinel so we know execution ended.
        wrapper_line = f". {str(tmp_path)}; echo '{self._sentinel}'\n"

        self._process.stdin.write(wrapper_line.encode())
        await self._process.stdin.drain()

        # read output from the process, until the sentinel is found
        try:
            async with asyncio.timeout(self._timeout):
                data = await self._process.stdout.readuntil(
                    self._sentinel.encode()
                )
                output = data.decode().split(self._sentinel, 1)[0]
        except asyncio.TimeoutError:
            self._timed_out = True
            raise ToolError(
                f"timed out: bash has not returned in {self._timeout} seconds and must be restarted",
            ) from None

        if output.endswith("\n"):
            output = output[:-1]

        # try to read any currently buffered stderr without blocking
        error = ""
        try:
            stderr_buf = self._process.stderr._buffer  # pyright: ignore[reportAttributeAccessIssue]
            error = stderr_buf.decode()
            if error.endswith("\n"):
                error = error[:-1]
            # clear the buffers so that the next output can be read correctly
            stderr_buf.clear()  # pyright: ignore[reportAttributeAccessIssue]
        except Exception:
            # If we cannot access internal buffer, fall back to no-op
            error = None

        # Attempt to remove the temporary file; ignore failures
        try:
            tmp_path.unlink(missing_ok=True)  # type: ignore[attr-defined]
        except Exception:
            pass

        return CLIResult(output=output, error=error)


class BashTool(BaseAnthropicTool):
    """
    A tool that allows the agent to run bash commands.
    The tool parameters are defined by Anthropic and are not editable.
    """

    _session: _BashSession | None
    name: ClassVar[Literal["bash"]] = "bash"
    api_type: ClassVar[Literal["bash_20241022"]] = "bash_20241022"

    def __init__(self):
        self._session = None
        super().__init__()

    async def __call__(
        self, command: str | None = None, restart: bool = False, **kwargs
    ):
        if restart:
            if self._session:
                self._session.stop()
            self._session = _BashSession()
            await self._session.start()

            return ToolResult(system="tool has been restarted.")

        if self._session is None:
            self._session = _BashSession()
            await self._session.start()

        if command is not None:
            return await self._session.run(command)

        raise ToolError("no command provided.")

    def to_params(self) -> BetaToolBash20241022Param:
        return {
            "type": self.api_type,
            "name": self.name,
        }
