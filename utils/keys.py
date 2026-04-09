from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa 
from cryptography import x509
from cryptography.x509 import NameOID
from cryptography.fernet import Fernet
from ipaddress import ip_address
from cryptography.hazmat.backends import default_backend

import sys, os, dotenv
from datetime import datetime, timezone, timedelta

env_file= os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
dotenv.load_dotenv(env_file)

def generate_key():
    key= Fernet.generate_key()

    with open(env_file, 'wb') as f:
        f.write(f"PASSWORD={key}".encode("utf-8"))

    #print(key)
    return key 


password= os.environ.get('PASSWORD')
password_byte= bytes(password, encoding="utf-8")
#print(password_byte, type(password_byte))



def generate_cert_and_key(host:str):
    global password_byte

    private_key= rsa.generate_private_key(
        public_exponent= 65537,
        key_size= 2048,
        backend= default_backend()
    )

    subject= issuer= x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, 'UK'),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, 'Local'),
        x509.NameAttribute(NameOID.LOCALITY_NAME, 'localhost'),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'Secure socekt layer'),
        x509.NameAttribute(NameOID.COMMON_NAME, host),
    ])

    ip_add= ip_address(host)

    cert= (
        x509.CertificateBuilder()
        .issuer_name(issuer)
        .subject_name(subject)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days= 365))
        .add_extension(
            x509.BasicConstraints(ca= True, path_length=None),
            critical=True
        )
        .add_extension(
            x509.SubjectAlternativeName([x509.IPAddress(ip_add)]),
            critical= False
        )
        .sign(
            private_key,
            hashes.SHA256(),
            backend= default_backend(),
        )
    )


    key_file= os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'key.pem'))
    cert_file= os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'cert.pem'))

    # Create private key file
    with open(key_file, 'wb') as f:
        f.write(
            private_key.private_bytes(
                encoding= serialization.Encoding.PEM,
                format= serialization.PrivateFormat.PKCS8,
                encryption_algorithm= serialization.BestAvailableEncryption(password_byte),
            )
        )

    # create certificate file
    with open(cert_file, 'wb') as f:
        f.write(
            cert.public_bytes(
                encoding=serialization.Encoding.PEM
            )
        )




if __name__ == "__main__":
    #generate_key()
    #generate_cert_and_key(host="127.0.0.1")
    pass 
