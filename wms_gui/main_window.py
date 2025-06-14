import sys
import os
import subprocess
import time
import threading
import requests # For service health check

if sys.platform == "win32":
    import winreg
import json # For parsing query response

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QMenuBar, QStatusBar, QMessageBox, QGroupBox, QPushButton, QCheckBox,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QTimer # For Qt.AlignmentFlag and QTimer

# Assuming common.i18n is accessible via sys.path modification in app.py
from common.i18n import Translator

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.current_language = "en"  # Default language
        self.translator = Translator(self.current_language)

        self.service_process = None
        self.service_status = "Unknown" # Initial status

        # Autostart related attributes (Windows specific)
        if sys.platform == "win32":
            self.autostart_registry_key_path = "Software\\Microsoft\\Windows\\CurrentVersion\\Run"
            self.autostart_value_name = "WMS_Service_AutoStart"
            self.autostart_script_name = "autostart_wms_service.bat"
            self.autostart_script_path = os.path.join(self.project_root, self.autostart_script_name)
            # Ensure autostart_checkbox is initialized before _update_autostart_control_texts is called via retranslate_ui
            self.autostart_checkbox = QCheckBox()


        self.init_ui()

        self.status_check_timer = QTimer(self)
        self.status_check_timer.timeout.connect(self.check_service_status_threaded)
        self.status_check_timer.start(5000) # Check every 5 seconds
        self.check_service_status_threaded() # Initial check

    def init_ui(self):
        self.setWindowTitle(self.translator.get_string("app_title"))
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.layout = QVBoxLayout(self.central_widget)
        self.setCentralWidget(self.central_widget)

        self.create_menus()
        self.init_service_controls()
        self.init_data_query_controls() # Initialize data query controls
        self.create_status_bar()

        # Add a welcome label (optional, could be removed if space is needed)
        self.label = QLabel(self.translator.get_string("welcome_message", "Welcome!"))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.label)

        self.layout.addStretch(1) # Pushes query group and service group up if label is removed or small.

    def init_data_query_controls(self):
        self.data_query_group = QGroupBox() # Title set in _update_data_query_control_texts
        query_group_layout = QVBoxLayout()

        # Input fields
        form_layout = QFormLayout()
        self.tray_number_label = QLabel()
        self.tray_number_input = QLineEdit()
        self.material_id_label = QLabel()
        self.material_id_input = QLineEdit()
        form_layout.addRow(self.tray_number_label, self.tray_number_input)
        form_layout.addRow(self.material_id_label, self.material_id_input)
        query_group_layout.addLayout(form_layout)

        # Query button
        self.query_button = QPushButton()
        self.query_button.clicked.connect(self.handle_query_button)
        query_group_layout.addWidget(self.query_button)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5) # ID, Material ID, Tray Number, Timestamp, Status
        # Header labels set in _update_data_query_control_texts
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setMinimumHeight(200) # Ensure it's visible
        query_group_layout.addWidget(self.results_table)

        self.data_query_group.setLayout(query_group_layout)
        self.layout.insertWidget(0, self.data_query_group) # Insert at the top of the main layout

        self._update_data_query_control_texts()


    def _update_data_query_control_texts(self):
        if not hasattr(self, 'data_query_group'): return # Not initialized yet

        self.data_query_group.setTitle(self.translator.get_string("data_query_group"))
        self.tray_number_label.setText(self.translator.get_string("tray_number_label"))
        self.material_id_label.setText(self.translator.get_string("material_id_label"))
        self.query_button.setText(self.translator.get_string("query_button"))

        headers = [
            self.translator.get_string("results_table_header_id", "ID"),
            self.translator.get_string("results_table_header_material_id", "Material ID"),
            self.translator.get_string("results_table_header_tray_number", "Tray Number"),
            self.translator.get_string("results_table_header_timestamp", "Timestamp"),
            self.translator.get_string("results_table_header_status", "Status")
        ]
        self.results_table.setHorizontalHeaderLabels(headers)


    def init_service_controls(self):
        self.service_management_group = QGroupBox() # Title set in _update_service_control_texts
        group_layout = QVBoxLayout()

        # Buttons
        button_layout = QHBoxLayout()
        self.start_service_button = QPushButton()
        self.stop_service_button = QPushButton()
        self.restart_service_button = QPushButton()

        self.start_service_button.clicked.connect(self.start_service)
        self.stop_service_button.clicked.connect(self.stop_service)
        self.restart_service_button.clicked.connect(self.restart_service)

        button_layout.addWidget(self.start_service_button)
        button_layout.addWidget(self.stop_service_button)
        button_layout.addWidget(self.restart_service_button)
        group_layout.addLayout(button_layout)

        # Status Display
        status_form_layout = QFormLayout()
        self.service_status_label_text = QLabel() # "Service Status:"
        self.service_status_value_label = QLabel(self.service_status) # Actual status value
        status_form_layout.addRow(self.service_status_label_text, self.service_status_value_label)
        group_layout.addLayout(status_form_layout)

        # Autostart Checkbox (Windows only)
        if sys.platform == "win32":
            # self.autostart_checkbox is already initialized in __init__
            self.autostart_checkbox.toggled.connect(self.toggle_autostart)
            group_layout.addWidget(self.autostart_checkbox)
            self.load_autostart_setting() # Load initial state

        self.service_management_group.setLayout(group_layout)
        self.layout.addWidget(self.service_management_group)
        self._update_service_control_texts()
        if sys.platform == "win32":
            self._update_autostart_control_texts()


    def _update_autostart_control_texts(self):
        if sys.platform == "win32" and hasattr(self, 'autostart_checkbox'):
            self.autostart_checkbox.setText(self.translator.get_string("autostart_label"))

    def _update_service_control_texts(self):
        self.service_management_group.setTitle(self.translator.get_string("service_management_group"))
        self.start_service_button.setText(self.translator.get_string("start_service_button"))
        self.stop_service_button.setText(self.translator.get_string("stop_service_button"))
        self.restart_service_button.setText(self.translator.get_string("restart_service_button"))
        self.service_status_label_text.setText(self.translator.get_string("service_status_label"))
        self.update_status_display() # Updates the value part of the status

    def create_menus(self):
        menu_bar = self.menuBar()

        # File Menu
        self.file_menu = menu_bar.addMenu("")  # Text set in _update_menu_texts
        self.exit_action = QAction("", self)    # Text set in _update_menu_texts
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_action)

        # Language Menu
        self.language_menu = menu_bar.addMenu("")  # Text set in _update_menu_texts

        self.english_action = QAction("", self)    # Text set in _update_menu_texts
        self.english_action.setCheckable(True)
        self.english_action.triggered.connect(lambda: self.change_language("en"))
        self.language_menu.addAction(self.english_action)

        self.chinese_action = QAction("", self)    # Text set in _update_menu_texts
        self.chinese_action.setCheckable(True)
        self.chinese_action.triggered.connect(lambda: self.change_language("zh"))
        self.language_menu.addAction(self.chinese_action)

        self._update_menu_texts() # Initial text setting

    def _update_menu_texts(self):
        # File Menu
        self.file_menu.setTitle("&" + self.translator.get_string("file_menu"))
        self.exit_action.setText(self.translator.get_string("exit_action"))

        # Language Menu
        self.language_menu.setTitle("&" + self.translator.get_string("language_menu"))
        self.english_action.setText(self.translator.get_string("english_action"))
        self.chinese_action.setText(self.translator.get_string("chinese_action"))

        # Update checked state of language actions
        if self.current_language == "en":
            self.english_action.setChecked(True)
            self.chinese_action.setChecked(False)
        elif self.current_language == "zh":
            self.english_action.setChecked(False)
            self.chinese_action.setChecked(True)

        # Update service control texts if they exist
        if hasattr(self, 'service_management_group'): # Check if UI fully initialized
             self._update_service_control_texts()
        if sys.platform == "win32" and hasattr(self, 'autostart_checkbox'):
            self._update_autostart_control_texts()
        if hasattr(self, 'data_query_group'):
            self._update_data_query_control_texts()


    def create_status_bar(self):
        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage(self.translator.get_string("status_ready", "Ready"))

    def change_language(self, lang_code):
        if self.current_language == lang_code:
            # If the language is already set to the selected one, ensure the menu item is checked
            # and do nothing else, or re-check it if it got unchecked somehow.
            if lang_code == "en":
                self.english_action.setChecked(True)
                self.chinese_action.setChecked(False)
            elif lang_code == "zh":
                self.english_action.setChecked(False)
                self.chinese_action.setChecked(True)
            return

        self.current_language = lang_code
        self.translator.set_language(lang_code)
        self.retranslate_ui()

    def retranslate_ui(self):
        self.setWindowTitle(self.translator.get_string("app_title"))
        self._update_menu_texts() # This will also update checked state
        self.statusBar().showMessage(self.translator.get_string("status_ready", "Ready"))
        self.label.setText(self.translator.get_string("welcome_message", "Welcome!"))
        if hasattr(self, 'service_management_group'):
            self._update_service_control_texts()
        if sys.platform == "win32" and hasattr(self, 'autostart_checkbox'):
            self._update_autostart_control_texts()
        if hasattr(self, 'data_query_group'):
            self._update_data_query_control_texts()

        self.update_status_display() # To re-translate status string like "Running"

    # --- Service Control Methods ---
    def start_service(self):
        if self.service_process is None or self.service_process.poll() is not None:
            try:
                # Ensure sys.executable is used, helpful for venv
                command = [sys.executable, "-m", "uvicorn", "wms_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
                self.service_process = subprocess.Popen(command, cwd=self.project_root)
                self.update_status_display("Unknown") # Optimistically set, will be verified
                QTimer.singleShot(1000, self.check_service_status_threaded) # Check quickly
            except Exception as e:
                QMessageBox.critical(self, "Error", self.translator.get_string("error_service_start", error=str(e)))
                self.update_status_display("Stopped")
        else:
            QMessageBox.information(self, "Info", "Service is already running or starting.")
            self.check_service_status_threaded() # Re-check status if button pressed while running

    def stop_service(self):
        if self.service_process and self.service_process.poll() is None:
            try:
                self.service_process.terminate()
                try:
                    self.service_process.wait(timeout=3) # Wait for graceful shutdown
                except subprocess.TimeoutExpired:
                    self.service_process.kill() # Force kill if not stopped
                    self.service_process.wait() # Ensure it's killed
                self.service_process = None
                self.update_status_display("Stopped")
            except Exception as e:
                QMessageBox.critical(self, "Error", self.translator.get_string("error_service_stop", error=str(e)))
                self.update_status_display("Unknown") # Status is uncertain
        else:
            # QMessageBox.information(self, "Info", "Service is not running.")
            # If service is not managed by GUI but is running, this won't stop it.
            # Forcing a check can update UI if an external service was stopped.
            self.update_status_display("Stopped") # Assume stopped if no process
            self.check_service_status_threaded()


    def restart_service(self):
        # Stop first, then start after a delay
        if self.service_process and self.service_process.poll() is None:
            self.stop_service()
            QTimer.singleShot(1000, self.start_service) # Delay to allow port to free up
        else: # If not running, just start it
             self.start_service()


    # --- Status Checking ---
    def update_status_display(self, specific_status=None):
        if specific_status:
            self.service_status = specific_status

        # Translate status string (e.g., "Running", "Stopped")
        translated_status = self.translator.get_string(f"status_{self.service_status.lower()}", self.service_status)
        self.service_status_value_label.setText(translated_status)

        # Enable/disable buttons based on status
        if self.service_status == "Running":
            self.start_service_button.setEnabled(False)
            self.stop_service_button.setEnabled(True)
            self.restart_service_button.setEnabled(True)
        elif self.service_status == "Stopped":
            self.start_service_button.setEnabled(True)
            self.stop_service_button.setEnabled(False)
            self.restart_service_button.setEnabled(False) # Or True to just act as "Start"
        else: # Unknown or some intermediate state
            self.start_service_button.setEnabled(True) # Allow attempting to start
            self.stop_service_button.setEnabled(False) # Can't stop if unknown
            self.restart_service_button.setEnabled(False)


    def check_service_status_threaded(self):
        # Run the actual health check in a non-GUI thread
        status_thread = threading.Thread(target=self._check_service_health, daemon=True)
        status_thread.start()

    def _check_service_health(self):
        new_status = "Unknown"
        if self.service_process and self.service_process.poll() is None:
            # Process was started by this GUI and is (or should be) running
            try:
                response = requests.get("http://localhost:8000/", timeout=1) # FastAPI root endpoint
                if response.status_code == 200:
                    new_status = "Running"
                else:
                    # Running but not healthy, or endpoint changed
                    new_status = "Unknown"
            except requests.ConnectionError:
                # Likely starting up, or crashed without process ending
                new_status = "Unknown" if self.service_process.poll() is None else "Stopped"
            except requests.Timeout:
                new_status = "Unknown" # Unresponsive
        else:
            # No active GUI-managed process, try to see if an external one is running
            try:
                response = requests.get("http://localhost:8000/", timeout=0.5)
                if response.status_code == 200:
                    new_status = "Running" # External service
                else:
                    new_status = "Stopped"
            except (requests.ConnectionError, requests.Timeout):
                new_status = "Stopped"

        # Schedule UI update on the main thread
        # Important: Pass the determined new_status to update_status_display
        QTimer.singleShot(0, lambda s=new_status: self.update_status_display(s))

    # --- Data Query Logic ---
    def handle_query_button(self):
        tray_number = self.tray_number_input.text().strip()
        material_id = self.material_id_input.text().strip()

        params = {}
        if tray_number:
            params['tray_number'] = tray_number
        if material_id:
            params['material_id'] = material_id

        # Disable button during query? Maybe not necessary due to threading
        # self.query_button.setEnabled(False)
        threading.Thread(target=self._execute_query, args=(params,), daemon=True).start()

    def _execute_query(self, params):
        try:
            # Assuming service is running on localhost:8000
            # TODO: Check service status first or make base URL configurable
            api_url = "http://localhost:8000/locations/"
            response = requests.get(api_url, params=params, timeout=5)

            if response.status_code == 200:
                try:
                    data = response.json()
                    QTimer.singleShot(0, lambda d=data: self.populate_results_table(d))
                except json.JSONDecodeError:
                    QTimer.singleShot(0, lambda: self.show_error_message("Query Error", "Failed to parse server response."))
            else:
                error_message = response.text
                QTimer.singleShot(0, lambda: self.show_error_message(f"Query Failed: {response.status_code}", error_message))

        except requests.exceptions.RequestException as e:
            QTimer.singleShot(0, lambda: self.show_error_message("Query Connection Error", str(e)))
        # finally:
            # QTimer.singleShot(0, lambda: self.query_button.setEnabled(True))


    def populate_results_table(self, data: list):
        self.results_table.setRowCount(0) # Clear previous results
        if not data:
            # Optionally, show a message in the table or status bar if no results
            return

        self.results_table.setRowCount(len(data))
        for row, item in enumerate(data):
            item_id = QTableWidgetItem(str(item.get('id', '')))

            material_id_val = item.get('material_id')
            material_id_str = str(material_id_val) if material_id_val is not None else ""
            material_id_item = QTableWidgetItem(material_id_str)

            tray_number_item = QTableWidgetItem(str(item.get('tray_number', '')))

            timestamp_val = item.get('timestamp', '')
            # Format timestamp if needed, e.g., from ISO format to a more readable one
            # For now, just string representation
            timestamp_item = QTableWidgetItem(str(timestamp_val))

            status_val = item.get('status', '')
            # Translate status value for display
            translated_status = self.translator.get_string(f"status_{status_val.lower()}", status_val)
            status_item = QTableWidgetItem(translated_status)

            self.results_table.setItem(row, 0, item_id)
            self.results_table.setItem(row, 1, material_id_item)
            self.results_table.setItem(row, 2, tray_number_item)
            self.results_table.setItem(row, 3, timestamp_item)
            self.results_table.setItem(row, 4, status_item)

        # Optional: Resize columns to content
        # self.results_table.resizeColumnsToContents()

    def show_error_message(self, title, message):
        QMessageBox.critical(self, title, message)


    # --- Autostart Logic (Windows Specific) ---
    def create_autostart_script(self) -> bool:
        if sys.platform != "win32":
            return False

        python_exe = sys.executable # Path to current python interpreter
        # Ensure paths are quoted if they contain spaces
        python_exe_quoted = f'"{python_exe}"'
        project_root_quoted = f'"{self.project_root}"'

        # Command to run uvicorn; adjust if your main:app is elsewhere or needs different args
        # Using -m uvicorn ensures it uses the uvicorn in the current environment
        command = f'{python_exe_quoted} -m uvicorn wms_service.main:app --host 0.0.0.0 --port 8000'

        script_content = f"""@echo off
cd /D {project_root_quoted}
echo Starting WMS Service...
{command}
"""
        try:
            with open(self.autostart_script_path, "w") as f:
                f.write(script_content)
            return True
        except IOError as e:
            QMessageBox.critical(self, "Error", f"Failed to create autostart script: {e}")
            return False

    def load_autostart_setting(self):
        if sys.platform != "win32" or not hasattr(self, 'autostart_checkbox'):
            return

        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.autostart_registry_key_path, 0, winreg.KEY_READ)
            value, reg_type = winreg.QueryValueEx(key, self.autostart_value_name)
            winreg.CloseKey(key)
            if value == self.autostart_script_path:
                self.autostart_checkbox.setChecked(True)
            else:
                self.autostart_checkbox.setChecked(False)
        except FileNotFoundError:
            self.autostart_checkbox.setChecked(False) # Key or value doesn't exist
        except Exception as e:
            # Other errors reading registry
            print(f"Error loading autostart setting: {e}") # Log for debugging
            self.autostart_checkbox.setChecked(False)


    def toggle_autostart(self, checked):
        if sys.platform != "win32":
            return

        try:
            if checked:
                if not self.create_autostart_script():
                    self.autostart_checkbox.setChecked(False) # Revert checkbox
                    return

                # HKCU should generally be writable without admin, but CreateKey ensures path exists
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.autostart_registry_key_path)
                winreg.SetValueEx(key, self.autostart_value_name, 0, winreg.REG_SZ, self.autostart_script_path)
                winreg.CloseKey(key)
                QMessageBox.information(self, "Autostart", "Autostart enabled. The service will attempt to start on next login.")

            else: # Unchecked
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.autostart_registry_key_path, 0, winreg.KEY_WRITE)
                try:
                    winreg.DeleteValue(key, self.autostart_value_name)
                except FileNotFoundError:
                    pass # Value already deleted or never existed, which is fine
                winreg.CloseKey(key)
                QMessageBox.information(self, "Autostart", "Autostart disabled.")
                # Optionally delete self.autostart_script_path here if desired
                # try:
                #     if os.path.exists(self.autostart_script_path):
                #         os.remove(self.autostart_script_path)
                # except OSError as e:
                #     QMessageBox.warning(self, "Warning", f"Could not delete autostart script: {e}")

        except Exception as e:
            QMessageBox.critical(self, "Registry Error", f"Failed to update autostart setting: {e}\nEnsure you have permissions to modify the registry.")
            # Revert checkbox state if operation failed
            self.autostart_checkbox.setChecked(not checked)


    def closeEvent(self, event):
        confirm_title = self.translator.get_string("confirm_exit_title", "Confirm Exit")
        confirm_text = self.translator.get_string("confirm_exit_text", "Are you sure you want to exit?")

        reply = QMessageBox.question(self, confirm_title, confirm_text,
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.status_check_timer.stop() # Stop timer
            self.stop_service() # Attempt to stop the service if running
            event.accept()
        else:
            event.ignore()

if __name__ == '__main__':
    import os
    project_root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if project_root_path not in sys.path:
        sys.path.insert(0, project_root_path)

    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())
