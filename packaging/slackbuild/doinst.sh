#! /bin/sh
 
# Create crontab entry
cat > sendmailanalyzer.cron << _EOF_
#
# SendmailAnalyzer log reporting daily cache
#0 1 * * * /usr/bin/sa_cache > /dev/null 2>&1
# Daemon restart after maillog logrotate (cron jobs at 4:41 every day)
# Feel free to replace this line by an entry in /etc/logrotate.d/syslog
#41 4 * * * /etc/rc.d/rc.sendmailanalyzer restart >/dev/null 2>&1
# On huge MTA you may want to have five minutes caching
#*/5 * * * * /usr/bin/sa_cache -a > /dev/null 2>&1

_EOF_

# Create default httpd configuration
cat > httpd-sendmailanalyzer.conf << _EOF_
#
# By default SendmailAnalyzer statistics are only accessible from localhost.
#
Alias /sareport /var/www/sendmailanalyzer

<Directory /var/www/sendmailanalyzer>
    Options ExecCGI
    AddHandler cgi-script .cgi
    DirectoryIndex sa_report.cgi
    Order deny,allow
    Deny from all
    Allow from 127.0.0.1
    Allow from ::1
    # Allow from .example.com
</Directory>

_EOF_

# Append crontab entry to root user
cat sendmailanalyzer.cron >> /var/spool/cron/crontabs/root
rm -f sendmailanalyzer.cron
# Append Apache configuration
install -D -m 0644 httpd-sendmailanalyzer.conf /etc/httpd/extra/httpd-sendmailanalyzer.conf
rm -f httpd-sendmailanalyzer.conf

cat >> /etc/httpd/httpd.conf << _EOF_

# Uncomment the following line to limit access to SysUsage statistics
#
#Include /etc/httpd/extra/httpd-sendmailanalyzer.conf

_EOF_


