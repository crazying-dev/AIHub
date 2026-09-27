import dotenv

dotenv.load_dotenv()

import route
import threading
import database

def RunFlask():
	route.app.run(host="127.0.0.1", port=2685, debug=False)

persistent = database.persistent.main()

threading.Thread(target=persistent.email, daemon=True).start()
threading.Thread(target=persistent.message, daemon=True).start()
# Flask 放在主线程里跑：它自身会阻塞；若继续用 daemon 线程，主线程一结束进程就退出了。
RunFlask()

