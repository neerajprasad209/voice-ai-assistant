"""
Custom exception class for the Voice AI Assistant.

Provides detailed exception messages including:
- File name
- Function name
- Line number
- Original exception
"""

from __future__ import annotations

import sys
from pathlib import Path


class VoiceAssistantException(Exception):
    """
    Base exception class for the Voice AI Assistant.

    Wrap any unexpected exception using this class to
    provide detailed debugging information.
    """

    def __init__(self, error: Exception):
        super().__init__(str(error))

        _, _, exc_tb = sys.exc_info()

        if exc_tb is None:
            self.file_name = "Unknown"
            self.line_number = "Unknown"
            self.function_name = "Unknown"
        else:
            frame = exc_tb.tb_frame

            self.file_name = Path(frame.f_code.co_filename).name
            self.function_name = frame.f_code.co_name
            self.line_number = exc_tb.tb_lineno

        self.original_error = str(error)

    def __str__(self) -> str:
        return (
            "\n"
            "VoiceAssistantException\n"
            f"File      : {self.file_name}\n"
            f"Function  : {self.function_name}\n"
            f"Line      : {self.line_number}\n"
            f"Error     : {self.original_error}"
        )