# vector_db.py - Vector Database Integration for MFASHA AI
import chromadb
from chromadb.config import Settings
import os
import hashlib
import json
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
import sqlite3

class VectorDatabase:
    """Vector Database for MFASHA AI using ChromaDB"""
    
    def __init__(self, persist_directory="./chroma_db"):
        """Initialize vector database"""
        self.persist_directory = persist_directory
        
        # Create directory if it doesn't exist
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Initialize embedding model
        print("🔄 Loading embedding model...")
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ Embedding model loaded")
        except Exception as e:
            print(f"❌ Error loading embedding model: {e}")
            print("💡 Install with: pip install sentence-transformers")
            raise
        
        # Create or get collections
        try:
            self.documents_collection = self.client.get_or_create_collection(
                name="documents",
                metadata={"hnsw:space": "cosine"}
            )
            
            self.conversations_collection = self.client.get_or_create_collection(
                name="conversations",
                metadata={"hnsw:space": "cosine"}
            )
            
            self.knowledge_collection = self.client.get_or_create_collection(
                name="knowledge",
                metadata={"hnsw:space": "cosine"}
            )
            
            print("✅ Vector database collections created")
        except Exception as e:
            print(f"❌ Error creating collections: {e}")
            raise
        
        print("✅ Vector database initialized")
    
    def _get_embedding(self, texts):
        """Get embeddings for texts"""
        if isinstance(texts, str):
            texts = [texts]
        return self.embedding_model.encode(texts).tolist()
    
    def add_document(self, text, metadata, collection="documents"):
        """Add a document to vector database"""
        try:
            # Generate unique ID
            doc_id = hashlib.md5(f"{text}_{datetime.now().timestamp()}".encode()).hexdigest()
            
            # Get appropriate collection
            if collection == "documents":
                coll = self.documents_collection
            elif collection == "conversations":
                coll = self.conversations_collection
            else:
                coll = self.knowledge_collection
            
            # Add to collection
            coll.add(
                documents=[text],
                metadatas=[metadata],
                ids=[doc_id],
                embeddings=self._get_embedding([text])
            )
            
            return doc_id
        except Exception as e:
            print(f"❌ Error adding document: {e}")
            return None
    
    def add_documents_batch(self, documents, metadatas, collection="documents"):
        """Add multiple documents at once"""
        try:
            if not documents:
                return []
            
            if collection == "documents":
                coll = self.documents_collection
            elif collection == "conversations":
                coll = self.conversations_collection
            else:
                coll = self.knowledge_collection
            
            # Generate IDs
            ids = [hashlib.md5(f"{doc}_{datetime.now().timestamp()}_{i}".encode()).hexdigest() 
                   for i, doc in enumerate(documents)]
            
            # Get embeddings
            embeddings = self._get_embedding(documents)
            
            # Add to collection
            coll.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
            
            return ids
        except Exception as e:
            print(f"❌ Error adding batch: {e}")
            return []
    
    def search(self, query, collection="documents", n_results=5):
        """Search for similar documents"""
        try:
            if collection == "documents":
                coll = self.documents_collection
            elif collection == "conversations":
                coll = self.conversations_collection
            else:
                coll = self.knowledge_collection
            
            results = coll.query(
                query_texts=[query],
                n_results=n_results,
                query_embeddings=self._get_embedding([query])
            )
            
            return results
        except Exception as e:
            print(f"❌ Error searching: {e}")
            return None
    
    def search_by_metadata(self, metadata_filter, collection="documents", n_results=10):
        """Search documents by metadata"""
        try:
            if collection == "documents":
                coll = self.documents_collection
            elif collection == "conversations":
                coll = self.conversations_collection
            else:
                coll = self.knowledge_collection
            
            results = coll.get(
                where=metadata_filter,
                limit=n_results
            )
            
            return results
        except Exception as e:
            print(f"❌ Error searching by metadata: {e}")
            return None
    
    def delete_document(self, doc_id, collection="documents"):
        """Delete a document from vector database"""
        try:
            if collection == "documents":
                coll = self.documents_collection
            elif collection == "conversations":
                coll = self.conversations_collection
            else:
                coll = self.knowledge_collection
            
            coll.delete(ids=[doc_id])
            return True
        except Exception as e:
            print(f"❌ Error deleting document: {e}")
            return False
    
    def get_collection_stats(self, collection="documents"):
        """Get statistics about a collection"""
        try:
            if collection == "documents":
                coll = self.documents_collection
                count = coll.count()
            elif collection == "conversations":
                coll = self.conversations_collection
                count = coll.count()
            else:
                coll = self.knowledge_collection
                count = coll.count()
            
            return {
                "collection": collection,
                "document_count": count,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            return None
    
    def get_collection_info(self):
        """Get information about all collections"""
        try:
            info = {
                "documents": self.documents_collection.count(),
                "conversations": self.conversations_collection.count(),
                "knowledge": self.knowledge_collection.count(),
                "persist_directory": self.persist_directory
            }
            return info
        except Exception as e:
            print(f"❌ Error getting collection info: {e}")
            return {"error": str(e)}
    
    def process_uploaded_file(self, file_path, filename, user_id):
        """Process an uploaded file and add to vector database"""
        try:
            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            
            # Extract text based on file type
            text_content = ""
            
            if file_ext in ['txt', 'py', 'js', 'html', 'css', 'json', 'xml', 'csv', 'md']:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text_content = f.read()
            
            elif file_ext == 'pdf':
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        for page in pdf_reader.pages[:20]:  # First 20 pages
                            text_content += page.extract_text() + "\n"
                except ImportError:
                    return {
                        "success": False,
                        "message": "PyPDF2 not installed. Install with: pip install PyPDF2"
                    }
            
            elif file_ext in ['doc', 'docx']:
                try:
                    import docx
                    doc = docx.Document(file_path)
                    text_content = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                except ImportError:
                    return {
                        "success": False,
                        "message": "python-docx not installed. Install with: pip install python-docx"
                    }
            
            elif file_ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
                try:
                    from PIL import Image
                    img = Image.open(file_path)
                    text_content = f"Image file: {filename}\nDimensions: {img.size[0]}x{img.size[1]} pixels\nMode: {img.mode}"
                except ImportError:
                    text_content = f"Image file: {filename} (Pillow not installed for detailed analysis)"
            
            else:
                return {
                    "success": False,
                    "message": f"Unsupported file type: {file_ext}"
                }
            
            if text_content:
                # Split into chunks for better retrieval
                chunks = self._chunk_text(text_content, chunk_size=1000, overlap=100)
                
                # Add each chunk to vector database
                documents = []
                metadatas = []
                
                for i, chunk in enumerate(chunks):
                    if chunk.strip():  # Only add non-empty chunks
                        documents.append(chunk)
                        metadatas.append({
                            "filename": filename,
                            "user_id": user_id,
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "file_type": file_ext,
                            "uploaded_at": datetime.now().isoformat(),
                            "file_path": file_path
                        })
                
                if documents:
                    doc_ids = self.add_documents_batch(documents, metadatas, "knowledge")
                    
                    return {
                        "success": True,
                        "chunks_added": len(documents),
                        "doc_ids": doc_ids,
                        "message": f"✅ Added {len(documents)} chunks from {filename} to knowledge base"
                    }
                else:
                    return {
                        "success": False,
                        "message": "No valid content extracted from file"
                    }
            else:
                return {
                    "success": False,
                    "message": "Could not extract text from file"
                }
                
        except Exception as e:
            print(f"Error processing file: {e}")
            return {
                "success": False,
                "message": f"Error processing file: {str(e)}"
            }
    
    def _chunk_text(self, text, chunk_size=1000, overlap=100):
        """Split text into overlapping chunks"""
        if not text:
            return []
        
        words = text.split()
        chunks = []
        
        if len(words) <= chunk_size:
            return [text]
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
        
        return chunks
    
    def search_knowledge_base(self, query, user_id=None, n_results=5):
        """Search the knowledge base for relevant information"""
        try:
            # Build where filter if user_id provided
            where_filter = None
            if user_id:
                where_filter = {"user_id": user_id}
            
            # Search
            results = self.knowledge_collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter,
                query_embeddings=self._get_embedding([query])
            )
            
            return results
        except Exception as e:
            print(f"❌ Error searching knowledge base: {e}")
            return None
    
    def add_conversation_memory(self, user_message, bot_response, user_id):
        """Add conversation to vector memory for context"""
        try:
            text = f"User: {user_message}\nAI: {bot_response}"
            metadata = {
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "user_message": user_message[:100],
                "bot_response": bot_response[:100],
                "type": "conversation"
            }
            
            doc_id = self.add_document(text, metadata, "conversations")
            return doc_id
        except Exception as e:
            print(f"❌ Error adding conversation memory: {e}")
            return None
    
    def get_related_conversations(self, query, user_id, n_results=3):
        """Get related past conversations for context"""
        try:
            results = self.conversations_collection.query(
                query_texts=[query],
                n_results=n_results,
                where={"user_id": user_id},
                query_embeddings=self._get_embedding([query])
            )
            return results
        except Exception as e:
            print(f"❌ Error getting related conversations: {e}")
            return None
    
    def delete_user_data(self, user_id):
        """Delete all data for a specific user"""
        try:
            # Delete from knowledge collection
            results = self.knowledge_collection.get(where={"user_id": user_id})
            if results and results['ids']:
                self.knowledge_collection.delete(ids=results['ids'])
            
            # Delete from conversations collection
            results = self.conversations_collection.get(where={"user_id": user_id})
            if results and results['ids']:
                self.conversations_collection.delete(ids=results['ids'])
            
            return True
        except Exception as e:
            print(f"❌ Error deleting user data: {e}")
            return False

# Global instance
vector_db = None

def init_vector_db():
    """Initialize vector database globally"""
    global vector_db
    try:
        vector_db = VectorDatabase()
        return vector_db
    except Exception as e:
        print(f"❌ Failed to initialize vector database: {e}")
        print("💡 Install required packages: pip install chromadb sentence-transformers")
        return None