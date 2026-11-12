from django.core.mail import send_mail, EmailMessage


class Util:
    @staticmethod
    def sendVerificationEmail(email, url):

        email_message = EmailMessage(subject='verify email',
                                     body='Link: {}'.format(url),
                                     to=[email])
        email_message.send()

    @staticmethod
    def sendInvitationEmail(email, url,message=None):
        body = """
                Message: {0}
                Link: {1}
        """.format(message,url)
        email_message = EmailMessage(subject='Invitation to join the company',
                                     body=body,
                                     to=[email])
        email_message.send()



def sendSMS(cellphone, message, provider=1):
    if provider == 0:
        import requests

        url = "http://www.AFE.ir/Url/SendSMS.aspx"
        username = "omd57@yahoo.com"
        password = "5855009"
        sender = "500048032"

        req = "{0}?Username={1}&Password={2}&Number={3}&Mobile={4}&SMS={5}".format(
            url, username, password, sender, cellphone, message
        )
        response = requests.get(req)
        return response
    else:
        from zeep import Client

        username = "500012345678914"
        password = "0017317584"
        sender = "500012345678914"
        url = "http://www.linepayamak.ir/Post/Send.asmx?wsdl"
        client = Client(url)
        response = client.service.SendSimpleSMS(
            username, password, cellphone, sender, message, False
        )
        return response

def sendVerificationSMS(cellphone, verification_code):
    # return sendSMS(cellphone,verification_code)
    import requests
    import json
    from django.conf import settings

    _api_key = settings.KAVENEGAR_API_KEY
    _template = settings.KAVENEGAR_TEMPLATE
    _rest_url = "https://api.kavenegar.com/v1/%s/verify/lookup.json" % _api_key
    _data = {"receptor": cellphone, "token": verification_code, "template": _template}
    _headers = {"Content-type": "application/json"}
    _response = requests.get(_rest_url, params=_data, headers=_headers)
    _resp = _response.text
    try:
        _resp = json.loads(_response.text)
    except:
        pass
    return {"result": _resp, "status": _response.status_code}