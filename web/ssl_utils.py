#!/usr/bin/env python3
"""
SSL utility functions for the Binance BBO stream web server.
Provides functions for ensuring SSL certificate directories 
and generating self-signed certificates.
"""
import logging
import os

logger = logging.getLogger(__name__)

def ensure_certs_directory():
    """
    Ensure certificates directory exists
    
    Returns:
        bool: True if directories were created successfully, False otherwise
    """
    cert_dir = "certs"
    
    try:
        os.makedirs(cert_dir, exist_ok=True)
        logger.info(f"Ensured certificates directory exists: {cert_dir}")
        return True
    except Exception as e:
        logger.error(f"Error creating certificate directories: {e}")
        return False

def create_ssl_certs(ssl_cert, ssl_key):
    """
    Generate self-signed SSL certificates
    
    Args:
        ssl_cert (str): Path to the certificate file
        ssl_key (str): Path to the key file
        
    Returns:
        bool: True if certificates were created successfully, False otherwise
    """
    logger.warning("SSL certificates not found. Creating self-signed certificates...")
    
    # Ensure directories exist
    if not ensure_certs_directory():
        logger.error("Failed to create certificate directories")
        return False
        
    try:
        # Generate self-signed certificates if they don't exist
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        import datetime

        # Generate a private key
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        # Generate a self-signed certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Binance BBO Stream"),
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
            # Valid for 365 days
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
            critical=False,
        ).sign(key, hashes.SHA256())

        # Write the certificate and key to files
        with open(ssl_cert, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        with open(ssl_key, "wb") as f:
            f.write(key.private_key_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        logger.info(f"Created self-signed certificates at {ssl_cert} and {ssl_key}")
        return True
    except Exception as e:
        logger.error(f"Error creating self-signed certificates: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
