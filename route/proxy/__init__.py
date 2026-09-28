"""入站协议路由：把各家客户端的协议翻译成 canonical，再交给 Relay 转发到上游。

模块分工：
- Common.py     ：鉴权、错误形状、与上游交互的公共流水线
- Chat.py       ：OpenAI Chat Completions / Completions(legacy) / Anthropic Messages / count_tokens / models
- Embeddings.py ：OpenAI Embeddings
- Responses.py  ：OpenAI Responses API
- Ollama.py     ：Ollama（/api/chat、/api/generate、/api/tags ...）
- Gemini.py     ：Gemini 原生 REST（/v1beta/models/...）
"""
import route.proxy.Common
import route.proxy.Chat
import route.proxy.Embeddings
import route.proxy.Responses
import route.proxy.Ollama
import route.proxy.Gemini