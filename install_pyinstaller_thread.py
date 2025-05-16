from PyQt6.QtCore import QThread, pyqtSignal
import subprocess


class InstallPyinstaller(QThread):
    console_output = pyqtSignal(str)
    def __init__(self):
        super().__init__()

    def kill_process(self):
        self.process.kill()
        self.process.wait()
     
    def run(self):
        try:
            self.process = subprocess.Popen(
            "pip3 install pyinstaller",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
            )
            for line in self.process.stdout:
                self.console_output.emit(line.strip())

            self.process.stdout.close()
            self.process.wait()

        except Exception as error:
            self.console_output.emit(f"An error occured: <b>{error}</b>")

        finally:
            self.quit()