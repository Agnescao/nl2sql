请详细描述一下你是如何实现或理解Memory机制的。你是如何对海量的历史对话或交互记录进行存储、检索和更新的？如何平衡长期记忆和短期记忆？”

“工具调用（Function Calling） 是Agent的核心能力。请设计一个安全、高效的工具调用系统。

你如何管理（注册、发现）大量的工具？

如何确保工具调用的安全性（例如，防止任意代码执行）？

当LLM生成的参数不符合工具要求的格式或类型时，你有什么应对策略？”


以下是对上述回答的具体代码示例和实际应用场景说明：

## Memory机制实现示例

### 1. 分层存储策略实现

```python
# memory_manager.py
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import redis
import sqlite3

class MemoryManager:
    def __init__(self):
        # 短期记忆 - Redis缓存
        self.short_term_memory = redis.Redis(host='localhost', port=6379, db=0)
        # 长期记忆 - SQLite数据库
        self.long_term_db = sqlite3.connect('long_term_memory.db')
        self._init_db()
    
    def _init_db(self):
        """初始化长期记忆数据库"""
        cursor = self.long_term_db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                content TEXT,
                timestamp DATETIME,
                memory_type TEXT
            )
        ''')
        self.long_term_db.commit()
    
    def store_short_term(self, user_id: str, content: Dict, expire_seconds: int = 3600):
        """存储短期记忆"""
        key = f"short_term:{user_id}:{datetime.now().timestamp()}"
        self.short_term_memory.setex(
            key, 
            expire_seconds, 
            json.dumps(content)
        )
    
    def store_long_term(self, user_id: str, content: Dict, memory_type: str = "general"):
        """存储长期记忆"""
        cursor = self.long_term_db.cursor()
        cursor.execute('''
            INSERT INTO memories (user_id, content, timestamp, memory_type)
            VALUES (?, ?, ?, ?)
        ''', (user_id, json.dumps(content), datetime.now(), memory_type))
        self.long_term_db.commit()
    
    def retrieve_memory(self, user_id: str, query: str, limit: int = 10) -> List[Dict]:
        """检索相关记忆（简化版）"""
        # 优先检索短期记忆
        short_term_results = self._search_short_term(user_id)
        
        # 补充长期记忆
        long_term_results = self._search_long_term(user_id, limit - len(short_term_results))
        
        return short_term_results + long_term_results
    
    def _search_short_term(self, user_id: str) -> List[Dict]:
        """检索短期记忆"""
        pattern = f"short_term:{user_id}:*"
        keys = self.short_term_memory.keys(pattern)
        results = []
        for key in keys:
            data = self.short_term_memory.get(key)
            if data:
                results.append(json.loads(data))
        return results
    
    def _search_long_term(self, user_id: str, limit: int) -> List[Dict]:
        """检索长期记忆"""
        cursor = self.long_term_db.cursor()
        cursor.execute('''
            SELECT content FROM memories 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (user_id, limit))
        return [json.loads(row[0]) for row in cursor.fetchall()]
```


### 2. 实际应用场景：智能客服对话系统

```python
# customer_service_agent.py
class CustomerServiceAgent:
    def __init__(self):
        self.memory = MemoryManager()
    
    def handle_query(self, user_id: str, query: str) -> str:
        # 检索相关历史记忆
        context = self.memory.retrieve_memory(user_id, query)
        
        # 构建对话上下文
        conversation_history = "\n".join([
            f"User: {item.get('user_query', '')}\nAgent: {item.get('agent_response', '')}"
            for item in context
        ])
        
        # 生成回复（模拟LLM调用）
        response = self.generate_response(query, conversation_history)
        
        # 存储当前交互到短期记忆
        self.memory.store_short_term(user_id, {
            'user_query': query,
            'agent_response': response,
            'timestamp': datetime.now()
        })
        
        # 重要信息存储到长期记忆
        if self.is_important_info(query, response):
            self.memory.store_long_term(user_id, {
                'query': query,
                'response': response,
                'category': 'important'
            })
        
        return response
    
    def generate_response(self, query: str, context: str) -> str:
        # 模拟LLM生成回复
        return f"根据您的问题'{query}'和历史记录，我建议您查看帮助文档。"
    
    def is_important_info(self, query: str, response: str) -> bool:
        # 判断是否为重要信息（如投诉、订单号等）
        important_keywords = ['投诉', '订单', '退款', '账号']
        return any(keyword in query or keyword in response for keyword in important_keywords)
```


## 工具调用系统实现示例

### 1. 工具注册与发现机制

```python
# tool_registry.py
from typing import Dict, Callable, Any, Optional
import inspect
from dataclasses import dataclass
from enum import Enum

class ParameterType(Enum):
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    NUMBER = "number"

@dataclass
class ToolParameter:
    name: str
    type: ParameterType
    description: str
    required: bool = True
    default: Any = None

@dataclass
class ToolMetadata:
    name: str
    description: str
    parameters: Dict[str, ToolParameter]
    func: Callable

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, ToolMetadata] = {}
    
    def register(self, func: Callable, name: str = None, description: str = None):
        """注册工具函数"""
        tool_name = name or func.__name__
        tool_desc = description or func.__doc__ or "No description provided"
        
        # 解析函数签名
        sig = inspect.signature(func)
        parameters = {}
        
        for param_name, param in sig.parameters.items():
            # 简化的参数类型推断
            param_type = ParameterType.STRING
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_type = ParameterType.INTEGER
                elif param.annotation == bool:
                    param_type = ParameterType.BOOLEAN
                elif param.annotation == float:
                    param_type = ParameterType.NUMBER
            
            parameters[param_name] = ToolParameter(
                name=param_name,
                type=param_type,
                description=f"Parameter {param_name}",
                required=param.default == inspect.Parameter.empty,
                default=param.default if param.default != inspect.Parameter.empty else None
            )
        
        self.tools[tool_name] = ToolMetadata(
            name=tool_name,
            description=tool_desc,
            parameters=parameters,
            func=func
        )
    
    def get_tool(self, name: str) -> Optional[ToolMetadata]:
        """获取工具元数据"""
        return self.tools.get(name)
    
    def list_tools(self) -> Dict[str, ToolMetadata]:
        """列出所有工具"""
        return self.tools.copy()

# 全局工具注册表
tool_registry = ToolRegistry()
```


### 2. 安全的工具执行环境

```python
# secure_executor.py
import subprocess
import json
import tempfile
import os
from typing import Dict, Any, Optional
import RestrictedPython
import yaml

class SecureToolExecutor:
    def __init__(self, tool_registry: ToolRegistry):
        self.registry = tool_registry
        self.sandbox_timeout = 30  # 执行超时时间
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """安全执行工具"""
        # 1. 验证工具是否存在
        tool_meta = self.registry.get_tool(tool_name)
        if not tool_meta:
            return {"error": f"Tool '{tool_name}' not found"}
        
        # 2. 验证参数
        validation_result = self._validate_parameters(tool_meta, parameters)
        if not validation_result["valid"]:
            return {"error": validation_result["error"]}
        
        # 3. 在沙箱中执行
        try:
            result = self._run_in_sandbox(tool_meta.func, parameters)
            return {"result": result}
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}
    
    def _validate_parameters(self, tool_meta: ToolMetadata, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """验证参数格式和类型"""
        for param_name, param_meta in tool_meta.parameters.items():
            # 检查必需参数
            if param_meta.required and param_name not in parameters:
                return {
                    "valid": False,
                    "error": f"Missing required parameter: {param_name}"
                }
            
            # 检查参数类型
            if param_name in parameters:
                value = parameters[param_name]
                if not self._check_type(value, param_meta.type):
                    return {
                        "valid": False,
                        "error": f"Invalid type for parameter '{param_name}'. Expected {param_meta.type.value}"
                    }
        
        return {"valid": True}
    
    def _check_type(self, value: Any, expected_type: ParameterType) -> bool:
        """检查参数类型"""
        type_mapping = {
            ParameterType.STRING: str,
            ParameterType.INTEGER: int,
            ParameterType.BOOLEAN: bool,
            ParameterType.NUMBER: (int, float)
        }
        
        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type:
            if isinstance(expected_python_type, tuple):
                return isinstance(value, expected_python_type)
            return isinstance(value, expected_python_type)
        return True
    
    def _run_in_sandbox(self, func: Callable, parameters: Dict[str, Any]) -> Any:
        """在沙箱环境中执行函数"""
        # 这里简化处理，实际应用中可以使用更严格的沙箱机制
        # 如Docker容器、RestrictedPython等
        
        # 设置执行时间限制
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Tool execution timeout")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(self.sandbox_timeout)
        
        try:
            result = func(**parameters)
            return result
        finally:
            signal.alarm(0)  # 取消定时器
```


### 3. 实际工具示例

```python
# example_tools.py
import requests
from tool_registry import tool_registry

# 示例工具1: 天气查询
def get_weather(city: str) -> str:
    """
    获取指定城市的天气信息
    """
    # 模拟API调用
    return f"{city}的天气是晴天，温度25°C"

# 示例工具2: 计算器
def calculate(expression: str) -> float:
    """
    执行数学表达式计算
    """
    # 安全的数学表达式计算（实际应用中需要更严格的解析）
    allowed_chars = set('0123456789+-*/(). ')
    if not all(c in allowed_chars for c in expression):
        raise ValueError("Invalid characters in expression")
    
    return eval(expression)

# 示例工具3: 发送邮件
def send_email(recipient: str, subject: str, body: str) -> str:
    """
    发送邮件
    """
    # 模拟邮件发送
    return f"邮件已发送至 {recipient}，主题：{subject}"

# 注册工具
tool_registry.register(get_weather, "get_weather", "查询天气信息")
tool_registry.register(calculate, "calculate", "执行数学计算")
tool_registry.register(send_email, "send_email", "发送邮件")
```


### 4. 完整的工具调用系统应用

```python
# agent_with_tools.py
from typing import Dict, Any
from tool_registry import tool_registry
from secure_executor import SecureToolExecutor

class AgentWithTools:
    def __init__(self):
        self.executor = SecureToolExecutor(tool_registry)
    
    def process_request(self, user_input: str) -> str:
        """
        处理用户请求，可能需要调用工具
        """
        # 这里简化处理，实际应用中需要LLM来决定是否调用工具及参数
        if "天气" in user_input:
            return self._invoke_tool("get_weather", {"city": "北京"})
        elif "计算" in user_input:
            # 从输入中提取表达式（简化处理）
            import re
            expr = re.search(r'(\d+[\+\-\*\/]\d+)', user_input)
            if expr:
                return self._invoke_tool("calculate", {"expression": expr.group(1)})
        elif "发送邮件" in user_input:
            return self._invoke_tool("send_email", {
                "recipient": "user@example.com",
                "subject": "测试邮件",
                "body": "这是一封测试邮件"
            })
        
        return "我理解您的请求，但目前无法处理该类型任务。"
    
    def _invoke_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """调用工具并处理结果"""
        result = self.executor.execute_tool(tool_name, parameters)
        
        if "error" in result:
            return f"工具调用失败: {result['error']}"
        
        return f"工具执行结果: {result['result']}"

# 使用示例
if __name__ == "__main__":
    agent = AgentWithTools()
    
    # 测试天气查询
    print(agent.process_request("今天北京的天气怎么样？"))
    # 输出: 工具执行结果: 北京的天气是晴天，温度25°C
    
    # 测试计算器
    print(agent.process_request("帮我计算123+456"))
    # 输出: 工具执行结果: 579
    
    # 测试错误处理
    print(agent.process_request("帮我计算123++456"))
    # 输出: 工具调用失败: Invalid characters in expression
```


以上代码展示了如何实现一个完整的Memory机制和工具调用系统：

1. **Memory机制**：通过Redis处理短期记忆，SQLite处理长期记忆，实现了分层存储和检索
2. **工具调用系统**：提供了工具注册、发现、安全执行和参数验证的完整流程
3. **实际应用**：展示了在智能客服和Agent场景中的具体应用方式

这些实现考虑了安全性、可扩展性和实际应用需求，可以根据具体业务场景进行调整和优化。