# MCP Firebase Server (Model Context Protocol)

This server implements the Model Context Protocol (MCP) to act as a bridge between a Large Language Model (LLM) like Claude and Firebase (Firestore). It allows the LLM to read from and write to Firestore collections by exposing these operations as MCP "tools."

This server is built using the official `mcp` Python SDK.

## Prerequisites

*   Python 3.7+ (preferably 3.8+ for `asynccontextmanager` and full type hinting features used by MCP)
*   Pip (Python package installer) or `uv` (recommended by MCP docs for project management)
*   A Firebase project with Firestore enabled.
*   A Firebase service account key JSON file.

## Setup

1.  **Clone/Download:**
    Ensure you have the server file (`mcp_firebase_server.py`), `requirements.txt`, etc., in a local directory.

2.  **Service Account Key:**
    *   The server needs a Firebase service account key to authenticate.
    *   **Option 1 (Recommended for MCP Client Configuration):** Set the `SERVICE_ACCOUNT_KEY_PATH` environment variable to the absolute path of your service account JSON file. This is the most flexible method when the server is launched by an MCP client.
    *   **Option 2 (Fallback):** If the `SERVICE_ACCOUNT_KEY_PATH` environment variable is not set, the server will look for a file named `serviceAccountKey.json` in its own directory (the same directory as `mcp_firebase_server.py`). If using this method, rename your key file accordingly.
    *   **Important:** Ensure your service account key file (however it's named or accessed) is kept secure and ideally listed in your `.gitignore` if a local copy exists in the project.

3.  **Firebase Storage Bucket (Optional):**
    *   If you intend to use Firebase Storage functionalities with this server (currently no tools use it, but it can be added), set the `FIREBASE_STORAGE_BUCKET` environment variable to your Firebase project's storage bucket name (e.g., `your-project-id.appspot.com`). The server will read and print this value if set.

4.  **Create a Virtual Environment (Recommended):**
    Using `venv`:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On macOS/Linux
    # venv\\Scripts\\activate   # On Windows
    ```
    Or, if using `uv` (as suggested by MCP docs for new projects):
    ```bash
    uv venv
    source .venv/bin/activate # Or similar, depending on your uv setup
    ```

5.  **Install Dependencies:**
    Using `pip`:
    ```bash
    pip install -r requirements.txt
    ```
    Or, if using `uv`:
    ```bash
    uv pip install -r requirements.txt
    ```
    This will install `mcp[cli]` and `firebase-admin`.

## Running the Server

There are a couple of ways to run this MCP server:

1.  **Direct Execution (for stdio transport via `run_server.sh`):**
    A `run_server.sh` script is provided to simplify launching the server. This script handles activating the virtual environment (if named `venv` and present in the project root) before running the Python script.

    First, make the script executable:
    ```bash
    chmod +x run_server.sh
    ```
    Then, run the server using the script:
    ```bash
    ./run_server.sh
    ```
    This is how an MCP client would typically be configured to launch the server (see "Using with Claude" section below).

2.  **Using MCP CLI for Development and Inspection (`mcp dev`):
    The `mcp` CLI (installed as part of `mcp[cli]`) provides a development server and inspector tool. This is highly recommended during development.
    ```bash
    mcp dev mcp_firebase_server.py
    ```
    This will start the server and often provide a web interface for inspecting its capabilities (tools, resources) and making test calls.

## MCP Tools Exposed

This server, named `MCPFirebaseServer`, exposes the following tools:

### 1. `mcp_firebase_query_firestore_collection`

*   **Description (from docstring):** Retrieves documents from a specified Firestore collection.
*   **Arguments:**
    *   `collection_name` (string, required): The name of the Firestore collection to query.
    *   `limit` (integer, optional, default: 50): The maximum number of documents to return.
*   **Returns:** A list of documents from the collection, or an error message.

### 2. `mcp_firebase_add_document_to_firestore`

*   **Description (from docstring):** Adds a new document with an auto-generated ID to the specified Firestore collection.
*   **Arguments:**
    *   `collection_name` (string, required): The name of the Firestore collection where the document will be added.
    *   `document_data` (object/dictionary, required): A dictionary representing the document to add.
*   **Returns:** A dictionary containing the success status and the ID of the new document, or an error message.

### 3. `mcp_firebase_list_firestore_collections`

*   **Description (from docstring):** Lists all top-level collections in the Firestore database.
*   **Arguments:**
    *   `random_string` (string, required): A dummy parameter (can be any string) as this tool takes no meaningful input.
*   **Returns:** A list of dictionaries, each containing the 'id' of a collection, or an error message.

### 4. `mcp_firebase_get_firestore_document`

*   **Description (from docstring):** Retrieves a specific document from a Firestore collection by its ID.
*   **Arguments:**
    *   `collection_name` (string, required): The name of the Firestore collection.
    *   `document_id` (string, required): The ID of the document to retrieve.
*   **Returns:** A dictionary representing the document data, or an error message.

### 5. `mcp_firebase_list_document_subcollections`

*   **Description (from docstring):** Lists all subcollections of a specified document in Firestore.
*   **Arguments:**
    *   `collection_name` (string, required): The name of the parent collection.
    *   `document_id` (string, required): The ID of the document whose subcollections are to be listed.
*   **Returns:** A list of dictionaries, each containing the 'id' of a subcollection, or an error message.

### 6. `mcp_firebase_update_firestore_document`

*   **Description (from docstring):** Updates an existing document in a specified Firestore collection.
*   **Arguments:**
    *   `collection_name` (string, required): The name of the Firestore collection.
    *   `document_id` (string, required): The ID of the document to update.
    *   `update_data` (object/dictionary, required): A dictionary containing the fields to update.
*   **Returns:** A dictionary containing the success status, or an error message.

### 7. `mcp_firebase_query_firestore_collection_with_filter`

*   **Description (from docstring):** Retrieves documents from a specified Firestore collection, filtering by field values (equality `==` only).
*   **Arguments:**
    *   `collection_name` (string, required): The name of the Firestore collection to query.
    *   `filters` (object/dictionary, required): A dictionary where keys are field names and values are the values to filter by (e.g., `{"category": "electronics", "available": True}`).
    *   `limit` (integer, optional, default: 50): The maximum number of documents to return.
*   **Returns:** A list of documents from the collection that match the filters, or an error message.

## Using with Claude (or other MCP Clients)

This MCP Firebase Server is designed to be run as a separate process, typically launched by an MCP client application (such as Claude Desktop or a custom application built with a platform like Windsurf that can manage MCP servers). The client then communicates with this server, usually over `stdio` (standard input/output) for locally run servers.

**General Integration Steps:**

1.  **Server Availability:** Ensure `mcp_firebase_server.py` and its dependencies (including `serviceAccountKey.json`) are accessible on the system where the MCP client will run or can launch processes.

2.  **Client Configuration:** The MCP client application needs to be configured to know how to start your `MCPFirebaseServer`. This configuration usually involves specifying:
    *   A **command** to execute (e.g., `python` or `uv run python`).
    *   **Arguments** for that command (e.g., the path to `mcp_firebase_server.py`).
    *   Optionally, any **environment variables** the server might need (though our current server expects `serviceAccountKey.json` in the same directory, an environment variable for the key path could be an alternative).

3.  **Launching and Communication:**
    *   When the MCP client needs to use a tool provided by this server, it will launch `mcp_firebase_server.py` using the configured command.
    *   The client and server then communicate over the MCP protocol (e.g., via `stdio`). The client can discover available tools (like `mcp_firebase_query_firestore_collection`, `mcp_firebase_add_document_to_firestore`, etc.) and call them.

**Conceptual Configuration Example (for an MCP Client like Claude Desktop):**

Many MCP-compatible client applications (like Claude Desktop, as referenced in MCP documentation) use a configuration file (often JSON) to define how to launch and manage MCP servers. While the exact format can vary by client, the principle is similar.

Below is a *conceptual* example based on patterns seen in MCP documentation. You would need to adapt this to the specific configuration mechanism of your chosen MCP client (Claude Desktop, Windsurf, etc.).

```json
{
  "mcpServers": {
    "my_firebase_mcp_connector": { // A unique name you assign to this server instance in the client's config
      "command": "/full/path/to/your/mc-firebase-server/run_server.sh", // IMPORTANT: Use the absolute path to the script
      "args": [], // Typically empty if run_server.sh handles everything
      // "cwd": "/full/path/to/your/mc-firebase-server/", // Usually not needed if run_server.sh cds to its own dir
      "env": {
        // Replace with the ACTUAL absolute path to your service account key file
        "SERVICE_ACCOUNT_KEY_PATH": "/path/to/your/serviceAccountKey.json", 
        // Optional: Replace with your actual Firebase Storage bucket name if needed by future tools
        "FIREBASE_STORAGE_BUCKET": "your-project-id.appspot.com" 
      }
    }
  }
}
```

**Key points for the configuration:**

*   **`"command"`**: The executable to run (e.g., `python`). Make sure it's in the system's PATH or provide the full path to the Python interpreter.
*   **`"args"`**: A list of arguments. The first argument is typically the script to execute. **It is crucial to use the full, absolute path to `mcp_firebase_server.py`** to ensure the client can find it, regardless of where the client itself is launched from.
*   **`"cwd"` (Current Working Directory)**: Sometimes, you might need to specify the working directory for the server process, especially if it relies on relative paths for other files (though our `serviceAccountKey.json` path is relative to the script itself, which is generally robust if the script path is absolute).
*   **`"env"`**: For passing environment variables. While our current server locates `serviceAccountKey.json` relative to its own path, a common pattern for more configurable servers is to pass credential paths or other settings via environment variables. The `SERVICE_ACCOUNT_KEY_PATH` is crucial for authentication. The `FIREBASE_STORAGE_BUCKET` is optional and currently unused by the provided tools, but might be relevant if storage-related tools are added later.

**Interaction Flow (Recap):**

1.  **Client Starts Server:** The MCP client (using the configuration above) starts `mcp_firebase_server.py`.
2.  **Server Initializes:** Our server attempts to connect to Firebase.
3.  **Tool Discovery & Calls:** The client discovers and calls tools like `mcp_firebase_query_firestore_collection` or `mcp_firebase_add_document_to_firestore` etc., as needed.
4.  **Server Responds:** Results are sent back to the client via `stdio`.

**Specific Instructions for Claude Desktop or Windsurf:**

*   **Claude Desktop:** If you are using Claude Desktop, refer to its documentation on how to add and configure custom MCP servers. The JSON structure above is a common pattern you might adapt.
*   **Windsurf:** If Windsurf is your orchestrator and it supports managing MCP servers, it will have its own method for defining and launching these external tool servers. You would need to consult Windsurf's documentation for the specifics, but the core information (command, arguments to run `mcp_firebase_server.py`) will be the same.

If your client doesn't have a dedicated MCP server management UI/config file, but can execute shell commands and interact via stdio, you would programmatically launch the `mcp_firebase_server.py` script and then use an MCP client library (like the one in `mcp.client.stdio`) to communicate with it.

## Development and Testing

*   Use `mcp dev mcp_firebase_server.py` to run the server with the MCP Inspector. This allows you to see discovered tools and test them interactively.
*   Ensure `serviceAccountKey.json` is correctly placed OR the `SERVICE_ACCOUNT_KEY_PATH` environment variable is set when the server is launched by an MCP client.
*   Check the server's console output for Firebase initialization messages and any runtime errors.

**The `run_server.sh` Script:**

The `run_server.sh` script in the project root is designed to:
1.  Determine its own location and change the current directory to there.
2.  Locate and activate a Python virtual environment named `venv` if it exists in the project root.
3.  Execute the `mcp_firebase_server.py` script using the `python` interpreter (ideally from the activated venv).

This script ensures that the MCP server runs in its intended environment. Remember to make it executable (`chmod +x run_server.sh`). 