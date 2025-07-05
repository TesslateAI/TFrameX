# tframex/mcp/content.py
"""
Enhanced content handling for MCP with multi-modal support and schema validation.
Provides structured output handling and content type management.
"""
import base64
import json
import logging
import mimetypes
from io import BytesIO
from typing import Dict, Any, Optional, Union, List, Type
from dataclasses import dataclass, field
from enum import Enum
import jsonschema
from pathlib import Path

logger = logging.getLogger("tframex.mcp.content")


class ContentType(Enum):
    """Supported content types."""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    BINARY = "binary"
    JSON = "json"
    STRUCTURED = "structured"


@dataclass
class ContentMetadata:
    """Metadata for content objects."""
    mime_type: Optional[str] = None
    encoding: Optional[str] = None
    size: Optional[int] = None
    checksum: Optional[str] = None
    schema_url: Optional[str] = None
    validation_status: Optional[str] = None
    source: Optional[str] = None
    annotations: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Content:
    """
    Represents multi-modal content with metadata and validation.
    """
    type: ContentType
    data: Union[str, bytes, Dict[str, Any]]
    metadata: ContentMetadata = field(default_factory=ContentMetadata)
    
    def to_mcp_format(self) -> Dict[str, Any]:
        """Convert to MCP content format."""
        result = {
            "type": self.type.value
        }
        
        if self.type == ContentType.TEXT:
            result["text"] = str(self.data)
        elif self.type == ContentType.IMAGE:
            if isinstance(self.data, bytes):
                result["data"] = base64.b64encode(self.data).decode('utf-8')
            else:
                result["data"] = str(self.data)
            result["mimeType"] = self.metadata.mime_type or "image/png"
        elif self.type == ContentType.AUDIO:
            if isinstance(self.data, bytes):
                result["data"] = base64.b64encode(self.data).decode('utf-8')
            else:
                result["data"] = str(self.data)
            result["mimeType"] = self.metadata.mime_type or "audio/wav"
        elif self.type == ContentType.JSON:
            result["data"] = self.data if isinstance(self.data, dict) else json.loads(str(self.data))
        elif self.type == ContentType.STRUCTURED:
            result["data"] = self.data
            if self.metadata.schema_url:
                result["schemaUrl"] = self.metadata.schema_url
        else:
            result["data"] = str(self.data)
        
        return result
    
    @classmethod
    def from_mcp_format(cls, mcp_content: Dict[str, Any]) -> "Content":
        """Create content from MCP format."""
        content_type = ContentType(mcp_content.get("type", "text"))
        
        metadata = ContentMetadata(
            mime_type=mcp_content.get("mimeType"),
            schema_url=mcp_content.get("schemaUrl")
        )
        
        if content_type == ContentType.TEXT:
            data = mcp_content.get("text", "")
        elif content_type in [ContentType.IMAGE, ContentType.AUDIO]:
            data_str = mcp_content.get("data", "")
            try:
                # Try to decode base64
                data = base64.b64decode(data_str)
            except Exception:
                # Fallback to string data (might be URL or text)
                data = data_str
        else:
            data = mcp_content.get("data", {})
        
        return cls(type=content_type, data=data, metadata=metadata)
    
    def validate_schema(self, schema: Dict[str, Any]) -> bool:
        """
        Validate content against JSON schema.
        
        Args:
            schema: JSON schema to validate against
            
        Returns:
            True if valid
        """
        if self.type not in [ContentType.JSON, ContentType.STRUCTURED]:
            logger.warning(f"Schema validation not supported for {self.type}")
            return False
        
        try:
            jsonschema.validate(self.data, schema)
            self.metadata.validation_status = "valid"
            return True
        except jsonschema.ValidationError as e:
            logger.error(f"Schema validation failed: {e}")
            self.metadata.validation_status = f"invalid: {e.message}"
            return False
        except Exception as e:
            logger.error(f"Schema validation error: {e}")
            self.metadata.validation_status = f"error: {str(e)}"
            return False


class ContentProcessor:
    """
    Processes and validates multi-modal content.
    """
    
    def __init__(self, 
                 max_content_size: int = 10 * 1024 * 1024,  # 10MB
                 supported_image_types: Optional[List[str]] = None,
                 supported_audio_types: Optional[List[str]] = None):
        """
        Initialize content processor.
        
        Args:
            max_content_size: Maximum content size in bytes
            supported_image_types: Supported image MIME types
            supported_audio_types: Supported audio MIME types
        """
        self.max_content_size = max_content_size
        self.supported_image_types = supported_image_types or [
            "image/png", "image/jpeg", "image/gif", "image/webp"
        ]
        self.supported_audio_types = supported_audio_types or [
            "audio/wav", "audio/mp3", "audio/ogg", "audio/flac"
        ]
        
        # Schema cache
        self._schema_cache: Dict[str, Dict[str, Any]] = {}
    
    async def process_content(self, raw_content: Union[str, bytes, Dict[str, Any]],
                            content_type: Optional[ContentType] = None,
                            mime_type: Optional[str] = None,
                            source: Optional[str] = None) -> Content:
        """
        Process raw content into structured Content object.
        
        Args:
            raw_content: Raw content data
            content_type: Content type hint
            mime_type: MIME type hint
            source: Content source (file path, URL, etc.)
            
        Returns:
            Processed Content object
        """
        # Detect content type if not provided
        if content_type is None:
            content_type = self._detect_content_type(raw_content, mime_type)
        
        # Create metadata
        metadata = ContentMetadata(
            mime_type=mime_type,
            source=source,
            size=self._calculate_size(raw_content)
        )
        
        # Validate size
        if metadata.size and metadata.size > self.max_content_size:
            raise ValueError(f"Content size ({metadata.size}) exceeds maximum ({self.max_content_size})")
        
        # Create content object
        content = Content(
            type=content_type,
            data=raw_content,
            metadata=metadata
        )
        
        # Type-specific processing
        await self._process_by_type(content)
        
        return content
    
    def _detect_content_type(self, data: Union[str, bytes, Dict[str, Any]], 
                           mime_type: Optional[str]) -> ContentType:
        """Detect content type from data and MIME type."""
        
        # Use MIME type if available
        if mime_type:
            if mime_type.startswith("image/"):
                return ContentType.IMAGE
            elif mime_type.startswith("audio/"):
                return ContentType.AUDIO
            elif mime_type.startswith("video/"):
                return ContentType.VIDEO
            elif mime_type == "application/json":
                return ContentType.JSON
        
        # Detect from data type
        if isinstance(data, dict):
            return ContentType.STRUCTURED
        elif isinstance(data, bytes):
            # Try to detect from magic bytes
            if data.startswith(b'\x89PNG'):
                return ContentType.IMAGE
            elif data.startswith(b'\xff\xd8\xff'):  # JPEG
                return ContentType.IMAGE
            elif data.startswith(b'RIFF') and b'WAVE' in data[:12]:
                return ContentType.AUDIO
            else:
                return ContentType.BINARY
        else:
            # String data - check if it's JSON
            try:
                json.loads(str(data))
                return ContentType.JSON
            except (json.JSONDecodeError, ValueError):
                return ContentType.TEXT
    
    def _calculate_size(self, data: Union[str, bytes, Dict[str, Any]]) -> int:
        """Calculate content size in bytes."""
        if isinstance(data, bytes):
            return len(data)
        elif isinstance(data, str):
            return len(data.encode('utf-8'))
        elif isinstance(data, dict):
            return len(json.dumps(data).encode('utf-8'))
        else:
            return len(str(data).encode('utf-8'))
    
    async def _process_by_type(self, content: Content) -> None:
        """Apply type-specific processing."""
        
        if content.type == ContentType.IMAGE:
            await self._process_image(content)
        elif content.type == ContentType.AUDIO:
            await self._process_audio(content)
        elif content.type == ContentType.JSON:
            await self._process_json(content)
        elif content.type == ContentType.STRUCTURED:
            await self._process_structured(content)
    
    async def _process_image(self, content: Content) -> None:
        """Process image content."""
        # Validate MIME type
        if content.metadata.mime_type not in self.supported_image_types:
            logger.warning(f"Unsupported image type: {content.metadata.mime_type}")
        
        # Add image-specific metadata
        if isinstance(content.data, bytes):
            try:
                # Could add PIL/Pillow integration here for size detection
                content.metadata.annotations["format"] = "binary"
            except Exception as e:
                logger.debug(f"Image processing error: {e}")
    
    async def _process_audio(self, content: Content) -> None:
        """Process audio content."""
        # Validate MIME type
        if content.metadata.mime_type not in self.supported_audio_types:
            logger.warning(f"Unsupported audio type: {content.metadata.mime_type}")
        
        # Add audio-specific metadata
        content.metadata.annotations["format"] = "binary"
    
    async def _process_json(self, content: Content) -> None:
        """Process JSON content."""
        # Ensure data is parsed
        if isinstance(content.data, str):
            try:
                content.data = json.loads(content.data)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON content: {e}")
                raise ValueError(f"Invalid JSON: {e}")
    
    async def _process_structured(self, content: Content) -> None:
        """Process structured content."""
        # Validate against schema if available
        if content.metadata.schema_url:
            schema = await self._load_schema(content.metadata.schema_url)
            if schema:
                content.validate_schema(schema)
    
    async def _load_schema(self, schema_url: str) -> Optional[Dict[str, Any]]:
        """Load JSON schema from URL or cache."""
        if schema_url in self._schema_cache:
            return self._schema_cache[schema_url]
        
        try:
            # For file:// URLs, load from filesystem
            if schema_url.startswith("file://"):
                file_path = Path(schema_url[7:])  # Remove file://
                if file_path.exists():
                    with open(file_path, 'r') as f:
                        schema = json.load(f)
                        self._schema_cache[schema_url] = schema
                        return schema
            
            # For HTTP URLs, would implement HTTP loading
            # For now, return None
            logger.warning(f"Schema loading not implemented for: {schema_url}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to load schema from {schema_url}: {e}")
            return None


class SchemaValidator:
    """
    JSON Schema validation for structured content.
    """
    
    def __init__(self):
        """Initialize schema validator."""
        self._validator_cache: Dict[str, jsonschema.protocols.Validator] = {}
    
    def validate(self, data: Any, schema: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate data against schema.
        
        Args:
            data: Data to validate
            schema: JSON schema
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Create or get cached validator
            schema_key = json.dumps(schema, sort_keys=True)
            if schema_key not in self._validator_cache:
                self._validator_cache[schema_key] = jsonschema.Draft7Validator(schema)
            
            validator = self._validator_cache[schema_key]
            
            # Validate
            errors = list(validator.iter_errors(data))
            if errors:
                error_msg = "; ".join([error.message for error in errors[:3]])  # First 3 errors
                return False, error_msg
            
            return True, None
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def create_schema_from_example(self, example_data: Any) -> Dict[str, Any]:
        """
        Generate JSON schema from example data.
        
        Args:
            example_data: Example data to generate schema from
            
        Returns:
            Generated JSON schema
        """
        def infer_type(value):
            if isinstance(value, bool):
                return "boolean"
            elif isinstance(value, int):
                return "integer"
            elif isinstance(value, float):
                return "number"
            elif isinstance(value, str):
                return "string"
            elif isinstance(value, list):
                return "array"
            elif isinstance(value, dict):
                return "object"
            else:
                return "string"  # Fallback
        
        def generate_schema(data):
            if isinstance(data, dict):
                properties = {}
                required = []
                
                for key, value in data.items():
                    properties[key] = generate_schema(value)
                    required.append(key)
                
                return {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            
            elif isinstance(data, list):
                if data:
                    # Use first item as template
                    item_schema = generate_schema(data[0])
                else:
                    item_schema = {"type": "string"}  # Default
                
                return {
                    "type": "array",
                    "items": item_schema
                }
            
            else:
                return {"type": infer_type(data)}
        
        return generate_schema(example_data)


class ContentTypeDetector:
    """
    Detects content type from file extensions and magic bytes.
    """
    
    # Magic byte patterns for common file types
    MAGIC_BYTES = {
        b'\x89PNG\r\n\x1a\n': 'image/png',
        b'\xff\xd8\xff': 'image/jpeg',
        b'GIF87a': 'image/gif',
        b'GIF89a': 'image/gif',
        b'RIFF': 'audio/wav',  # Needs further checking
        b'\x1a\x45\xdf\xa3': 'video/webm',
        b'ftypmp4': 'video/mp4',
        b'%PDF': 'application/pdf',
    }
    
    @classmethod
    def detect_from_filename(cls, filename: str) -> Optional[str]:
        """Detect MIME type from filename."""
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type
    
    @classmethod
    def detect_from_bytes(cls, data: bytes) -> Optional[str]:
        """Detect MIME type from magic bytes."""
        for magic, mime_type in cls.MAGIC_BYTES.items():
            if data.startswith(magic):
                # Special case for RIFF (could be WAV or AVI)
                if magic == b'RIFF' and b'WAVE' in data[:12]:
                    return 'audio/wav'
                elif magic == b'RIFF' and b'AVI ' in data[:12]:
                    return 'video/avi'
                return mime_type
        
        return None
    
    @classmethod
    def detect(cls, data: Union[str, bytes], filename: Optional[str] = None) -> Optional[str]:
        """Detect MIME type from data and/or filename."""
        # Try filename first
        if filename:
            mime_type = cls.detect_from_filename(filename)
            if mime_type:
                return mime_type
        
        # Try magic bytes
        if isinstance(data, bytes):
            return cls.detect_from_bytes(data)
        
        return None