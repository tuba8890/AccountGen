# [--- Imports ---]
from flask import Flask, request, redirect, session, render_template, flash, url_for, jsonify, send_from_directory
from flask_pymongo import PyMongo
from authlib.integrations.flask_client import OAuth
from functools import wraps
from dotenv import load_dotenv
import requests, datetime, os, time, uuid, json, base64, calendar, Functions, time, random




# [--- Flask Setup ---]
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_NAME"] = "userSession"
app.secret_key = os.environ.get('SECRET_KEY')
generationRequests = {}




# [--- Login Required Wrap ---]
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" not in session or not session["logged_in"]:
            flash("Please log in to access this page.", "warning")
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function




# [--- MongoDB ---]
app.config["MONGO_URI"] = os.environ.get('MONGO_URI')
mongo = PyMongo(app)




# [--- Discord OAUTH ---]
oauth = OAuth()
oauth.init_app(app)
discord = oauth.register(
    name="discord",
    client_id=os.environ.get('CLIENT_ID'),
    client_secret=os.environ.get('CLIENT_SECRET'),
    authorize_url="https://discord.com/api/oauth2/authorize",
    authorize_params=None,
    access_token_url="https://discord.com/api/oauth2/token",
    access_token_params=None,
    refresh_token_url=None,
    redirect_to="discordCallback",
    client_kwargs={"scope": "identify email"},
)




# [--- Index Route ---]
@app.route("/")
def index():
    # [--- Getting User/Checking if Authenticated ---]
    sessionObj = session.get("user", False)
    if sessionObj:
        userID = sessionObj.get("id", False)
        if userID:
            return redirect("/dashboard")

    siteSettings = mongo.db.site.find_one({"_id": "1"})
    if not siteSettings:
        Functions.firstTimeSetupMongo(mongo)

    siteName = os.environ.get('NAME')

    return render_template("index.html", siteName=siteName)



# [--- Logout Route ---]
@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    session.pop("user", None)
    flash("Logged Out!", "danger")
    return redirect("/")



# [--- Login Route ---]
@app.route("/login")
def login():
    return discord.authorize_redirect(url_for("callback", _external=True))



# [--- Callback Route ---]
@app.route("/callback")
def callback():
    try:
        token = discord.authorize_access_token()
    except Exception as e:
        print(str(e))
        flash("Error during authorization. Please try again.", "danger")
        return redirect(url_for("login"))

    if not token:
        flash("No token received. Please try again.", "danger")
        return redirect(url_for("login"))

    resp = discord.get("https://discord.com/api/users/@me")

    if not resp or resp.status_code != 200:
        flash("Failed to fetch user info from Discord.", "danger")
        return redirect(url_for("login"))

    user_info = resp.json()

    userID = user_info['id']
    userName = user_info['username']
    userAvatar = user_info['avatar']
    userEmail = user_info['email']

    user = mongo.db.users.find_one({"_id": userID})

    if not user:
        # CREATING USER DATA
        Functions.createUser(mongo, userID, userName, userEmail, userAvatar)

        # UPDATING SITE STATISTICS
        siteSettings = mongo.db.site.find_one({"_id": "1"})

        currentUsers = siteSettings['statistics']['users']
        currentUsers = currentUsers + 1

        mongo.db.site.update_one(
            {"_id": "1"},
            {"$set": {"statistics.users": currentUsers}},
        )



    # Creating User/Checking if User Exists

    session["user"] = {"id": userID}
    session["logged_in"] = True

    return redirect("/dashboard")



# [--- Dashboard Route ---]
@app.route("/dashboard")
@login_required
def dashboard(): 

    # [--- Getting User/Checking if Authenticated ---]
    userID = session["user"]["id"]
    userData = mongo.db.users.find_one({"_id": userID})
    if not userData:
        return redirect("/logout")



    # [--- User Details ---]
    user = {
        "avatar": userData['details']['avatar'],
        "tier": userData['details']['tier'],
        "name": userData['details']['name'],
        "id": userID,
        "adminid": os.environ.get('ADMIN_ID'),
    }



    # [--- Site Details ---]
    siteData = mongo.db.site.find_one({"_id": "1"})
    site = {
        "users": siteData['statistics']['users'],
        "totalGenerations": siteData['statistics']['totalGenerations'],
        "restocks": siteData['statistics']['restocks'],
        "message": {
            "title": siteData['message']["title"],
            "content": siteData['message']["content"],
        },
        "name": os.environ.get('NAME'),
        "letter": os.environ.get('LETTER'),
    }



    # [--- User Statistics ---]
    today = datetime.datetime.now()
    month = today.strftime('%m')
    day = today.strftime('%d')
    year = today.strftime('%y')
    dayCount = f"{str(day)}{str(month)}{str(year)}"
    monthCount = f"{str(month)}{str(year)}"

        # [--- Daily ---]
    if userData['history']['daily'].get(dayCount, 0):
        todayGenerations = userData['history']['daily'].get(dayCount, 0)
        todayGenerationsLeft = (100-int(todayGenerations))
    else:
        todayGenerations = 0
        todayGenerationsLeft = 100

        # [--- Monthly ---]
    year = int(year) + 2000
    _, days = calendar.monthrange(int(year), int(month))
    monthTotal = 100 * days
    if userData['history']['monthly'].get(monthCount, 0):
        monthlyGenerations = userData['history']['monthly'].get(monthCount, 0)
        monthlyGenerationsLeft = (monthTotal-int(monthlyGenerations))
    else:
        monthlyGenerations = 0
        monthlyGenerationsLeft = monthTotal

        # [--- Table ---]
    generations = {
        "today": todayGenerations,
        "todayLeft": todayGenerationsLeft,
        "month": monthlyGenerations,
        "monthLeft": monthlyGenerationsLeft,
        "monthTotal": monthTotal,
        "lifetime": userData['statistics']['totalGenerated'],
        "recent": userData['history']['recent'],
    }



    # [--- Return Render ---]
    return render_template("Dashboard.html", user=user, site=site, generations=generations)

@app.route('/discord')
def discord_redirect():
    return redirect(os.environ.get('DISCORD_INVITE'))


@app.errorhandler(404)
def page_not_found(e):

        # [--- Getting User/Checking if Authenticated ---]
    # [--- Getting User/Checking if Authenticated ---]
    sessionObj = session.get("user", False)
    if not sessionObj:
        return redirect("/logout")

    # [--- Getting User/Checking if Authenticated ---]
    userID = session["user"]["id"]
    userData = mongo.db.users.find_one({"_id": userID})
    if not userData:
        return redirect("/logout")

        # [--- User Details ---]
    user = {
        "avatar": userData['details']['avatar'],
        "tier": userData['details']['tier'],
        "name": userData['details']['name'],
        "id": userID,
        "adminid": os.environ.get('ADMIN_ID'),
    }



    # [--- Site Details ---]
    siteData = mongo.db.site.find_one({"_id": "1"})
    site = {
        "users": siteData['statistics']['users'],
        "totalGenerations": siteData['statistics']['totalGenerations'],
        "restocks": siteData['statistics']['restocks'],
        "message": {
            "title": siteData['message']["title"],
            "content": siteData['message']["content"],
        },
        "name": os.environ.get('NAME'),
        "letter": os.environ.get('LETTER'),
    }



    return render_template('404.html', user=user, site=site)





# [--- Generator Route ---]
@app.route("/generator")
@login_required
def freeGenerator(): 

    # [--- Getting User/Checking if Authenticated ---]
    userID = session["user"]["id"]
    userData = mongo.db.users.find_one({"_id": userID})
    if not userData:
        return redirect("/logout")



    # [--- User Details ---]
    user = {
        "avatar": userData['details']['avatar'],
        "tier": userData['details']['tier'],
        "name": userData['details']['name'],
        "id": userID,
        "adminid": os.environ.get('ADMIN_ID'),
    }



    # [--- Site Details ---]
    siteData = mongo.db.site.find_one({"_id": "1"})
    site = {
        "users": siteData['statistics']['users'],
        "totalGenerations": siteData['statistics']['totalGenerations'],
        "restocks": siteData['statistics']['restocks'],
        "message": {
            "title": siteData['message']["title"],
            "content": siteData['message']["content"],
        },
        "name": os.environ.get('NAME'),
        "letter": os.environ.get('LETTER'),
    }



    # [--- User Statistics ---]
    today = datetime.datetime.now()
    month = today.strftime('%m')
    day = today.strftime('%d')
    year = today.strftime('%y')
    dayCount = f"{str(day)}{str(month)}{str(year)}"

        # [--- Daily ---]
    if userData['history']['daily'].get(dayCount, 0):
        todayGenerations = userData['history']['daily'].get(dayCount, 0)
        todayGenerationsLeft = (100-int(todayGenerations))
    else:
        todayGenerations = 0
        todayGenerationsLeft = 100

        # [--- Table ---]
    generations = {
        "today": todayGenerations,
        "todayLeft": todayGenerationsLeft,
        "recent": userData['history']['recent'],
    }



    # [--- Generators ---]
    generators = siteData['generators']


    # [--- Return Render ---]
    return render_template("Generator.html", user=user, generations=generations, site=site, generators=generators)


# [--- Generator Requests ---]
# [--- Generate (POST) ---]
@app.route("/generate", methods=["POST"])
@login_required
def generate():

    # [--- Rate Limiting ---]
    client_ip = request.remote_addr
    if client_ip in generationRequests and time.time() - generationRequests[client_ip] < 10:
        return jsonify({'status': 102})
    generationRequests[client_ip] = time.time()



    # [--- Getting User/Checking if Authenticated ---]
    userID = session["user"]["id"]
    userData = mongo.db.users.find_one({"_id": userID})
    if not userData:
        return redirect("/logout")



    # [--- User Statistics ---]
    today = datetime.datetime.now()
    month = today.strftime('%m')
    day = today.strftime('%d')
    year = today.strftime('%y')
    dayCount = f"{str(day)}{str(month)}{str(year)}"
    monthCount = f"{str(month)}{str(year)}"


        # [--- Daily ---]
    if userData['history']['daily'].get(dayCount, 0):
        todayGenerations = userData['history']['daily'].get(dayCount, 0)
    else:
        todayGenerations = 0

        # [--- Monthly ---]
    year = int(year) + 2000
    _, days = calendar.monthrange(int(year), int(month))
    monthTotal = 100 * days
    if userData['history']['monthly'].get(monthCount, 0):
        monthlyGenerations = userData['history']['monthly'].get(monthCount, 0)
    else:
        monthlyGenerations = 0

        # [--- If Reached Max Daily ---]
    if todayGenerations == 100:
        return jsonify({'status': 101})



    # [--- Generating Account ---]
    generator = request.args.get('generator')

        # [--- Checking if Exists ---]
    siteData = mongo.db.site.find_one({"_id": "1"})


    generators = siteData['generators']

        # [--- Finding Generator ---]
    for generatorLoop, generatorDetails in generators.items():
        if generatorLoop.lower() == generator.lower():
            with open(f'accounts/{generatorLoop.lower()}.txt', 'r') as file:

                # [--- Checking Stock ---]
                contents = file.read()
                if not contents:
                    return jsonify({'status': 104})

                # [--- Getting Random Line ---]
                lines = [line for line in contents.splitlines() if line.strip() != '']
                account = random.choice(lines)

                # [--- Updating User Generations ---]
                todayGenerations += 1
                monthlyGenerations += 1
                lifetimeGenerations = userData['statistics']['totalGenerated'] + 1
                mongo.db.users.update_one(
                    {"_id": userID},
                    {"$set": {
                        f"history.daily.{str(dayCount)}": todayGenerations,
                        f"history.monthly.{str(monthCount)}": monthlyGenerations,
                        f"statistics.totalGenerated": lifetimeGenerations,
                        }
                    },
                )

                # [--- Updating History ---]
                currentHistory = userData['history']['recent']
                now_utc = datetime.datetime.utcnow()
                formatted_date = now_utc.strftime("%d %B %Y %H:%M UTC")

                newHistory = Functions.updateHistory(currentHistory, generatorDetails['name'], formatted_date, account)

                mongo.db.users.update_one(
                    {"_id": userID},
                    {"$set": {
                        f"history.recent": newHistory,
                        }
                    },
                )


                return jsonify({'status': 105, "credentials": account})

        # [--- Generator Not Found ---]
    return jsonify({'status': 103})


# [--- Generator Delete (POST) ---]
@app.route("/generator/delete", methods=["POST"])
@login_required
def generatorDelete():

    # [--- Getting User/Checking if Authenticated ---]
    userID = session["user"]["id"]
    userData = mongo.db.users.find_one({"_id": userID})
    if not userData:
        return redirect("/logout")
    if not int(userID) == int(os.environ.get('ADMIN_ID')):
        return redirect("/dashboard")



    # [--- Request Parameters ---]
    generator = request.args.get('generator')



    # [--- Update Database ---]
    mongo.db.site.update_one(
        {"_id": "1"},
        {
            "$unset": {
                f"generators.{generator}": '',
            }
        },
        upsert=True,
    )



    # [--- Return Render ---]
    return redirect("/admin")


# [--- Generator Clear (POST) ---]
@app.route("/generator/clear", methods=["POST"])
@login_required
def generatorClear():

    # [--- Getting User/Checking if Authenticated ---]
    userID = session["user"]["id"]
    userData = mongo.db.users.find_one({"_id": userID})
    if not userData:
        return redirect("/logout")
    if not int(userID) == int(os.environ.get('ADMIN_ID')):
        return redirect("/dashboard")



    # [--- Request Parameters ---]
    generator = request.args.get('generator')



    # [--- Clear File ---]
    with open(f'accounts/{generator}.txt', 'w') as file:
        file.write('')



    # [--- Return Render ---]
    return redirect("/admin")


# [--- Generator Create (POST) ---]
@app.route("/generator/create", methods=["POST"])
@login_required
def generatorCreate():

    # [--- Getting User/Checking if Authenticated ---]
    userID = session["user"]["id"]
    userData = mongo.db.users.find_one({"_id": userID})
    if not userData:
        return redirect("/logout")
    if not int(userID) == int(os.environ.get('ADMIN_ID')):
        return redirect("/dashboard")



    # [--- Request Parameters ---]
    generatorID = request.form.get("generatorID").lower()
    generatorDisplay = request.form.get("generatorDisplay")
    generatorID = ''.join([char for char in generatorID if char.isalpha()])



    # [--- Update Database ---]
    mongo.db.site.update_one(
        {"_id": "1"},
        {
            "$set": {
                f"generators.{generatorID}.name": generatorDisplay,
            }
        },
        upsert=True,
    )



    # [--- Create File ---]
    with open(f'accounts/{generatorID}.txt', 'w') as file:
        file.write('')



    # [--- Return Render ---]
    return redirect("/admin")


# [--- Generator Add (POST) ---]
@app.route("/generator/add", methods=["POST"])
@login_required
def generatorAdd():

    # [--- Getting User/Checking if Authenticated ---]
    userID = session["user"]["id"]
    userData = mongo.db.users.find_one({"_id": userID})
    if not userData:
        return redirect("/logout")
    if not int(userID) == int(os.environ.get('ADMIN_ID')):
        return redirect("/dashboard")



    # [--- Request Parameters ---]
    generator = request.args.get('generator')



    # [--- Getting File ---]
    if 'file' not in request.files:
        return jsonify({'status': 100})

    file = request.files['file']

    if file.filename == '':
        return jsonify({'status': 100})

    if not file.filename.endswith('.txt'):
        return jsonify({'status': 101})

    # [--- Updating File ---]
    uploaded_file_contents = file.read()

    with open(f'accounts/{generator}.txt', 'a') as file:
        file.write('\n')
        file.write(uploaded_file_contents.decode('utf-8'))

    with open(f'accounts/{generator}.txt', 'r') as file:
        lines = [line for line in file if line.strip() != '']
        line_count = len(lines)



    # [--- Return Render ---]
    return jsonify({'status': 102, 'newStock': line_count})








# [--- Proxy Route ---]
@app.route("/proxies")
@login_required
def proxies(): 

    # [--- Getting User/Checking if Authenticated ---]
    userID = session["user"]["id"]
    userData = mongo.db.users.find_one({"_id": userID})
    if not userData:
        return redirect("/logout")



    # [--- User Details ---]
    user = {
        "avatar": userData['details']['avatar'],
        "tier": userData['details']['tier'],
        "name": userData['details']['name'],
        "id": userID,
        "adminid": os.environ.get('ADMIN_ID'),
    }



    # [--- Site Details ---]
    siteData = mongo.db.site.find_one({"_id": "1"})
    site = {
        "users": siteData['statistics']['users'],
        "totalGenerations": siteData['statistics']['totalGenerations'],
        "restocks": siteData['statistics']['restocks'],
        "message": {
            "title": siteData['message']["title"],
            "content": siteData['message']["content"],
        },
        "name": os.environ.get('NAME'),
        "letter": os.environ.get('LETTER'),
    }



    # [--- Generators ---]
    proxies = siteData['proxies']


    # [--- Return Render ---]
    return render_template("Proxies.html", user=user, site=site, proxies=proxies)

# [--- Proxy Requests ---]
# [--- Proxy Create (POST) ---]
@app.route("/proxy/create", methods=["POST"])
@login_required
def proxyCreate():

    # [--- Getting User/Checking if Authenticated ---]
    userID = session["user"]["id"]
    userData = mongo.db.users.find_one({"_id": userID})
    if not userData:
        return redirect("/logout")
    if not int(userID) == int(os.environ.get('ADMIN_ID')):
        return redirect("/dashboard")



    # [--- Request Parameters ---]
    proxyID = random.randint(111111111111111111, 999999999999999999)
    proxyTitle = request.form.get("proxyTitle")
    creator = userData['details']['name']
    date = int(time.time())
    proxyType = request.form.get("proxyType")


    # [--- Getting File ---]
    if 'proxyFile' not in request.files:
        return redirect("/admin")

    file = request.files['proxyFile']

    if file.filename == '':
        return redirect("/admin")

    if not file.filename.endswith('.txt'):
        return redirect("/admin")

    # [--- Updating File ---]
    uploaded_file_contents = file.read()
    with open(f"proxies/{proxyID}.txt", 'a') as target_file:
        target_file.write(uploaded_file_contents.decode('utf-8'))

        # [--- Update Database ---]
    mongo.db.site.update_one(
        {"_id": "1"},
        {
            "$set": {
                f"proxies.{proxyID}.title": proxyTitle,
                f"proxies.{proxyID}.uploader": creator,
                f"proxies.{proxyID}.date": date,
                f"proxies.{proxyID}.type": proxyType,
            }
        },
        upsert=True,
    )



    # [--- Return Render ---]
    return redirect("/admin")

# [--- Proxy Delete (POST) ---]
@app.route("/proxy/delete", methods=["POST"])
@login_required
def proxyDelete():

    # [--- Getting User/Checking if Authenticated ---]
    userID = session["user"]["id"]
    userData = mongo.db.users.find_one({"_id": userID})
    if not userData:
        return redirect("/logout")
    if not int(userID) == int(os.environ.get('ADMIN_ID')):
        return redirect("/dashboard")



    # [--- Request Parameters ---]
    proxy = request.args.get('proxy')



    # [--- Update Database ---]
    mongo.db.site.update_one(
        {"_id": "1"},
        {
            "$unset": {
                f"proxies.{proxy}": '',
            }
        },
        upsert=True,
    )



    # [--- Return Render ---]
    return redirect("/admin")

# [--- Proxy Download (GET) ---]
@app.route('/download/proxy/<int:number>.txt', methods=['GET'])
def downloadProxy(number):
    directory = "proxies"
    filename = f"{number}.txt"
    return send_from_directory(directory, filename, as_attachment=True)








# [--- Combo Route ---]
@app.route("/combos")
@login_required
def combos(): 

    # [--- Getting User/Checking if Authenticated ---]
    userID = session["user"]["id"]
    userData = mongo.db.users.find_one({"_id": userID})
    if not userData:
        return redirect("/logout")



    # [--- User Details ---]
    user = {
        "avatar": userData['details']['avatar'],
        "tier": userData['details']['tier'],
        "name": userData['details']['name'],
        "id": userID,
        "adminid": os.environ.get('ADMIN_ID'),
    }



    # [--- Site Details ---]
    siteData = mongo.db.site.find_one({"_id": "1"})
    site = {
        "users": siteData['statistics']['users'],
        "totalGenerations": siteData['statistics']['totalGenerations'],
        "restocks": siteData['statistics']['restocks'],
        "message": {
            "title": siteData['message']["title"],
            "content": siteData['message']["content"],
        },
        "name": os.environ.get('NAME'),
        "letter": os.environ.get('LETTER'),
    }



    # [--- Generators ---]
    combos = siteData['combos']


    # [--- Return Render ---]
    return render_template("Combos.html", user=user, site=site, combos=combos)

# [--- Combo Requests ---]
# [--- Combo Create (POST) ---]
@app.route("/combo/create", methods=["POST"])
@login_required
def comboCreate():

    # [--- Getting User/Checking if Authenticated ---]
    userID = session["user"]["id"]
    userData = mongo.db.users.find_one({"_id": userID})
    if not userData:
        return redirect("/logout")
    if not int(userID) == int(os.environ.get('ADMIN_ID')):
        return redirect("/dashboard")



    # [--- Request Parameters ---]
    comboID = random.randint(111111111111111111, 999999999999999999)
    comboTitle = request.form.get("comboTitle")
    creator = userData['details']['name']
    date = int(time.time())
    comboType = request.form.get("comboType")


    # [--- Getting File ---]
    if 'comboFile' not in request.files:
        return redirect("/admin")

    file = request.files['comboFile']

    if file.filename == '':
        return redirect("/admin")

    if not file.filename.endswith('.txt'):
        return redirect("/admin")

    # [--- Updating File ---]
    uploaded_file_contents = file.read()
    with open(f"combos/{comboID}.txt", 'a') as target_file:
        target_file.write(uploaded_file_contents.decode('utf-8'))

        # [--- Update Database ---]
    mongo.db.site.update_one(
        {"_id": "1"},
        {
            "$set": {
                f"combos.{comboID}.title": comboTitle,
                f"combos.{comboID}.uploader": creator,
                f"combos.{comboID}.date": date,
                f"combos.{comboID}.type": comboType,
            }
        },
        upsert=True,
    )



    # [--- Return Render ---]
    return redirect("/admin")

# [--- Combo Delete (POST) ---]
@app.route("/combo/delete", methods=["POST"])
@login_required
def comboDelete():

    # [--- Getting User/Checking if Authenticated ---]
    userID = session["user"]["id"]
    userData = mongo.db.users.find_one({"_id": userID})
    if not userData:
        return redirect("/logout")
    if not int(userID) == int(os.environ.get('ADMIN_ID')):
        return redirect("/dashboard")



    # [--- Request Parameters ---]
    combo = request.args.get('combo')



    # [--- Update Database ---]
    mongo.db.site.update_one(
        {"_id": "1"},
        {
            "$unset": {
                f"combos.{combo}": '',
            }
        },
        upsert=True,
    )



    # [--- Return Render ---]
    return redirect("/admin")

# [--- Combo Download (GET) ---]
@app.route('/download/combo/<int:number>.txt', methods=['GET'])
def downloadCombo(number):
    directory = "combos"
    filename = f"{number}.txt"
    return send_from_directory(directory, filename, as_attachment=True)


# [--- Admin Only ---]
# [--- Admin Route ---]
@app.route("/admin")
@login_required
def admin(): 

    # [--- Getting User/Checking if Authenticated ---]
    userID = session["user"]["id"]
    userData = mongo.db.users.find_one({"_id": userID})
    if not userData:
        return redirect("/logout")
    if not int(userID) == int(os.environ.get('ADMIN_ID')):
        return redirect("/dashboard")



    # [--- User Details ---]
    user = {
        "avatar": userData['details']['avatar'],
        "tier": userData['details']['tier'],
        "name": userData['details']['name'],
        "id": userID,
        "adminid": os.environ.get('ADMIN_ID'),
    }



    # [--- Site Details ---]
    siteData = mongo.db.site.find_one({"_id": "1"})
    site = {
        "users": siteData['statistics']['users'],
        "totalGenerations": siteData['statistics']['totalGenerations'],
        "restocks": siteData['statistics']['restocks'],
        "message": {
            "title": siteData['message']["title"],
            "content": siteData['message']["content"],
        },
        "name": os.environ.get('NAME'),
        "letter": os.environ.get('LETTER'),
    }
    generators = siteData['generators']
    generatorsTable = {}
    for generator, generatorInfo in generators.items():
        with open(f'accounts/{generator}.txt', 'r') as file:
            lines = [line for line in file if line.strip() != '']
            line_count = len(lines)
        generatorsTable[generator] = {"name": generatorInfo['name'], "stock": line_count}

    proxies = siteData['proxies']
    combos = siteData['combos']

    
    # [--- Return Render ---]
    return render_template("Admin.html", user=user, site=site, generators=generatorsTable, proxies=proxies, combos=combos)

# [--- Message Update (POST) ---]
@app.route("/message/update", methods=["POST"])
@login_required
def updateMessage():

    # [--- Getting User/Checking if Authenticated ---]
    userID = session["user"]["id"]
    userData = mongo.db.users.find_one({"_id": userID})
    if not userData:
        return redirect("/logout")
    if not int(userID) == int(os.environ.get('ADMIN_ID')):
        return redirect("/dashboard")



    # [--- Request Parameters ---]
    messageTitle = request.form.get("title")
    messageContent = request.form.get("content")



    # [--- Update Database ---]
    mongo.db.site.update_one(
        {"_id": "1"},
        {
            "$set": {
                f"message.title": messageTitle,
                f"message.content": messageContent,
            }
        },
        upsert=True,
    )



    # [--- Return Render ---]
    return redirect("/admin")




if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=os.environ.get('PORT'))