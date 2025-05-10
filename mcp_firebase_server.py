import firebase_admin
from firebase_admin import credentials, firestore
import os
import asyncio
from contextlib import asynccontextmanager
from typing import Any, Dict, List, AsyncIterator, Optional

from mcp.server.fastmcp import FastMCP, Context # Context might be needed for lifespan access

# Global Firestore client, will be initialized in lifespan
db: Optional[firestore.Client] = None
firebase_storage_bucket_name: Optional[str] = None # To store the bucket name

# SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), 'serviceAccountKey.json') # Fallback if env var not set

@asynccontextmanager
async def firebase_lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Manage Firebase Admin SDK initialization and shutdown."""
    global db, firebase_storage_bucket_name

    service_account_path_env = os.environ.get('SERVICE_ACCOUNT_KEY_PATH')
    firebase_storage_bucket_name = os.environ.get('FIREBASE_STORAGE_BUCKET')

    effective_service_account_path = service_account_path_env
    if not effective_service_account_path:
        effective_service_account_path = os.path.join(os.path.dirname(__file__), 'serviceAccountKey.json')
        print(f"SERVICE_ACCOUNT_KEY_PATH not set, falling back to local file: {effective_service_account_path}")
    else:
        print(f"Using SERVICE_ACCOUNT_KEY_PATH from environment: {effective_service_account_path}")

    if firebase_storage_bucket_name:
        print(f"FIREBASE_STORAGE_BUCKET from environment: {firebase_storage_bucket_name}")
    else:
        print("FIREBASE_STORAGE_BUCKET environment variable not set.")

    print("Attempting to initialize Firebase Admin SDK...")
    if os.path.exists(effective_service_account_path):
        try:
            cred = credentials.Certificate(effective_service_account_path)
            # Check if Firebase app is already initialized to prevent re-initialization error
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
            else:
                print("Firebase Admin SDK already initialized.")
            db = firestore.client()
            print("Firebase Admin SDK initialized successfully and Firestore client obtained.")
            yield # Server is active
        except Exception as e:
            print(f"Error initializing Firebase Admin SDK: {e}")
            print("Firebase tools will not be available. Please add a valid service account key.")
            # Still yield to allow the server to run, but tools should check 'db'
            yield
        finally:
            # Firebase Admin SDK doesn't have an explicit shutdown method for the app
            # If firebase_admin.get_app() is called, it can be deleted by firebase_admin.delete_app(app)
            # For simplicity, we'll skip explicit de-initialization here as it's often managed by process exit.
            print("Firebase lifespan context exited.")
    else:
        print(f"Service account key file not found at: {effective_service_account_path}")
        print("Firebase tools will not be available. Please add 'serviceAccountKey.json'.")
        yield # Server is active but Firebase is not connected


# Create an MCP server instance
# The name "MCPFirebaseServer" can be used by clients to identify this server.
mcp_server = FastMCP(
    name="MCPFirebaseServer",
    description="An MCP server to interact with Firebase Firestore.",
    lifespan=firebase_lifespan
)

@mcp_server.tool()
async def query_firestore_collection(collection_name: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieves documents from a specified Firestore collection.

    Args:
        collection_name: The name of the Firestore collection to query.
        limit: The maximum number of documents to return (default is 50).

    Returns:
        A list of documents from the collection, where each document is a dictionary.
        Returns an empty list if the collection doesn't exist or an error occurs.
    """
    global db
    if not db:
        print("Error: Firestore client not initialized. Cannot query collection.")
        return [{"error": "Firestore not initialized. Check server logs and serviceAccountKey.json."}]

    print(f"Querying collection: {collection_name} with limit {limit}")
    documents = []
    try:
        docs_ref = db.collection(collection_name).limit(limit).stream()
        for doc in docs_ref:
            doc_data = doc.to_dict()
            if doc_data: # Ensure doc_data is not None
                 doc_data['id'] = doc.id
                 documents.append(doc_data)
        print(f"Found {len(documents)} documents in '{collection_name}'.")
        return documents
    except Exception as e:
        print(f"Error querying collection '{collection_name}': {e}")
        return [{"error": f"Failed to query collection '{collection_name}': {str(e)}"}]

@mcp_server.tool()
async def add_document_to_firestore(collection_name: str, document_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adds a new document with an auto-generated ID to the specified Firestore collection.

    Args:
        collection_name: The name of the Firestore collection where the document will be added.
        document_data: A dictionary representing the document to add.

    Returns:
        A dictionary containing the success status and the ID of the new document, or an error message.
    """
    global db
    if not db:
        print("Error: Firestore client not initialized. Cannot add document.")
        return {"success": False, "error": "Firestore not initialized. Check server logs and serviceAccountKey.json."}

    print(f"Adding document to collection: {collection_name}")
    try:
        # add() returns a tuple: (timestamp, DocumentReference)
        timestamp, doc_ref = db.collection(collection_name).add(document_data)
        print(f"Document added with ID: {doc_ref.id} to collection '{collection_name}'.")
        return {"success": True, "id": doc_ref.id, "message": f"Document added to '{collection_name}'"}
    except Exception as e:
        print(f"Error adding document to '{collection_name}': {e}")
        return {"success": False, "error": f"Failed to add document to '{collection_name}': {str(e)}"}

@mcp_server.tool()
async def list_firestore_collections() -> List[Dict[str, str]]:
    """
    Lists all top-level collections in the Firestore database.

    Returns:
        A list of dictionaries, where each dictionary contains the 'id' of a collection.
        Returns an error message if Firestore is not initialized or an error occurs.
    """
    global db
    if not db:
        print("Error: Firestore client not initialized. Cannot list collections.")
        return [{"error": "Firestore not initialized. Check server logs."}]

    print("Listing all Firestore collections...")
    collections_list = []
    try:
        for coll_ref in db.collections():
            collections_list.append({"id": coll_ref.id})
        print(f"Found {len(collections_list)} collections.")
        return collections_list
    except Exception as e:
        print(f"Error listing collections: {e}")
        return [{"error": f"Failed to list collections: {str(e)}"}]

@mcp_server.tool()
async def get_firestore_document(collection_name: str, document_id: str) -> Dict[str, Any]:
    """
    Retrieves a specific document from a Firestore collection by its ID.

    Args:
        collection_name: The name of the Firestore collection.
        document_id: The ID of the document to retrieve.

    Returns:
        A dictionary representing the document data, including its ID.
        Returns an error message if the document doesn't exist, Firestore is not initialized, or an error occurs.
    """
    global db
    if not db:
        print("Error: Firestore client not initialized. Cannot get document.")
        return {"error": "Firestore not initialized. Check server logs."}

    print(f"Getting document with ID '{document_id}' from collection '{collection_name}'...")
    try:
        doc_ref = db.collection(collection_name).document(document_id)
        doc = doc_ref.get()
        if doc.exists:
            doc_data = doc.to_dict()
            if doc_data: # Should always be true if doc.exists
                doc_data['id'] = doc.id
                print(f"Document '{document_id}' found in '{collection_name}'.")
                return doc_data
            else: # Should not happen if doc.exists, but good to handle
                print(f"Document '{document_id}' found but has no data in '{collection_name}'.")
                return {"id": doc.id, "data": None, "message": "Document exists but contains no data."}
        else:
            print(f"Document with ID '{document_id}' not found in collection '{collection_name}'.")
            return {"error": f"Document '{document_id}' not found in '{collection_name}'."}
    except Exception as e:
        print(f"Error getting document '{document_id}' from '{collection_name}': {e}")
        return {"error": f"Failed to get document '{document_id}' from '{collection_name}': {str(e)}"}

@mcp_server.tool()
async def list_document_subcollections(collection_name: str, document_id: str) -> List[Dict[str, str]]:
    """
    Lists all subcollections of a specified document in Firestore.

    Args:
        collection_name: The name of the parent collection.
        document_id: The ID of the document whose subcollections are to be listed.

    Returns:
        A list of dictionaries, where each dictionary contains the 'id' of a subcollection.
        Returns an error message if Firestore is not initialized, the document doesn't exist, or an error occurs.
    """
    global db
    if not db:
        print("Error: Firestore client not initialized. Cannot list subcollections.")
        return [{"error": "Firestore not initialized. Check server logs."}]

    print(f"Listing subcollections for document '{document_id}' in collection '{collection_name}'...")
    try:
        doc_ref = db.collection(collection_name).document(document_id)
        # First, check if the document exists, as get_collections() might not error on a non-existent doc path directly
        doc_snapshot = doc_ref.get()
        if not doc_snapshot.exists:
            print(f"Document '{document_id}' not found in collection '{collection_name}'. Cannot list subcollections.")
            return [{"error": f"Document '{document_id}' not found in '{collection_name}'."}]

        subcollections = []
        for coll_ref in doc_ref.collections():
            subcollections.append({"id": coll_ref.id})
        
        if subcollections:
            print(f"Found {len(subcollections)} subcollections for document '{document_id}'.")
        else:
            print(f"No subcollections found for document '{document_id}' in '{collection_name}'.")
        return subcollections
    except Exception as e:
        print(f"Error listing subcollections for document '{document_id}': {e}")
        return [{"error": f"Failed to list subcollections for '{document_id}': {str(e)}"}]

if __name__ == "__main__":
    print("Starting MCP Firebase Server...")
    # This will typically run the server using stdio transport
    mcp_server.run() 