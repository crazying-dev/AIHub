"""community 子包：社区 key（otherkey 表）。

用户把自己的上游 key 上传到社区池，池内按 model / name 匹配、按 priority 排序调度：
每次真正打到上游就把 used + 1，达到 maxuse 后自动跳过。

不能用 “from database.community import *”（与 key 子包同理，会自引用拿到空命名空间）。
"""

from . import Candidates
from . import Delete
from . import List
from . import New
from . import Use

__all__ = ["New", "List", "Delete", "Candidates", "Use"]
