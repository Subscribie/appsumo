from flask import Flask, request, render_template, redirect, url_for, flash, session
import os
import logging
from dotenv import load_dotenv
import smtplib
import requests
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
import backoff
from urllib.parse import urlparse

load_dotenv()  # take environment variables from .env.

SEND_FROM_EMAIL = os.getenv("SEND_FROM_EMAIL")
SEND_TO_EMAIL = os.getenv("SEND_TO_EMAIL")
EMAIL_HOST = os.getenv("EMAIL_HOST")
SUBSCRIBIE_SHOP_SUBMISSION_ENDPOINT = os.getenv("SUBSCRIBIE_SHOP_SUBMISSION_ENDPOINT")
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")


@backoff.on_exception(
    backoff.expo,
    (requests.exceptions.RequestException, Exception),
    max_time=60,
)
def get_new_shop_url(url):
    """get_new_shop_url will rety visiting the new shop url
    until a http 200 response is received"""
    req = requests.get(url)
    if req.status_code != 200:
        raise Exception("get_new_shop_url status_code was not 200, maybe retrying")
    return req

@app.route("/test")
def test():
    return request.url

@app.route("/", methods=["POST", "GET"])
@app.route("/appsumo", methods=["POST", "GET"])
@app.route("/pitchground", methods=["POST", "GET"])
@app.route("/coderedemption", methods=["POST", "GET"]
def index():
    subscribie_domain = os.getenv("SUBSCRIBIE_DOMAIN")
    if 'appsumo' in request.url:
        reseller = "AppSumo"
    elif 'pitchground' in request.url:
        reseller = "PitchGround"
    elif 'coderedemption' in request.url:
        reseller = "Lifetime"
    else:
        reseller = request.path.replace("/","").capitalize()

    if request.method == "POST":
        session["formData"] = request.form
        print(request.form)
        email = request.form.get("email")
        redemption_code = request.form.get("redemption_code")
        person_name = request.form.get("person_name")
        company_name = request.form.get("company_name")
        password = request.form.get("password")
        submission = f"{email},{redemption_code},{person_name}, {company_name}\n"
        check_shop_name = requests.get(
            f"{subscribie_domain}/api/shop-name-taken/{company_name}"
        )
        if check_shop_name.json() is False:
            with open("./submissions.csv", "a") as fp:
                fp.write(submission)
            send_mail()
            # Submit new site build
            req = requests.post(
                SUBSCRIBIE_SHOP_SUBMISSION_ENDPOINT,
                data={
                    "company_name": company_name,
                    "email": email,
                    "password": password,
                    "title-0": "Plan 1",
                    "interval_amount-0": 10099,
                    "interval_unit-0": "monthly",
                    "description-0": "Change plan description in your shop dashboard",
                },
            )
            # Send user into their new shop right away
            login_url = req.text
            shop_url = f"{urlparse(req.text).scheme}://{urlparse(req.text).netloc}"

            try:
                # Retry until shop is ready
                get_new_shop_url(shop_url)
            except Exception as e:
                return redirect(url_for("error_creating_shop"))

            # Take visitor directly into their shop
            # note login_url is a one-time login url sent by Subscribie,
            return redirect(login_url)
        else:
            flash("The Business Name already exists, please provide another name")
            return redirect(url_for("index", subscribie_domain=subscribie_domain))
    if session.get("formData") == None:
        session["formData"] = {}
    return render_template("index.html", subscribie_domain=subscribie_domain, reseller=reseller)


@app.route("/we-will-be-in-touch")
def error_creating_shop():
    return "<style>body { font-family: sans-serif;}</style><h1>Thanks! We'll be right with you...</h1><p>Things are super busy right now, but don't worry! We're creating your shop in a queue and will be in touch with you with your shop login soon.</p><p>Thank you for your patience. 😊</p>"


def send_mail(
    send_from=SEND_FROM_EMAIL,
    send_to=[SEND_TO_EMAIL],
    subject="appsumo latest csv",
    text="see attachmrnt",
    files=["./submissions.csv"],
    server=EMAIL_HOST,
):
    assert isinstance(send_to, list)

    msg = MIMEMultipart()
    msg["From"] = send_from
    msg["To"] = COMMASPACE.join(send_to)
    msg["Date"] = formatdate(localtime=True)
    msg["Subject"] = subject

    msg.attach(MIMEText(text))

    for f in files or []:
        with open(f, "rb") as fil:
            part = MIMEApplication(fil.read(), Name=basename(f))
        # After the file is closed
        part["Content-Disposition"] = 'attachment; filename="%s"' % basename(f)
        msg.attach(part)
    try:
        smtp = smtplib.SMTP(server)
        smtp.sendmail(send_from, send_to, msg.as_string())
        smtp.close()
    except ConnectionRefusedError as e:
        logging.error(f"ConnectionRefusedError sending email {e}")
    except Exception as e:
        logging.error(f"Unhandled Exception sending email {e}")
