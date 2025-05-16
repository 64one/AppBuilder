from PyQt6.QtCore import QThread, pyqtSignal
import subprocess


class BuilderThread(QThread):
    """Runs pyinstaller commands to build an executable"""
    console_output = pyqtSignal(str)
    def __init__(self, command:str):
        super().__init__()
        self.command = command
        self.error_encountered = False

    def kill_process(self):
        self.process.kill()
        self.process.wait()
   
    def run(self):
        try:
            self.console_output.emit("<b>Application building initiated...</b>")
            self.process = subprocess.Popen(
                self.command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            for line in self.process.stdout:
                self.console_output.emit(line)  # Send output to UI
            self.process.stdout.close()
            self.process.wait()

        except Exception as error:
            self.console_output.emit(f'<p style="color: red;">An error occured: <b>{error}</b></p>')

        finally:
            self.quit()