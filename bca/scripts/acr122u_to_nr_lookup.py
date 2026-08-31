#!/usr/bin/env python3

import json
import time
import urllib.request
import urllib.error

from smartcard.System import readers
from smartcard.Exceptions import NoCardException, CardConnectionException

NODE_RED_URL = "http://127.0.0.1:1880/bca/api/band-lookup"
POLL_SECONDS = 0.25

GET_UID_APDU = [0xFF, 0xCA, 0x00, 0x00, 0x00]


def pick_reader():
    found = readers()
    if not found:
        return None

    for reader in found:
        name = str(reader).upper()
        if "ACR122" in name or "ACS" in name:
            return reader

    return found[0]


def post_uid(uid):
    body = json.dumps({"uid": uid}).encode("utf-8")

    req = urllib.request.Request(
        NODE_RED_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=5) as response:
        text = response.read().decode("utf-8")
        return response.status, text


def main():
    print("BCA ACR122U -> Node-RED lookup bridge")
    print(f"Posting scans to: {NODE_RED_URL}")
    print("Press Ctrl+C to stop.")
    print("")

    current_uid = None
    last_reader_name = None

    while True:
        reader = pick_reader()

        if reader is None:
            print("No PC/SC reader found.")
            current_uid = None
            time.sleep(2)
            continue

        reader_name = str(reader)
        if reader_name != last_reader_name:
            print(f"Using reader: {reader_name}")
            last_reader_name = reader_name

        try:
            conn = reader.createConnection()
            conn.connect()

            data, sw1, sw2 = conn.transmit(GET_UID_APDU)

            if sw1 == 0x90 and sw2 == 0x00 and data:
                uid = "".join(f"{b:02X}" for b in data)

                if uid != current_uid:
                    current_uid = uid
                    print("")
                    print(f"SCAN UID: {uid}")

                    try:
                        status, response_text = post_uid(uid)
                        print(f"Node-RED HTTP: {status}")

                        try:
                            response_json = json.loads(response_text)
                            print(response_json.get("display_text", response_text))
                        except json.JSONDecodeError:
                            print(response_text)

                    except urllib.error.URLError as e:
                        print(f"ERROR posting to Node-RED: {e}")

            time.sleep(POLL_SECONDS)

        except NoCardException:
            current_uid = None
            time.sleep(POLL_SECONDS)

        except CardConnectionException:
            current_uid = None
            time.sleep(POLL_SECONDS)

        except KeyboardInterrupt:
            print("")
            print("Stopped.")
            break

        except Exception as e:
            print(f"ERROR: {e}")
            current_uid = None
            time.sleep(1)


if __name__ == "__main__":
    main()
