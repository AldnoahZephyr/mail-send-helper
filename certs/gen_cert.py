# -*- coding: utf-8 -*-
"""使用 Python cryptography 库生成自签名代码签名证书 (PFX)"""
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

OUT_DIR = Path(__file__).resolve().parent
PFX_PATH = OUT_DIR / "MailSendHelper.pfx"
CER_PATH = OUT_DIR / "MailSendHelper.cer"
PFX_PASS = b"mail123"

print("=== MailSendHelper 自签名证书生成 (Python) ===")
print()

# 1. 生成 RSA 密钥对
print("[1/4] 正在生成 RSA 4096 密钥对...")
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=4096,
    backend=default_backend()
)
print("    密钥已生成")

# 2. 构建证书主题和 SAN
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MailSendHelper"),
    x509.NameAttribute(NameOID.COMMON_NAME, "MailSendHelper"),
])

now = datetime.now(timezone.utc)

cert = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(private_key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(now)
    .not_valid_after(now + timedelta(days=365 * 10))  # 10 年
    # 代码签名必需的扩展
    .add_extension(
        x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.CODE_SIGNING]),
        critical=True,
    )
    .add_extension(
        x509.KeyUsage(
            digital_signature=True,
            content_commitment=False,
            key_encipherment=False,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=False,
            crl_sign=False,
            encipher_only=False,
            decipher_only=False,
        ),
        critical=True,
    )
    .sign(private_key, hashes.SHA256(), default_backend())
)

print(f"    证书指纹: {cert.fingerprint(hashes.SHA256()).hex()}")
print(f"    有效期至: {cert.not_valid_after_utc.strftime('%Y-%m-%d')}")

# 3. 导出 PFX (PKCS#12) —— Windows 代码签名用
print("[2/4] 正在导出 PFX 证书文件...")
p12 = pkcs12.serialize_key_and_certificates(
    name=b"MailSendHelper",
    key=private_key,
    cert=cert,
    cas=None,
    encryption_algorithm=serialization.BestAvailableEncryption(PFX_PASS),
)
PFX_PATH.write_bytes(p12)
print(f"    PFX 已保存: {PFX_PATH}")

# 4. 导出 CER (公钥证书)
print("[3/4] 正在导出 CER 公钥证书...")
CER_PATH.write_bytes(cert.public_bytes(serialization.Encoding.DER))
print(f"    CER 已保存: {CER_PATH}")

# 5. 提示
print()
print("[4/4] 证书已生成，接下来请以管理员身份运行 gen_cert.ps1 将证书导入受信任的根存储。")
print(f"    或手动操作：双击 {CER_PATH} → 安装证书 → 「受信任的根证书颁发机构」")
print()
print("完成后即可运行 build.bat 进行打包签名。")
