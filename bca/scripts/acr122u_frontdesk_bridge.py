#!/usr/bin/env python3

import json
import time
import urllib.request
import urllib.error

from smartcard.System import readers
from smartcard.Exceptions import NoCardException, CardConnectionException

SCAN_URL = "http://127.0.0.1:1880/bca/api/frontdesk-scan"
STATUS_URL = "http://127.0.0.1:1880/bca/api/frontdesk-scanner-status"
SCANNER_ID = "frontdesk_acr122u_1"

POLL_SECONDS = 0.25
HEARTBEAT_SECONDS = 1.0

GET_UID_APDU = [0xFF, 0xCA, 0x00, 0x00, 0x00]


def post_json(url, payload, timeout=3):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=timeout) as response:
        text = response.read().decode("utf-8")
        return response.status, text


def post_status(connected, reader_name="", message=""):
    payload = {
        "scanner_id": SCANNER_ID,
        "status": "connected" if connected else "not_connected",
        "connected": bool(connected),
        "reader_name": reader_name,
        "message": message,
    }

    try:
        return post_json(STATUS_URL, payload, timeout=2)
    except Exception as exc:
        print(f"STATUS POST ERROR: {exc}")
        return None, ""


def post_scan(uid):
    payload = {
        "scanner_id": SCANNER_ID,
        "uid": uid,
    }

    return post_json(SCAN_URL, payload, timeout=5)


def pick_reader():
    found = readers()

    if not found:
        return None

    for reader in found:
        name = str(reader).upper()
        if "ACR122" in name or "ACS" in name:
            return reader

    return found[0]


def main():
    print("BCA ACR122U front-desk scanner bridge")
    print(f"Scanner ID: {SCANNER_ID}")
    print(f"Scan URL: {SCAN_URL}")
    print(f"Status URL: {STATUS_URL}")
    print("Press Ctrl+C to stop.")
    print("")

    current_uid = None
    last_reader_name = None
    last_heartbeat = 0

    while True:
        try:
            reader = pick_reader()

            if reader is None:
                current_uid = None
                now = time.monotonic()

                if now - last_heartbeat >= HEARTBEAT_SECONDS:
                    print("Scanner status: NOT CONNECTED")
                    post_status(False, "", "No PC/SC reader found.")
                    last_heartbeat = now

                time.sleep(1)
                continue

            reader_name = str(reader)

            if reader_name != last_reader_name:
                print(f"Using reader: {reader_name}")
                last_reader_name = reader_name

            now = time.monotonic()

            if now - last_heartbeat >= HEARTBEAT_SECONDS:
                post_status(True, reader_name, "Scanner connected.")
                last_heartbeat = now

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
                            status, response_text = post_scan(uid)
                            print(f"Node-RED scan HTTP: {status}")

                            try:
                                response_json = json.loads(response_text)
                                print(
                                    response_json.get("message")
                                    or response_json.get("code")
                                    or response_text
                                )
                            except json.JSONDecodeError:
                                print(response_text)

                        except urllib.error.URLError as exc:
                            print(f"ERROR posting scan to Node-RED: {exc}")

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
            post_status(False, last_reader_name or "", "Scanner bridge stopped.")
            break

        except Exception as exc:
            print(f"ERROR: {exc}")
            current_uid = None
            post_status(False, last_reader_name or "", str(exc))
            time.sleep(1)


if __name__ == "__main__":
    main()
