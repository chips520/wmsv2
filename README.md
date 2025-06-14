# WMS Service Application (WMSv2)

## English

### Overview
This application provides a Warehouse Management Service (WMS) to record and manage material location information. It features an HTTP API for programmatic access and a local GUI application for service management and data interaction.

### Features
- Records material location status, item ID, timestamp, tray ID, and optional process information.
- HTTP API with GET and POST methods for all operations.
- Swagger UI for API documentation and testing (available at `/docs` when the service is running).
- Local GUI application (built with Tkinter) to:
    - Start, stop, and restart the HTTP service.
    - Perform CRUD (Create, Read, Update, Delete) operations on material locations.
    - Switch interface language between English and Chinese.
- Data stored in a local SQLite database (`db.sqlite3`).
- Internationalized GUI (English and Chinese).

### Setup and Running

**Prerequisites:**
- Python 3.7+
- Pip (Python package installer)

**Installation:**
1.  **Clone the repository (if applicable) or ensure all files are in your project directory.**
2.  **Navigate to the project root directory.**
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: This step is crucial and must be performed in a functional Python environment.*

**Running the HTTP API Service:**
The API service is built with FastAPI and run using Uvicorn.
1.  **Navigate to the project root directory.**
2.  **Run the Uvicorn server:**
    ```bash
    uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
    ```
    The API will be available at `http://127.0.0.1:8000`.
    Swagger UI will be at `http://127.0.0.1:8000/docs`.
    The database `db.sqlite3` will be created in the project root when the API starts for the first time and tables are initialized.

**Running the GUI Application:**
The GUI application provides an interface to manage the service and data.
1.  **Ensure Python and Tkinter are correctly installed.**
2.  **Navigate to the project root directory.**
3.  **Run the GUI script:**
    ```bash
    python gui/main_window.py
    ```
    *Note: The GUI attempts to start/stop the Uvicorn server as a subprocess. Ensure `uvicorn` is accessible in your system's PATH or that the Python environment where `uvicorn` is installed is active.*

### Internationalization (i18n)
- The GUI supports English (`en`) and Chinese (`zh`).
- Language can be switched directly from the GUI.
- Translation files are located in `locale/<lang_code>/LC_MESSAGES/gui.json`.

---

## 中文 (Chinese)

### 概述
此应用程序提供了一个仓库管理服务 (WMS)，用于记录和管理料位信息。它具有用于编程访问的 HTTP API 和用于服务管理及数据交互的本地 GUI 应用程序。

### 功能特点
- 记录料位状态、物料ID、时间戳、料盘号以及可选的工序信息。
- HTTP API，所有操作均使用 GET 和 POST 方法。
- Swagger UI 用于 API 文档和测试 (服务运行时位于 `/docs` 路径)。
- 本地 GUI 应用程序 (使用 Tkinter 构建) 用于：
    - 启动、停止和重启 HTTP 服务。
    - 对料位信息执行 CRUD (创建、读取、更新、删除) 操作。
    - 在英文和中文之间切换界面语言。
- 数据存储在本地 SQLite 数据库 (`db.sqlite3`) 中。
- 国际化的 GUI (英文和中文)。

### 安装与运行

**环境要求:**
- Python 3.7+
- Pip (Python 包安装器)

**安装步骤:**
1.  **克隆仓库 (如果适用) 或确保所有文件都在您的项目目录中。**
2.  **导航到项目根目录。**
3.  **安装依赖:**
    ```bash
    pip install -r requirements.txt
    ```
    *注意: 此步骤至关重要，必须在可用的 Python 环境中执行。*

**运行 HTTP API 服务:**
API 服务使用 FastAPI 构建，并通过 Uvicorn 运行。
1.  **导航到项目根目录。**
2.  **运行 Uvicorn 服务器:**
    ```bash
    uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
    ```
    API 将在 `http://127.0.0.1:8000` 上可用。
    Swagger UI 将位于 `http://127.0.0.1:8000/docs`。
    数据库 `db.sqlite3` 将在 API 首次启动并初始化表结构时在项目根目录中创建。

**运行 GUI 应用程序:**
GUI 应用程序提供了一个管理服务和数据的界面。
1.  **确保 Python 和 Tkinter 已正确安装。**
2.  **导航到项目根目录。**
3.  **运行 GUI 脚本:**
    ```bash
    python gui/main_window.py
    ```
    *注意: GUI 会尝试作为子进程启动/停止 Uvicorn 服务器。请确保 `uvicorn` 在您的系统 PATH 中可访问，或者 `uvicorn`所在的 Python 环境已激活。*

### 国际化 (i18n)
- GUI 支持英文 (`en`) 和中文 (`zh`)。
- 可以直接从 GUI 切换语言。
- 翻译文件位于 `locale/<语言代码>/LC_MESSAGES/gui.json`。