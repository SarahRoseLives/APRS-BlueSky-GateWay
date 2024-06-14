from atproto import Client
import socket
import re
import time

# Initialize client for bluesky
user = 'YOUR_USERNAME'
password = 'YOUR_PASSWORD'

client = Client(base_url='https://bsky.social') # Base URL for bluesky server
client.login(user, password)

client.post("Gateway Started")

# APRS-IS credentials
callsign = "NOCALL"  # Replace with your callsign
passcode = "12345"   # Replace with your APRS-IS passcode
server = "rotate.aprs2.net"
port = 14580

appname = 'BlueSkyGateWay'

def connect_to_aprs_is():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server, port))
    login_command = f"user {callsign} pass {passcode} vers {appname} 1.0 filter b/{callsign}\n"
    sock.sendall(login_command.encode())
    return sock

def listen_for_messages(sock):
    buffer = ""
    while True:
        try:
            data = sock.recv(4096).decode(errors='ignore')
            if not data:
                break
            buffer += data
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                process_line(line.strip())
        except (socket.error, socket.timeout) as e:
            print(f"Socket error occurred: {e}")
            print("Reconnecting...")
            sock.close()
            time.sleep(5)  # Wait before reconnecting
            sock = connect_to_aprs_is()

def process_line(line):
    if f"{callsign}" in line:
        print(f"Message to {callsign}: {line}")
        if "logresp" in line:
            pass  # Handle the log response here if needed
        else:
            pattern = r'^([A-Z0-9-]+)>.*::[A-Z0-9-]+\s*:(.*)$'
            match = re.match(pattern, line)
            if match:
                fromcall = match.group(1)
                message = match.group(2).strip()
                print(f"From: {fromcall} Message: {message}")

                client = Client(base_url='https://bsky.social')
                client.login(user, password)

                client.send_post(f'{fromcall}: {message}')
                print(f'Sent: {fromcall}: {message}')
            else:
                print("No match found")

def main():
    sock = None
    try:
        sock = connect_to_aprs_is()
        print(f"Connected to APRS-IS as {callsign}. Listening for messages to {callsign}...")
        listen_for_messages(sock)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if sock:
            sock.close()

if __name__ == "__main__":
    main()
