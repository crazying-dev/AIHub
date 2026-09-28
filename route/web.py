"""
前端托管：让 Flask 直接接管打包产物 dist/。

- /                -> dist/index.html
- /assets/xxx.js   -> 带 hash 的构建产物（长期强缓存）
- 其它未命中路径   -> 回退到 dist/index.html（前端是 history 模式路由，
                      刷新 /console、/docs 这类地址时不能 404）
- /api/*、/v1/*、/v1beta/* -> 属于后端接口，不做 SPA 回退，找不到就 404

可以用环境变量 AIHUB_DIST 指定其它产物目录。
"""

import os

import flask
from werkzeug.exceptions import NotFound

from route.app import app

# 后端自身占用的路径前缀，这些路径永远不会回退到前端页面
RESERVED_PREFIXES = {"api", "v1", "v1beta"}

BUILD_HINT = """前端产物不存在：{dist}

请先在项目根目录构建前端：

    pnpm install
    pnpm build

（构建后刷新本页即可；开发阶段也可以直接用 pnpm dev 的 5173 端口）
"""


def DistDir() -> str:
	return flask.current_app.config["DIST_DIR"]


def SendIndex() -> flask.Response:
	"""返回 SPA 入口页面；产物还没构建时给出可读的提示而不是 404。"""
	dist = DistDir()
	index = os.path.join(dist, "index.html")
	if not os.path.isfile(index):
		return flask.make_response(
			(BUILD_HINT.format(dist=dist), 503, {"Content-Type": "text/plain; charset=utf-8"})
		)
	response = flask.send_file(index, mimetype="text/html")
	# index.html 引用了带 hash 的资源，本身不能缓存
	response.headers["Cache-Control"] = "no-cache"
	return response


@app.get("/")
@app.get("/index.html")
def Index():
	return SendIndex()


@app.get("/<path:path>")
def Frontend(path: str):
	if path.split("/", 1)[0] in RESERVED_PREFIXES:
		flask.abort(404)
	try:
		response = flask.send_from_directory(DistDir(), path)
	except NotFound:
		# 静态文件不存在：交给前端路由处理
		return SendIndex()
	if path.startswith("assets/"):
		# 文件名带内容 hash，可以放心长期缓存
		response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
	else:
		response.headers["Cache-Control"] = "no-cache"
	return response
