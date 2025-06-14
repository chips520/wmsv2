import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import subprocess
import time
import os
import json

try:
    import requests
except ImportError:
    messagebox.showerror("Dependency Error", "The 'requests' library is not installed. API features will not work.")
    requests = None

LOCALE_DIR = os.path.join(os.path.dirname(__file__), '..', 'locale')
DEFAULT_LANG = 'en'
current_lang = DEFAULT_LANG
translations = {}

def load_translations(lang):
    global translations
    try:
        locale_file_path = os.path.join(LOCALE_DIR, lang, 'LC_MESSAGES', 'gui.json')
        if not os.path.exists(locale_file_path): # Fallback for simple structure
            locale_file_path = os.path.join(LOCALE_DIR, f'{lang}.json')

        if os.path.exists(locale_file_path):
            with open(locale_file_path, 'r', encoding='utf-8') as f:
                translations = json.load(f)
        else:
            if lang != 'en':
                messagebox.showwarning("Localization Error", f"Translation file for '{lang}' not found at {locale_file_path}. Falling back to English.")
            if lang != 'en' and current_lang != DEFAULT_LANG: # Load default if specific language fails and it's not already default
                 load_translations(DEFAULT_LANG)
    except Exception as e:
        messagebox.showerror("Localization Error", f"Could not load translations for {lang}: {e}")
        translations = {}

def _(text_key):
    return translations.get(text_key, text_key)

class AppServiceGUI:
    SERVICE_NAME = "WMSServiceHTTP"
    API_BASE_URL = "http://127.0.0.1:8000"

    def __init__(self, master):
        self.master = master
        load_translations(current_lang)
        master.title(_("WMS Service Manager"))
        master.geometry("850x650") # Slightly wider for new fields

        style = ttk.Style()
        style.theme_use('clam')

        # --- Frames ---
        top_frame = ttk.Frame(master)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        service_control_frame = ttk.LabelFrame(top_frame, text=_("Service Control"))
        service_control_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tray_query_frame = ttk.LabelFrame(top_frame, text=_("Tray Operations / Query"))
        tray_query_frame.pack(side=tk.LEFT, fill=tk.X, padx=10)

        crud_frame = ttk.LabelFrame(master, text=_("Slot Content Management"))
        crud_frame.pack(padx=10, pady=10, fill="both", expand=True)

        lang_frame = ttk.Frame(master)
        lang_frame.pack(padx=10, pady=5, fill="x", side=tk.BOTTOM)

        # --- Language Selection ---
        ttk.Label(lang_frame, text=_("Language:")).pack(side=tk.LEFT, padx=5)
        self.lang_var = tk.StringVar(value=current_lang)
        lang_options = ["en", "zh"]
        lang_menu = ttk.OptionMenu(lang_frame, self.lang_var, current_lang, *lang_options, command=self.change_language)
        lang_menu.pack(side=tk.LEFT)

        # --- Service Control Widgets ---
        self.start_button = ttk.Button(service_control_frame, text=_("Start Service"), command=self.start_service_command)
        self.start_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.stop_button = ttk.Button(service_control_frame, text=_("Stop Service"), command=self.stop_service_command)
        self.stop_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.restart_button = ttk.Button(service_control_frame, text=_("Restart Service"), command=self.restart_service_command)
        self.restart_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.status_label = ttk.Label(service_control_frame, text=_("Service Status: Unknown"), width=30)
        self.status_label.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)

        # --- Tray Query/Selection ---
        ttk.Label(tray_query_frame, text=_("Tray ID:")).pack(side=tk.LEFT, padx=5, pady=2)
        self.query_tray_id_entry = ttk.Entry(tray_query_frame, width=15)
        self.query_tray_id_entry.pack(side=tk.LEFT, padx=5, pady=2)
        self.get_tray_slots_button = ttk.Button(tray_query_frame, text=_("Get Tray Slots"), command=self.get_locations_for_selected_tray)
        self.get_tray_slots_button.pack(side=tk.LEFT, padx=5, pady=2)


        # --- CRUD Input Fields (Slot Content Management) ---
        entry_frame = ttk.Frame(crud_frame)
        entry_frame.pack(pady=5, fill="x")

        ttk.Label(entry_frame, text=_("Target Tray ID:")).grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.op_tray_id_entry = ttk.Entry(entry_frame, width=20)
        self.op_tray_id_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")

        ttk.Label(entry_frame, text=_("Target Slot Index:")).grid(row=0, column=2, padx=5, pady=2, sticky="w")
        self.op_slot_index_entry = ttk.Entry(entry_frame, width=10)
        self.op_slot_index_entry.grid(row=0, column=3, padx=5, pady=2, sticky="ew")

        ttk.Label(entry_frame, text=_("Item ID (for place/update):")).grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.op_item_id_entry = ttk.Entry(entry_frame, width=20)
        self.op_item_id_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")

        ttk.Label(entry_frame, text=_("Process Info (Opt):")).grid(row=1, column=2, padx=5, pady=2, sticky="w")
        self.op_process_info_entry = ttk.Entry(entry_frame, width=20)
        self.op_process_info_entry.grid(row=1, column=3, padx=5, pady=2, sticky="ew")

        entry_frame.columnconfigure(1, weight=1)
        entry_frame.columnconfigure(3, weight=1)

        # --- CRUD Buttons (Slot Content Management) ---
        button_frame = ttk.Frame(crud_frame)
        button_frame.pack(pady=5, fill="x")

        self.place_item_button = ttk.Button(button_frame, text=_("Place/Update Item"), command=self.place_or_update_item)
        self.place_item_button.pack(side=tk.LEFT, padx=5)
        self.clear_slot_button = ttk.Button(button_frame, text=_("Clear Slot Item"), command=self.clear_slot_item_command)
        self.clear_slot_button.pack(side=tk.LEFT, padx=5)
        self.get_specific_slot_button = ttk.Button(button_frame, text=_("Get Specific Slot"), command=self.get_specific_slot_command)
        self.get_specific_slot_button.pack(side=tk.LEFT, padx=5)
        self.find_empty_slot_button = ttk.Button(button_frame, text=_("Find Empty Slot on Tray"), command=self.find_empty_slot_on_tray_command)
        self.find_empty_slot_button.pack(side=tk.LEFT, padx=5)


        # --- Results Display (Treeview) ---
        self.results_tree = ttk.Treeview(crud_frame, columns=("DB_ID", "Tray ID", "Slot Index", "Item ID", "Timestamp", "Process Info"), show="headings")
        self.results_tree.pack(pady=10, fill="both", expand=True)
        self.results_tree.heading("DB_ID", text=_("Loc. DB ID"))
        self.results_tree.heading("Tray ID", text=_("Tray ID"))
        self.results_tree.heading("Slot Index", text=_("Slot Index"))
        self.results_tree.heading("Item ID", text=_("Item ID"))
        self.results_tree.heading("Timestamp", text=_("Timestamp"))
        self.results_tree.heading("Process Info", text=_("Process Info"))

        self.results_tree.column("DB_ID", width=70, stretch=tk.NO)
        self.results_tree.column("Tray ID", width=100)
        self.results_tree.column("Slot Index", width=70)
        self.results_tree.column("Item ID", width=150)
        self.results_tree.column("Timestamp", width=180)
        self.results_tree.column("Process Info", width=150)

        scrollbar = ttk.Scrollbar(self.results_tree, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.results_tree.bind("<Double-1>", self.on_tree_double_click)


        self.check_service_status_periodically()

    def on_tree_double_click(self, event):
        item_iid = self.results_tree.focus() # Get selected item's internal ID
        if not item_iid: return

        item_values = self.results_tree.item(item_iid, 'values')
        if not item_values or len(item_values) < 4: return # Expecting at least DB_ID, Tray_ID, Slot_Index, Item_ID

        # Populate operation fields from selected row
        self.op_tray_id_entry.delete(0, tk.END)
        self.op_tray_id_entry.insert(0, item_values[1]) # Tray ID

        self.op_slot_index_entry.delete(0, tk.END)
        self.op_slot_index_entry.insert(0, item_values[2]) # Slot Index

        self.op_item_id_entry.delete(0, tk.END)
        self.op_item_id_entry.insert(0, item_values[3]) # Item ID

        if len(item_values) >=6 : # Process Info
            self.op_process_info_entry.delete(0, tk.END)
            self.op_process_info_entry.insert(0, item_values[5])


    def change_language(self, lang_code): # Identical to previous
        global current_lang
        current_lang = lang_code
        load_translations(lang_code)
        self.update_ui_texts()

    def update_ui_texts(self): # Needs updates for new/changed widgets
        self.master.title(_("WMS Service Manager"))

        # Top Frame children
        top_frame_children = self.master.winfo_children()[0].winfo_children()
        top_frame_children[0].config(text=_("Service Control")) # service_control_frame
        top_frame_children[1].config(text=_("Tray Operations / Query")) # tray_query_frame

        # Service Control Frame children
        sc_children = top_frame_children[0].winfo_children()
        sc_children[0].config(text=_("Start Service")) # start_button
        sc_children[1].config(text=_("Stop Service"))  # stop_button
        sc_children[2].config(text=_("Restart Service"))# restart_button
        # status_label text is handled in check_service_status

        # Tray Query Frame children
        tq_children = top_frame_children[1].winfo_children()
        tq_children[0].config(text=_("Tray ID:")) # Label for query_tray_id_entry
        tq_children[2].config(text=_("Get Tray Slots")) # get_tray_slots_button

        # CRUD Frame (Slot Content Management)
        self.master.winfo_children()[1].config(text=_("Slot Content Management")) # crud_frame
        crud_frame_children = self.master.winfo_children()[1].winfo_children()

        entry_frame = crud_frame_children[0]
        entry_frame.winfo_children()[0].config(text=_("Target Tray ID:"))
        entry_frame.winfo_children()[2].config(text=_("Target Slot Index:"))
        entry_frame.winfo_children()[4].config(text=_("Item ID (for place/update):"))
        entry_frame.winfo_children()[6].config(text=_("Process Info (Opt):"))

        button_frame = crud_frame_children[1]
        button_frame.winfo_children()[0].config(text=_("Place/Update Item"))
        button_frame.winfo_children()[1].config(text=_("Clear Slot Item"))
        button_frame.winfo_children()[2].config(text=_("Get Specific Slot"))
        button_frame.winfo_children()[3].config(text=_("Find Empty Slot on Tray"))

        # Treeview Headings
        self.results_tree.heading("DB_ID", text=_("Loc. DB ID"))
        self.results_tree.heading("Tray ID", text=_("Tray ID"))
        self.results_tree.heading("Slot Index", text=_("Slot Index"))
        self.results_tree.heading("Item ID", text=_("Item ID"))
        self.results_tree.heading("Timestamp", text=_("Timestamp"))
        self.results_tree.heading("Process Info", text=_("Process Info"))

        # Language Frame Label
        lang_frame = self.master.winfo_children()[2] # lang_frame
        lang_frame.winfo_children()[0].config(text=_("Language:"))


    # Service control methods (_run_sc_command, start_service_command, etc.) are identical to previous version
    def _run_sc_command(self, action, service_name):
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            result = subprocess.run(['sc', action, service_name], capture_output=True, text=True, check=False, startupinfo=startupinfo, creationflags=subprocess.CREATE_NO_WINDOW)
            if result.returncode == 0 or "SUCCESS" in result.stdout or "PENDING" in result.stdout :
                 if "PENDING" in result.stdout or "PENDING" in result.stderr : return "PENDING"
                 return "SUCCESS"
            else:
                error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
                if "service does not exist" in error_msg.lower(): messagebox.showerror(_("Service Error"), _("Service '{}' not found. Please ensure it is installed.").format(service_name))
                elif "Access is denied" in error_msg or "OpenService FAILED 5" in error_msg : messagebox.showerror(_("Permission Error"), _("Access Denied. Please run the GUI as Administrator to manage services."))
                else: messagebox.showerror(_("Service Error"), f"{_('Failed to')} {action} {_('service')} '{service_name}':\n{error_msg}")
                return "FAILED"
        except FileNotFoundError: messagebox.showerror(_("Error"), _("'sc.exe' not found. This GUI needs to run on Windows with System32 in PATH.")); return "FAILED"
        except Exception as e: messagebox.showerror(_("Error"), f"{_('An unexpected error occurred interacting with service')}: {e}"); return "FAILED"

    def start_service_command(self): self._run_sc_command('start', self.SERVICE_NAME); self.master.after(1000, self.check_service_status)
    def stop_service_command(self): self._run_sc_command('stop', self.SERVICE_NAME); self.master.after(1000, self.check_service_status)
    def restart_service_command(self):
        if self._run_sc_command('stop', self.SERVICE_NAME) != "FAILED": self.master.after(3000, lambda: self._run_sc_command('start', self.SERVICE_NAME))
        self.master.after(5000, self.check_service_status)

    def get_service_status_from_sc(self):
        try:
            startupinfo = subprocess.STARTUPINFO(); startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW; startupinfo.wShowWindow = subprocess.SW_HIDE
            result = subprocess.run(['sc', 'query', self.SERVICE_NAME], capture_output=True, text=True, check=False, startupinfo=startupinfo, creationflags=subprocess.CREATE_NO_WINDOW)
            if result.returncode != 0 and "service does not exist" in result.stdout.lower() + result.stderr.lower(): return "NOT INSTALLED"
            output = result.stdout.lower()
            if "state" not in output:
                if "failed 1060" in output or "does not exist" in output : return "NOT INSTALLED"
                return "UNKNOWN"
            for line in result.stdout.splitlines():
                if "STATE" in line:
                    state_val = line.split(":")[1].strip().split(" ")[0]
                    if state_val == "1": return "STOPPED";  # 1 = STOPPED
                    if state_val == "2": return "START_PENDING"
                    if state_val == "3": return "STOP_PENDING"
                    if state_val == "4": return "RUNNING"
                    return "UNKNOWN_STATE_" + state_val
            return "UNKNOWN"
        except FileNotFoundError: return "SC_NOT_FOUND"
        except Exception: return "QUERY_ERROR"

    def check_service_status(self): # Largely same, minor text update
        status = self.get_service_status_from_sc()
        status_text_key = f"Service Status: {status.replace('_', ' ').title()}" # Generic key
        status_text_val = _(status_text_key) # Try to translate "Service Status: Running" etc.

        # If specific translation not found, build it more manually
        if status_text_val == status_text_key :
            status_desc = _(status.replace('_', ' ').title()) # Translate "Running", "Stopped"
            if status_desc == status.replace('_', ' ').title() and status != "UNKNOWN" : # if status itself is not translated
                 status_desc = status # use raw status if no translation
            status_text_val = f"{_('Service Status:')} {status_desc}"


        if status == "RUNNING":
            if requests:
                try:
                    response = requests.get(f"{self.API_BASE_URL}/health", timeout=1)
                    status_text_val += " | API OK" if response.status_code == 200 else " | API Error"
                except requests.exceptions.ConnectionError: status_text_val += " | API Unreachable"
                except Exception: status_text_val += " | API Check Error"
            else: status_text_val += _(" | API Check Skipped (requests missing)")
            self.start_button.config(state=tk.DISABLED); self.stop_button.config(state=tk.NORMAL); self.restart_button.config(state=tk.NORMAL)
        elif status == "STOPPED":
            self.start_button.config(state=tk.NORMAL); self.stop_button.config(state=tk.DISABLED); self.restart_button.config(state=tk.DISABLED)
        elif status == "NOT INSTALLED" or status == "SC_NOT_FOUND":
            self.start_button.config(state=tk.DISABLED); self.stop_button.config(state=tk.DISABLED); self.restart_button.config(state=tk.DISABLED)
        elif status in ["START_PENDING", "STOP_PENDING"]:
            self.start_button.config(state=tk.DISABLED); self.stop_button.config(state=tk.DISABLED); self.restart_button.config(state=tk.DISABLED)
        else: # UNKNOWN, QUERY_ERROR
            self.start_button.config(state=tk.NORMAL); self.stop_button.config(state=tk.NORMAL); self.restart_button.config(state=tk.NORMAL)
        self.status_label.config(text=status_text_val)

    def check_service_status_periodically(self): self.check_service_status(); self.master.after(5000, self.check_service_status_periodically)

    # --- CRUD Methods (Updated for new API structure) ---
    def _make_api_request(self, method, endpoint, json_data=None, params=None): # Identical
        if not requests: messagebox.showerror(_("Error"), _("'requests' library not available. Cannot perform API operations.")); return None
        try:
            url = f"{self.API_BASE_URL}{endpoint}"
            response = requests.request(method, url, json=json_data, params=params, timeout=10)
            response.raise_for_status()
            if response.status_code == 204: return {} # Success with no content
            return response.json()
        except requests.exceptions.HTTPError as e:
            detail = str(e)
            try: detail = e.response.json().get("detail", e.response.text)
            except: pass # Keep original detail if parsing fails
            messagebox.showerror(_("API Error"), f"{_('Failed')} ({e.response.status_code}): {detail}")
        except requests.exceptions.ConnectionError: messagebox.showerror(_("Connection Error"), _("Failed to connect to the API service. Is it running and responsive?"))
        except requests.exceptions.Timeout: messagebox.showerror(_("Timeout Error"), _("The API request timed out."))
        except Exception as e: messagebox.showerror(_("Error"), f"{_('An unexpected error occurred')}: {e}")
        return None

    def _clear_op_entries(self):
        self.op_tray_id_entry.delete(0, tk.END)
        self.op_slot_index_entry.delete(0, tk.END)
        self.op_item_id_entry.delete(0, tk.END)
        self.op_process_info_entry.delete(0, tk.END)

    def _display_results(self, data): # Identical
        for i in self.results_tree.get_children(): self.results_tree.delete(i)
        if not data: return
        if not isinstance(data, list): data = [data]
        for item in data:
            self.results_tree.insert("", tk.END, values=(
                item.get('id', 'N/A'), item.get('tray_id', 'N/A'),
                item.get('slot_index', 'N/A'), item.get('item_id', 'N/A'),
                item.get('timestamp', 'N/A'), item.get('process_info', '')
            ))

    def get_locations_for_selected_tray(self):
        tray_id = self.query_tray_id_entry.get()
        if not tray_id: messagebox.showwarning(_("Input Error"), _("Please enter a Tray ID to query.")); return

        result = self._make_api_request("GET", f"/trays/{tray_id}/locations/")
        self._display_results(result if result else [])
        if result is None: # API error already shown
             messagebox.showinfo(_("Info"), _("Could not retrieve slots for Tray ID '{}'. Check if tray exists or service is running.").format(tray_id))


    def place_or_update_item(self):
        tray_id = self.op_tray_id_entry.get()
        slot_index_str = self.op_slot_index_entry.get()
        item_id = self.op_item_id_entry.get() # This is the item to place/update
        process_info = self.op_process_info_entry.get()

        if not tray_id or not slot_index_str:
            messagebox.showwarning(_("Input Error"), _("Target Tray ID and Target Slot Index are required."))
            return
        if not item_id: # If item_id is empty, it's more like a "clear" or "set to empty" operation
            messagebox.showwarning(_("Input Error"), _("Item ID to place cannot be empty. Use 'Clear Slot Item' to empty a slot."))
            return

        try: slot_index = int(slot_index_str)
        except ValueError: messagebox.showwarning(_("Input Error"), _("Slot Index must be a number.")); return

        payload = {"item_id": item_id}
        if process_info: payload["process_info"] = process_info

        # For placing/updating, we might want to allow overwrite.
        # The API endpoint POST /trays/{tray_id}/locations/{slot_index}/item/ has an allow_overwrite query param.
        # Let's add a checkbox or decide a default for the GUI. For now, default to allow_overwrite=true for simplicity of this button.
        endpoint = f"/trays/{tray_id}/locations/{slot_index}/item/?allow_overwrite=true"
        result = self._make_api_request("POST", endpoint, json_data=payload)

        if result:
            messagebox.showinfo(_("Success"), _("Item placed/updated successfully in Tray '{}', Slot {}: {}").format(tray_id, slot_index, item_id))
            self._clear_op_entries()
            # Refresh view if current query_tray_id matches op_tray_id
            if self.query_tray_id_entry.get() == tray_id:
                 self.get_locations_for_selected_tray()

    def clear_slot_item_command(self):
        tray_id = self.op_tray_id_entry.get()
        slot_index_str = self.op_slot_index_entry.get()
        if not tray_id or not slot_index_str:
            messagebox.showwarning(_("Input Error"), _("Target Tray ID and Target Slot Index for clearing are required."))
            return
        try: slot_index = int(slot_index_str)
        except ValueError: messagebox.showwarning(_("Input Error"), _("Slot Index must be a number.")); return

        if not messagebox.askyesno(_("Confirm Clear"), _("Are you sure you want to clear the item from Tray '{}', Slot {}?").format(tray_id, slot_index)):
            return

        # API endpoint: POST /trays/{tray_id}/locations/{slot_index}/clear/
        # It takes an optional query param `set_item_id_to` which defaults to "" in API.
        result = self._make_api_request("POST", f"/trays/{tray_id}/locations/{slot_index}/clear/")
        if result is not None: # API returns the updated location or error
            messagebox.showinfo(_("Success"), _("Slot item cleared successfully for Tray '{}', Slot {}.").format(tray_id, slot_index))
            # Refresh view if current query_tray_id matches op_tray_id
            if self.query_tray_id_entry.get() == tray_id:
                 self.get_locations_for_selected_tray()


    def get_specific_slot_command(self):
        tray_id = self.op_tray_id_entry.get() # Use op_tray_id as it's more specific for an operation
        slot_index_str = self.op_slot_index_entry.get()
        if not tray_id or not slot_index_str:
            messagebox.showwarning(_("Input Error"), _("Target Tray ID and Target Slot Index are required to get a specific slot."))
            return
        try: slot_index = int(slot_index_str)
        except ValueError: messagebox.showwarning(_("Input Error"), _("Slot Index must be a number.")); return

        result = self._make_api_request("GET", f"/trays/{tray_id}/locations/{slot_index}/")
        self._display_results(result if result else []) # Display single result or clear if not found
        if result is None : messagebox.showinfo(_("Info"),_("Slot {} on Tray ID '{}' not found or error during fetch.").format(slot_index, tray_id))


    def find_empty_slot_on_tray_command(self):
        tray_id = self.op_tray_id_entry.get()
        if not tray_id: # Tray ID from operation fields is needed
            messagebox.showwarning(_("Input Error"), _("Target Tray ID is required to find an empty slot."))
            return

        result = self._make_api_request("GET", f"/trays/{tray_id}/available_slot/")
        if result:
            messagebox.showinfo(_("Available Slot"), _("Found available slot on Tray '{}': Slot Index {}").format(result['tray_id'], result['slot_index']))
            self._display_results(result)
            self.op_tray_id_entry.delete(0, tk.END); self.op_tray_id_entry.insert(0, result['tray_id'])
            self.op_slot_index_entry.delete(0,tk.END); self.op_slot_index_entry.insert(0, str(result['slot_index']))
            self.op_item_id_entry.delete(0,tk.END)
            self.op_process_info_entry.delete(0,tk.END)
        elif result is None:
             messagebox.showinfo(_("No Slot"), _("No available empty slot found on Tray '{}'.").format(tray_id))
             self._display_results([])
        # else: API error already shown


if __name__ == "__main__":
    root = tk.Tk()
    app = AppServiceGUI(root)
    root.mainloop()
