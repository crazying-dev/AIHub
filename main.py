import route
import threading

def RunFlask():
	route.app.run(host="127.0.0.1", port=2685, debug=False)

threading.Thread(target=RunFlask, daemon=True).start()

