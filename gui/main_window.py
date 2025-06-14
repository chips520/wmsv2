import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import subprocess
import threading
import time
import os
import json # For i18n

try:
    import requests # Assumed to be installed in the execution environment
except ImportError:
    # This allows the GUI to at least start and show a message if requests is missing
    messagebox.showerror("Dependency Error", "The 'requests' library is not installed. API features will not work.")
    requests = None


# --- Internationalization (Basic Setup) ---
# In a real app, this would be more robust, perhaps using gettext or a dedicated library.
# For now, we'll load from simple JSON files.
LOCALE_DIR = os.path.join(os.path.dirname(__file__), '..', 'locale') # Assumes locale is one level up from gui
DEFAULT_LANG = 'en'
current_lang = DEFAULT_LANG
translations = {}

def load_translations(lang):
    global translations
    try:
        # Corrected path construction for locale files
        locale_file_path = os.path.join(LOCALE_DIR, lang, 'LC_MESSAGES', 'gui.json')
        if not os.path.exists(locale_file_path):
            # Fallback to a common location if per-language subdir doesn't exist or is structured differently
            locale_file_path = os.path.join(LOCALE_DIR, f'{lang}.json')

        if os.path.exists(locale_file_path):
            with open(locale_file_path, 'r', encoding='utf-8') as f:
                translations = json.load(f)
        else:
            if lang != 'en': # Avoid error message for default English if its file is missing
                messagebox.showwarning("Localization Error", f"Translation file for '{lang}' not found at {locale_file_path}. Falling back to English.")
            # Fallback to English if the selected lang file is missing
            if lang != 'en' and DEFAULT_LANG not in translations: # ensure en is loaded if primary attempt fails
                 load_translations(DEFAULT_LANG) # Load default if specific language fails
    except Exception as e:
        messagebox.showerror("Localization Error", f"Could not load translations for {lang}: {e}")
        translations = {} # Reset to empty if error

def _(text_key):
    return translations.get(text_key, text_key) # Return key itself if not found

# --- Application ---
class AppServiceGUI:
    def __init__(self, master):
        self.master = master
        self.service_process = None
        self.api_base_url = "http://127.0.0.1:8000" # Default FastAPI port

        # Load initial translations
        load_translations(current_lang)
        master.title(_("WMS Service Manager"))

        # --- Styling ---
        style = ttk.Style()
        style.theme_use('clam') # Using a theme that tends to look better cross-platform

        # --- Frames ---
        control_frame = ttk.LabelFrame(master, text=_("Service Control"))
        control_frame.pack(padx=10, pady=10, fill="x")

        crud_frame = ttk.LabelFrame(master, text=_("Data Management (CRUD)"))
        crud_frame.pack(padx=10, pady=10, fill="both", expand=True)

        lang_frame = ttk.Frame(master)
        lang_frame.pack(padx=10, pady=5, fill="x")

        # --- Language Selection ---
        ttk.Label(lang_frame, text=_("Language:")).pack(side=tk.LEFT, padx=5)
        self.lang_var = tk.StringVar(value=current_lang)
        # In a real app, you might scan `locale` directory for available languages
        lang_options = ["en", "zh"]
        lang_menu = ttk.OptionMenu(lang_frame, self.lang_var, current_lang, *lang_options, command=self.change_language)
        lang_menu.pack(side=tk.LEFT)


        # --- Service Control Widgets ---
        self.start_button = ttk.Button(control_frame, text=_("Start Service"), command=self.start_service)
        self.start_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.stop_button = ttk.Button(control_frame, text=_("Stop Service"), command=self.stop_service, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.restart_button = ttk.Button(control_frame, text=_("Restart Service"), command=self.restart_service, state=tk.DISABLED)
        self.restart_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.status_label = ttk.Label(control_frame, text=_("Service Status: Not Running"))
        self.status_label.pack(side=tk.LEFT, padx=5, pady=5)

        # --- CRUD Widgets ---
        # Entry fields
        entry_frame = ttk.Frame(crud_frame)
        entry_frame.pack(pady=5, fill="x")

        ttk.Label(entry_frame, text=_("Item ID:")).grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.item_id_entry = ttk.Entry(entry_frame, width=30)
        self.item_id_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")

        ttk.Label(entry_frame, text=_("Tray ID:")).grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.tray_id_entry = ttk.Entry(entry_frame, width=30)
        self.tray_id_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")

        ttk.Label(entry_frame, text=_("Process Info (Opt):")).grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.process_info_entry = ttk.Entry(entry_frame, width=30)
        self.process_info_entry.grid(row=2, column=1, padx=5, pady=2, sticky="ew")

        ttk.Label(entry_frame, text=_("Location ID (for Get/Update/Delete):")).grid(row=0, column=2, padx=5, pady=2, sticky="w")
        self.location_id_entry = ttk.Entry(entry_frame, width=10)
        self.location_id_entry.grid(row=0, column=3, padx=5, pady=2, sticky="ew")

        entry_frame.columnconfigure(1, weight=1)
        entry_frame.columnconfigure(3, weight=1)


        # Buttons for CRUD
        button_frame = ttk.Frame(crud_frame)
        button_frame.pack(pady=5, fill="x")

        self.create_button = ttk.Button(button_frame, text=_("Create"), command=self.create_location)
        self.create_button.pack(side=tk.LEFT, padx=5)

        self.get_one_button = ttk.Button(button_frame, text=_("Get by ID"), command=self.get_location_by_id)
        self.get_one_button.pack(side=tk.LEFT, padx=5)

        self.get_all_button = ttk.Button(button_frame, text=_("Get All"), command=self.get_all_locations)
        self.get_all_button.pack(side=tk.LEFT, padx=5)

        self.update_button = ttk.Button(button_frame, text=_("Update by ID"), command=self.update_location)
        self.update_button.pack(side=tk.LEFT, padx=5)

        self.delete_button = ttk.Button(button_frame, text=_("Delete by ID"), command=self.delete_location)
        self.delete_button.pack(side=tk.LEFT, padx=5)

        self.clear_item_button = ttk.Button(button_frame, text=_("Clear Item by ID"), command=self.clear_location_item)
        self.clear_item_button.pack(side=tk.LEFT, padx=5)


        # Results display (Treeview)
        self.results_tree = ttk.Treeview(crud_frame, columns=("ID", "Item ID", "Tray ID", "Timestamp", "Process Info"), show="headings")
        self.results_tree.pack(pady=10, fill="both", expand=True)
        self.results_tree.heading("ID", text="ID")
        self.results_tree.heading("Item ID", text=_("Item ID"))
        self.results_tree.heading("Tray ID", text=_("Tray ID"))
        self.results_tree.heading("Timestamp", text=_("Timestamp"))
        self.results_tree.heading("Process Info", text=_("Process Info"))

        self.results_tree.column("ID", width=50, stretch=tk.NO)
        self.results_tree.column("Item ID", width=150)
        self.results_tree.column("Tray ID", width=150)
        self.results_tree.column("Timestamp", width=180)
        self.results_tree.column("Process Info", width=200)

        # Scrollbar for Treeview
        scrollbar = ttk.Scrollbar(self.results_tree, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.check_service_status_periodically()


    def change_language(self, lang_code):
        global current_lang
        current_lang = lang_code
        load_translations(lang_code)
        self.update_ui_texts()

    def update_ui_texts(self):
        self.master.title(_("WMS Service Manager"))
        # Update all widget texts that use _()
        # Control Frame
        self.master.winfo_children()[0].config(text=_("Service Control")) # control_frame
        self.start_button.config(text=_("Start Service"))
        self.stop_button.config(text=_("Stop Service"))
        self.restart_button.config(text=_("Restart Service"))
        self.status_label.config(text=_("Service Status: Not Running") if not self.service_process else _("Service Status: Running"))

        # CRUD Frame
        self.master.winfo_children()[1].config(text=_("Data Management (CRUD)")) # crud_frame

        # Entry Labels (assuming grid layout as in init)
        entry_frame = self.master.winfo_children()[1].winfo_children()[0] # crud_frame -> entry_frame
        entry_frame.winfo_children()[0].config(text=_("Item ID:")) # Label for item_id_entry
        entry_frame.winfo_children()[2].config(text=_("Tray ID:")) # Label for tray_id_entry
        entry_frame.winfo_children()[4].config(text=_("Process Info (Opt):")) # Label for process_info_entry
        entry_frame.winfo_children()[6].config(text=_("Location ID (for Get/Update/Delete):")) # Label for location_id_entry

        # CRUD Buttons
        button_frame = self.master.winfo_children()[1].winfo_children()[1] # crud_frame -> button_frame
        button_frame.winfo_children()[0].config(text=_("Create"))
        button_frame.winfo_children()[1].config(text=_("Get by ID"))
        button_frame.winfo_children()[2].config(text=_("Get All"))
        button_frame.winfo_children()[3].config(text=_("Update by ID"))
        button_frame.winfo_children()[4].config(text=_("Delete by ID"))
        button_frame.winfo_children()[5].config(text=_("Clear Item by ID"))

        # Treeview Headings
        self.results_tree.heading("Item ID", text=_("Item ID"))
        self.results_tree.heading("Tray ID", text=_("Tray ID"))
        self.results_tree.heading("Timestamp", text=_("Timestamp"))
        self.results_tree.heading("Process Info", text=_("Process Info"))

        # Language Frame Label
        lang_frame = self.master.winfo_children()[2] # lang_frame
        lang_frame.winfo_children()[0].config(text=_("Language:"))


    def _execute_command(self, command_list, cwd=None): # Added cwd parameter
        try:
            # For Windows, prevent console window from popping up for uvicorn
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
            # Pass cwd to Popen if specified
            process = subprocess.Popen(command_list, startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW, cwd=cwd)
            return process
        except FileNotFoundError:
            messagebox.showerror(_("Error"), _("Command (uvicorn or python) not found. Ensure it's in your PATH."))
            return None
        except Exception as e:
            messagebox.showerror(_("Error"), f"{_('Failed to execute command')}: {e}")
            return None

    def start_service(self):
        if self.service_process and self.service_process.poll() is None:
            messagebox.showinfo(_("Info"), _("Service is already running."))
            return

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        app_module = "app.main:app"

        # Pass project_root as cwd to ensure uvicorn runs in the correct directory
        self.service_process = self._execute_command(
            ["uvicorn", app_module, "--host", "127.0.0.1", "--port", "8000"],
            cwd=project_root
        )

        if self.service_process:
            self.status_label.config(text=_("Service Status: Starting..."))
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.restart_button.config(state=tk.NORMAL)
            self.master.after(2000, self.check_service_status)


    def stop_service(self):
        if self.service_process and self.service_process.poll() is None:
            try:
                self.service_process.terminate()
                self.service_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.service_process.kill()
                messagebox.showinfo(_("Info"), _("Service forcefully stopped."))
            except Exception as e:
                messagebox.showerror(_("Error"), f"{_('Error stopping service')}: {e}")
            self.service_process = None
            self.status_label.config(text=_("Service Status: Stopped"))
        else:
            self.status_label.config(text=_("Service Status: Not Running"))

        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.restart_button.config(state=tk.DISABLED)

    def restart_service(self):
        self.stop_service()
        self.master.after(1000, self.start_service)


    def check_service_status(self):
        if self.service_process and self.service_process.poll() is None:
            try:
                if not requests: raise Exception("Requests library not available.")
                response = requests.get(f"{self.api_base_url}/health", timeout=1)
                if response.status_code == 200:
                    self.status_label.config(text=_("Service Status: Running"))
                    self.start_button.config(state=tk.DISABLED)
                    self.stop_button.config(state=tk.NORMAL)
                    self.restart_button.config(state=tk.NORMAL)
                else:
                    self.status_label.config(text=_("Service Status: Error/Unresponsive"))
            except requests.exceptions.ConnectionError:
                self.status_label.config(text=_("Service Status: Starting/Not Ready"))
            except Exception as e:
                self.status_label.config(text=_("Service Status: Error checking"))
                print(f"Error checking service status: {e}")
        elif self.service_process and self.service_process.poll() is not None:
            self.status_label.config(text=_("Service Status: Stopped (Terminated Unexpectedly)"))
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.restart_button.config(state=tk.DISABLED)
            self.service_process = None
        else:
             self.status_label.config(text=_("Service Status: Not Running"))
             self.start_button.config(state=tk.NORMAL)
             self.stop_button.config(state=tk.DISABLED)
             self.restart_button.config(state=tk.DISABLED)


    def check_service_status_periodically(self):
        self.check_service_status()
        self.master.after(5000, self.check_service_status_periodically)


    def _make_api_request(self, method, endpoint, json_data=None, params=None):
        if not requests:
            messagebox.showerror(_("Error"), _("'requests' library not available. Cannot perform API operations."))
            return None
        try:
            url = f"{self.api_base_url}{endpoint}"
            response = requests.request(method, url, json=json_data, params=params, timeout=10)
            response.raise_for_status()

            if response.status_code == 204:
                return {}
            return response.json()
        except requests.exceptions.HTTPError as e:
            detail = e.response.json().get("detail", e.response.text) if e.response.content else str(e)
            messagebox.showerror(_("API Error"), f"{_('Failed')} ({e.response.status_code}): {detail}")
        except requests.exceptions.ConnectionError:
            messagebox.showerror(_("Connection Error"), _("Failed to connect to the API service. Is it running?"))
        except requests.exceptions.Timeout:
            messagebox.showerror(_("Timeout Error"), _("The API request timed out."))
        except Exception as e:
            messagebox.showerror(_("Error"), f"{_('An unexpected error occurred')}: {e}")
        return None

    def _clear_entries(self):
        self.item_id_entry.delete(0, tk.END)
        self.tray_id_entry.delete(0, tk.END)
        self.process_info_entry.delete(0, tk.END)
        self.location_id_entry.delete(0, tk.END)

    def _display_results(self, data):
        for i in self.results_tree.get_children():
            self.results_tree.delete(i)

        if not data:
            return

        if not isinstance(data, list):
            data = [data]

        for item in data:
            item_id = item.get('item_id', 'N/A')
            tray_id = item.get('tray_id', 'N/A')
            timestamp = item.get('timestamp', 'N/A')
            process_info = item.get('process_info', '')
            loc_id = item.get('id', 'N/A')
            self.results_tree.insert("", tk.END, values=(loc_id, item_id, tray_id, timestamp, process_info))


    def create_location(self):
        item_id = self.item_id_entry.get()
        tray_id = self.tray_id_entry.get()
        process_info = self.process_info_entry.get()

        if not item_id or not tray_id:
            messagebox.showwarning(_("Input Error"), _("Item ID and Tray ID are required."))
            return

        payload = {"item_id": item_id, "tray_id": tray_id}
        if process_info:
            payload["process_info"] = process_info

        result = self._make_api_request("POST", "/locations/", json_data=payload)
        if result:
            messagebox.showinfo(_("Success"), _("Location created successfully!"))
            self._display_results(result)
            self._clear_entries()
            self.get_all_locations()

    def get_location_by_id(self):
        loc_id_str = self.location_id_entry.get()
        if not loc_id_str.isdigit():
            messagebox.showwarning(_("Input Error"), _("Valid Location ID (number) is required."))
            return

        result = self._make_api_request("GET", f"/locations/id/{loc_id_str}")
        if result:
            self._display_results(result)
        else:
            self._display_results([])

    def get_all_locations(self):
        result = self._make_api_request("GET", "/locations/?limit=1000")
        if result:
            self._display_results(result)
        else:
            self._display_results([])


    def update_location(self):
        loc_id_str = self.location_id_entry.get()
        if not loc_id_str.isdigit():
            messagebox.showwarning(_("Input Error"), _("Valid Location ID (number) for update is required."))
            return

        payload = {}
        item_id = self.item_id_entry.get()
        tray_id = self.tray_id_entry.get()
        process_info = self.process_info_entry.get()

        if item_id: payload["item_id"] = item_id
        if tray_id: payload["tray_id"] = tray_id
        if process_info: payload["process_info"] = process_info

        if not payload:
            messagebox.showwarning(_("Input Error"), _("At least one field (Item ID, Tray ID, Process Info) must be provided for update."))
            return

        result = self._make_api_request("POST", f"/locations/update/{loc_id_str}/", json_data=payload)
        if result:
            messagebox.showinfo(_("Success"), _("Location updated successfully!"))
            self.get_all_locations()

    def delete_location(self):
        loc_id_str = self.location_id_entry.get()
        if not loc_id_str.isdigit():
            messagebox.showwarning(_("Input Error"), _("Valid Location ID (number) for delete is required."))
            return

        if not messagebox.askyesno(_("Confirm Delete"), _("Are you sure you want to delete location ID {}?").format(loc_id_str)):
            return

        result = self._make_api_request("POST", f"/locations/delete/{loc_id_str}/")
        if result is not None:
            messagebox.showinfo(_("Success"), _("Location deleted successfully!"))
            self.get_all_locations()

    def clear_location_item(self):
        loc_id_str = self.location_id_entry.get()
        if not loc_id_str.isdigit():
            messagebox.showwarning(_("Input Error"), _("Valid Location ID (number) to clear is required."))
            return

        if not messagebox.askyesno(_("Confirm Clear"), _("Are you sure you want to clear the item from location ID {}?").format(loc_id_str)):
            return

        result = self._make_api_request("POST", f"/locations/clear/{loc_id_str}/")
        if result:
            messagebox.showinfo(_("Success"), _("Location item cleared successfully!"))
            self.get_all_locations()

# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    # Create dummy locale files for testing if they don't exist
    # This is for dev convenience; in prod they should be packaged.
    os.makedirs(os.path.join(LOCALE_DIR, 'en', 'LC_MESSAGES'), exist_ok=True)
    os.makedirs(os.path.join(LOCALE_DIR, 'zh', 'LC_MESSAGES'), exist_ok=True)

    dummy_en_translations = {
        "WMS Service Manager": "WMS Service Manager", "Service Control": "Service Control",
        "Start Service": "Start Service", "Stop Service": "Stop Service", "Restart Service": "Restart Service",
        "Service Status: Not Running": "Service Status: Not Running", "Service Status: Running": "Service Status: Running",
        "Service Status: Starting...": "Service Status: Starting...", "Service Status: Stopped": "Service Status: Stopped",
        "Service Status: Error/Unresponsive": "Service Status: Error/Unresponsive",
        "Service Status: Starting/Not Ready": "Service Status: Starting/Not Ready",
        "Service Status: Error checking": "Service Status: Error checking",
        "Service Status: Stopped (Terminated Unexpectedly)": "Service Status: Stopped (Terminated Unexpectedly)",
        "Data Management (CRUD)": "Data Management (CRUD)", "Item ID:": "Item ID:", "Tray ID:": "Tray ID:",
        "Process Info (Opt):": "Process Info (Opt):", "Location ID (for Get/Update/Delete):": "Location ID (for Get/Update/Delete):",
        "Create": "Create", "Get by ID": "Get by ID", "Get All": "Get All", "Update by ID": "Update by ID", "Delete by ID": "Delete by ID",
        "Clear Item by ID": "Clear Item by ID", "Timestamp": "Timestamp", "Process Info": "Process Info",
        "Language:":"Language:", "Error": "Error", "Info": "Info", "Success": "Success", "Input Error": "Input Error", "API Error": "API Error",
        "Connection Error": "Connection Error", "Timeout Error": "Timeout Error", "Confirm Delete": "Confirm Delete", "Confirm Clear": "Confirm Clear",
        "Failed to connect to the API service. Is it running?": "Failed to connect to the API service. Is it running?",
        "Command (uvicorn or python) not found. Ensure it's in your PATH.": "Command (uvicorn or python) not found. Ensure it's in your PATH.",
        "Failed to execute command": "Failed to execute command", "Service is already running.": "Service is already running.",
        "Item ID and Tray ID are required.": "Item ID and Tray ID are required.", "Location created successfully!": "Location created successfully!",
        "Valid Location ID (number) is required.": "Valid Location ID (number) is required.",
        "At least one field (Item ID, Tray ID, Process Info) must be provided for update.": "At least one field (Item ID, Tray ID, Process Info) must be provided for update.",
        "Location updated successfully!": "Location updated successfully!",
        "Are you sure you want to delete location ID {}?": "Are you sure you want to delete location ID {}?",
        "Location deleted successfully!": "Location deleted successfully!",
        "Are you sure you want to clear the item from location ID {}?": "Are you sure you want to clear the item from location ID {}?",
        "Location item cleared successfully!": "Location item cleared successfully!",
        "Error stopping service": "Error stopping service", "Service forcefully stopped.": "Service forcefully stopped.",
        "'requests' library not available. Cannot perform API operations.": "'requests' library not available. Cannot perform API operations.",
        "An unexpected error occurred": "An unexpected error occurred", "Failed": "Failed",
        "Localization Error": "Localization Error", "Translation file for '{}' not found at {}. Falling back to English.": "Translation file for '{}' not found at {}. Falling back to English.",
        "Could not load translations for {}": "Could not load translations for {}"
    }
    en_path = os.path.join(LOCALE_DIR, 'en', 'LC_MESSAGES', 'gui.json')
    if not os.path.exists(en_path):
        with open(en_path, 'w', encoding='utf-8') as f_en:
            json.dump(dummy_en_translations, f_en, ensure_ascii=False, indent=4)

    dummy_zh_translations = {
        "WMS Service Manager": "WMS 服务管理器", "Service Control": "服务控制",
        "Start Service": "启动服务", "Stop Service": "停止服务", "Restart Service": "重启服务",
        "Service Status: Not Running": "服务状态: 未运行", "Service Status: Running": "服务状态: 运行中",
        "Service Status: Starting...": "服务状态: 启动中...", "Service Status: Stopped": "服务状态: 已停止",
        "Service Status: Error/Unresponsive": "服务状态: 错误/无响应",
        "Service Status: Starting/Not Ready": "服务状态: 启动中/未就绪",
        "Service Status: Error checking": "服务状态: 检查出错",
        "Service Status: Stopped (Terminated Unexpectedly)": "服务状态: 已停止 (异常终止)",
        "Data Management (CRUD)": "数据管理 (CRUD)", "Item ID:": "物料ID:", "Tray ID:": "料盘ID:",
        "Process Info (Opt):": "工序信息 (可选):", "Location ID (for Get/Update/Delete):": "位置ID (查/改/删):",
        "Create": "创建", "Get by ID": "按ID查询", "Get All": "查询全部", "Update by ID": "按ID更新", "Delete by ID": "按ID删除",
        "Clear Item by ID": "清除物料 (按ID)", "Timestamp": "时间戳", "Process Info": "工序信息",
        "Language:":"语言:", "Error": "错误", "Info": "信息", "Success": "成功", "Input Error": "输入错误", "API Error": "API 错误",
        "Connection Error": "连接错误", "Timeout Error": "超时错误", "Confirm Delete": "确认删除", "Confirm Clear": "确认清除",
        "Failed to connect to the API service. Is it running?": "无法连接到API服务。服务是否正在运行？",
        "Command (uvicorn or python) not found. Ensure it's in your PATH.": "找不到命令 (uvicorn 或 python)。请确保它在您的 PATH 环境变量中。",
        "Failed to execute command": "执行命令失败", "Service is already running.": "服务已经在运行。",
        "Item ID and Tray ID are required.": "物料ID和料盘ID是必填项。", "Location created successfully!": "位置创建成功！",
        "Valid Location ID (number) is required.": "需要有效的位置ID (数字)。",
        "At least one field (Item ID, Tray ID, Process Info) must be provided for update.": "更新操作至少需要提供一个字段 (物料ID, 料盘ID, 工序信息)。",
        "Location updated successfully!": "位置更新成功！",
        "Are you sure you want to delete location ID {}?": "您确定要删除位置ID {}吗？",
        "Location deleted successfully!": "位置删除成功！",
        "Are you sure you want to clear the item from location ID {}?": "您确定要清除位置ID {} 的物料信息吗？",
        "Location item cleared successfully!": "位置物料信息清除成功！",
        "Error stopping service": "停止服务时出错", "Service forcefully stopped.": "服务已强制停止。",
        "'requests' library not available. Cannot perform API operations.": "'requests' 库不可用。无法执行API操作。",
        "An unexpected error occurred": "发生意外错误", "Failed": "失败",
        "Localization Error": "本地化错误", "Translation file for '{}' not found at {}. Falling back to English.": "未找到 '{}' 的翻译文件 (路径: {})。将回退到英文。",
        "Could not load translations for {}": "无法加载 {} 的翻译"
    }
    zh_path = os.path.join(LOCALE_DIR, 'zh', 'LC_MESSAGES', 'gui.json')
    if not os.path.exists(zh_path):
        with open(zh_path, 'w', encoding='utf-8') as f_zh:
            json.dump(dummy_zh_translations, f_zh, ensure_ascii=False, indent=4)

    app = AppServiceGUI(root)
    root.mainloop()
