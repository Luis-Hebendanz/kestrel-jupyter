from ipykernel.kernelbase import Kernel
import os
import logging

from kestrel.codegen.display import DisplayWarning
from kestrel.session import Session
from kestrel_jupyter_kernel.config import LOG_FILE_NAME


_logger = logging.getLogger(__name__)


class KestrelKernel(Kernel):
    implementation = "kestrel"
    implementation_version = "1.0"
    language = "kestrel"
    language_version = "1.0"
    # https://jupyter-client.readthedocs.io/en/stable/messaging.html#msging-kernel-info
    language_info = {"name": "kestrel", "file_extension": ".hf"}
    banner = "Kestrel"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.kestrel_session = Session()
        _set_logging(
            self.kestrel_session.debug_mode,
            os.path.join(self.kestrel_session.runtime_directory, LOG_FILE_NAME),
        )

    def do_complete(self, code, cursor_pos):
        return {
            "matches": self.kestrel_session.do_complete(code, cursor_pos),
            "cursor_end": cursor_pos,
            "cursor_start": cursor_pos,
            "metadata": {},
            "status": "ok",
        }

    def do_execute(
        self, code, silent, store_history=True, user_expressions=None, allow_stdin=False
    ):

        errmsg = None

        if not silent:
            try:
                outputs = self.kestrel_session.execute(code)
                warning = "\n".join(
                    [
                        "[WARNING] " + x.to_string()
                        for x in outputs
                        if isinstance(x, DisplayWarning)
                    ]
                )
                self.send_response(
                    self.iopub_socket, "stream", {"name": "stderr", "text": warning}
                )
                output_html = "\n".join(
                    [x.to_html() for x in outputs if not isinstance(x, DisplayWarning)]
                )
                self.send_response(
                    self.iopub_socket,
                    "display_data",
                    {"data": {"text/html": output_html}, "metadata": {}},
                )

            except Exception as e:
                _logger.error("Exception occurred", exc_info=True)
                self.send_response(
                    self.iopub_socket, "stream", {"name": "stderr", "text": str(e)}
                )

        return {
            "status": "ok",
            "execution_count": self.execution_count,
            "payload": [],
            "user_expressions": {},
        }


def _set_logging(debug_flag, log_file_path):
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%H:%M:%S",
        level=logging.DEBUG if debug_flag else logging.INFO,
        handlers=[logging.FileHandler(log_file_path)],
    )
