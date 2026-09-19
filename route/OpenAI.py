from route.app import *

@app.route("/v1/chat/completions", methods=["POST"])
def OpenAI():
	auth_header = flask.request.headers.get("Authorization")
	api_key = auth_header.removeprefix("Bearer ") if (auth_header and auth_header.startswith("Bearer ")) else None
	
	data = flask.request.get_json()
	message = data["meaasge"]
	model = data["model"]
	return "OK"
