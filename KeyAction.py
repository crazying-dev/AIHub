import database


def NewKey(UserID):
	keyid = database.key.New.NewKey(UserID)
	return f"ah-{keyid}"


Get = database.key.Get.Get
