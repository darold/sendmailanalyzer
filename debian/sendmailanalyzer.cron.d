# SendmailAnalyzer log reporting daily cache
0 1 * * * /usr/bin/sa_cache > /dev/null 2>&1
# Daemon restart after mail.log logrotate (cron jobs at 6:25 every day)
26 6 * * * /etc/init.d/sendmailanalyzer restart >/dev/null 2>&1
# On huge MTA you may want to have five minutes caching
*/5 * * * * /usr/bin/sa_cache -a > /dev/null 2>&1
