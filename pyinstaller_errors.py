import re

ERROR_PATTERNS = [
   # Command-line argument errors
   r"pyinstaller: error: the following arguments are required: (\w+)",
   r"pyinstaller: error: (.*)",

   # Common PyInstaller errors
   r"Error: (.*)",
   r"ImportError: (.*)",
   r"ModuleNotFoundError: (.*)",
   r"FileNotFoundError: (.*)",
   r"PermissionError: (.*)",
   r"UnicodeDecodeError: (.*)",

   # PyInstaller specific errors
   r"FATAL: (.*)",
   r"Fatal Python error: (.*)",
   r"RecursionError: (.*)",
   r"Failed to execute script (.*)",

   # Hook related errors
   r"Hook-.*' failed with: (.*)",
   r"ModuleNotFoundError: No module named '(\w+)'",

   # Binary loading errors
   r"Cannot find (.*)",
   r"Failed to load (.*)",

   # General errors
   r"\[ERROR\] (.*)",
   r"Script file .* does not exist.",
   r"Unable to find .*",
   r"Aborting build process.*"
]


def check_for_errors(line: str) -> str:
   for pattern in ERROR_PATTERNS:
      match = re.search(pattern, line, re.IGNORECASE)
      if match:
         error_msg = match.group(1) if len(match.groups()) > 0 else line
         return error_msg
   return ""