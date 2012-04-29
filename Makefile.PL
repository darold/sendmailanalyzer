use ExtUtils::MakeMaker qw(prompt WriteMakefile);

my @ALLOWED_ARGS = ('LOGFILE','BINDIR','CONFDIR','PIDDIR','BASEDIR','HTMLDIR','MANDIR','DOCDIR','DESTDIR','QUIET','INSTALLDIRS');

# Parse command line arguments and store them as environment variables
while ($_ = shift) {
	my ($k,$v) = split(/=/, $_, 2);
	if (grep(/^$k$/, @ALLOWED_ARGS)) {
		$ENV{$k} = $v;
	}
}
$ENV{DESTDIR} =~ s/\/$//;

# Default install path
my $LOGFILE = $ENV{LOGFILE} || '/var/log/maillog';
my $BINDIR = $ENV{BINDIR} || '/usr/local/sendmailanalyzer';
my $CONFDIR = $ENV{CONFDIR} || '/usr/local/sendmailanalyzer';
my $PIDDIR = $ENV{PIDDIR} || '/var/run';
my $BASEDIR = $ENV{BASEDIR} || '/usr/local/sendmailanalyzer/data';
my $HTMLDIR = $ENV{HTMLDIR} || '/usr/local/sendmailanalyzer/www';
my $MANDIR = $ENV{MANDIR} || '/usr/local/sendmailanalyzer/doc';
my $DOCDIR = $ENV{DOCDIR} || '/usr/local/sendmailanalyzer/doc';
my $DESTDIR = $ENV{DESTDIR} || '';
$ENV{INSTALLDIRS} ||= 'vendor';

# Try to find all binary used by SysUsage
my $tail = `which tail`;
chomp($tail);
if (!$tail) {
	die "NOTICE: This tool requires system command: tail, can't find it in your path\n";
}
my $grep = `which grep`;
chomp($grep);
if (!$grep) {
	die "NOTICE: This tool requires the sysstat package, can't find grep in your path\n";
}
my $zcat = `which zcat`;
chomp($zcat);



# Setup ok. generating sendmailanalyzer.conf config file
unless(open(OUTCFG, ">sendmailanalyzer.conf")) {
	print "\nError: can't write config file sendmailanalyzer.conf, $!\n";
	exit 0;
}

	print OUTCFG qq{
# Path to the maillog file to analyse.
# Can be overwritten with --log or -l
LOG_FILE	$LOGFILE

# Path to store the pid file (sendmailanalyzer.pid).
PID_FILE	$PIDDIR

# Path to the system tail command.
# Can be overwritten with --tail or -t
TAIL_PROG	$tail

# tail system command argument to pass.
# Can be overwritten with --args or -a
TAIL_ARGS	-n 0 -F

# zcat system command used to parse compressed log file
ZCAT_PROG	$zcat

# Output directory for data storage.
# Can be overwritten with --output or -o
OUT_DIR		$BASEDIR

# Turn on/off debug mode.
# Can be overwritten with --debug or -d
DEBUG		0

# Parse maillog from begining before running tail program.
# Can be overwritten with --full or -f
FULL		0

# Do not run tail program and exit after a full parsing of the log file
# Can be overwritten with --break or -b
BREAK		0

# Delay in second to flush to disk collected data.
# Can be overwritten with --write-delay or -w
DELAY		5

# Syslog name of the MTA. Syslog write it to maillog with the pid as follow:
# ... sendmail[1234] ... This is required to only parse relevant logged lines
# Can be overwritten with --sendmail or -s
# You can set multiple Syslog name as a list separated by a pipe '|'
MTA_NAME	sm-mta|sendmail|postfix

# Syslog name of MailScanner. Syslog write it to maillog with the pid as follow:
# ... MailScanner[1234] ... This is required to only parse relevant logged lines
# Can be overwritten with --mailscanner or -m
MAILSCAN_NAME	MailScanner

# Number of object displayed in the top statistics
TOP		25

# Number of object displayed in the top mailbox statistics
TOP_MBOX	25

# Space separated list of DNS name of the mail hubs (where email are redirected
# if this host is a gateway or a hub)
MAIL_HUB

# Space separated list of DNS name of the MTA gateway (where external mail
# comes from if this host is a hub or a delivery system)
MAIL_GW

# Default domain or hostname to add to an email address if there's just the
# username. When the host is a delivery system it is possible that the user
# email address do not have the domain part (ex: \@domain.com). By default
# SendmailAnalyzer will add the '\@localhost' domain but you may want to change
# this domain, so use this directive
DEFAULT_DOMAIN	\@localhost

# Max number of recipient per message to report sender
MAX_RCPT	25

# Max size per message to report sender in byte
MAX_SIZE	10000000

# Select the freeing space method:
# - delete: remove all daily data files before the current month
# - archive: make a gzipped tarbal of all data files before the current month
# - none: don't do anything. Need lot of space disk.
# Default is delete.
FREE_SPACE	archive

# Compute statistics and cache for a list of domain and display a link in the
# front page for a per domain access. See DOMAIN_USER if you want to grant
# special access on these pages. You can have multiple DOMAIN_REPORT lines
# for better reading.
# If you are running rsyslog with multiple host use DOMAIN_HOST_REPORT instead.
# See DOMAIN_USER if you want to grant special access on these pages.
#DOMAIN_REPORT	domain1.com,domain2.com

# Same as above but with host distinction for use with rsyslog.
# You can have multiple LOCAL_HOST_DOMAIN lines, ie: one per host.
#DOMAIN_HOST_REPORT	sysloghost1	domain1.com,domain2.com
#DOMAIN_HOST_REPORT	sysloghost2	domain3.com,domain4.com

# Path to the language translation file (relative to the CGI directory).
# Default: lang/en_US
#LANG	lang/fr_FR

# Size Unit to use, default is Bytes. Other values are KBytes and MBytes
SIZE_UNIT	MBytes

# Max line to show in detail view. Default is 100
MAX_LINE	100

# List of admin users separated by coma
# They will have full access to all report
#ADMIN   sa_admin

#List of per user domain access control. The first field is the username and
#the second field (separated by tabulation) is a coma separated list of domain
#name to be allowed to this user. You could add as many lines of DOMAIN_USER
#as you want in the configuration file.
#DOMAIN_USER	user1	domain1.com,domain3.com
#DOMAIN_USER	user2	domain2.com,...

# Path to the Sendmail.org logo
URL_LOGO	salogo.png

# Syslog name of Amavis. Syslog write it to maillog with the pid as follow:
# ... amavis[1234] ... This is required to only parse relevant logged lines
AMAVIS_NAME	amavis

# Path to SMTP error code file (relative to the CGI directory)
# Default: lang/ERROR_CODE
ERROR_CODE	lang/ERROR_CODE

# Coma separated list of internal domain to be used when sendmailanalyzer is
# running on a mail host which received message from any side. SA can't know
# what message are internal or external in this case, so the only way to know
# if a mail come from Internet or Lan/Wan is to check the domain part of the
# relay sender address. You can have multiple LOCAL_DOMAIN lines for better
# reading.
# If you are running rsyslog with multiple host use LOCAL_HOST_DOMAIN instead.
#LOCAL_DOMAIN   domain1.com domain2.com

# Same as above but with host distinction for use with rsyslog.
# You can have multiple LOCAL_HOST_DOMAIN lines, ie: one per host.
#LOCAL_HOST_DOMAIN   sysloghost1	domain1.com domain2.com

# Syslog name of MimeDefang. Syslog write it to maillog with the pid as follow:
# ... mimedefang.pl[1234] ... This is required to only parse relevant logged lines
# Based on parsing mimedefang log generated by method md_graphdefang_log()
MD_NAME		mimedefang.pl

# Anonymize reports. This remove sender and recipient adresses from reports.
ANONYMIZE	0

# Replace some hostname in all relay information for anonymization
# You must used one REPLACE_HOST line per replacement.
REPLACE_HOST	internal.relay.dom	external.relay.dom

# Make report for Spam detail. Default is enable. This allow you to see score
# and complete detail of your favorite antispam.
SPAM_DETAIL	1

# Enable/Disable SMTP Auth view. Note that it is already disable in per domain
# views. Default show it: 1
SMTP_AUTH	1

# Enable/Disable Spam views. Default show it: 1
SPAM_VIEW	1

# Enable/Disable Virus views. Default show it: 1
VIRUS_VIEW	1

# Enable/Disable Notification views. Default show it: 1
DSN_VIEW	1

# Enable/Disable Postgrey usage views. Default show it: 1
POSTGREY_VIEW   1

# List of antispam name separated by a comma used for Spam details view. You may
# want to custom this list to just show menu link on available reports. Default
# list is: spamdmilter,jchkmail,dnsbl,spamassassin,amavis,mimedefang,dnsblmilter
SPAM_TOOLS	spamdmilter,jchkmail,dnsbl,spamassassin,amavis,mimedefang,dnsblmilter

# Enable/Disable messaging/spam/virus/dsn direction statistics. Default is show.
# On some mailhost this could show wrong information if the direction could
# not be easily determined. So you can remove these views by setting it to 0.
SHOW_DIRECTION	1

# Use to combined mailhost report on a single report. This allow you to
# aggregate multiple mailhost that syslogs to a remote server throught
# rsyslog to have only one SendmailAnalyzer report. The value must only use
# alphanumeric character as it is used to create subdirectory.
#MERGING_HOST	agghostname

# Syslog name of Clamd. When using Mailscanner with clamd if you want virus
# report you must configure clamd to log with syslog and use LOCAL_MAIL.
# ... clamd[1234] ...
# Can be overwritten with --clamd or -n
CLAMD_NAME	clamd

# Syslog name of Postgrey. Syslog write it to maillog with the pid as follow:
# ... postgrey[1234] ... This is required to only parse relevant logged lines
# Can be overwritten with --postgrey or -g
POSTGREY_NAME	postgrey

};
close(OUTCFG);

unless(open(INST, ">install_all.sh")) {
	print "\nError: can't write post install file install_all.sh, $!\n";
	exit 0;
}
print INST qq{#!/bin/sh
if [ ! -d "$DESTDIR$BINDIR" ]; then
	mkdir -p $DESTDIR$BINDIR
fi
if [ ! -d "$DESTDIR$CONFDIR" ]; then
	mkdir -p $DESTDIR$CONFDIR
fi
if [ ! -d "$DESTDIR$HTMLDIR" ]; then
	mkdir -p $DESTDIR$HTMLDIR/lang
fi
if [ ! -d "$DESTDIR$BASEDIR" ]; then
	mkdir -p $DESTDIR$BASEDIR
fi
if [ ! -d "$DESTDIR$MANDIR" ]; then
	mkdir -p $DESTDIR$MANDIR
fi
if [ ! -d "$DESTDIR$DOCDIR" ]; then
	mkdir -p $DESTDIR$DOCDIR
fi
if [ ! -d "$DESTDIR$PIDDIR" ]; then
	mkdir -p $DESTDIR$PIDDIR
fi

if [ -e $DESTDIR$CONFDIR/sendmailanalyzer.conf ]; then
	echo "File sendmailanalyzer.conf already exists. Rename it into sendmailanalyzer.conf.old"
	mv $DESTDIR$CONFDIR/sendmailanalyzer.conf $DESTDIR$CONFDIR/sendmailanalyzer.conf.old
fi
install -m 644 sendmailanalyzer.conf $DESTDIR$CONFDIR/
install -m 755 sendmailanalyzer $DESTDIR$BINDIR/
install -m 755 sa_cache $DESTDIR$BINDIR/
install -m 755 cgi-bin/sa_report.cgi $DESTDIR$HTMLDIR/
install -m 755 cgi-bin/grafit.cgi $DESTDIR$HTMLDIR/
install -m 644 cgi-bin/lang/* $DESTDIR$HTMLDIR/lang/
install -m 644 salogo.png $DESTDIR$HTMLDIR/
pod2man doc/sendmailanalyzer.pod doc/sendmailanalyzer.3
install -m 644 doc/sendmailanalyzer.3 $DESTDIR$MANDIR/
install -m 644 README $DESTDIR$DOCDIR/
install -m 644 INSTALL $DESTDIR$DOCDIR/
install -m 644 ChangeLog $DESTDIR$DOCDIR/

};
if (!$ENV{QUIET}) {
	print INST qq{
echo "
-----------------------------------------------------------------------------

1. Start SendmailAnalyzer daemon with: 

	$BINDIR/sendmailanalyzer -f

   or use one of the starters script provided in the start_scripts/ directory.

2. Modify your httpd.conf to allow access to CGI scripts like follow:

	Alias /sareport $HTMLDIR

	<Directory $HTMLDIR>
	    Options ExecCGI
	    AddHandler cgi-script .cgi
	    DirectoryIndex sa_report.cgi
	    Order deny,allow
	    Deny from all
	    Allow from 127.0.0.1
	    Allow from ::1
	    # Allow from .example.com
	</Directory>

3. If necessary, give additional hosT access to SendmailAnalyzer in httpd.conf.
   Restart and ensure that httpd is running.

4. Browse to http://mta.host.dom/sareport/ to ensure that things are working
   properly.

5. Setup a cronjob to run sa_cache and restart SendmailAnalyzer daemon after
   maillog logrotate as follow:

     # SendmailAnalyzer log reporting daily cache
     0 1 * * * $BINDIR/sa_cache > /dev/null 2>&1
     # On huge MTA you may want to have five minutes caching
     #*/5 * * * * $BINDIR/sa_cache -a > /dev/null 2>&1

6. Add an entry in /etc/logrotate.d/syslog to restart SendmailAnalyzer when
   maillog is rotated or create a cron job.

For more information, see $DOCDIR/README file.

-----------------------------------------------------------------------------
" | more
};
}
close(INST);
`chmod 755 install_all.sh`;

`perl -p -i -e 's#my \\\$CONFIG_FILE .*#my \\\$CONFIG_FILE = "$CONFDIR/sendmailanalyzer.conf";#' sendmailanalyzer sa_cache`;
`perl -p -i -e 's#my \\\$CONFIG_FILE .*#my \\\$CONFIG_FILE = "$CONFDIR/sendmailanalyzer.conf";#' cgi-bin/*.cgi`;

`perl -p -i -e 's#SALYZER=.*#SALYZER=$BINDIR/sendmailanalyzer#' start_scripts/*`;
`perl -p -i -e 's#PIDFILE=.*#PIDFILE=$PIDDIR/sendmailanalyzer.pid#' start_scripts/*`;

WriteMakefile(
    'NAME'         => 'sendmailanalyzer',
    'VERSION_FROM' => 'sendmailanalyzer',
    'dist'         => {
			'COMPRESS'=>'gzip -9f', 'SUFFIX' => 'gz',
			'ZIP'=>'/usr/bin/zip','ZIPFLAGS'=>'-rl'
		      },
    'AUTHOR'       => 'Gilles Darold (gilles@darold.net)',
    'ABSTRACT'     => 'Sendmail log analyzer',
    'DESTDIR'      => $ENV{DESTDIR},
    'INSTALLDIRS'  => $ENV{INSTALLDIRS},
    'clean'        => {FILES => "install_all.sh sendmailanalyzer.conf"}
);

sub MY::install {
	my $self = shift;

	my $string = $self->MM::install;
	$string =~ s/(pure_install\s+)(.*)/$1 install_all $2/;

	return $string;
}

sub MY::postamble {
	my $postamble = <<'END';
install_all: install_all.sh
	sh install_all.sh
END
	return $postamble;
}

if (!$ENV{QUIET}) {
	print "Done...\n\n";
	print "Now type 'make && make install'\n\n";
}
