"""route/api 通用辅助：登录态校验与参数归一化。"""
from route.app import *
import database


def UserID():
	"""从 Cookie 取登录态，校验通过返回 UserID；未登录（或校验失败）返回 None"""
	Cookies = flask.request.cookies
	UID = Cookies.get("id") or Cookies.get("ID")
	UserToken = Cookies.get("token")
	if not UID or not UserToken:
		return None
	if not database.user.verify.verifyUser_UserID___UserToken(UID, UserToken):
		return None
	return UID


def Int(Value, Default=None):
	"""把前端传来的字符串/数字转成 int，非法就返回默认值"""
	if Value is None or Value == "":
		return Default
	try:
		return int(Value)
	except (TypeError, ValueError):
		return Default


def Text(Value):
	"""去首尾空白；空串归一化为 None"""
	Result = str(Value).strip() if Value is not None else ""
	return Result or None


def TextList(Value):
	"""把前端传来的 id 列表归一化为 list[str]（去重、去空）；非法返回空列表"""
	if Value is None:
		return []
	if isinstance(Value, str):
		Parts = [Value]
	else:
		try:
			Parts = list(Value)
		except TypeError:
			Parts = []
	Result = []
	for Part in Parts:
		Item = str(Part).strip()
		if Item and Item not in Result:
			Result.append(Item)
	return Result
