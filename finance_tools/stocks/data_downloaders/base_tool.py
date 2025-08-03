"""Base tool class and registration system for Enhanced Memory Agent Framework."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import logging
import inspect
import pandas as pd
from datetime import datetime
 

logger = logging.getLogger(__name__)

class ToolCategory(Enum):
    """Broad categories for tool classification."""
    DATA_RETRIEVAL = "data_retrieval"
    DATA_ANALYSIS = "data_analysis"
    WEB_SCRAPING = "web_scraping"
    FINANCIAL = "financial"
    IMAGE_PROCESSING = "image_processing"
    TEXT_PROCESSING = "text_processing"
    FILE_OPERATIONS = "file_operations"
    API_INTEGRATION = "api_integration"
    SEARCH = "search"
    COMPUTATION = "computation"
    VISUALIZATION = "visualization"
    COMMUNICATION = "communication"
    UTILITY = "utility"
    RESEARCH = "research"
    AUTOMATION = "automation"
    MACHINE_LEARNING = "machine_learning"
    DATABASE = "database"
    CLOUD_SERVICES = "cloud_services"
    SECURITY = "security"
    MONITORING = "monitoring"


@dataclass
class ToolFunctionSpec:
    """Specification for a tool function/method."""
    name: str
    description: str
    parameters: Dict[str, Any]
    returns: Dict[str, Any]
    examples: List[str] = field(default_factory=list)
    complexity: str = "medium"  # low, medium, high
    execution_time_estimate: int = 60  # seconds


@dataclass
class ToolMetadata:
    """Comprehensive metadata for a tool."""
    tool_id: str
    name: str
    description: str
    version: str
    category: ToolCategory
    subcategories: List[str] = field(default_factory=list)
    
    # Capabilities and functions
    functions: List[ToolFunctionSpec] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    
    # Semantic information
    keywords: List[str] = field(default_factory=list)
    synonyms: List[str] = field(default_factory=list)
    use_cases: List[str] = field(default_factory=list)
    
    # Technical specifications
    input_types: List[str] = field(default_factory=list)
    output_types: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    
    # Quality and reliability
    reliability_score: float = 0.8
    performance_rating: float = 0.8
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Usage information
    usage_count: int = 0
    success_rate: float = 1.0
    average_execution_time: float = 60.0
    
    # Documentation
    documentation_url: Optional[str] = None
    examples: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result['category'] = self.category.value
        return result
    
    def get_searchable_text(self) -> str:
        """Get all searchable text content for semantic matching."""
        text_parts = [
            self.name,
            self.description,
            ' '.join(self.keywords),
            ' '.join(self.synonyms),
            ' '.join(self.use_cases),
            ' '.join(self.capabilities),
            ' '.join(self.subcategories)
        ]
        
        # Add function descriptions
        for func in self.functions:
            text_parts.extend([func.name, func.description])
        
        return ' '.join(filter(None, text_parts)).lower()


class ToolArgumentType(Enum):
    """Supported argument types for tools."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    DATE = "date"
    DATETIME = "datetime"


@dataclass
class ToolArgument:
    """Represents a tool argument specification."""
    name: str
    type: ToolArgumentType
    description: str
    required: bool = True
    default: Any = None
    choices: Optional[List[Any]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None  # For string validation
    
    def validate(self, value: Any) -> bool:
        """Validate argument value against specification."""
        if value is None:
            return not self.required
            
        # Type validation
        if self.type == ToolArgumentType.STRING and not isinstance(value, str):
            return False
        elif self.type == ToolArgumentType.INTEGER and not isinstance(value, int):
            return False
        elif self.type == ToolArgumentType.FLOAT and not isinstance(value, (int, float)):
            return False
        elif self.type == ToolArgumentType.BOOLEAN and not isinstance(value, bool):
            return False
        elif self.type == ToolArgumentType.LIST and not isinstance(value, list):
            return False
        elif self.type == ToolArgumentType.DICT and not isinstance(value, dict):
            return False
            
        # Range validation
        if self.min_value is not None and value < self.min_value:
            return False
        if self.max_value is not None and value > self.max_value:
            return False
            
        # Choices validation
        if self.choices is not None and value not in self.choices:
            return False
            
        return True


@dataclass
class ToolCapability:
    """Represents a tool capability/feature."""
    name: str
    description: str
    input_types: List[ToolArgumentType]
    output_type: str
    examples: List[str] = field(default_factory=list)


@dataclass 
class ToolResult:
    """Standardized tool execution result."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'metadata': self.metadata,
            'execution_time': self.execution_time
        }
    
    def to_json(self) -> str:
        """Convert result to JSON string."""
        return json.dumps(self.to_dict(), default=str, indent=2)
    
    def as_df(self):
        """Convert result to DataFrame using get_as_df function."""
        try:
            from ...utils.dataframe_utils import get_as_df
            return get_as_df(self)
        except ImportError:
            # Fallback if get_as_df is not available
            if hasattr(self.data, 'data') and isinstance(self.data['data'], pd.DataFrame):
                return self.data['data']
            elif isinstance(self.data, pd.DataFrame):
                return self.data
            else:
                raise ValueError("Cannot convert result to DataFrame")


class BaseTool(ABC):
    """Abstract base class for all tools in the framework."""
    
    def __init__(self, name: str, description: str, version: str = "1.0.0"):
        self.name = name
        self.description = description
        self.version = version
        self._arguments: List[ToolArgument] = []
        self._capabilities: List[ToolCapability] = []
        self._setup_complete = False
        
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given arguments."""
        pass
    
    def get_name(self) -> str:
        """Get tool name."""
        return self.name
    
    def get_description(self) -> str:
        """Get tool description."""
        return self.description
    
    def get_version(self) -> str:
        """Get tool version."""
        return self.version
    
    def get_arguments(self) -> List[ToolArgument]:
        """Get list of tool arguments."""
        return self._arguments.copy()
    
    def get_capabilities(self) -> List[ToolCapability]:
        """Get list of tool capabilities."""
        return self._capabilities.copy()
    
    def add_argument(self, argument: ToolArgument) -> None:
        """Add an argument specification."""
        self._arguments.append(argument)
    
    def add_capability(self, capability: ToolCapability) -> None:
        """Add a capability specification."""
        self._capabilities.append(capability)
    
    def validate_arguments(self, **kwargs) -> Dict[str, Any]:
        """Validate provided arguments against specifications."""
        errors = []
        validated_args = {}
        
        # Check required arguments
        for arg in self._arguments:
            if arg.required and arg.name not in kwargs:
                errors.append(f"Required argument '{arg.name}' is missing")
                continue
                
            value = kwargs.get(arg.name, arg.default)
            if not arg.validate(value):
                errors.append(f"Invalid value for argument '{arg.name}': {value}")
                continue
                
            validated_args[arg.name] = value
        
        # Check for unexpected arguments
        expected_args = {arg.name for arg in self._arguments}
        unexpected_args = set(kwargs.keys()) - expected_args
        if unexpected_args:
            errors.append(f"Unexpected arguments: {', '.join(unexpected_args)}")
        
        if errors:
            raise ValueError(f"Argument validation failed: {'; '.join(errors)}")
            
        return validated_args
    
    def get_argument_list(self) -> Dict[str, Dict[str, Any]]:
        """Get structured argument list for documentation."""
        return {
            arg.name: {
                'type': arg.type.value,
                'description': arg.description,
                'required': arg.required,
                'default': arg.default,
                'choices': arg.choices,
                'min_value': arg.min_value,
                'max_value': arg.max_value,
                'pattern': arg.pattern
            }
            for arg in self._arguments
        }
    
    def get_usage_info(self) -> Dict[str, Any]:
        """Get comprehensive tool usage information."""
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'arguments': self.get_argument_list(),
            'capabilities': [
                {
                    'name': cap.name,
                    'description': cap.description,
                    'input_types': [t.value for t in cap.input_types],
                    'output_type': cap.output_type,
                    'examples': cap.examples
                }
                for cap in self._capabilities
            ]
        }
    
    def setup(self) -> None:
        """Setup tool (called once after registration)."""
        if not self._setup_complete:
            self._setup_tool()
            self._setup_complete = True
    
    def _setup_tool(self) -> None:
        """Override this method to perform tool-specific setup."""
        pass


class ToolRegistry:
    """Global registry for managing tools."""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._tool_functions: Dict[str, Callable] = {}
        
    def register(self, tool: BaseTool) -> None:
        """Register a tool instance."""
        if tool.name in self._tools:
            logger.warning(f"Tool '{tool.name}' is already registered. Overwriting.")
        
        self._tools[tool.name] = tool
        tool.setup()  # Setup the tool after registration
        logger.info(f"Registered tool: {tool.name} v{tool.version}")
    
    def register_function(self, name: str, func: Callable, tool_class: type) -> None:
        """Register a function-based tool."""
        if name in self._tool_functions:
            logger.warning(f"Function tool '{name}' is already registered. Overwriting.")
        
        self._tool_functions[name] = func
        
        # Create a wrapper tool instance for consistency
        wrapper_tool = self._create_function_wrapper(name, func, tool_class)
        self.register(wrapper_tool)
    
    def _create_function_wrapper(self, name: str, func: Callable, tool_class: type) -> BaseTool:
        """Create a BaseTool wrapper for function-based tools."""
        class FunctionToolWrapper(BaseTool):
            def __init__(self):
                super().__init__(name, func.__doc__ or f"Function-based tool: {name}")
                self._func = func
                self._tool_class = tool_class
                
                # Copy arguments and capabilities from the tool class if available
                if hasattr(tool_class, '_arguments'):
                    self._arguments = tool_class._arguments.copy()
                if hasattr(tool_class, '_capabilities'):
                    self._capabilities = tool_class._capabilities.copy()
            
            def execute(self, **kwargs) -> ToolResult:
                try:
                    validated_args = self.validate_arguments(**kwargs)
                    result = self._func(**validated_args)
                    
                    if isinstance(result, ToolResult):
                        return result
                    else:
                        return ToolResult(success=True, data=result)
                except Exception as e:
                    return ToolResult(success=False, error=str(e))
        
        return FunctionToolWrapper()
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a registered tool by name."""
        return self._tools.get(name)
    
    def get_all_tools(self) -> Dict[str, BaseTool]:
        """Get all registered tools."""
        return self._tools.copy()
    
    def get_tool_names(self) -> List[str]:
        """Get list of all registered tool names."""
        return list(self._tools.keys())
    
    def execute_tool(self, name: str, **kwargs) -> ToolResult:
        """Execute a tool by name."""
        tool = self.get_tool(name)
        if not tool:
            return ToolResult(
                success=False, 
                error=f"Tool '{name}' not found. Available tools: {', '.join(self.get_tool_names())}"
            )
        
        try:
            return tool.execute(**kwargs)
        except Exception as e:
            return ToolResult(success=False, error=f"Tool execution failed: {str(e)}")
    
    def get_tools_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all registered tools."""
        return {name: tool.get_usage_info() for name, tool in self._tools.items()}


# Global tool registry instance
_global_registry = ToolRegistry()


def register_tool(name: str = None):
    """Decorator to register tools with both registries."""
    def decorator(cls_or_func):
        tool_name = name or (cls_or_func.__name__ if hasattr(cls_or_func, '__name__') else str(cls_or_func))
        
        if isinstance(cls_or_func, type) and issubclass(cls_or_func, BaseTool):
            # Class-based tool
            tool_instance = cls_or_func()
            _global_registry.register(tool_instance)
            
            # Also register with semantic registry
            metadata = _generate_tool_metadata(tool_instance)
            print(metadata)
            
        elif callable(cls_or_func):
            # Function-based tool
            _global_registry.register_function(tool_name, cls_or_func, type(cls_or_func))
            
            # Generate metadata for function-based tool
            wrapper_tool = _global_registry.get_tool(tool_name)
            if wrapper_tool:
                metadata = _generate_tool_metadata(wrapper_tool)
                #register_tool_with_metadata(metadata)
        else:
            raise ValueError(f"Invalid tool type: {type(cls_or_func)}. Must be BaseTool subclass or callable.")
        
        return cls_or_func
    
    return decorator


def _generate_tool_metadata(tool: BaseTool) -> ToolMetadata:
    """Generate comprehensive metadata for a tool."""
    
    # Determine category based on tool name and description
    category = _infer_tool_category(tool.name, tool.description)
    
    # Extract keywords from name and description
    keywords = _extract_keywords(f"{tool.name} {tool.description}")
    
    # Generate function specifications
    functions = []
    capabilities = tool.get_capabilities()
    
    if capabilities:
        # Tool has capabilities defined - use them
        for capability in capabilities:
            func_spec = ToolFunctionSpec(
                name=capability.name,
                description=capability.description,
                parameters={
                    arg.name: {
                        "type": arg.type.value,
                        "description": arg.description,
                        "required": arg.required,
                        "default": arg.default
                    }
                    for arg in tool.get_arguments()
                },
                returns={
                    "type": capability.output_type,
                    "description": f"Result from {capability.name}"
                },
                examples=capability.examples
            )
            functions.append(func_spec)
    else:
        # Function-based tool without capabilities - create default function spec
        func_spec = ToolFunctionSpec(
            name="execute",
            description=tool.description or f"Execute {tool.name}",
            parameters={
                arg.name: {
                    "type": arg.type.value,
                    "description": arg.description,
                    "required": arg.required,
                    "default": arg.default
                }
                for arg in tool.get_arguments()
            },
            returns={
                "type": "dict",
                "description": f"Result from {tool.name}"
            },
            examples=[]
        )
        functions.append(func_spec)
    
    # Generate use cases based on tool type
    use_cases = _generate_use_cases(tool.name, tool.description, category)
    
    return ToolMetadata(
        tool_id=tool.name,
        name=tool.name,
        description=tool.description,
        version=tool.version,
        category=category,
        subcategories=_generate_subcategories(tool.name, tool.description),
        functions=functions,
        capabilities=[cap.name for cap in capabilities] if capabilities else ["execute"],
        keywords=keywords,
        synonyms=_generate_synonyms(tool.name),
        use_cases=use_cases,
        input_types=[arg.type.value for arg in tool.get_arguments()],
        output_types=[cap.output_type for cap in capabilities] if capabilities else ["dict"],
        dependencies=[],  # Could be extracted from tool requirements
        requirements=[]   # Could be extracted from tool setup
    )


def _infer_tool_category(name: str, description: str) -> ToolCategory:
    """Infer tool category from name and description."""
    text = f"{name} {description}".lower()
    
    category_keywords = {
        ToolCategory.FINANCIAL: ['stock', 'market', 'trading', 'financial', 'investment', 'news'],
        ToolCategory.DATA_ANALYSIS: ['analysis', 'calculate', 'technical', 'indicator', 'rsi', 'ema', 'macd'],
        ToolCategory.WEB_SCRAPING: ['web', 'scrape', 'crawl', 'extract', 'html'],
        ToolCategory.SEARCH: ['search', 'find', 'lookup', 'query', 'duck'],
        ToolCategory.DATA_RETRIEVAL: ['download', 'fetch', 'get', 'retrieve', 'yfinance'],
        ToolCategory.COMPUTATION: ['calculate', 'compute', 'date', 'time'],
        ToolCategory.API_INTEGRATION: ['api', 'yahoo', 'finance', 'yf']
    }
    
    for category, keywords in category_keywords.items():
        if any(keyword in text for keyword in keywords):
            return category
    
    return ToolCategory.UTILITY


def _extract_keywords(text: str) -> List[str]:
    """Extract meaningful keywords from text."""
    import re
    
    # Remove punctuation and split
    words = re.sub(r'[^\w\s]', ' ', text.lower()).split()
    
    # Remove common stop words
    stop_words = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
        'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
        'to', 'was', 'will', 'with', 'tool', 'using'
    }
    
    keywords = [word for word in words if word not in stop_words and len(word) > 2]
    return list(set(keywords))  # Remove duplicates


def _generate_synonyms(tool_name: str) -> List[str]:
    """Generate synonyms for tool name."""
    synonyms_map = {
        'financial_news_search': ['news search', 'stock news', 'market news'],
        'get_stock_data_yf': ['stock data', 'yahoo finance', 'market data'],
        'technical_analysis': ['ta', 'indicators', 'chart analysis'],
        'web_search_tool_duckduck': ['web search', 'search engine', 'internet search'],
        'calculate_date': ['date calculation', 'time calculation', 'date math']
    }
    
    return synonyms_map.get(tool_name, [])


def _generate_subcategories(name: str, description: str) -> List[str]:
    """Generate subcategories for a tool."""
    text = f"{name} {description}".lower()
    subcategories = []
    
    if 'news' in text:
        subcategories.append('news_analysis')
    if 'stock' in text or 'market' in text:
        subcategories.append('stock_market')
    if 'technical' in text:
        subcategories.append('technical_indicators')
    if 'search' in text:
        subcategories.append('information_retrieval')
    if 'data' in text:
        subcategories.append('data_processing')
    
    return subcategories


def _generate_use_cases(name: str, description: str, category: ToolCategory) -> List[str]:
    """Generate use cases for a tool."""
    use_cases = []
    text = f"{name} {description}".lower()
    
    if category == ToolCategory.FINANCIAL:
        use_cases.extend([
            "Investment research and analysis",
            "Market trend identification",
            "Portfolio optimization",
            "Risk assessment"
        ])
    elif category == ToolCategory.DATA_ANALYSIS:
        use_cases.extend([
            "Technical indicator calculation",
            "Statistical analysis of financial data",
            "Trend analysis and forecasting"
        ])
    elif category == ToolCategory.SEARCH:
        use_cases.extend([
            "Market research",
            "News gathering",
            "Information discovery"
        ])
    elif category == ToolCategory.DATA_RETRIEVAL:
        use_cases.extend([
            "Historical data collection",
            "Real-time market data access",
            "Data pipeline construction"
        ])
    
    return use_cases


def get_registered_tools() -> Dict[str, BaseTool]:
    """Get all registered tools from global registry."""
    return _global_registry.get_all_tools()


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    return _global_registry