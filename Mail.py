"""注册验证码邮件发送（163 邮箱 SMTP）。

配置来自环境变量，本地开发写在项目根目录的 .env（见 .env.example）：

	SMTP_HOST       发信服务器，默认 smtp.163.com
	SMTP_PORT       端口，默认 465
	SMTP_TLS        传输加密：ssl（465，默认）/ starttls（587）/ none（明文，仅内网中继）
	SMTP_TIMEOUT    连接与发送超时（秒），默认 20
	SMTP_USER       发件邮箱，默认 ourpet001@163.com
	SMTP_PASSWORD   163 授权码（不是网页登录密码），未配置时视为邮件服务不可用
	SMTP_FROM_NAME  发件人显示名，默认 AIHub

对外只有两个入口：

	Configured()            邮件服务是否已配置
	SendCode(ToEmail, Code) 发送「AIHub 注册验证码」，失败一律抛 MailError

注意：163 邮箱做 SMTP 认证必须用「授权码」（在邮箱设置的 POP3/SMTP/IMAP 里开启服务时生成），
并且发信地址要与 SMTP_USER 一致，否则会被服务器以 535 / 553 拒绝。
"""
import os
import smtplib
import ssl
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# 验证码有效期（分钟），与 database/persistent.py 清理 email 表的 300 秒阈值保持一致
CODE_TTL_MINUTES = 5

# 默认发信邮箱：沿用论坛那套 163 邮箱
DEFAULT_USER = "ourpet001@163.com"

# SMTP 认证阶段错误码 → 中文提示
_AUTH_ERROR_HINTS = {
	535: "账号或授权码错误（163 邮箱要填授权码，不是登录密码）",
	551: "发信账户状态异常，请到邮箱设置里检查发信权限",
	553: "发信地址被拒绝，请检查 SMTP_USER 是否是真实存在的邮箱",
	552: "发信额度已用尽",
	436: "MAIL FROM 与实际发信地址不一致",
}


class MailError(RuntimeError):
	"""邮件发送失败，message 为中文说明。"""


def _Env(Name, Default=""):
	"""读环境变量：空字符串按未配置处理。"""
	return (os.getenv(Name) or Default).strip()


def _Int(Name, Default):
	"""读整数环境变量，值非法时退回默认值。"""
	try:
		return int(_Env(Name) or Default)
	except ValueError:
		return Default


def _Password():
	"""授权码：顺手粘贴时容易带上空格，这里去掉所有空白字符。"""
	return _Env("SMTP_PASSWORD").replace(" ", "")


def Configured() -> bool:
	"""邮件服务是否已配置：缺授权码就没法发信（发件邮箱有默认值，一般不缺）。"""
	return bool(_Env("SMTP_USER", DEFAULT_USER) and _Password())


def _BuildText(Code):
	"""纯文本正文（部分邮件客户端不渲染 HTML）。"""
	return (
		"你正在注册 AIHub 账号，请使用下面的验证码完成注册：\n\n"
		f"　　{Code}\n\n"
		f"验证码 {CODE_TTL_MINUTES} 分钟内有效，请勿转发或泄露给他人。\n"
		"若并非本人操作，忽略本邮件即可，你的账号不会有任何变化。\n"
	)


def _BuildHtml(Code):
	"""HTML 正文，配色沿用前端主题色 --accent(#7c3aed)。"""
	return (
		'<!DOCTYPE html>\n<html lang="zh-CN"><head><meta charset="UTF-8" />'
		'<meta name="viewport" content="width=device-width,initial-scale=1.0" />'
		'<title>AIHub 注册验证码</title></head>'
		'<body style="margin:0;padding:0;background:#f5f5f7;'
		'font-family:-apple-system,BlinkMacSystemFont,Segoe UI,PingFang SC,Microsoft YaHei,sans-serif;'
		'color:#374151;">'
		'<table width="100%" cellpadding="0" cellspacing="0" border="0" role="presentation" '
		'style="background:#f5f5f7;padding:32px 0;"><tr><td align="center">'
		'<table width="100%" cellpadding="0" cellspacing="0" border="0" role="presentation" '
		'style="max-width:560px;margin:0 auto;">'
		'<tr><td style="padding:14px 24px;background:#7c3aed;border-radius:10px 10px 0 0;'
		'color:#ffffff;font-size:16px;font-weight:700;">AIHub</td></tr>'
		'<tr><td style="background:#ffffff;padding:28px 24px;border-radius:0 0 10px 10px;">'
		'<div style="font-size:18px;font-weight:700;color:#1f2937;margin:0 0 14px;">注册验证码</div>'
		'<div style="font-size:15px;line-height:1.8;color:#4b5563;">'
		'你正在注册 AIHub 账号，请使用下面的验证码完成注册：</div>'
		'<div style="margin:20px 0;padding:14px 0;text-align:center;background:#f7f5ff;'
		'border:1px solid #e6e0ff;border-radius:8px;font-size:28px;font-weight:700;'
		f'letter-spacing:6px;color:#7c3aed;">{Code}</div>'
		'<div style="font-size:15px;line-height:1.8;color:#4b5563;">验证码 '
		f'<strong>{CODE_TTL_MINUTES} 分钟内有效</strong>，请勿转发或泄露给他人。</div>'
		'<div style="font-size:12px;line-height:1.7;color:#9ca3af;margin-top:8px;">'
		'若并非本人操作，忽略本邮件即可，你的账号不会有任何变化。</div>'
		'</td></tr>'
		'<tr><td align="center" style="padding-top:20px;font-size:12px;color:#9ca3af;line-height:1.8;">'
		'本邮件由系统自动发送，请勿直接回复。</td></tr>'
		'</table></td></tr></table></body></html>'
	)


def _Connect(Context, Host, Port, Mode, Timeout):
	"""按 SMTP_TLS 建立连接：ssl（465，默认）/ starttls（587）/ none（明文）。"""
	if Mode in ("starttls", "tls", "587"):
		Server = smtplib.SMTP(Host, Port, timeout=Timeout)
		Server.ehlo()
		Server.starttls(context=Context)
		Server.ehlo()
		return Server
	if Mode in ("none", "plain", "cleartext", "off"):
		return smtplib.SMTP(Host, Port, timeout=Timeout)
	return smtplib.SMTP_SSL(Host, Port, context=Context, timeout=Timeout)


def _AuthMessage(Error):
	"""把 SMTP 认证失败的真实错误码 / 原因拼成中文提示。"""
	Code = getattr(Error, "smtp_code", None)
	Raw = getattr(Error, "smtp_error", b"")
	if isinstance(Raw, (bytes, bytearray)):
		Raw = Raw.decode("utf-8", "ignore")
	Raw = str(Raw or "").strip()
	Hint = _AUTH_ERROR_HINTS.get(Code, "账号或授权码错误")
	Text = f"SMTP 认证失败（{Code}）：{Hint}" if Code else f"SMTP 认证失败：{Hint}"
	if Raw:
		Text += f" - {Raw}"
	return Text


def SendCode(ToEmail, Code):
	"""给 ToEmail 发送注册验证码。

	成功返回 None，任何失败都抛 MailError（调用方据此返回 502）。
	发信是阻塞的（163 通常 1~3 秒），注册流程只在用户点「发送验证码」时触发一次，可以接受。
	"""
	Password = _Password()
	if not Password:
		raise MailError("邮件服务未配置（缺少 SMTP_PASSWORD）")

	Sender = _Env("SMTP_USER", DEFAULT_USER)
	Host = _Env("SMTP_HOST", "smtp.163.com")
	Port = _Int("SMTP_PORT", 465)
	Mode = _Env("SMTP_TLS", "ssl").lower()
	Timeout = _Int("SMTP_TIMEOUT", 20)
	SenderName = _Env("SMTP_FROM_NAME", "AIHub")

	Message = MIMEMultipart("alternative")
	Message["From"] = Header(SenderName, "utf-8").encode() + f" <{Sender}>"
	Message["To"] = ToEmail
	Message["Subject"] = Header("AIHub 注册验证码", "utf-8")
	Message.attach(MIMEText(_BuildText(Code), "plain", "utf-8"))
	Message.attach(MIMEText(_BuildHtml(Code), "html", "utf-8"))

	Server = None
	try:
		Server = _Connect(ssl.create_default_context(), Host, Port, Mode, Timeout)
		Server.login(Sender, Password)
		Server.sendmail(Sender, [ToEmail], Message.as_string())
	except smtplib.SMTPAuthenticationError as Error:
		raise MailError(_AuthMessage(Error)) from Error
	except smtplib.SMTPRecipientsRefused as Error:
		raise MailError(f"收件地址被拒绝：{ToEmail}") from Error
	except (smtplib.SMTPException, OSError) as Error:
		raise MailError(f"邮件发送失败：{Error}") from Error
	finally:
		if Server is not None:
			try:
				Server.quit()
			except Exception:
				pass


__all__ = ["MailError", "Configured", "SendCode", "CODE_TTL_MINUTES"]
