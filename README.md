# WMS Service Application (WMSv2)

## English

### Overview
This application provides a Warehouse Management Service (WMS) to record and manage material location information on configurable trays. It features an HTTP API for programmatic access and a local GUI application for service management and data interaction. The HTTP API can be run as a Windows Service.

### Core Features
- **Tray Management:** Define trays with specific IDs, descriptions, and maximum slot capacities.
- **Slot Management:** Each tray has a defined number of indexed slots (`slot_index`).
- **Material Tracking:** Records material location status, `item_id` in a specific `tray_id` at a `slot_index`, timestamp, and optional process information.
- **HTTP API:** RESTful API (using GET/POST methods) for all operations.
    - Tray CRUD operations.
    - Slot content management (place item, clear item, get slot details).
    - Queries for available slots on a tray.
    - Queries to find locations of a specific item.
- **Swagger UI:** API documentation and testing available at `/docs` when the service is running.
- **Windows Service:** The HTTP API can be installed and run as a background Windows Service for continuous operation and auto-start.
- **Local GUI Application:** (Tkinter)
    - Start, stop, and check the status of the WMS Windows Service.
    - Query trays and their slot contents.
    - Manage items in slots (place, clear, view specific slot).
    - Switch interface language (English/Chinese).
- **Data Storage:** Local SQLite database (`db.sqlite3`) with `trays` and `material_locations` tables.
- **Internationalization (i18n):** GUI supports English (`en`) and Chinese (`zh`).

### Setup and Running

**Prerequisites:**
- Python 3.7+
- Pip (Python package installer)
- (For Windows Service) Administrator privileges for service installation.

**Installation:**
1.  **Clone the repository or ensure all project files are in your project directory.**
2.  **Navigate to the project root directory.**
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    This installs `fastapi`, `uvicorn`, `sqlalchemy`, `pypiwin32` (for Windows service), and `requests` (for GUI).
    *Note: This step is crucial and must be performed in a functional Python environment.*

**Running the HTTP API Service (Development Mode):**
For development, you can run the API directly with Uvicorn.
1.  **Navigate to the project root directory.**
2.  **Run the Uvicorn server:**
    ```bash
    uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
    ```
    The API will be available at `http://127.0.0.1:8000`.
    Swagger UI: `http://127.0.0.1:8000/docs`.
    The database `db.sqlite3` and tables will be created in the project root on first run if they don't exist.

**Running as a Windows Service:**
See `SERVICE_SETUP.md` for detailed instructions on installing and managing the WMS HTTP API as a Windows Service.

**Running the GUI Application:**
1.  **Ensure Python and Tkinter are correctly installed, and dependencies from `requirements.txt` are met.**
2.  **Navigate to the project root directory.**
3.  **Run the GUI script:**
    ```bash
    python gui/main_window.py
    ```
    The GUI will interact with the (ideally) running Windows Service or the Uvicorn development server. Ensure the API is accessible at `http://127.0.0.1:8000`.

### Key API Endpoint Structure
- **Trays:**
    - `POST /trays/`: Create a new tray (auto-initializes slots).
    - `GET /trays/`: List all trays.
    - `GET /trays/{tray_id}/`: Get a specific tray (includes its slot details).
    - `POST /trays/{tray_id}/update/`: Update tray description.
    - `POST /trays/{tray_id}/delete/`: Delete a tray.
- **Material Locations (Slots):**
    - `GET /trays/{tray_id}/locations/`: List all slots for a tray.
    - `GET /trays/{tray_id}/locations/{slot_index}/`: Get a specific slot.
    - `POST /trays/{tray_id}/locations/{slot_index}/item/`: Place/update an item in a slot.
    - `POST /trays/{tray_id}/locations/{slot_index}/clear/`: Clear an item from a slot.
    - `GET /trays/{tray_id}/available_slot/`: Find an available empty slot on a tray.
- **Items:**
    - `GET /items/{item_id}/locations/`: Find where an item is located.
- **Admin (Direct DB ID access):**
    - `GET /locations/`, `GET /locations/{location_id}/`, etc.

Refer to the Swagger UI (`/docs`) for full API details and request/response models.

### Internationalization (i18n)
- The GUI supports English (`en`) and Chinese (`zh`).
- Language can be switched directly from the GUI.
- Translation files: `locale/<lang_code>/LC_MESSAGES/gui.json`.

### Design Details
Refer to `design.md` for the database schema and application design considerations.

### Development History
Refer to `history.md` for a log of development activities during the session.

---

## 中文 (Chinese)

### 概述
此应用程序提供了一个仓库管理服务 (WMS)，用于记录和管理可配置料盘上的料位信息。它具有用于编程访问的 HTTP API 和用于服务管理及数据交互的本地 GUI 应用程序。HTTP API 可以作为 Windows 服务运行。

###核心功能
- **料盘管理:** 定义具有特定ID、描述和最大料位数（容量）的料盘。
- **料位管理:** 每个料盘都有确定数量的索引化料位 (`slot_index`)。
- **物料追踪:** 在特定料盘 (`tray_id`) 的特定料位 (`slot_index`) 上记录物料ID (`item_id`)、状态、时间戳以及可选的工序信息。
- **HTTP API:** RESTful API (使用 GET/POST 方法) 支持所有操作。
    - 料盘 CRUD 操作。
    - 料位内容管理 (放置物料、清空料位、获取料位详情)。
    - 查询料盘上的可用空料位。
    - 查询特定物料所在的位置。
- **Swagger UI:** API 文档和测试 (服务运行时位于 `/docs` 路径)。
- **Windows 服务:** HTTP API 可以作为后台 Windows 服务安装和运行，以实现持续操作和开机自启。
- **本地 GUI 应用程序:** (Tkinter)
    - 启动、停止和检查 WMS Windows 服务的状态。
    - 查询料盘及其料位内容。
    - 管理料位中的物料 (放置、清空、查看特定料位)。
    - 切换界面语言 (英文/中文)。
- **数据存储:** 本地 SQLite 数据库 (`db.sqlite3`)，包含 `trays` 和 `material_locations` 表。
- **国际化 (i18n):** GUI 支持英文 (`en`) 和中文 (`zh`)。

### 安装与运行

**环境要求:**
- Python 3.7+
- Pip (Python 包安装器)
- (对于 Windows 服务) 安装服务需要管理员权限。

**安装步骤:**
1.  **克隆仓库或确保所有项目文件都在您的项目目录中。**
2.  **导航到项目根目录。**
3.  **安装依赖:**
    ```bash
    pip install -r requirements.txt
    ```
    这将安装 `fastapi`, `uvicorn`, `sqlalchemy`, `pypiwin32` (用于 Windows 服务) 和 `requests` (用于 GUI)。
    *注意: 此步骤至关重要，必须在可用的 Python 环境中执行。*

**运行 HTTP API 服务 (开发模式):**
在开发期间，您可以直接使用 Uvicorn 运行 API。
1.  **导航到项目根目录。**
2.  **运行 Uvicorn 服务器:**
    ```bash
    uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
    ```
    API 将在 `http://127.0.0.1:8000` 上可用。
    Swagger UI: `http://127.0.0.1:8000/docs`。
    如果数据库 `db.sqlite3` 和相关表不存在，它们将在首次运行时在项目根目录中创建。

**作为 Windows 服务运行:**
有关安装和管理 WMS HTTP API 作为 Windows 服务的详细说明，请参阅 `SERVICE_SETUP.md`。

**运行 GUI 应用程序:**
1.  **确保 Python、Tkinter 已正确安装，并且 `requirements.txt` 中的依赖项已满足。**
2.  **导航到项目根目录。**
3.  **运行 GUI 脚本:**
    ```bash
    python gui/main_window.py
    ```
    GUI 将与 (理想情况下) 正在运行的 Windows 服务或 Uvicorn 开发服务器进行交互。请确保 API 在 `http://127.0.0.1:8000` 可访问。

### 主要 API 端点结构
- **料盘 (Trays):**
    - `POST /trays/`: 创建新料盘 (自动初始化料位)。
    - `GET /trays/`: 列出所有料盘。
    - `GET /trays/{tray_id}/`: 获取特定料盘信息 (包括其料位详情)。
    - `POST /trays/{tray_id}/update/`: 更新料盘描述。
    - `POST /trays/{tray_id}/delete/`: 删除料盘。
- **料位 (Material Locations / Slots):**
    - `GET /trays/{tray_id}/locations/`: 列出料盘的所有料位。
    - `GET /trays/{tray_id}/locations/{slot_index}/`: 获取特定料位信息。
    - `POST /trays/{tray_id}/locations/{slot_index}/item/`: 在特定料位放置/更新物料。
    - `POST /trays/{tray_id}/locations/{slot_index}/clear/`: 清空特定料位的物料。
    - `GET /trays/{tray_id}/available_slot/`: 查找料盘上的可用空料位。
- **物料 (Items):**
    - `GET /items/{item_id}/locations/`: 查找特定物料所在的位置。
- **管理 (直接通过数据库ID访问):**
    - `GET /locations/`, `GET /locations/{location_id}/`, 等。

请参阅 Swagger UI (`/docs`) 获取完整的 API 详细信息和请求/响应模型。

### 国际化 (i18n)
- GUI 支持英文 (`en`) 和中文 (`zh`)。
- 可以直接从 GUI 切换语言。
- 翻译文件位于 `locale/<语言代码>/LC_MESSAGES/gui.json`。

### 设计详情
有关数据库架构和应用程序设计注意事项，请参阅 `design.md`。

### 开发历史
有关本会话期间的开发活动日志，请参阅 `history.md`。