import base64
import re

import requests

class ComodoException(Exception):
    pass

def send_application(first_name, last_name, email_address, country, spkac, revocation_password):
    session = requests.Session()
    resp = session.get('https://secure.comodo.com/products/frontpage?area=SecureEmailCertificate')
    try:
        sid_token = re.search('name=SID value=(\w+)', resp.text).group(1)
    except Exception:
        raise ComodoException("Couldn't extract SID token")

    resp = session.post('https://secure.comodo.com/products/!SecureEmailCertificate_Signup', {
        'SID': sid_token,
        'foreName': first_name,
        'surname': last_name,
        'emailAddress': email_address,
        'countryName': country,
        'spkac': spkac,
        'challengePassword': revocation_password,
        'iAccept': 'on',
        'submitButton': 'Next >',
    })
    if 'Application is successful!' in resp.text:
        return
    try:
        reason = re.search(r'loadPage\(\) {.+?alert\("(.+?)"\).+?}', resp.text, re.S).group(1)
    except Exception:
        raise ComodoException('Application failed for unknown reason')
    raise ComodoException('Application failed: ' + reason)

def retrieve_certificate_chain(collection_password):
    session = requests.Session()
    resp = session.post('https://secure.comodo.com/products/download/CollectCCC', {
        'collectionCode': collection_password,
        'queryType': '1',
        'responseType': '3',
        'responseEncoding': '0',
        'responseMimeType': 'application/x-x509-user-cert',
        'product': '9',
    })
    certificate_chain = b'\n'.join(resp.content.splitlines()[1:])
    return certificate_chain
