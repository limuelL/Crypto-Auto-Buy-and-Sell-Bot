import smtplib


class SendEmailAfterTrade:
    sender = 'sender email address'
    receiver = 'reciever email address'
    subject = 'subject of message'
    body = ''

    def __init__(self, password):
        self.password = password

    def send_mail_message(self):

        message = f"""From: Trading Bot{self.sender}\n
        To: Creator {self.receiver}\n
        Subject: {self.subject}\n
        {self.body}    
        """

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()

        try:
            server.login(self.sender, self.password)
            print('Logged in...')

            server.sendmail(self.sender, self.receiver, message)
            print('Email has been sent!')
        except smtplib.SMTPAuthenticationError:
            print('Unable to sign in...')

