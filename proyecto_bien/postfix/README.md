# Postfix local

El login no usa Google ni Outlook: entrega el mensaje a `SMTP_HOST:SMTP_PORT`, que por defecto es `127.0.0.1:25`. Esta carpeta documenta la instancia propia que debe ejecutarse en Linux, una VM o un contenedor Docker porque Postfix no es un servicio nativo de Windows.

En el servidor de correo configura un dominio que controles, por ejemplo `mail.midominio.edu`, y una cuenta `info@mail.midominio.edu`. Los valores minimos de `/etc/postfix/main.cf` son:

```ini
myhostname = mail.midominio.edu
myorigin = $myhostname
mydestination = $myhostname, localhost.$mydomain, localhost
inet_interfaces = all
inet_protocols = ipv4
```

Para entrega directa agrega un registro DNS `A` para `mail.midominio.edu`, un `MX` para el dominio, SPF, DKIM y DMARC. No abras un relay abierto: permite solo las redes internas del proyecto en `mynetworks` y usa `smtpd_recipient_restrictions` con `reject_unauth_destination`.

En `.env` del proyecto usa la cuenta de la instancia:

```env
SMTP_HOST=127.0.0.1
SMTP_PORT=25
SMTP_FROM=info@mail.midominio.edu
SMTP_STARTTLS=false
```

Comprueba conectividad con `Test-NetConnection 127.0.0.1 -Port 25` desde Windows. Luego registra una cuenta con un correo real y confirma que el mensaje aparece en los logs de Postfix y en el buzón de destino. Para desarrollo local puede mantenerse `info@localhost`, pero ese remitente no garantiza entrega fuera de la red local.