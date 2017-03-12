import base64
from collections import OrderedDict

from asn1crypto.core import Sequence, OctetBitString, IA5String, Null
from asn1crypto.keys import PublicKeyInfo
from asn1crypto.algos import AlgorithmIdentifier
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.x509.oid import SignatureAlgorithmOID

class PKAC(Sequence):
    _fields = [
        ('spki', PublicKeyInfo),
        ('challenge', IA5String),
    ]

class SPKAC(Sequence):
    _fields = [
        ('publicKeyAndChallenge', PKAC),
        ('signatureAlgorithm', AlgorithmIdentifier),
        ('signature', OctetBitString),
    ]

def create_spkac(private_key, challenge=''):
    public_key = private_key.public_key()
    public_der = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    pkac = PKAC()
    pkac['spki'] = PublicKeyInfo.wrap(public_der, 'rsa')
    pkac['spki']['public_key'] = OrderedDict([
        ('modulus', public_key.public_numbers().n),
        ('public_exponent', public_key.public_numbers().e),
    ])
    pkac['challenge'] = ''

    spkac = SPKAC()
    spkac['publicKeyAndChallenge'] = pkac
    spkac['signatureAlgorithm'] = OrderedDict([
        ('algorithm', SignatureAlgorithmOID.RSA_WITH_MD5.dotted_string),
        ('parameters', Null()),
    ])
    spkac['signature'] = private_key.sign(
        spkac['publicKeyAndChallenge'].dump(),
        padding.PKCS1v15(),
        hashes.MD5(),
    )
    return base64.b64encode(spkac.dump())
