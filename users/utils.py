from decouple import config
from trycourier import Courier

client = Courier(auth_token=config('COURIER_TOKEN'))

def account_verification_mail(email:str, link:str, first_name:str):
    client.send_message(
        message={
            "to": {
            "email": "nksarps@gmail.com",
            },
            "template": config("ACCOUNT_VERIFICATION_TEMPLATE_ID"),
            "data": {
            "appName": "BNK",
            "firstName": first_name,
            "link": link,
            },
        }
    )


def password_reset_mail(email:str, link:str, first_name:str):
    client.send_message(
        message={
            "to": {
            "email": email,
            },
            "template": config("PASSWORD_RESET_TEMPLATE_ID"),
            "data": {
            "appName": "BNK",
            "firstName": first_name,
            "link": link,
            },
        }
    )