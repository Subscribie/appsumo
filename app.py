from flask import Flask, request, render_template, redirect
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

load_dotenv()  # take environment variables from .env.

SEND_FROM_EMAIL = os.getenv("SEND_FROM_EMAIL")
SEND_TO_EMAIL = os.getenv("SEND_TO_EMAIL")
EMAIL_HOST = os.getenv("EMAIL_HOST")
SUBSCRIBIE_SHOP_SUBMISSION_ENDPOINT = os.getenv("SUBSCRIBIE_SHOP_SUBMISSION_ENDPOINT")

app = Flask(__name__)


@app.route("/", methods=["POST", "GET"])
@app.route("/appsumo", methods=["POST", "GET"])
def index():
    if request.method == "POST":
        print(request.form)
        email = request.form.get("email")
        redemption_code = request.form.get("redemption_code")
        person_name = request.form.get("person_name")
        company_name = request.form.get("company_name")
        password = request.form.get("password")
        submission = f"{email},{redemption_code},{person_name}, {company_name}\n"
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
        if req.status_code != 200:
            return redirect(url_for("error_creating_shop"))

        shop_url = req.text
        breakpoint()
        return redirect(shop_url)

    return render_template("index.html")


@app.route("/we-will-be-in-touch")
def error_creating_shop():
    return "Wow! Things we busy right now, don't worry, we're creating your shop and will be in touch"


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
