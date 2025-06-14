# WMS HTTP API - Windows Service Setup

This document provides instructions for setting up and managing the WMS HTTP API as a Windows Service.

## Prerequisites

1.  **Python Environment:** Ensure Python 3.7+ is installed and configured in your system's PATH.
2.  **Application Files:** All application files (the `app` directory, `requirements.txt`, etc.) should be deployed to a stable location on the server (e.g., `C:\WMS_Service`).
3.  **Dependencies:** Install all required Python packages:
    ```bash
    pip install -r requirements.txt
    ```
    This includes `pypiwin32` which is necessary for Windows service integration.
4.  **Administrator Privileges:** You will need Administrator rights to install, start, stop, or remove the Windows service. All `python app/service.py ...` commands and `sc.exe` commands below should be run from an **Administrator Command Prompt or PowerShell**.

## Service Details

-   **Service Name (internal):** `WMSServiceHTTP`
-   **Service Display Name:** `WMS HTTP Service`
-   **Service Script:** `app/service.py` (relative to your project root)
-   **Log File:** `wms_service.log` (created in the project root directory)

## Installation

1.  **Open an Administrator Command Prompt or PowerShell.**
2.  **Navigate to the project root directory** where `app/service.py` is located.
    ```bash
    cd C:\path\to\your\wmsv2_project
    ```
3.  **Install the service:**
    ```bash
    python app/service.py install
    ```
    If successful, you should see a message like "Service WMSServiceHTTP installed".

## Managing the Service

### Check Status

You can check the status of the service using the `sc` command:
```bash
sc query WMSServiceHTTP
```
Look for the `STATE` line in the output.

### Start the Service

-   Using `sc.exe`:
    ```bash
    sc start WMSServiceHTTP
    ```
-   Using the service script:
    ```bash
    python app/service.py start
    ```
-   Using Windows Services GUI:
    1.  Open `services.msc`.
    2.  Find "WMS HTTP Service" in the list.
    3.  Right-click and select "Start".

### Stop the Service

-   Using `sc.exe`:
    ```bash
    sc stop WMSServiceHTTP
    ```
-   Using the service script:
    ```bash
    python app/service.py stop
    ```
-   Using Windows Services GUI:
    1.  Open `services.msc`.
    2.  Find "WMS HTTP Service" in the list.
    3.  Right-click and select "Stop".

### Restart the Service

The service script has a `restart` command:
```bash
python app/service.py restart
```
This will attempt to stop and then start the service.

### Configure Auto-Start

To make the service start automatically when Windows boots:
1.  **Using `sc.exe`:**
    ```bash
    sc config WMSServiceHTTP start=auto
    ```
    (Note: `start= auto` with a space might be needed for some Windows versions, try `start=auto` first).
2.  **Using Windows Services GUI:**
    1.  Open `services.msc`.
    2.  Find "WMS HTTP Service".
    3.  Right-click and select "Properties".
    4.  Change "Startup type" to "Automatic".
    5.  Click "OK".

## Viewing Logs

The service logs information, errors, and Uvicorn startup/shutdown messages to `wms_service.log` located in the project root directory. Check this file for troubleshooting.

## Uninstallation

1.  **Ensure the service is stopped** (see "Stop the Service" above).
2.  **Open an Administrator Command Prompt or PowerShell.**
3.  **Navigate to the project root directory.**
4.  **Remove the service:**
    ```bash
    python app/service.py remove
    ```
    If successful, you should see a message like "Service WMSServiceHTTP removed".

## Debugging the Service Code

If you need to debug the service logic itself (not Uvicorn, but the `app/service.py` wrapper):
```bash
python app/service.py debug
```
This will run the service code in the console. Press `Ctrl+C` to stop it. Uvicorn will output to the console as well. This does not interact with the Windows SCM.
