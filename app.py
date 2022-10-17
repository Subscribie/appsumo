from flask import Flask, request, render_template, url_for, redirect
import os

app = Flask(__name__)


@app.route("/appsumo/special-access", methods=["GET"])
def thanks():
    return "Thanks! Here's your special access AppSumo Subscribie plan link: ..."


@app.route("/test", methods=["POST", "GET"])
@app.route("/appsumo", methods=["POST", "GET"])
def hello_world():
    if request.method == "POST":
        print(request.form)
        email = request.form.get("email")
        redemption_code = request.form.get("redemption_code")
        lastname = request.form.get("lastname")

        submission = f"{email},{redemption_code},{lastname}\n"
        with open("./submissions.csv", "a") as fp:
            fp.write(submission)
        send_mail()
        return redirect(url_for("thanks"))
    return render_template("index.html")


import smtplib
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate


def send_mail(
    send_from=SEND_FROM_EMAIL,
    send_to=[SEND_TO_EMAIL],
    subject="appsumo latest csv",
    text="see attachmrnt",
    files=["./submissions.csv"],
    server="127.0.0.1",
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

    smtp = smtplib.SMTP(server)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.close()
