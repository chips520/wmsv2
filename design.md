# WMSv2 Application Design Document

## 1. Overview

This document outlines the proposed database design for the WMSv2 application, focusing on managing material locations on various trays, each with a predefined capacity. This design uses two primary tables: `trays` and `material_locations`.

## 2. Core Requirements Addressed

This design aims to solve the following key requirements:
1.  **Pre-defined Slot Capacity per Tray:** Each tray (e.g., AGV tray, transfer station tray) has a specific, pre-set number of material locations (slots).
2.  **Unique Identification of Slots:** Each slot on a specific tray must be uniquely identifiable.
3.  **Tracking Material in Slots:** The system must track which material (by `item_id`) is in which slot, or if a slot is empty or disabled.
4.  **Finding Available Empty Slots:** The system must be able to identify valid empty slots on a specific tray or across all trays.
5.  **Error Handling for Placement:** If an attempt is made to place an item and no suitable empty slot is available, the system must return a clear error indication.
6.  **Querying Item Location:** The system must be able to find the tray and slot for a given `item_id`.

## 3. Database Design

We will use a relational database (e.g., SQLite) with the following two tables:

### 3.1. `trays` Table

This table stores information about each physical or logical tray in the system.

**Columns:**

*   `tray_id` (TEXT, Primary Key):
    *   A unique identifier for the tray (e.g., "AGV1", "TS01", "MANUAL_INSPECT_A").
    *   This ID will be human-readable or system-defined.
*   `description` (TEXT, Nullable):
    *   A brief description of the tray (e.g., "AGV 1 Left Tray", "Main Transfer Station Area 1").
*   `max_slots` (INTEGER, NOT NULL):
    *   The total number of available material location slots on this tray. For example, an AGV tray might have `max_slots = 50`.
*   `created_at` (DATETIME, Default: CURRENT_TIMESTAMP):
    *   Timestamp of when the tray was registered in the system.
*   `updated_at` (DATETIME, Default: CURRENT_TIMESTAMP, On Update: CURRENT_TIMESTAMP):
    *   Timestamp of the last update to the tray's information.

**Example Data:**

| tray_id   | description           | max_slots |
|-----------|-----------------------|-----------|
| "AGV1"    | "AGV Robot 1 Tray"    | 50        |
| "TS01"    | "Transfer Station 01" | 60        |

### 3.2. `material_locations` Table

This table stores the state of each individual slot on every tray.

**Columns:**

*   `id` (INTEGER, Primary Key, Auto-increment):
    *   A unique internal ID for the database record itself.
*   `tray_id` (TEXT, NOT NULL, Foreign Key references `trays.tray_id`):
    *   The identifier of the tray this slot belongs to.
*   `slot_index` (INTEGER, NOT NULL):
    *   The specific index or position of this slot on the tray (e.g., 1, 2, ..., up to `trays.max_slots` for the given `tray_id`).
*   `item_id` (TEXT, Nullable):
    *   The identifier of the material or sample currently in this slot.
    *   `NULL` or an empty string (`""`) indicates the slot is **empty/available**.
    *   A special predefined value (e.g., `"-99"`, `"-1"`, or `"DISABLED"`) indicates the slot is **disabled** or not usable.
*   `timestamp` (DATETIME, Default: CURRENT_TIMESTAMP, On Update: CURRENT_TIMESTAMP):
    *   Timestamp of the last modification to this slot's state (e.g., when an item was placed, removed, or the slot was disabled).
*   `process_info` (TEXT, Nullable):
    *   Optional information about the last operation or process related to this slot (e.g., task ID, operation type).

**Constraints:**

*   **Composite Unique Key:** A unique constraint must be placed on the combination of (`tray_id`, `slot_index`) to ensure that each slot on a tray is represented only once.

**Example Data:**

| id  | tray_id | slot_index | item_id    | timestamp                 |
|-----|---------|------------|------------|---------------------------|
| 1   | "AGV1"  | 1          | "SAMPLE001"| 2023-10-27 10:00:00       |
| 2   | "AGV1"  | 2          | ""         | 2023-10-27 09:00:00       |
| ... | ...     | ...        | ...        | ...                       |
| 50  | "AGV1"  | 50         | "-99"      | 2023-10-27 11:00:00       |
| 51  | "TS01"  | 1          | "SAMPLE002"| 2023-10-27 10:05:00       |

## 4. System Operations and Logic

### 4.1. Tray Initialization (Pre-setting Slot Quantities)

When a new tray is commissioned and added to the `trays` table (e.g., `tray_id="AGV2"`, `max_slots=50`):
1.  A record for "AGV2" is inserted into the `trays` table.
2.  The system (or an administrative function) should then **automatically populate** the `material_locations` table with `max_slots` number of records for this new `tray_id`.
    *   For `tray_id="AGV2"` and `max_slots=50`, 50 records would be inserted:
        *   (`tray_id="AGV2"`, `slot_index=1`, `item_id=""`)
        *   (`tray_id="AGV2"`, `slot_index=2`, `item_id=""`)
        *   ...
        *   (`tray_id="AGV2"`, `slot_index=50`, `item_id=""`)
    *   This ensures that all slots are explicitly represented in the database from the start, mostly as empty.

### 4.2. Finding an Available Empty Slot

**Input:** `tray_id` (if placing on a specific tray) or no `tray_id` (if any tray is acceptable, though usually placement is targeted).

**Logic:**
1.  Query the `material_locations` table:
    ```sql
    SELECT tray_id, slot_index
    FROM material_locations
    WHERE item_id = ''  -- Or IS NULL, depending on convention for empty
      AND tray_id = :target_tray_id -- Optional: if specific tray is targeted
    ORDER BY slot_index ASC -- Or any other preferred order (e.g., last_used_time)
    LIMIT 1;
    ```
2.  **API Response:**
    *   **Success (Slot Found):** Return the `tray_id` and `slot_index` of the found empty slot.
        *   HTTP Status: `200 OK`
        *   Response Body: `{"tray_id": "AGV1", "slot_index": 2}`
    *   **Failure (No Empty Slot Found on Target Tray):**
        *   HTTP Status: `404 Not Found` (or a custom `4xx` like `409 Conflict` if "no slot" is a business rule conflict).
        *   Response Body: `{"error": "NO_EMPTY_SLOT_AVAILABLE", "message": "No empty slot found on tray X"}`. This error code (`NO_EMPTY_SLOT_AVAILABLE`) is crucial for the scheduling system.
    *   **Failure (Target Tray Does Not Exist or Invalid):**
        *   HTTP Status: `404 Not Found`
        *   Response Body: `{"error": "TRAY_NOT_FOUND", "message": "Tray X does not exist"}`

### 4.3. Placing an Item into a Slot

**Input:** `item_id`, `target_tray_id`, `target_slot_index`.

**Logic:**
1.  **Verify Slot Existence and Availability:**
    *   Query `material_locations`:
      ```sql
      SELECT item_id FROM material_locations
      WHERE tray_id = :target_tray_id AND slot_index = :target_slot_index;
      ```
    *   If no record is found: The slot does not exist (error).
    *   If a record is found, check its `item_id`:
        *   If `item_id` is empty (`""` or `NULL`): The slot is available.
        *   If `item_id` is not empty (contains another item or is disabled): The slot is occupied or not usable (error).
2.  **Perform Update (if available):**
    ```sql
    UPDATE material_locations
    SET item_id = :new_item_id, timestamp = CURRENT_TIMESTAMP -- and other fields
    WHERE tray_id = :target_tray_id
      AND slot_index = :target_slot_index
      AND (item_id = '' OR item_id IS NULL); -- Optimistic concurrency: ensure it's still empty
    ```
    Check the number of rows affected by the update. If 0 rows affected (and the slot was supposed to be empty), it means another process might have taken it.
3.  **API Response:**
    *   **Success:**
        *   HTTP Status: `200 OK`
        *   Response Body: Details of the updated location.
    *   **Failure (Slot Occupied/Disabled):**
        *   HTTP Status: `409 Conflict`
        *   Response Body: `{"error": "SLOT_NOT_AVAILABLE", "message": "Slot X on tray Y is occupied or disabled."}`
    *   **Failure (Slot Does Not Exist):**
        *   HTTP Status: `404 Not Found`
        *   Response Body: `{"error": "SLOT_NOT_FOUND", "message": "Slot X on tray Y does not exist."}`
    *   **Failure (Item Already Exists Elsewhere - Optional Check):**
        *   If the system enforces that an `item_id` can only be in one place.
        *   HTTP Status: `409 Conflict`
        *   Response Body: `{"error": "ITEM_ALREADY_EXISTS", "message": "Item Z is already located at tray A, slot B."}`

### 4.4. Other Operations

*   **Disabling/Enabling a Slot:** Update the `item_id` to/from the "DISABLED" special value.
*   **Clearing an Item from a Slot:** Update the `item_id` to `""` (empty).
*   **Querying Item Location:** `SELECT tray_id, slot_index FROM material_locations WHERE item_id = :item_to_find;`

## 5. API Endpoints (Conceptual)

Based on this design, API endpoints would be structured to handle these operations:

*   `POST /trays` (Create a new tray, potentially triggering slot initialization)
*   `GET /trays/{tray_id}`
*   `GET /trays/{tray_id}/locations` (Get all slots for a tray)
*   `GET /trays/{tray_id}/available_slot` (Implements logic from 4.2)
*   `PUT /locations/{tray_id}/{slot_index}/item` (Place/update item in slot, implements logic from 4.3)
    *   Body: `{"item_id": "SAMPLE123", "process_info": "..."}`
*   `DELETE /locations/{tray_id}/{slot_index}/item` (Clear item from slot)
*   `PUT /locations/{tray_id}/{slot_index}/status` (Disable/Enable slot)
    *   Body: `{"status": "DISABLED"}` or `{"status": "EMPTY"}`
*   `GET /items/{item_id}/location` (Find where a specific item is)

## 6. Conclusion

This two-table design (`trays` and `material_locations`) provides a structured and robust way to manage material locations with predefined tray capacities. It allows for efficient querying of empty slots, clear error handling for placement operations, and straightforward management of slot states, thereby supporting the needs of an automated scheduling system.
