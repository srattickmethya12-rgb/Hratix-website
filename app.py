import os
import re
import smtplib
import socket
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from flask import url_for # type: ignore[import]
from dotenv import load_dotenv  # type: ignore[import]
from flask import Flask, render_template, request  # type: ignore[import]

load_dotenv()

# --- Configuration -----------------------------------------------------
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

# SMTP settings used for every outgoing email.
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SENDER_NAME = os.getenv("SENDER_NAME", "HRATIX")

# There's no database anymore, so this inbox is the ONLY record of a lead —
# every contact-form submission is delivered here as a notification email.
# Defaults to the sending account itself if not set separately.
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", SMTP_USERNAME)

# Where a visitor's own "thanks, we got it" email should be replied to.
REPLY_TO = os.getenv("REPLY_TO", SMTP_USERNAME)

# WhatsApp click-to-chat number, in international format with no
# spaces/dashes/plus sign (e.g. 15551234567 for +1 555 123 4567).
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER", "")

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

app = Flask(__name__)


# --- Email sending --------------------------------------------------------

def _build_message(subject: str, to_addr: str, text_body: str, html_body: str, reply_to: str = None) -> MIMEMultipart:
    """
    Assemble a MIME email with both a plain-text and an HTML part.
    Including both (rather than HTML-only) and setting Date/Message-ID are
    basic, easily-missed things spam filters specifically check for.
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{SENDER_NAME} <{SMTP_USERNAME}>"
    msg["To"] = to_addr
    if reply_to:
        msg["Reply-To"] = reply_to
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=(SMTP_USERNAME or "").split("@")[-1] or None)
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))
    return msg


def _deliver(msg: MIMEMultipart, to_addr: str) -> None:
    """
    Open an SMTP connection, authenticate, and send. Shared by every email
    this app sends, so there's exactly one place that can get the
    connection logic wrong instead of several copies drifting apart.

    Raises RuntimeError with a specific, actionable message on failure —
    a generic "something went wrong" is nearly useless when debugging why
    mail isn't sending.
    """
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        raise RuntimeError(
            "SMTP_USERNAME / SMTP_PASSWORD are not set. Check your .env file "
            "(copy .env.example to .env if you haven't yet) and restart the "
            "app — environment variables are only read once, at startup."
        )

    try:
        # Port 465 is implicit SSL and needs SMTP_SSL; port 587 (and 25) use
        # a plaintext connection that's then upgraded with STARTTLS. Using
        # the wrong one for a given port is a common reason sending silently
        # hangs or is rejected, so pick the right transport automatically.
        if SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10)
        else:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)

        with server:
            server.ehlo()
            if SMTP_PORT != 465:
                server.starttls()
                server.ehlo()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_USERNAME, to_addr, msg.as_string())

    except smtplib.SMTPAuthenticationError as exc:
        raise RuntimeError(
            "SMTP login was rejected. If this is Gmail, you almost certainly "
            "need an App Password (not your normal account password) — "
            "generate one at https://myaccount.google.com/apppasswords "
            "(requires 2-Step Verification to be turned on). "
            f"Original error: {exc}"
        ) from exc
    except (smtplib.SMTPConnectError, TimeoutError, socket.timeout, ConnectionRefusedError) as exc:
        raise RuntimeError(
            f"Could not connect to {SMTP_SERVER}:{SMTP_PORT}. Check SMTP_SERVER/"
            "SMTP_PORT are correct, and that your host/network/firewall allows "
            f"outbound connections on port {SMTP_PORT} (some hosts block it). "
            f"Original error: {exc}"
        ) from exc
    except smtplib.SMTPRecipientsRefused as exc:
        raise RuntimeError(
            f"The receiving server rejected the recipient address {to_addr!r}: {exc}"
        ) from exc
    except smtplib.SMTPException as exc:
        raise RuntimeError(f"SMTP error while sending email: {exc}") from exc


def send_confirmation_email(to_name: str, to_email: str) -> None:
    """Email the visitor to confirm we received their message. Best-effort —
    see contact() for why a failure here doesn't block showing success."""
    html_body = render_template("email/contact_confirmation.html", name=to_name)
    text_body = (
        f"Hi {to_name},\n\n"
        "Thanks for reaching out to HRATIX. We've received your message and "
        "will get back to you shortly.\n\n"
        "- The HRATIX Team"
    )
    msg = _build_message(
        subject="Thanks for reaching out to HRATIX",
        to_addr=to_email,
        text_body=text_body,
        html_body=html_body,
        reply_to=REPLY_TO,
    )
    _deliver(msg, to_email)


def send_admin_notification_email(name: str, email: str, phone: str, message: str) -> None:
    """
    Email the HRATIX inbox with the enquiry details. With no database, this
    is the only place a submitted lead is ever recorded — so unlike the
    visitor confirmation, a failure here is treated as the submission
    itself having failed (see contact()).
    """
    if not ADMIN_EMAIL:
        raise RuntimeError(
            "ADMIN_EMAIL (and SMTP_USERNAME, its fallback) are both unset, so "
            "there's no inbox to deliver the enquiry to. Set ADMIN_EMAIL in .env."
        )

    subject = f"New enquiry from {name} — HRATIX website"
    text_body = (
        f"New contact form submission:\n\n"
        f"Name: {name}\n"
        f"Email: {email}\n"
        f"Phone: {phone}\n\n"
        f"Message:\n{message}\n"
    )
    html_body = render_template(
        "email/admin_notification.html",
        name=name, email=email, phone=phone, message=message,
    )
    msg = _build_message(
        subject=subject,
        to_addr=ADMIN_EMAIL,
        text_body=text_body,
        html_body=html_body,
        # Reply-To is the visitor's own address, so replying from your inbox
        # goes straight back to them.
        reply_to=email,
    )
    _deliver(msg, ADMIN_EMAIL)


@app.context_processor
def inject_globals():
    """Make shared values available to every template (footer year, WhatsApp number)."""
    return {
        "current_year": datetime.utcnow().year,
        "whatsapp_number": WHATSAPP_NUMBER,
    }


if FLASK_DEBUG:
    @app.route("/dev/test-email")
    def dev_test_email():
        """
        Local debugging helper — only registered when FLASK_DEBUG=true.
        Visit /dev/test-email?to=you@example.com&kind=confirmation (or
        &kind=admin) to trigger a real send attempt and see the *actual*
        SMTP error on screen, instead of it only showing up in the server
        log during a real form submission.
        """
        to = request.args.get("to")
        kind = request.args.get("kind", "confirmation")
        if not to:
            return "Usage: /dev/test-email?to=you@example.com&kind=confirmation|admin", 400
        try:
            if kind == "admin":
                send_admin_notification_email("Test User", to, "0000000000", "This is a test enquiry.")
            else:
                send_confirmation_email("Test User", to)
        except Exception as exc:
            return f"FAILED: {exc}", 500
        return f"Sent OK ({kind}) to {to}"

@app.route("/sitemap.xml")
def sitemap_xml():
    pages = [
        {"loc": url_for("home", _external=True), "priority": "1.0", "changefreq": "weekly"},
        {"loc": url_for("pricing", _external=True), "priority": "0.9", "changefreq": "monthly"},
        {"loc": url_for("contact", _external=True), "priority": "0.8", "changefreq": "monthly"},
    ]
    xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>',
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for page in pages:
        xml_parts.append(
            f"  <url><loc>{page['loc']}</loc>"
            f"<changefreq>{page['changefreq']}</changefreq>"
            f"<priority>{page['priority']}</priority></url>"
        )
    xml_parts.append("</urlset>")
    return "\n".join(xml_parts), 200, {"Content-Type": "application/xml; charset=utf-8"}

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/pricing")
def pricing():
    return render_template("pricing.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method != "POST":
        return render_template("contact.html", msg_sent=False)

    name = (request.form.get("name") or "").strip()
    email = (request.form.get("email") or "").strip()
    phone = (request.form.get("phone") or "").strip()
    message = (request.form.get("message") or "").strip()

    # --- Basic server-side validation ---
    if not name or not email or not phone or not message:
        return render_template(
            "contact.html",
            msg_sent=False,
            error="Please fill in every field before sending your message.",
        )

    if not EMAIL_RE.match(email):
        return render_template(
            "contact.html",
            msg_sent=False,
            error="That email address doesn't look right. Please double-check it.",
        )

    # With no database, the admin notification email IS the record of this
    # lead — if it doesn't go through, the enquiry is lost entirely, so
    # this must not fail silently the way a best-effort send would.
    #try:
    #    send_admin_notification_email(name, email, phone, message)
    #except Exception as exc:
    #    app.logger.error("Failed to deliver contact form enquiry: %s", exc)
    #    return render_template(
    #        "contact.html",
    #        msg_sent=False,
    #        error="We couldn't send your message right now. Please try again "
    #              "shortly, or reach us directly via WhatsApp.",
    #    )

    # The visitor's own confirmation copy is a courtesy, not the record of
    # the lead (the admin email above already succeeded), so a hiccup here
    # shouldn't make them think their enquiry was lost. Log it instead.
    try:
        send_confirmation_email(name, email)
    except Exception as exc:
        app.logger.error("Enquiry delivered but visitor confirmation email failed: %s", exc)

    return render_template("contact.html", msg_sent=True)


if __name__ == "__main__":
    # Most hosting platforms assign a port dynamically via the PORT env var
    # and expect the app to listen on 0.0.0.0, not the 127.0.0.1 Flask binds
    # to by default. Binding to localhost only would make the app
    # unreachable once deployed, even though it'd work fine locally.
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=FLASK_DEBUG)
