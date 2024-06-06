from multiprocessing import freeze_support
from multiprocessing.spawn import freeze_support as freeze_support_spawn

from autogpt_server.data.execution import ExecutionQueue
from autogpt_server.executor import start_executor_manager
from autogpt_server.server import start_server


def background_process() -> None:
    """
    Runs the server in the background
    """
    freeze_support()
    freeze_support_spawn()
    main()


def main() -> None:
    queue = ExecutionQueue()
    start_executor_manager(5, queue)
    start_server(queue)


if __name__ == "__main__":
    # These directives are required to make multiprocessing work with cx_Freeze
    # and are both required and safe across platforms (Windows, macOS, Linux)
    # They must be placed at the beginning of the executions before any other
    # multiprocessing code is run
    freeze_support()
    freeze_support_spawn()
    main()
