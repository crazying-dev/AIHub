from route.app import app

# 注册路由
import route.index
import route.OpenAI
import route.api

__all__ = ["app"]
