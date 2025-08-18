from rich.console import Console
from rich.live import Live


class BaseBlock:
    """
    a visual "block" on the terminal.
    """

    def __init__(self, use_live: bool = True):
        self.use_live = use_live
        self.console = Console()
        self.live = (
            Live(auto_refresh=False, console=self.console, vertical_overflow="visible")
            if use_live
            else None
        )
        if self.live:
            self.live.start()

    def update_from_message(self, message):
        raise NotImplementedError("Subclasses must implement this method")

    def end(self):
        if self.live:
            self.refresh(cursor=False)
            self.live.stop()

    def refresh(self, cursor=True):
        raise NotImplementedError("Subclasses must implement this method")

    def as_renderable(self, cursor: bool = True):
        """
        Return a Rich renderable representing the current state of the block.
        Subclasses must implement this method.
        """
        raise NotImplementedError("Subclasses must implement this method")
