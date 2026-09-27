"""key 子包：导出 New / Get 两个子模块。

不能用 “from database.key import *”：那是在本包尚未初始化完时自引用，
__all__ 还没生效，结果是空命名空间，database.key.Get 会不存在。
"""

from . import Get
from . import New

__all__ = ["New", "Get"]
