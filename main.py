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
threading.Thread(target=RunFlask, daemon=True).start()

