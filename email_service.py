import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sqlite3
import threading
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_PATH = "imoveis.db"

def get_config():
    """Retrieves SMTP configuration from DB."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT key, value FROM system_config")
        rows = cur.fetchall()
        conn.close()
        return {row[0]: row[1] for row in rows}
    except Exception as e:
        logging.error(f"Error fetching config: {e}")
        return {}

def send_email_sync(to_email, subject, body):
    """Sends email synchronously (blocking)."""
    if not to_email:
        logging.warning("No recipient email provided.")
        return False

    config = get_config()
    smtp_server = config.get("smtp_server")
    smtp_port = config.get("smtp_port")
    smtp_user = config.get("smtp_user")
    smtp_password = config.get("smtp_password")
    
    if not all([smtp_server, smtp_port, smtp_user, smtp_password]):
        logging.warning("SMTP configuration incomplete.")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to_email, msg.as_string())
        server.quit()
        logging.info(f"Email sent to {to_email}")
        return True
    except Exception as e:
        logging.error(f"Failed to send email to {to_email}: {e}")
        return False

def send_email_async(to_email, subject, body):
    """Sends email asynchronously using a thread."""
    thread = threading.Thread(target=send_email_sync, args=(to_email, subject, body))
    thread.daemon = True
    thread.start()

# --- Helper for Styling ---

def _get_email_template(title, content):
    """Wraps content in a professional HTML email template."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4; }}
            .container {{ max-width: 600px; margin: 20px auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
            .header {{ background-color: #0d6efd; color: #ffffff; padding: 20px; text-align: center; }}
            .header h2 {{ margin: 0; font-size: 24px; }}
            .content {{ padding: 30px; }}
            .footer {{ background-color: #333; color: #aaa; text-align: center; padding: 15px; font-size: 12px; }}
            .alert-box {{ background-color: #e9ecef; border-left: 5px solid #0d6efd; padding: 15px; margin: 20px 0; }}
            .label {{ font-weight: bold; color: #555; }}
            .highlight {{ color: #0d6efd; font-weight: bold; }}
            .warning {{ color: #dc3545; font-weight: bold; }}
            .success {{ color: #198754; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>{title}</h2>
            </div>
            <div class="content">
                {content}
            </div>
            <div class="footer">
                <p>Sistema ONR - Notificação Automática</p>
                <p>&copy; {datetime.now().year} Feitosa Soluções. Todos os direitos reservados.</p>
            </div>
        </div>
    </body>
    </html>
    """

# --- Predefined Notification Templates ---

def notify_admin_download(user, ip, location, file_info, admin_emails):
    """Notify admins about file download."""
    subject = f"⚠️ Alerta de Segurança: Download Realizado por {user}"
    content = f"""
    <p>Um download ou visualização de arquivo sensível foi registrado no sistema.</p>
    
    <div class="alert-box">
        <p><span class="label">Usuário:</span> <span class="highlight">{user}</span></p>
        <p><span class="label">Arquivo/Ação:</span> {file_info}</p>
        <p><span class="label">Data/Hora:</span> {location['time']}</p>
        <p><span class="label">Endereço IP:</span> {ip}</p>
        <p><span class="label">Localização Estimada:</span> {location['city']} - {location['region']}</p>
    </div>
    
    <p style="font-size: 0.9em; color: #666;">Por favor, verifique se esta atividade é reconhecida.</p>
    """
    body = _get_email_template("Alerta de Segurança", content)
    
    for email in admin_emails:
        send_email_async(email, subject, body)

def notify_user_created(user_email, username, password):
    """Notify new user with credentials."""
    subject = "Bem-vindo ao Sistema ONR"
    content = f"""
    <p>Olá,</p>
    <p>Sua conta de acesso ao <strong>Sistema Indicador Real (ONR)</strong> foi criada com sucesso.</p>
    
    <div class="alert-box">
        <p><span class="label">Usuário:</span> <span class="highlight">{username}</span></p>
        <p><span class="label">Senha Temporária:</span> <span class="highlight">{password}</span></p>
    </div>
    
    <p>Recomendamos que você altere sua senha imediatamente após o primeiro login.</p>
    <p style="text-align: center; margin-top: 30px;">
        <a href="https://webonr.feitosasolucoes.com.br/" style="background-color: #0d6efd; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Acessar Sistema</a>
    </p>
    """
    body = _get_email_template("Bem-vindo(a)!", content)
    send_email_async(user_email, subject, body)

def notify_reset_password(user_email, new_password):
    """Send temporary password to user."""
    subject = "Redefinição de Senha - Sistema ONR"
    content = f"""
    <p>Recebemos uma solicitação para redefinir sua senha.</p>
    
    <div class="alert-box">
        <p><span class="label">Nova Senha Temporária:</span></p>
        <p style="font-size: 24px; letter-spacing: 2px; text-align: center;" class="highlight">{new_password}</p>
    </div>
    
    <p>Use esta senha para entrar no sistema. Você será solicitado a criar uma nova senha pessoal.</p>
    <p>Se você não solicitou esta alteração, entre em contato com o suporte imediatamente.</p>
    """
    body = _get_email_template("Senha Redefinida", content)
    send_email_async(user_email, subject, body)

def notify_backup_status(status, details, supervisor_emails):
    """Notify supervisors about backup status."""
    status_text = "Sucesso" if status else "Falha"
    subject = f"Relatório de Backup: {status_text}"
    
    color_class = "success" if status else "warning"
    icon = "✅" if status else "❌"
    
    content = f"""
    <p>O processo de backup automático do banco de dados foi finalizado.</p>
    
    <div class="alert-box" style="border-color: {'#198754' if status else '#dc3545'};">
        <h3 class="{color_class}">{icon} Status: {status_text}</h3>
        <p>{details}</p>
    </div>
    
    <p>Este arquivo pode ser usado para restaurar o sistema em caso de falhas.</p>
    """
    body = _get_email_template(f"Backup - {status_text}", content)
    
    for email in supervisor_emails:
        send_email_async(email, subject, body)

def notify_admin_new_user(admin_emails, new_username, created_by):
    """Notify admins about a new user creation."""
    subject = f"🔔 Novo Usuário Criado: {new_username}"
    content = f"""
    <p>Um novo usuário foi cadastrado no sistema.</p>
    
    <div class="alert-box">
        <p><span class="label">Usuário Criado:</span> <span class="highlight">{new_username}</span></p>
        <p><span class="label">Criado por:</span> {created_by}</p>
        <p><span class="label">Data:</span> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
    </div>
    """
    body = _get_email_template("Novo Registro de Usuário", content)
    
    for email in admin_emails:
        send_email_async(email, subject, body)
