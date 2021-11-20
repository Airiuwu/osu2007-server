from blacksheep.server.templating import use_templates
from blacksheep.server.responses import text
from blacksheep.server import Application
from helpers import consoleHelper
from jinja2 import PackageLoader
from cmyui import AsyncSQLPool
from hashlib import sha256, md5
from objects import glob
import config, re
import base64

app = Application()
returnTemplate = use_templates(app, loader=PackageLoader("app", "templates"), enable_async=True)
glob.db = AsyncSQLPool()

async def before_start(application: Application) -> None:
	try: await glob.db.connect(config.mysql)
	except Exception as error: consoleHelper.logError(msg=error)

@app.route("/")
async def home(request):
	return await returnTemplate("index", {"0": "0", "1": "1"})

@app.route('/register', methods=['GET', 'POST'])
async def register(request):
	if request.method == "POST":
		data = await request.form()
		username, password, email = data["username"], md5(data["password"].encode('utf-8')).hexdigest(), data["email"]

		checkUsername = await glob.db.fetch("SELECT * FROM users WHERE username = %s", [username])
		checkEmail = await glob.db.fetch("SELECT * FROM users WHERE email = %s", [email])

		if checkUsername is not None:
			consoleHelper.logFail(msg=f"Someone has tried to create an account with a taken username => {username}")
			return text(f"The username, {username} is already being used")
		if checkEmail is not None: 
			consoleHelper.logFail(msg=f"Someone has tried to create an account with a taken email => {email}")
			return text(f"The email, {email} is already being used.")
		else:
			await glob.db.execute("INSERT INTO users (`username`, `password`, `email`, `banned`) VALUES (%s, %s, %s, %s)", [username, password, email, '0'])
			consoleHelper.logInfo(msg=f"New account has been created => {username}")
			return text(f"Your account is now registered, {username}")

	return await returnTemplate("register", {"0": "0", "1": "1"})

@app.route("/web/osu-login.php", methods=['GET'])
async def login(request):
	response = "0"
	username, password = request.query.get("username"), request.query.get("password")
	checkLogin = await glob.db.fetch("SELECT * FROM users WHERE username = %s AND password = %s", [username[0], password[0]])
	if checkLogin is None:
		consoleHelper.logFail(msg=f"{username[0]}'s login has failed.")
	elif checkLogin["banned"] == "1":
		consoleHelper.logFail(msg=f"{username[0]}'s login has failed. (user is banned)")
	else:
		consoleHelper.logInfo(msg=f"{username[0]} has logged in.")
		response = "1"
	return text(response)

@app.route("/web/osu-getscores.php", methods=['GET'])
async def retrieveScores(request):
	mapHash = request.query.get("c")
	perfect = "False"
	getScores = await glob.db.fetchall("SELECT * FROM scores WHERE mapHash = %s AND outdated = 0 AND pass = 1 ORDER BY score DESC", [mapHash[0]])
	bannedMapCheck = await glob.db.fetch("SELECT * FROM `banned_maps` WHERE `mapHash` = %s", [mapHash[0]])
	if bannedMapCheck is None and getScores is not None:
		for row in getScores:
			if row["perfect"] == 1:
				perfect = "True"
			userData = await glob.db.fetch("SELECT * FROM users WHERE id = %s", [row["playerId"]])
			if userData["banned"] == 1:
				return
			else:
				consoleHelper.logInfo(msg=f"{userData['username']} has requested scores for => {mapHash[0]}")
				return text(f"{row['id']}:{userData['username']}:{row['score']}:{row['combo']}:{row['count50']}:{row['count100']}:{row['count300']}:{row['countMiss']}:{row['countKatu']}:{row['countGeki']}:{perfect}:{row['mods']}\n")

@app.route("/web/osu-submit.php", methods=['POST'])
async def submitScore(request):
	perfect, passedScore, outdated = "0", "0", "0"
	score, password = request.query.get("score"), request.query.get("pass")
	scoreData = re.split('[-:]', score[0])
	userData = await glob.db.fetch("SELECT * FROM users WHERE username = %s AND password = %s", [scoreData[1], password[0]])
	bannedMapCheck = await glob.db.fetch("SELECT * FROM `banned_maps` WHERE `mapHash` = %s", [scoreData[0]])
	if scoreData[11] == "True": perfect = 1
	if scoreData[14] == "True": passedScore = 1
	if userData is not None or userData["banned"] == "0" or bannedMapCheck is None:
		highScore = await glob.db.fetch("SELECT * FROM scores WHERE mapHash = %s AND playerId = %s AND outdated = 0 AND pass = 1 ORDER BY score DESC", [scoreData[0], userData["id"]])
		if highScore is not None:
			print(highScore)
			print(f"{scoreData[9]} | {highScore['score']}")
			if int(scoreData[9]) > int(highScore["score"]):
				if passedScore != "0":
					outdated = "1"
					await glob.db.execute("UPDATE scores SET outdated = %s WHERE id = %s", [outdated, highScore["id"]])

		consoleHelper.logInfo(msg=f"{userData['username']} has submitted a score on => {scoreData[0]}")
		await glob.db.execute("INSERT INTO scores (`mapHash`, `playerId`, `score`, `combo`, `count50`, `count100`, `count300`, `countMiss`, `countKatu`, `countGeki`, `perfect`, `mods`, `pass`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", [scoreData[0], userData["id"], scoreData[9], scoreData[10], scoreData[5], scoreData[4], scoreData[3], scoreData[8], scoreData[7], scoreData[6], perfect, scoreData[13], passedScore])
		if passedScore != "0":
			lastScore = await glob.db.fetch("SELECT * FROM scores WHERE playerId = %s AND mapHash = %s AND pass = 1 ORDER BY id DESC", [userData["id"], scoreData[0]])
			if lastScore is not None:
				data = await request.read()
				print(data)
				with open(f"app/static/replays/replay_{lastScore['id']}.osr", "wb") as replay:
					replay.write(data)

@app.route("/web/osu-getreplay.php", methods=['GET', 'POST'])
async def getReplay(request):
	replayID = request.query.get("c")
	# with open(f"data/replays/replay_{replayID[0]}.osr", "rb") as replay:
	# 	replayData = replay.read()
	# 	replay.close()
	# return(replayData)

app.on_start += before_start
consoleHelper.printHeader()