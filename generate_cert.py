from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import datetime
import socket

def generate_self_signed_cert():
    # Detect IP
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip_addr = s.getsockname()[0]
    except:
        ip_addr = "127.0.0.1"
    s.close()

    # Generate key
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Generate cert
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"BR"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"Amazonas"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"Manacapuru"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Cartorio 2 Oficio"),
        x509.NameAttribute(NameOID.COMMON_NAME, f"{ip_addr}"),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=3650)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName(u"localhost"), x509.IPAddress(import_ip_address(ip_addr))]),
        critical=False,
    ).sign(key, hashes.SHA256())

    # Write key
    with open("key.pem", "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    # Write cert
    with open("cert.pem", "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
        
    print(f"Certificado gerado para IP: {ip_addr}")

def import_ip_address(ip):
    import ipaddress
    return ipaddress.ip_address(ip)

if __name__ == "__main__":
    generate_self_signed_cert()
