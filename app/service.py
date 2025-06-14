import win32serviceutil  # Main utility for Windows services
import win32service      # Constants and service status
import win32event        # For event handling (e.g., stop event)
import servicemanager    # For logging/event log
import sys
import os
import subprocess
import time
import logging

# Get the directory of the current script (service.py)
# This helps locate main.py if the service is run with a different CWD by SCM
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = BASE_DIR # If main.py is in the same directory as service.py
# If main.py is in the parent directory of 'app' (i.e., project root)
# and service.py is in 'app', then project_root for uvicorn would be:
PROJECT_ROOT = os.path.dirname(BASE_DIR)


# Configure logging for the service
log_file_path = os.path.join(PROJECT_ROOT, 'wms_service.log') # Log in project root
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

class WMSService(win32serviceutil.ServiceFramework):
    _svc_name_ = "WMSServiceHTTP"
    _svc_display_name_ = "WMS HTTP Service"
    _svc_description_ = "Manages the Warehouse Management System HTTP API via Uvicorn."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.process = None
        self.is_running = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        logging.info("WMS Service stop requested.")
        self.is_running = False
        if self.process:
            logging.info(f"Terminating Uvicorn process (PID: {self.process.pid}).")
            self.process.terminate() # Send SIGTERM
            try:
                self.process.wait(timeout=10) # Wait for up to 10 seconds
                logging.info("Uvicorn process terminated.")
            except subprocess.TimeoutExpired:
                logging.warning("Uvicorn process did not terminate in time, killing.")
                self.process.kill() # Force kill
            except Exception as e:
                logging.error(f"Error during Uvicorn termination: {e}")
            self.process = None
        win32event.SetEvent(self.hWaitStop) # Signal that stop is complete
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        logging.info("WMS Service started. Starting Uvicorn...")

        # Command to run Uvicorn. Ensure paths are correct.
        # Uvicorn should be callable if its Python env is in PATH, or use full path to uvicorn.
        # The module is app.main:app, relative to the project_root.
        # Assumes this service.py is in 'app' folder, and project_root is one level up.
        uvicorn_command = [
            sys.executable, # Use the same Python interpreter that's running the service
            "-m", "uvicorn",
            "app.main:app",
            "--host", "127.0.0.1",
            "--port", "8000"
            # Add other Uvicorn options like --workers if needed,
            # but for a service, --reload is usually not used.
        ]

        while self.is_running:
            try:
                logging.info(f"Attempting to start Uvicorn with command: {' '.join(uvicorn_command)}")
                logging.info(f"Uvicorn CWD: {PROJECT_ROOT}")

                # Ensure the CWD for uvicorn is the project root so it can find app.main
                self.process = subprocess.Popen(uvicorn_command, cwd=PROJECT_ROOT)
                logging.info(f"Uvicorn process started with PID: {self.process.pid}")

                # Wait for the process to complete or for a stop signal
                while self.is_running and self.process.poll() is None:
                    win32event.WaitForSingleObject(self.hWaitStop, 1000) # Check for stop signal every second

                if not self.is_running: # Service stop was requested
                    break

                # If we are here, the process terminated unexpectedly (poll() is not None)
                # and service stop was not requested.
                logging.warning(f"Uvicorn process (PID: {self.process.pid if self.process else 'N/A'}) terminated unexpectedly with code {self.process.returncode if self.process else 'N/A'}.")
                self.process = None # Clear the dead process

                if self.is_running: # If service is still supposed to be running, wait before restarting
                    logging.info("Waiting 30 seconds before attempting to restart Uvicorn...")
                    time.sleep(30)

            except Exception as e:
                logging.error(f"Error in SvcDoRun main loop: {e}")
                if self.is_running: # If error occurred and service should be running, wait before retry
                    logging.info("Waiting 60 seconds after error before retrying Uvicorn start...")
                    time.sleep(60)

        # Clean exit if loop is broken by self.is_running = False
        if self.process and self.process.poll() is None:
             logging.info("Service exiting, ensuring Uvicorn process is terminated.")
             self.process.terminate()
             try:
                self.process.wait(timeout=5)
             except subprocess.TimeoutExpired:
                self.process.kill()
        logging.info("WMS Service run loop ended.")


if __name__ == '__main__':
    if len(sys.argv) == 1:
        # If run without arguments, try to initialize the service manager
        # This allows the SCM to start the service.
        try:
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(WMSService)
            servicemanager.StartServiceCtrlDispatcher()
        except win32service.error as details:
            import winerror
            if details.winerror == winerror.ERROR_FAILED_SERVICE_CONTROLLER_CONNECT:
                win32serviceutil.usage() # Show usage if not run by SCM or as admin for install
            else:
                raise # Raise other SCM errors
    else:
        # Handle command line arguments for install, remove, debug, start, stop
        win32serviceutil.HandleCommandLine(WMSService)

# Example Usage from an Administrator Command Prompt:
# To Install: python app/service.py install
# To Start:   python app/service.py start (or use 'net start WMSServiceHTTP')
# To Stop:    python app/service.py stop (or use 'net stop WMSServiceHTTP')
# To Remove:  python app/service.py remove
# To Debug:   python app/service.py debug (runs in console, Ctrl+C to stop)
