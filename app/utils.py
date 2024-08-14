import imaplib

def check_mailbox(login, password, server, port):
    try:
        mail = imaplib.IMAP4_SSL(server, port)
        mail.login(login, password)
        mail.logout()
        return True
    except Exception as e:
        print(f"Error checking mailbox: {e}")
        return False

def check_gmail(login, password):
    try:
        print(login, password)
        mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
        mail.login(login, password)
        mail.logout()
        return True
    except Exception as e:
        print(f"Error checking Gmail: {e}")
        return False

def get_server_and_port(service):
    if service == 'yandex':
        return 'imap.yandex.ru', 993
    elif service == 'mail':
        return 'imap.mail.ru', 993
    elif service == 'gmail':
        return 'imap.gmail.com', 993
    else:
        raise ValueError("Unknown service type")
