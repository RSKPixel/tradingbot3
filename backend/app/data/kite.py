import logging
from kiteconnect import KiteConnect
import kiteconnect.exceptions as ke

logging.basicConfig(level=logging.DEBUG)
kite = KiteConnect(api_key="tw96psyyds0yj8vj")


def connection() -> KiteConnect:
    try:
        with open("access_token.txt", "r") as f:
            access_token = f.read().strip()

        kite.set_access_token(access_token)
        profile = kite.profile()
        return kite
    except ke.TokenException as e:
        logging.error("Error setting access token: %s", e)
        print("Login URL:", kite.login_url())
        request_token = input("Enter request token: ")

        try:
            data = kite.generate_session(
                request_token, api_secret="3iewov9onkbytzramkt263r9lvcdzks9")
            kite.set_access_token(data["access_token"])
            # Save the access token for future use
            with open("access_token.txt", "w") as f:
                f.write(data["access_token"])
            return kite
        except Exception as e:
            logging.error("Error generating session: %s", e)
            print(
                "Failed to generate session. Please check your request token and API secret.")
            return None
    return None
