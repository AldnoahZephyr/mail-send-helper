# MailSendHelper 自签名证书生成脚本
# 用法：在目录下右键 → "使用 PowerShell 运行"，或管理员 PowerShell 中执行 .\gen_cert.ps1
# 如果以管理员运行，会自动将证书导入"受信任的根证书颁发机构"，彻底解决杀软误报。

$ErrorActionPreference = "Stop"

$certName   = "MailSendHelper"
$pfxPath    = Join-Path $PSScriptRoot "MailSendHelper.pfx"
$cerPath    = Join-Path $PSScriptRoot "MailSendHelper.cer"
$pfxPass    = "mail123"   # PFX 密码，build.bat 签名时会用到

Write-Host "=== MailSendHelper 自签名证书生成 ===" -ForegroundColor Cyan
Write-Host ""

# 1. 删除旧证书（如果存在）
if (Test-Path $pfxPath) { Remove-Item $pfxPath -Force; Write-Host "[1/4] 已删除旧 PFX" -ForegroundColor Gray }
if (Test-Path $cerPath) { Remove-Item $cerPath -Force }

# 2. 创建自签名代码签名证书
Write-Host "[2/4] 正在生成代码签名证书..." -ForegroundColor Yellow
$cert = New-SelfSignedCertificate `
    -Type CodeSigningCert `
    -Subject "CN=$certName, O=$certName, C=CN" `
    -KeyUsage DigitalSignature `
    -KeyAlgorithm RSA `
    -KeyLength 4096 `
    -NotAfter (Get-Date).AddYears(10) `
    -CertStoreLocation "Cert:\CurrentUser\My"

Write-Host "    指纹: $($cert.Thumbprint)" -ForegroundColor Green
Write-Host "    有效期至: $($cert.NotAfter)" -ForegroundColor Green

# 3. 导出 PFX（带密码保护）
Write-Host "[3/4] 正在导出 PFX 证书文件..." -ForegroundColor Yellow
$securePass = ConvertTo-SecureString -String $pfxPass -Force -AsPlainText
Export-PfxCertificate `
    -Cert $cert `
    -FilePath $pfxPath `
    -Password $securePass | Out-Null
Write-Host "    PFX 已保存: $pfxPath" -ForegroundColor Green

# 导出 CER（公钥证书，可选）
Export-Certificate -Cert $cert -FilePath $cerPath -Type CERT | Out-Null
Write-Host "    CER 已保存: $cerPath" -ForegroundColor Gray

# 4. 尝试导入到受信任的根证书颁发机构（需管理员权限）
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if ($isAdmin) {
    Write-Host "[4/4] 正在导入到受信任的根证书颁发机构..." -ForegroundColor Yellow
    try {
        $store = New-Object System.Security.Cryptography.X509Certificates.X509Store("Root", "CurrentUser")
        $store.Open("ReadWrite")
        # 先检查是否已存在
        $existing = $store.Certificates | Where-Object { $_.Thumbprint -eq $cert.Thumbprint }
        if (-not $existing) {
            $store.Add($cert)
            Write-Host "    证书已导入到「受信任的根证书颁发机构」，杀软不会再误报！" -ForegroundColor Green
        } else {
            Write-Host "    证书已存在于受信任的根证书颁发机构中，无需重复导入。" -ForegroundColor Green
        }
        $store.Close()
    } catch {
        Write-Host "    导入失败: $_" -ForegroundColor Red
        Write-Host "    请手动双击 $cerPath 安装证书到「受信任的根证书颁发机构」" -ForegroundColor Yellow
    }
} else {
    Write-Host "[4/4] 未以管理员运行，跳过自动导入" -ForegroundColor DarkYellow
    Write-Host ""
    Write-Host "=== 重要 ===" -ForegroundColor Yellow
    Write-Host "请以管理员身份重新运行此脚本，将证书导入受信任的根存储，彻底解决杀软误报。"
    Write-Host "或手动操作：双击 $cerPath → 安装证书 → 选择「受信任的根证书颁发机构」。"
}

Write-Host ""
Write-Host "完成！现在可以运行 build.bat 进行打包签名了。" -ForegroundColor Cyan
