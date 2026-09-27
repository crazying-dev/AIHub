import os
from pathlib import Path

import flask

# 项目根目录（route/ 的上一级），前端构建产物默认在 <root>/dist。
# static_folder=None 关掉 Flask 自带的 /static 路由，前端资源统一由 route/web.py 接管。
BASE_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = Path(os.getenv("AIHUB_DIST") or (BASE_DIR / "dist")).resolve()

app = flask.Flask("ComputeRelay", static_folder=None)
app.config["DIST_DIR"] = str(DIST_DIR)
