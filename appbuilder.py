from PyQt6.QtWidgets import (
   QApplication, QMainWindow, QMessageBox, 
   QDialog, QFileDialog, QLabel
   )
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QClipboard
from PyQt6 import uic

from pathlib import Path
import os
import re
import sys
import subprocess
import shlex
import shutil
import webbrowser

import resources
from pyinstaller_errors import check_for_errors
from install_pyinstaller_thread import InstallPyinstaller
from run_builder_thread import BuilderThread


class AppWindow(QMainWindow):
   def __init__(self):
      super().__init__()
      main_path = Path(__file__).parent
      uic.loadUi(main_path.joinpath("UI", "builder.ui"), self)
      self.signals()
      self.update_command()

      self.toast_label = QLabel("", self)
      self.toast_label.setStyleSheet(
         """
         background-color: #3498db; 
         color: white; 
         padding: 5px; 
         border-radius: 5px;
         """
      )
      self.toast_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
      self.toast_label.setVisible(False)

   def closeEvent(self, event):
      if self.is_builder_running():
         event.ignore()
         self.show_toast("App building in process, wait till finished to exit!")
         return
      event.accept()
            
   def signals(self) -> None:
      # Menu Actions
      self.actionInstallPyinstaller.triggered.connect(self.install_pyinstaller)
      self.actionPyinstallerDocs.triggered.connect(
         lambda: webbrowser.open("https://pyinstaller.org/en/stable/usage.html")
         )

      # Home tab
      self.scriptButton.clicked.connect(self.select_script)
      self.iconButton.clicked.connect(self.select_icon)
      self.outputPathButton.clicked.connect(self.select_output_path)
      self.appNameLineEdit.textChanged.connect(self.update_command)

      self.copyCommandButton.clicked.connect(self.copy_command)
      self.injectCommandButton.clicked.connect(self.inject_command)

      # Clearing lineEdits has already been connected in th ui file
      for button in (
         self.clearScriptPathButton, 
         self.clearIconPathButton,
         self.clearOutputPathButton
      ):
         button.clicked.connect(self.update_command)

      for radio_but in (
         self.yesConsoleButton, self.noConsoleButton,
         self.yesOneFileButton, self.noOneFileButton,
         self.yesClearTempButton, self.noClearTempButton
      ):
         radio_but.clicked.connect(self.update_command)

      self.resetButton.clicked.connect(self.reset)
      self.buildButton.clicked.connect(self.build)

      # Add files Tab
      self.addFilesButton.clicked.connect(self.add_dependancy_files)
      self.removeFilesButton.clicked.connect(self.remove_dependancy_file)
      self.addFileInfoButton.clicked.connect(self.show_adding_files_info)

      self.addFolderButton.clicked.connect(self.add_dependancy_folder)
      self.removeFolderButton.clicked.connect(self.remove_dependancy_folder)
      self.addFolderInfoButton.clicked.connect(self.show_adding_folders_info)
      
   def select_script(self):
      file_path, ok = QFileDialog.getOpenFileName(
         self, 
         "Select Script", 
         str(Path.cwd()),
         "Python Scripts(*.py *.pyw)"
      )
      if ok and Path(file_path).is_file():
         self.scriptLineEdit.setText(file_path)
         os.chdir(Path(file_path).parent)
         self.appNameLineEdit.setText(Path(file_path).stem)
         self.update_command()

   def select_icon(self):
      file_path, ok = QFileDialog.getOpenFileName(
            self, 
            "Select Icon", 
            str(Path.cwd()),
            "Icon Files (*.ico)"
      )
      if ok and Path(file_path).is_file():
         self.iconLineEdit.setText(file_path)
         self.update_command()

   def show_toast(self, message:str, period:int=2000):
      self.toast_label.setText(message)
      self.toast_label.adjustSize()
      # Center horizontally, 50px from top
      self.toast_label.move(
         (self.width() - self.toast_label.width()) // 2, 50
      )
      self.toast_label.setVisible(True)
      QTimer.singleShot(period, lambda: self.toast_label.setVisible(False))

   def copy_command(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.commandTextEdit.toPlainText())
        self.show_toast("Command copied!")

   def inject_command(self) -> None:
      clipboard = QApplication.clipboard()
      text = clipboard.text()
      if "pyinstaller" not in text.lower():
         self.show_toast("No command detected from clipboard!")
         return

      self.extract_commands(text)
      self.update_command()
      self.show_toast("Command injected successfully")

   def extract_commands(self, command:str) -> None:
      parts = shlex.split(command)

      self.noClearTempButton.setChecked(True)
      base_path = "" # Folder that contains the Python file

      index = 0
      while index < len(parts):
         word = parts[index]

         # Start of command
         if word.lower() == "pyinstaller":
            index += 1
            continue

         # Script Path
         elif word.endswith(".py") and os.path.isfile(word):
            script_path = word
            self.scriptLineEdit.setText(script_path)
            name_from_script = Path(script_path).stem
            base_path = Path(script_path).parent
            self.appNameLineEdit.setText(name_from_script)

         # Console window
         elif word == "--noconsole":
            self.noConsoleButton.setChecked(False)
         elif word == "--console":
            self.yesConsoleButton.setChecked(True)

         # One file/dir
         elif word == "--onefile":
            self.yesOneFileButton.setChecked(True)
         elif word == "--onedir":
            self.noOneFileButton.setChecked(True)

         # Clean temp files
         elif word == "--clean":
            self.yesClearTempButton.setChecked(True)
         
         # App Name
         elif word == "--name" and index + 1 < len(parts):
            app_name = parts[index + 1]
            self.appNameLineEdit.setText(app_name)
            index += 1 # Jump the next item as it's the app name

         # App icon
         elif word == "--icon" and index + 1 < len(parts):
            icon_path = parts[index + 1]
            if Path(icon_path).is_file():
               self.iconLineEdit.setText(icon_path)
            index += 1

         # Added data: files and folders
         elif word == "--add-data" and index + 1 < len(parts):
            data_entry = parts[index + 1]
            try:
               data_path, _ = data_entry.split(";")
               data_path = Path(data_path)
               if data_path.name in ("*.*", "*"): # Folders
                  # replacing \ with / is just to make the command standard
                  # as the app adds the files/folders this way when
                  folder = str(data_path.parent).replace("\\", "/")
                  self.folderListWidget.addItem(folder)
               else: # Files
                  if base_path:
                     full_file_path = str(base_path.joinpath(data_path))
                     self.filesListWidget.addItem(full_file_path.replace("\\", "/"))
            except ValueError:
               self.show_toast(f"Invalid --add-data format: {data_entry}")
            finally:
               index += 1

         # Output/distribution path
         elif word == "--distpath" and index + 1 < len(parts):
            dist_path = parts[index + 1]
            if Path(dist_path).is_dir():
               self.outputPathLineEdit.setText(dist_path)
            index += 1

         # Move to next item
         index += 1

   def reset(self):
      button = QMessageBox.question(
         self,
         "Confirm Reset",
         "You're about to reset to defaults, are you sure?"
      )
      if button == QMessageBox.StandardButton.No:
         return

      if self.is_builder_running():
         self.outputTextEdit.clear()
      else:
         self.outputTextEdit.clear()

      self.scriptLineEdit.clear()
      self.iconLineEdit.clear()
      self.appNameLineEdit.clear()
      self.noConsoleButton.setChecked(True)
      self.yesOneFileButton.setChecked(True)
      self.yesClearTempButton.setChecked(True)
      self.outputPathLineEdit.clear()
      self.filesListWidget.clear()
      self.folderListWidget.clear()
      self.update_command()

   def select_output_path(self) -> None:
      folder = QFileDialog.getExistingDirectory(self, "Select Output Path")
      if os.path.isdir(folder):
         self.outputPathLineEdit.setText(folder)
         self.update_command()
         
   def add_dependancy_files(self) -> None:
      file_paths, ok = QFileDialog.getOpenFileNames(
         self, 
         "Select Files", 
         str(Path.cwd()), 
         "All Files (*)"
      )
      if file_paths and ok:
         self.filesListWidget.addItems(file_paths)
         self.update_command()

   def remove_dependancy_file(self) -> None:
      self.filesListWidget.takeItem(self.filesListWidget.currentRow())
      self.update_command()

   def add_dependancy_folder(self) -> None:
      directory = QFileDialog.getExistingDirectory(self, "Select Folder")
      if os.path.isdir(directory):
         self.folderListWidget.addItem(directory)
         self.update_command()

   def remove_dependancy_folder(self) -> None:
      self.folderListWidget.takeItem(self.folderListWidget.currentRow())
      self.update_command()

   def update_command(self) -> None:
      cmd = "pyinstaller"
      script_path = self.scriptLineEdit.text()
      if Path(script_path).is_file():
         cmd += f' "{script_path}"'

      if self.yesClearTempButton.isChecked():
         cmd += " --clean"

      if self.noConsoleButton.isChecked():
         cmd += " --noconsole"
      else:
         cmd += " --console"

      if self.yesOneFileButton.isChecked():
         cmd += " --onefile"
      else:
         cmd += " --onedir"

      name = self.appNameLineEdit.text().strip()
      if name:
         cmd += f' --name "{name}"'

      icon_path = self.iconLineEdit.text()
      if Path(icon_path).is_file():
         cmd += f' --icon "{icon_path}"'

      # Folders and Files are added relative to script path
      if Path(script_path).is_file():
         parent_path = Path(script_path).parent

         # Individual files
         for row in range(self.filesListWidget.count()):
            try:
               file_path = self.filesListWidget.item(row).text()
               rel_path = Path(file_path).relative_to(parent_path).parent # Remove filename
               rel_path = str(rel_path).replace("\\", "/")
               cmd += f' --add-data "{file_path};{rel_path}"'
            except ValueError:
               self.show_toast(f"{file_path} must be realtive to {parent_path}")

         # Folders
         for row in range(self.folderListWidget.count()):
            try:
               folder = self.folderListWidget.item(row).text()
               rel_path = Path(folder).relative_to(parent_path)
               rel_path = str(rel_path).replace("\\", "/")
               # Add every file in the folder to the relative path
               cmd += f' --add-data "{folder}/*.*;{rel_path}"'
            except ValueError:
               self.show_toast(
                  message=f"'{folder}' is not in the subpath of '{parent_path}'",
                  period=5000
                  )

      dest_path = self.outputPathLineEdit.text()
      # Note: Path("").is_dir()==True but os.path.isdir("")==False
      if os.path.isdir(dest_path):
         cmd += f' --distpath "{dest_path}"'

      self.commandTextEdit.setText(cmd)

   def update_output(self, console_output:str) -> None:
      if check_for_errors(console_output):
         self.outputTextEdit.append(f'<p style="color: red;">{console_output}</p>')
         self.show_toast("An error occured.")
         self.buildButton.show()
         return

      if "Building EXE from EXE-00.toc completed successfully" in console_output:
         self.show_toast("Process Completed", 4000)
         self.outputTextEdit.append(f"<b>{console_output}</b>")
         self.buildButton.show()
      else:
         self.outputTextEdit.append(console_output)
  
   def build(self) -> None:
      if not shutil.which("pyinstaller"):
         self.show_toast("pyinstaller not installed", 3000)
         return

      elif self.is_builder_running():
         self.show_toast("Another building is running.", 3000)
         return

      self.outputTextEdit.clear()
      self.builder_thread = BuilderThread(self.commandTextEdit.toPlainText())
      self.builder_thread.console_output.connect(self.update_output)
      self.builder_thread.start()
      self.buildButton.hide()
      self.tabWidget.setCurrentIndex(2)

   def is_builder_running(self) -> bool:
      if hasattr(self, "builder_thread"):
         if self.builder_thread.isRunning():
            return True
      return False

   def install_pyinstaller(self) -> None:
      if shutil.which("pyinstaller"):
         self.show_toast("pyinstaller already installed", 3000)
         return

      self.installer_thread = InstallPyinstaller()
      self.installer_thread.console_output.connect(self.update_output)
      self.installer_thread.start()
      self.tabWidget.setCurrentIndex(2)

   def show_adding_files_info(self) -> None:
      QMessageBox.information(
         self,
         "Adding Files",
         f"""
         <b>Adding Files</b><br><br>
         - File paths must be <u>relative</u> to the script's location.<br>
         - Files will be bundled with the <b>same directory structure</b> as provided.<br>
         - E.g bird.png in "C:\\FlappyBird\\Images\\bird.png" will be added to<br>
           "base_path\\Images" if script path is e.g "C:\\FlappyBird\\flappybird.py"<br>
         """
      )

   def show_adding_folders_info(self) -> None:
      QMessageBox.information(
         self,
         "Adding Folders",
         f"""
         <b>Adding Folders</b><br><br>
         - Folder paths must also be <u>relative</u> to the script's location.<br>
         - <b>All files</b> inside the specified folders will be included in the EXE.<br>
         - The folder structure will be preserved during bundling.<br>
         - E.g All files in "C:\\FlappyBird\\Images" will be added to<br>
            "base_path\\Images" if script path is e.g "C:\\FlappyBird\\flappybird.py"<br>
         """
      )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("fusion")
    window = AppWindow()
    window.show()
    sys.exit(app.exec())