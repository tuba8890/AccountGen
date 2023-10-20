# AccountGen
 ## Features
 - Discord Login
 - MongoDB Datebase Intergration
 - .env Configuration
 - Daily/Monthly Generation Limit
 - Unlimited Different Account Generators
 - Global Statistics
 - Combo Lists
 - Proxy Lists
 - Admin Dashboard (Create generator, add accounts, delete generator, add proxy, delete proxy, add combo, delete combo, edit message)

## Setup
1. Make sure you have Python.
2. Download this github and have the source folder.
3. In the source folder, open cmd and run ```pip install -r requirements.txt```
4. Open the .env in an editor, and paste your MongoURI link. (https://www.mongodb.com/docs/manual/reference/connection-string/)
5. Go to the Discord Developer Portal (https://discord.com/developers/applications) and create a new application.
6. Go under the OAuth tab and get the client ID, paste this under the CLIENT_ID in .env.
7. On the Developer Portal, click Reset Secret and paste this value under the CLIENT_SECRET in .env.
8. On the Developer Portal, click Add Redirect. Put localhost:8080/callback and any other domains you are using.
9. Put your Discord user ID under ADMIN_ID in .env.
10. Customise the Site Information values in the .env to your liking. It is recommended to keep the port 8080.
11. Run ``Start.py`` and it should be running.
12. Everything else is self-explanatory for creating generators, adding stock etc. Just go under the admin tab.
13. If you want others to be able to access it, google a tutorial for port forwarding.

## Pictures
![One](https://i.imgur.com/T2f3Lwr.png)
![Two](https://i.imgur.com/LOtnilm.png)
![Three](https://i.imgur.com/XfPnYGi.png)
![Four](https://i.imgur.com/XxIONse.png)
![Five](https://i.imgur.com/BCWLRFS.png)

