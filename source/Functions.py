from flask import Flask, request, redirect, session, render_template, flash, url_for
from flask_pymongo import PyMongo


def firstTimeSetupMongo(mongo):
    default_values = {
        "_id": "1",
        "statistics": {
            "users": 0,
            "totalGenerations": 0,
            "restocks": 0,
        },
        "message": {
            "title": "Place Holder",
            "content": "Update this to display your own message in Admin Settings.",
        },
        "generators": {},
        "proxies": {},
        "combos": {},
    }
    mongo.db.site.insert_one(default_values)


def createUser(mongo, userID, userName, userEmail, userAvatar):
    DEFAULTVALUES = {
        "_id": userID,
        "details": {
            "name": userName,
            "email": userEmail,
            "tier": "Free Tier",
            "avatar": f"https://cdn.discordapp.com/avatars/{userID}/{userAvatar}.png",
        },
        "statistics": {"totalGenerated": 0},
        "history": {
            "daily": {},
            "monthly": {},
            "recent": {
                "1": {
                    "type": "",
                    "date": "",
                    "credentials": "",
                },
                "2": {
                    "type": "",
                    "date": "",
                    "credentials": "",
                },
                "3": {
                    "type": "",
                    "date": "",
                    "credentials": "",
                },
                "4": {
                    "type": "",
                    "date": "",
                    "credentials": "",
                },
                "5": {
                    "type": "",
                    "date": "",
                    "credentials": "",
                },
            },
        },
    }

    mongo.db.users.insert_one(DEFAULTVALUES)


def updateHistory(table, hTypew, date, credentials):
    newHistory = {
        "1": {
            "type": "",
            "date": "",
            "credentials": "",
        },
        "2": {
            "type": "",
            "date": "",
            "credentials": "",
        },
        "3": {
            "type": "",
            "date": "",
            "credentials": "",
        },
        "4": {
            "type": "",
            "date": "",
            "credentials": "",
        },
        "5": {
            "type": "",
            "date": "",
            "credentials": "",
        },
    }

    newHistory["5"]["type"] = table["4"]["type"]
    newHistory["5"]["date"] = table["4"]["date"]
    newHistory["5"]["credentials"] = table["4"]["credentials"]

    newHistory["4"]["type"] = table["3"]["type"]
    newHistory["4"]["date"] = table["3"]["date"]
    newHistory["4"]["credentials"] = table["3"]["credentials"]

    newHistory["3"]["type"] = table["2"]["type"]
    newHistory["3"]["date"] = table["2"]["date"]
    newHistory["3"]["credentials"] = table["2"]["credentials"]

    newHistory["2"]["type"] = table["1"]["type"]
    newHistory["2"]["date"] = table["1"]["date"]
    newHistory["2"]["credentials"] = table["1"]["credentials"]

    newHistory["1"]["type"] = hTypew
    newHistory["1"]["date"] = date
    newHistory["1"]["credentials"] = credentials

    return newHistory
