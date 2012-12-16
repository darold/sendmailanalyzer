#!/usr/bin/perl
#
#    SendmailAnalyzer: maillog parser and statistics reports tool for Sendmail
#    Copyright (C) 2002-2012 Gilles Darold
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
use vars qw($SOFTWARE $VERSION $AUTHOR $COPYRIGHT);
use strict;
no strict qw/refs/;

use CGI qw(:all);
use Benchmark;
use MIME::QuotedPrint qw(decode_qp);
use MIME::Base64 qw(decode_base64);
use Time::Local 'timelocal_nocheck';

$| = 1;

# Configuration storage hash
my %CONFIG = ();
# Other configuration directives
my $CONFIG_FILE = "/usr/local/sendmailanalyzer/sendmailanalyzer.conf";
my $LAST_PARSE_FILE = 'LAST_PARSED';

$SOFTWARE  = "SendmailAnalyzer";
$VERSION   = '8.5';
$AUTHOR    = "Gilles Darold <gilles\@darold.net>";
$COPYRIGHT = "&copy; 2002-2012 - Gilles Darold <gilles\@darold.net>";

our %TRANSLATE = ();
our %SMTP_ERROR_CODE = ();
our %ESMTP_ERROR_CODE = ();
our %ANTISPAM_NAME = (
	'spamdmilter' => 'Spamd-Milter',
	'jchkmail' => 'J-ChkMail',
	'dnsbl' => 'RBL Check',
	'spamassassin' => 'SpamAssassin',
	'amavis' => 'Amavis',
	'mimedefang' => 'MIMEDefang',
	'dnsblmilter' => 'DNSBL-Milter',
	'spamd' => 'Spamd',
);

my $CGI = new CGI;

my $HOST = $CGI->param('host') || '';
my $CURDATE = $CGI->param('date') || '';
my $DOMAIN = $CGI->param('domain') || '';
my $TYPE = $CGI->param('type') || '';
my $PERI = $CGI->param('peri') || '';
my $SEARCH = $CGI->param('search') || '';
my $HOUR = $CGI->param('hour') || '';
my $VIEW = $CGI->param('view') || '';
my $LANG = $CGI->param('lang') || '';

my $MAXPIECOUNT = 10;
my $DEFAULT_CHARSET='iso-8859-1';

# Read configuration file
&read_config($CONFIG_FILE);

# Write sendmailanalyzer header
$CGI->charset($CONFIG{HTML_CHARSET} || $DEFAULT_CHARSET);
print $CGI->header();
print $CGI->start_html(-title=>"sendmailanalyzer v$VERSION");
	
	print qq{
<style type="text/css">
<!--/* <![CDATA[ */
body {font-family:sans-serif;font-size:10pt;color:#000000;background-color:#f0f0f0;}
select { font-size:8pt; height: 15px; color: #4179a1; border:1px solid #f0f0f0;}
#report {font-family:sans-serif;font-size:12pt;color:#4179a1;}
#report table{border-collapse:collapse;}
#report a { border-style: none; text-decoration: none; }
#report a:active { color: #4179a1; }
#report a:visited { color: #4179a1; }
#report a:link { color: #4179a1; }
#report a:hover { color: #ffffff; background-color: #CC6600; }
td {padding:0px;font-family:sans-serif;font-size:8pt;color:#000000;background-color:#f0f0f0;}
.tdtop {padding:2px;font-family:sans-serif;font-size:8pt; font-weight: bold; color:#4179a1;background-color:#ffffff; border: 1px solid #4179a1;}
.tdtopn {padding:2px;font-family:sans-serif;font-size:8pt; font-weight: normal; color:#4179a1;background-color:#ffffff; border: 1px solid #4179a1; text-align: left;}
.tdtopnr {padding:2px;font-family:sans-serif;font-size:8pt; font-weight: normal; color:#4179a1;background-color:#ffffff; border: 1px solid #4179a1; text-align: right;}
.tdtopnc {padding:2px;font-family:sans-serif;font-size:8pt; font-weight: normal; color:#4179a1;background-color:#ffffff; border: 1px solid #4179a1; text-align: center;}
th {padding:0px;font-family:sans-serif;font-size:8pt;color:#ffffff;background-color:#4179a1; border: solid thin #4179a1;}
.thhead2 {padding:0px;font-family:sans-serif;font-size:12pt;color:#CC6600;background-color:#ffffff; border: solid thin #4179a1; text-align: center;}
.thhead {padding:0px;font-family:sans-serif;font-size:10pt;color:#ffffff;background-color:#4179a1; border: solid thin #4179a1; text-align: center;}
.tdhead {padding:0px;font-family:sans-serif;font-size:8pt; font-weight: bold;color:#CC6600;background-color:#ffffff; border: solid thin #4179a1; text-align: center;}
.title {font-family:sans-serif;font-weight:bold;font-size:20pt;color:#CC6600;}
.usertitle {font-family:sans-serif;font-size:14pt;color:#ffffff;}
.calborder {padding: 0px; border: solid thin #4179a1; background-color:#dddddd;}
.smalltitle {font-family:sans-serif;font-size:14pt;color:#CC6600;}
.subtitle {font-family:sans-serif;font-size:12pt;color:#4179a1;}
.small {font-family:sans-serif;font-size:8pt;color:#000000;}
pre {font-family:sans-serif;font-size:9pt;color:#ffffff;background-color:#4179a1;}
pre a { border-style: none; text-decoration: none; }
pre a:active { color: #ffffff; }
pre a:visited { color: #ffffff; }
pre a:link { color: #ffffff; }
pre a:hover { color: #ffffff; background-color: #CC6600; }
.error {font-family:sans-serif;font-size:10pt;color:#FF0000;}
#info {border: none; width: 100%; height: 600px;}
#menu {font-family:sans-serif;font-size:10pt;color: #ffffff; background-color: #4179a1;}
#menu th {margin-right: 100px}
#menu a { border-style: none; text-decoration: none; }
#menu a:active { color: #ffffff; }
#menu a:visited { color: #ffffff; }
#menu a:link { color: #ffffff; }
#menu a:hover { color: #ffffff; background-color: #CC6600; }
#listhost {font-family:sans-serif;font-size:12pt;color:#4179a1;}
#listhost a { border-style: none; text-decoration: none; }
#listhost a:active { color: #4179a1; }
#listhost a:visited { color: #4179a1; }
#listhost a:link { color: #4179a1; }
#listhost a:hover { color: #ffffff; background-color: #CC6600; }
#temporal {font-family:sans-serif;font-size:12pt;color:#4179a1;}
#temporal a { border-style: none; text-decoration: none; background-color:#dddddd;}
#temporal a:active { color: #4179a1; background-color:#dddddd;}
#temporal a:visited { color: #4179a1; background-color:#dddddd;}
#temporal a:link { color: #4179a1; background-color:#dddddd;}
#temporal a:hover { color: #ffffff; background-color: #CC6600; }
#temporal td {padding:0px;font-family:sans-serif;font-size:8pt;color:#000000;background-color:#dddddd;}
a { border-style: none; text-decoration: none; font-family:sans-serif;color:#4179a1;}
a:active { color: #4179a1; }
a:visited { color: #4179a1; }
a:link { color: #4179a1; }
a:hover { color: #ffffff; background-color: #CC6600; }
/* ]]> */-->
</style>
};
# CSS style used in temporal menu for the current hour/day/month
my $SELCURRENT = ' style="color: #4179a1; font-weight: bold;"';

if (my $ret = &secure_params()) {
	&logerror("Bad CGI param, hacking attempt: $ret");
	print $CGI->end_html();
	die "FATAL: Bad CGI param, hacking attempt: $ret\n";
}

# Check if output dir exist
if (!-d $CONFIG{OUT_DIR}) {
	die "FATAL: Output directory $CONFIG{OUT_DIR} should exists !\n";
}

# Check dynamic change of language
if ($LANG) {
	$CONFIG{LANG} =~ s/\/[^\/]+$/\/$LANG/;
	if (!-e $CONFIG{LANG}) {
		# Falling back to default
		$CONFIG{LANG} =~ s/\/[^\/]+$/\/en_US/;
	}
}
# Check if lang file is readable
if (!-e $CONFIG{LANG}) {
	&logerror("Language file $CONFIG{LANG} doesn't exist!");
	print $CGI->end_html();
	die "FATAL: Language file is not readable, $CONFIG{LANG}\n";
} else {
	do "$CONFIG{LANG}";
}
$CURDATE ||= &get_curdate();

# Check if smtp error code file is readable
if (-e $CONFIG{ERROR_CODE}) {
        do "$CONFIG{ERROR_CODE}";
}

# Print global header
&sa_header($CGI) if (!$VIEW);

# Set default host report if there's only one host and no per domain report.
my @syshost = get_list_host();
if ( !$HOST && ($#syshost == 0) && ($#{$CONFIG{DOMAIN_REPORT}} == -1) && (scalar keys %{$CONFIG{DOMAIN_HOST_REPORT}} == 0) ) {
	$HOST = $syshost[0];
}

# Choose the interface to display
if (!$HOST) {
	# List available statistics
	&show_list_host(@syshost) if (&check_auth);
} elsif ($TYPE && $PERI) {
	# Show details
	&show_detail($HOST, $CURDATE, $HOUR, $TYPE, $PERI, $SEARCH) if (&check_auth);
} elsif (!$VIEW) {
	print "<table id=\"menu\" width=\"100%\"><tr><td colspan=\"2\">\n";
	&show_temporal_menu($HOST, $CURDATE, $HOUR, $DOMAIN);
	my $iframe_param = "view=empty&host=$HOST&date=$CURDATE&lang=$LANG&domain=$DOMAIN";
	if ($CGI->param('update') ne '') {
		foreach my $p ($CGI->param()) {
			next if ( ($p eq 'update') || ($p eq 'view') );
			$iframe_param .= "&$p=" . $CGI->param($p);
		}
		$iframe_param = "view=" . $CGI->param('update') . "&" . $iframe_param;
	}
	print qq{
</td></tr>
<tr><th height="600px" align="left" valign="top" nowrap="1" style="padding: 10px">
<br>
<a href="$ENV{SCRIPT_NAME}?view=empty&host=$HOST&date=$CURDATE&lang=$LANG&domain=$DOMAIN" target="info">$TRANSLATE{'Global Statistics'}</a>
<ul>
<li><a href="$ENV{SCRIPT_NAME}?view=messageflow&host=$HOST&date=$CURDATE&lang=$LANG&domain=$DOMAIN&hour=$HOUR" target="info">$TRANSLATE{'Messaging'}</a></li>};
	if ($CONFIG{SPAM_VIEW}) {
		print qq{<li><a href="$ENV{SCRIPT_NAME}?view=spamflow&host=$HOST&date=$CURDATE&lang=$LANG&domain=$DOMAIN&hour=$HOUR" target="info">$TRANSLATE{'Spamming'}</a></li>};
	}
	if ($CONFIG{VIRUS_VIEW}) {
		print qq{<li><a href="$ENV{SCRIPT_NAME}?view=virusflow&host=$HOST&date=$CURDATE&lang=$LANG&domain=$DOMAIN&hour=$HOUR" target="info">$TRANSLATE{'Virus Detection'}</a></li>};
	}
	if ($CONFIG{DSN_VIEW}) {
		print qq{<li><a href="$ENV{SCRIPT_NAME}?view=dsnflow&host=$HOST&date=$CURDATE&lang=$LANG&domain=$DOMAIN&hour=$HOUR" target="info">$TRANSLATE{'Delivery Status Notification'}</a></li>};
	}
	print qq{
<li><a href="$ENV{SCRIPT_NAME}?view=rejectflow&host=$HOST&date=$CURDATE&lang=$LANG&domain=$DOMAIN&hour=$HOUR" target="info">$TRANSLATE{'Rejection SysErr'}</a></li>
<li><a href="$ENV{SCRIPT_NAME}?view=statusflow&host=$HOST&date=$CURDATE&lang=$LANG&domain=$DOMAIN&hour=$HOUR" target="info">$TRANSLATE{'Status'}</a></li>
};
	# SMTP Auth can not be shown by domain
	if (!$DOMAIN && $CONFIG{SMTP_AUTH}) {
		print qq{
<li><a href="$ENV{SCRIPT_NAME}?view=authflow&host=$HOST&date=$CURDATE&lang=$LANG&domain=$DOMAIN&hour=$HOUR" target="info">$TRANSLATE{'SMTP Auth'}</a></li>
};
	}
	print qq{
</ul>
<a href="$ENV{SCRIPT_NAME}?view=empty&host=$HOST&date=$CURDATE&lang=$LANG&domain=$DOMAIN" target="info">$TRANSLATE{'Top Statistics'}</a>
<ul>
<li><a href="$ENV{SCRIPT_NAME}?view=topsender&host=$HOST&date=$CURDATE&lang=$LANG&domain=$DOMAIN&hour=$HOUR" target="info">$TRANSLATE{'Senders'}</a></li>
<li><a href="$ENV{SCRIPT_NAME}?view=toprecipient&host=$HOST&date=$CURDATE&lang=$LANG&domain=$DOMAIN&hour=$HOUR" target="info">$TRANSLATE{'Recipients'}</a></li>};
	if ($CONFIG{SPAM_VIEW}) {
		print qq{<li><a href="$ENV{SCRIPT_NAME}?view=topspam&host=$HOST&date=$CURDATE&lang=$LANG&domain=$DOMAIN&hour=$HOUR" target="info">$TRANSLATE{'Spamming'}</a></li>};
	}
	if ($CONFIG{VIRUS_VIEW}) {
		print qq{<li><a href="$ENV{SCRIPT_NAME}?view=topvirus&host=$HOST&date=$CURDATE&lang=$LANG&domain=$DOMAIN&hour=$HOUR" target="info">$TRANSLATE{'Virus Detection'}</a></li>};
	}
	if ($CONFIG{DSN_VIEW}) {
		print qq{<li><a href="$ENV{SCRIPT_NAME}?view=topdsn&host=$HOST&date=$CURDATE&lang=$LANG&domain=$DOMAIN&hour=$HOUR" target="info">$TRANSLATE{'Delivery Status Notification'}</a></li>};
	}
	print qq{
<li><a href="$ENV{SCRIPT_NAME}?view=topreject&host=$HOST&date=$CURDATE&lang=$LANG&domain=$DOMAIN&hour=$HOUR" target="info">$TRANSLATE{'Rejection SysErr'}</a></li>
};
if ($CURDATE !~ /00$/) {
	print qq{<li><a href="$ENV{SCRIPT_NAME}?view=toplimit&host=$HOST&date=$CURDATE&lang=$LANG&domain=$DOMAIN&hour=$HOUR" target="info">$TRANSLATE{'Limits'}</a></li>};
}
# SMTP Auth can not be shown by domain
if (!$DOMAIN && $CONFIG{SMTP_AUTH}) {
	print qq{
<li><a href="$ENV{SCRIPT_NAME}?view=topauth&host=$HOST&date=$CURDATE&lang=$LANG&domain=$DOMAIN&hour=$HOUR" target="info">$TRANSLATE{'SMTP Auth'}</a></li>
};
}
print qq{
</ul>
};
	if ($CONFIG{SPAM_DETAIL}) {
		print qq{
<a href="$ENV{SCRIPT_NAME}?view=empty&host=$HOST&date=$CURDATE&lang=$LANG&domain=$DOMAIN" target="info">$TRANSLATE{'AntiSpam details'}</a>
<ul>
};
		for my $typ (sort keys %ANTISPAM_NAME) {
			print qq{
<li><a href="$ENV{SCRIPT_NAME}?view=$typ&host=$HOST&date=$CURDATE&lang=$LANG&domain=$DOMAIN&hour=$HOUR" target="info">$ANTISPAM_NAME{$typ}</a></li>
};
		}
		print qq{
</ul>
};
	}
	print qq{
</th><td valign="top" width="100%"><iframe id="info" name="info" src="$ENV{SCRIPT_NAME}?$iframe_param"></iframe>
</td></tr></table>
};
} elsif ($VIEW eq 'empty') {
	my $curdomain = '';
	$curdomain = " [$DOMAIN]" if ($DOMAIN);
	my $back = '';
	if ($CONFIG{ADMIN} && $ENV{REMOTE_USER} && !grep(/^$ENV{REMOTE_USER}$/, split(/[\s\t,;]+/, $CONFIG{ADMIN})) ) {
		$back = "?host=$HOST&date=$CURDATE&lang=$LANG&domain=$DOMAIN" if ($DOMAIN);
	} elsif ($LANG) {
		$back = "?lang=$LANG";
	}
	print qq{
<form name="viewname"><input type="hidden" name="view" value="empty"></form>
<table width="100%" height="550px" valign="top"><tr><td valign="center" align="center">
<font class=\"title\">\U$HOST\E$curdomain</font><br>
<a href="$ENV{SCRIPT_NAME}$back" target="_parent"><img src="$CONFIG{URL_LOGO}" border="0" title="$TRANSLATE{'Acknowledgement'}" align=\"top\"></a><br>
};
	my $last = &get_last_parse();
	$last =~ s/^(...\s+\d+\s+\d+:\d+:\d+).*/$1/;
	print "<font class=\"small\">$TRANSLATE{'Last record'}: ", 1900+(localtime(time))[5], " $last</font>\n" if ($last);
	print "</td></tr></table>\n";
} else {
	print qq{
<form name="viewname"><input type="hidden" name="view" value="$VIEW"></form>
<table id="report" width="100%" height="550px"" valign="top"><tr><td valign="center" align="center">
};
	&show_stats($HOST, $CURDATE, $HOUR, $DOMAIN, $VIEW) if (&check_auth);
	print "\n</td></tr></table>\n";
}

# Write sendmailanalyzer footer
&sa_footer($CGI) if (!$VIEW);

print $CGI->end_html();

exit 0;

#-------------------------------- ROUTINES ------------------------------------

our %GLOBAL_STATUS = ();
our %STATS = ();
our %AUTH = ();
our $SIZE_UNIT = 1;
our $UNIQID = 0;

our %topsender = ();
our %toprcpt = ();
our %topspam = ();
our %topvirus = ();
our %topreject = ();
our %toperr = ();
our %topdsn = ();
our %topmaxrcpt = ();
our %topmaxsize = ();
our %delivery = ();
our %messaging = ();
our %spam = ();
our %virus = ();
our %reject = ();
our %err = ();
our %dsn = ();
our %topspamdetail = ();
our %auth = ();
our %topauth = ();
our %toppostgrey = ();

####
# Read last parsed line from file
####
sub get_last_parse
{
	my $last_parsed = '';

	if (-e "$CONFIG{OUT_DIR}/$LAST_PARSE_FILE") {
		if (not open(IN, "$CONFIG{OUT_DIR}/$LAST_PARSE_FILE") ) {
			&logerror("Can't read to file $CONFIG{OUT_DIR}/$LAST_PARSE_FILE: $!");
		} else {
			$last_parsed = <IN>;
			close(IN);
		}
	}
	
	return $last_parsed;
}

####
# Routine used to log sendmailanalyzer errors or send emails alert if requested
####
sub logerror
{
	my $str = shift;

	print "<p class=\"error\">ERROR: $str</p>\n";
}

####
# Read configuration file
####
sub read_config
{
	my $file = shift;

	if (!-e $file) {
		$file = '/etc/sendmailanalyzer.conf';
	}
	if (!-e $file) {
		&logerror("Configuration file $file doesn't exists");
		return;
	} else {
		if (not open(IN, $file)) {
			&logerror("Can't read configuration file $file: $!");
		} else {
			while (<IN>) {
				chomp;
				s/#.*//;
				s/^[\s\t]+//;
				s/[\s\t]$//;
				if ($_ ne '') {
					my ($var, $val) = split(/[\s\t]+/, $_, 2); 
					if ($var =~ /DOMAIN_USER/i) {
						my ($usr, @doms) = split(/[\t,;\s]/, $val);
						push(@{$CONFIG{DOMAIN_USER}{$usr}}, @doms);
					} elsif ($var =~ /DOMAIN_HOST_REPORT/i) {
						my ($hst, @doms) = split(/[\t,;\s]/, $val);
						push(@{$CONFIG{DOMAIN_HOST_REPORT}{$hst}}, @doms);
					} elsif ($var =~ /DOMAIN_REPORT/i) {
						push(@{$CONFIG{DOMAIN_REPORT}}, split(/[\t,;\s]/, $val));
					} elsif ($var =~ /LOCAL_DOMAIN/i) {
						push(@{$CONFIG{LOCAL_DOMAIN}}, split(/[\t,;\s]/, $val));
					} elsif ($var =~ /LOCAL_HOST_DOMAIN/i) {
						my ($hst, @doms) = split(/[\t,;\s]/, $val);
						push(@{$CONFIG{LOCAL_HOST_DOMAIN}{$hst}}, @doms);
					} elsif ($var =~ /REPLACE_HOST/i) {
						 my ($pat, $repl) = split(/[\t,;\s]/, $val);
						$CONFIG{REPLACE_HOST}{$pat} = $repl;
					} else {
						$CONFIG{$var} = $val if (!defined $CONFIG{$var} && ($val ne ''));
					}
				}
			}
			close(IN);
		}
	}
	# Set default values
	$CONFIG{OUT_DIR} ||= '/var/www/sendmailanalyzer';
	$CONFIG{TOP} ||= 25;
	$CONFIG{MAIL_HUB} ||= '';
	$CONFIG{MAIL_GW} ||= '';
	$CONFIG{LANG} ||= 'lang/en_US';
	# Normalyze size unit
	if ($CONFIG{SIZE_UNIT} eq 'KBytes') {
		$SIZE_UNIT = 1000;
	} elsif ($CONFIG{SIZE_UNIT} eq 'MBytes') {
		$SIZE_UNIT = 1000000;
	} else {
		$CONFIG{SIZE_UNIT} = 'KBytes';
		$SIZE_UNIT = 1;
	}
	if (!exists $CONFIG{SPAM_DETAIL}) {
		$CONFIG{SPAM_DETAIL} = 1;
	}
	if (!exists $CONFIG{SMTP_AUTH}) {
		$CONFIG{SMTP_AUTH} = 1;
	}
	if (!exists $CONFIG{SPAM_VIEW}) {
		$CONFIG{SPAM_VIEW} = 1;
	}
	if (!exists $CONFIG{VIRUS_VIEW}) {
		$CONFIG{VIRUS_VIEW} = 1;
	}
	if (!exists $CONFIG{DSN_VIEW}) {
		$CONFIG{DSN_VIEW} = 1;
	}
	if (!exists $CONFIG{SHOW_DIRECTION}) {
		$CONFIG{SHOW_DIRECTION} = 1;
	}
	if ($CONFIG{SPAM_TOOLS}) {
		my @names = split(/[,;\s\t]+/, $CONFIG{SPAM_TOOLS});
		foreach my $k (keys %ANTISPAM_NAME) {
			if (!grep(/^$k$/i, @names)) {
				delete $ANTISPAM_NAME{$k};
			}
		}
	}

}

sub sa_header
{
	my $q = shift;

	my $title = 'Sendmail Report';
	if ($CONFIG{ANONYMIZE}) {
		$title = 'Sendmail Anonymized Report';
	}
	my $back = '';
	if ($CONFIG{ADMIN} && $ENV{REMOTE_USER} && !grep(/^$ENV{REMOTE_USER}$/, split(/[\s\t,;]+/, $CONFIG{ADMIN})) ) {
		$back = "?host=$HOST&date=$CURDATE&lang=$LANG&domain=$DOMAIN" if ($DOMAIN);
	} elsif ($LANG) {
		$back = "?lang=$LANG";
	}
	print "<a href=\"$ENV{SCRIPT_NAME}$back\"><img src=\"$CONFIG{URL_LOGO}\" border=\"0\" title=\"$TRANSLATE{'Acknowledgement'}\" align=\"top\"></a>\n";
	print "<font class=\"title\" align=\"center\">$title</font>\n";
	if ($CONFIG{ADMIN} && $ENV{REMOTE_USER} && !grep(/^$ENV{REMOTE_USER}$/, split(/[\s\t,;]+/, $CONFIG{ADMIN})) && !exists($CONFIG{DOMAIN_USER}{$ENV{REMOTE_USER}}) ) {
		&logerror("Access denied for user: $ENV{REMOTE_USER}.");
		&sa_footer($q);
		exit 0;
	}
	print $q->start_form();
}

sub sa_footer
{
	my $q = shift;

	print qq{
</FORM>	
<pre>
Powered by <a href="http://sendmailanalyzer.darold.net/" target="_blank target="_blank">$SOFTWARE v$VERSION</a> (GPLv3)
$TRANSLATE{'Acknowledgement'}
</pre>
};
}


####
# Search previous record before a given date
####
sub get_previous
{
	my ($hostname, $year, $month, $day) = @_;

	if ($day ne '00') {
		$day--; 
		$day = sprintf("%02d", $day);
		while (!-d "$CONFIG{OUT_DIR}/$hostname/$year/$month/$day") {
			$day--; 
			if ($day <= 0) {
				$day = 31;
				$month--;
			}
			if ($month <= 0) {
				$month = 12;
				$year--;
			}
			$day = sprintf("%02d", $day);
			$month = sprintf("%02d", $month);
			last if (!-d "$CONFIG{OUT_DIR}/$hostname/$year/$month");
		}
		return "$year$month$day" if (-d "$CONFIG{OUT_DIR}/$hostname/$year/$month/$day");
	} elsif ($month ne '00') {
		$month--; 
		$month = sprintf("%02d", $month);
		while (!-d "$CONFIG{OUT_DIR}/$hostname/$year/$month") {
			$month--;
			if ($month <= 0) {
				$month = 12;
				$year--;
			}
			$month = sprintf("%02d", $month);
			last if (!-d "$CONFIG{OUT_DIR}/$hostname/$year");
		}
		return "$year$month" . "00" if (-d "$CONFIG{OUT_DIR}/$hostname/$year/$month");
	} else {
		$year--;
		if (-d "$CONFIG{OUT_DIR}/$hostname/$year") {
			return $year . "0000"
		}
	}

	return;
}

####
# Search next record after a given date
####
sub get_next
{
	my ($hostname, $year, $month, $day) = @_;

	if ($day ne '00') {
		$day++; 
		$day = sprintf("%02d", $day);
		while (!-d "$CONFIG{OUT_DIR}/$hostname/$year/$month/$day") {
			$day++; 
			if ($day > 31) {
				$day = 1;
				$month++;
			}
			if ($month > 12) {
				$month = 1;
				$year++;
			}
			$day = sprintf("%02d", $day);
			$month = sprintf("%02d", $month);
			last if (!-d "$CONFIG{OUT_DIR}/$hostname/$year/$month");
		}
		return "$year$month$day" if (-d "$CONFIG{OUT_DIR}/$hostname/$year/$month/$day");
	} elsif ($month ne '00') {
		$month++; 
		$month = sprintf("%02d", $month);
		while (!-d "$CONFIG{OUT_DIR}/$hostname/$year/$month") {
			$month++;
			if ($month > 12) {
				$month = 1;
				$year++;
			}
			$month = sprintf("%02d", $month);
			last if (!-d "$CONFIG{OUT_DIR}/$hostname/$year");
		}
		return "$year$month" . "00" if (-d "$CONFIG{OUT_DIR}/$hostname/$year/$month");
	} else {
		$year--;
		if (-d "$CONFIG{OUT_DIR}/$hostname/$year") {
			return $year . "0000";
		}
	}

	return;
}

####
# Display Month navigator
####
sub month_link
{
	my ($hostname, $year, $month, $domain) = @_;

	my $str = qq{
<TABLE class="calborder">
<TR><TH colspan="4" align="center">$TRANSLATE{'Month View'}</TH></TR>};
	for my $d ("01" .. "12") {
		$str .= "<TR align=center>" if (grep(/^$d$/,'01','05','09'));
		if ( !-d "$CONFIG{OUT_DIR}/$hostname/$year/$d" ) {
			$str .= "<TD>$TRANSLATE{$d}</TD>";
		} else {
			my $date = $year . $d . '00';
			my $tag = 'td';
			$tag = 'th' if ($d eq $month);
			my $type = '';
			$type = $SELCURRENT if ($d eq $month);
			$str .= "<$tag><a$type href=\"javascript:\" onclick=\"document.location.href='$ENV{SCRIPT_NAME}?host=$hostname&date=$date&domain=$domain&lang=$LANG&update='+window.frames['info'].document.forms['viewname'].elements['view'].value; return false;\">$TRANSLATE{$d}</a></$tag>";
		}
		$str .=  "</TR>\n" if ( grep(/^$d$/, '04', '08', '12') );
	}
	$str .=  "</TABLE>\n";

	return $str;
}

####
# Display Hour navigator
####
sub hour_link
{
	my ($hostname, $year, $month, $day, $hour, $domain) = @_;

	my ($sec,$min,$h,$mday,$mon,$y,$wday,$yday,$isdst) = localtime(time);
	$mon++;
	$mon = sprintf("%02d", $mon);
	$mday = sprintf("%02d", $mday);
	$y += 1900;

	return if ( ($mon ne $month) || ($day eq '00'));
	
	my $str = "<TABLE class=\"calborder\">\n<TR><TH colspan=\"24\">$TRANSLATE{'Hour View'}</TH></TR>\n<TR>";
	for my $d ("00" .. "23") {
		if ( ("$year$month$day" eq "$y$mon$mday") && ($d > $h) ) {
			$str .= "<TD>$d</TD>";
		} else {
			my $tag = 'TD';
			$tag = 'TH' if (($hour ne '') && ($d == $hour));
			my $type = '';
			$type = $SELCURRENT if (($hour ne '') && ($d == $hour));
			my $date = $year . $month . $day;
			$str .= "<$tag><a$type href=\"javascript:\" onclick=\"document.location.href='$ENV{SCRIPT_NAME}?host=$hostname&date=$date&hour=$d&domain=$domain&lang=$LANG&update='+window.frames['info'].document.forms['viewname'].elements['view'].value; return false;\">$d</a></$tag>";
		}
	}
	$str .=  "</TR>\n</TABLE>\n";

	return $str;
}


####
# Display day navigator
####
sub day_link
{
	my ($hostname, $year, $month, $day, $domain) = @_;

	my $str = "<table class=\"calborder\">\n<tr><th colspan=\"7\">$TRANSLATE{'Day View'}</th></tr>\n";
	my @wday = qw(Su Mo Tu We Th Fr Sa);
	if (exists $TRANSLATE{WeekDay}) {
		@wday = split(/\s+/, $TRANSLATE{WeekDay});
	}
	$str .= "<tr><td align=\"center\">" . join('</td><td align=\"center\">', @wday) . "</td></tr>\n";
	my @currow = ('','','','','','','');
	for my $d ("01" .. "31") {
		my $wd = &get_day_of_week($year,$month,$d);
		if ( !-d "$CONFIG{OUT_DIR}/$hostname/$year/$month/$d" ) {
			$currow[$wd] = "<td>$d</td>";
		} else {
			my $date = $year . $month . $d;
			my $tag = 'td';
			$tag = 'th' if ($d eq $day);
			my $type = '';
			$type = $SELCURRENT if ($d eq $day);
			$currow[$wd] = "<$tag><a$type href=\"javascript:\" onclick=\"document.location.href='$ENV{SCRIPT_NAME}?host=$hostname&date=$date&domain=$domain&lang=$LANG&update='+window.frames['info'].document.forms['viewname'].elements['view'].value; return false;\">$d</a></$tag>";
		}
		if ($wd == 6) {
			map { $_ = "<td>&nbsp;</td>" if ($_ eq ''); } @currow;
			$str .= "<tr>" . join('', @currow) . "</tr>\n";
			@currow = ('','','','','','','');
			
		}
	}
	map { $_ = "<td>&nbsp;</td>" if ($_ eq ''); } @currow;
	$str .= "<tr>" . join('', @currow) . "</tr>\n";
	$str .=  "</table>\n";

	return $str;
}

####
# Get the week day of a date
####
sub get_day_of_week
{
	my ($year, $month, $day) = @_;

	$day = (localtime(timelocal_nocheck(0,0,0,$day,--$month,$year)))[6];

	return $day;
}

####
# Display year navigator
####
sub year_link
{
	my ($hostname, $domain, $curyear) = @_;

	if (not opendir(DIR, "$CONFIG{OUT_DIR}/$hostname")) {
		&logerror("Can't open directory $CONFIG{OUT_DIR}/$hostname: $!\n");
		return;
	}
	my @dirs = grep { /^\d+$/ && -d "$CONFIG{OUT_DIR}/$hostname/$_" } readdir(DIR);
	closedir(DIR);

	my $str = qq{
<select name="year" onchange="document.location.href='$ENV{SCRIPT_NAME}?host=$hostname&date='+this.options[this.options.selectedIndex].value+'0000'+'&domain=$domain&lang=$LANG&update='+window.frames['info'].document.forms['viewname'].elements['view'].value;">
};
	foreach my $d (@dirs) {
		my $sel = '';
		$sel = ' selected="1"' if ($d eq $curyear);
		$str .= "<option value=\"$d\"$sel>$d</option>";
	}
	$str .= "</select>\n";

	return $str;
}

####
# Show temporal menu
####
sub show_temporal_menu
{
	my ($hostname, $date, $hour, $domain) = @_;

	my ($current, $year, $mon, $mday, $period, $x_label, $begin, $end) = &normalyze_date($date, $hour);

	my $timestamp = $year;
	$timestamp = $TRANSLATE{$mon} . ' ' . $timestamp if ($mon ne '00');
	$timestamp =  $mday . ' ' . $timestamp if ($mday ne '00');

	my $previous = &get_previous($hostname, $year, $mon, $mday);
	my $next = &get_next($hostname, $year, $mon, $mday);
	
	# Compute time navigation menus
	my $year_view = &year_link($hostname, $domain, $year);
	my $month_view = &month_link($hostname,$year,$mon,$domain);
	my $day_view = &day_link($hostname,$year,$mon,$mday,$domain);
	my $hour_view = &hour_link($hostname,$year,$mon,$mday,$hour,$domain);

	print qq{
<table border="0" width="100%">
<tr>
<th align="left" nowrap="1">
<a href="javascript:" onclick="if (document.forms[0].year.options[document.forms[0].year.options.selectedIndex].value != '') document.location.href='$ENV{SCRIPT_NAME}?host=$hostname&date='+document.forms[0].year.options[document.forms[0].year.options.selectedIndex].value+'0000'+'&domain=$domain&lang=$LANG&update='+window.frames['info'].document.forms['viewname'].elements['view'].value; return false;">$TRANSLATE{Years}</a>: $year_view
</th>
<th align="center" width="100%">
};
	if ($previous) {
		print "<a href=\"javascript:\" onclick=\"document.location.href='$ENV{SCRIPT_NAME}?host=$hostname&date=$previous&domain=$domain&lang=$LANG&update='+window.frames['info'].document.forms['viewname'].elements['view'].value; return false;\">&lt;&lt; $TRANSLATE{Previous}</a>";
	} else {
		print "&lt;&lt; $TRANSLATE{Previous}";
	}
	print " &nbsp;&nbsp; - &nbsp;&nbsp; [$timestamp] &nbsp;&nbsp; - &nbsp;&nbsp; ";
	if ($next) {
		print "<a href=\"javascript:\" onclick=\"document.location.href='$ENV{SCRIPT_NAME}?host=$hostname&date=$next&domain=$domain&lang=$LANG&update='+window.frames['info'].document.forms['viewname'].elements['view'].value; return false;\">$TRANSLATE{Next} &gt;&gt;</a>";
	} else {
		print "$TRANSLATE{Next} &gt;&gt;";
	}
	my $curdomain = '';
	$curdomain = " [$DOMAIN]" if ($DOMAIN);
	print qq{
</th>
<td rowspan="2" align="center" valign="top">
<div id="temporal">
$day_view
</div>
</td>
</tr>
<tr>
<td valign="top" align="left" nowrap="1">
<div id="temporal" align="center">
$month_view
<div>
</td>
<td class="smalltitle" align="center">
$period$curdomain
<br>
<div id="temporal">
$hour_view
</div>
</td>
</tr>
<tr>
<!-- th align="left" colspan="4">
&nbsp;
</th -->
</tr>
</table>
};

}

####
# Display all host statistics collected
####
sub show_list_host
{
	my @dirs = @_;

	print "<table width=\"100%\"><tr><th>&nbsp;</th></tr></table>\n";

	my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time);
	$mon++;
	$year += 1900;
	$mon = sprintf("%02d",$mon);
	$mday = sprintf("%02d",$mday);
	my $curday = $year . $mon . $mday;
	print "<div id=\"listhost\">\n";
	foreach my $h (@dirs) {
		print "<ul><li>$TRANSLATE{'Consult global statistics for'} <a href=\"$ENV{SCRIPT_NAME}?host=$h&date=$curday&lang=$LANG\" target=\"_top\">'$h'</a>\n" if (!$ENV{REMOTE_USER} || !$CONFIG{ADMIN} || grep(/^$ENV{REMOTE_USER}$/, split(/[\s\t,;]+/, $CONFIG{ADMIN})) );
		print "<ul>" if (($#{$CONFIG{DOMAIN_REPORT}} >= 0) || (scalar keys %{$CONFIG{DOMAIN_HOST_REPORT}} > 0));
		if (!$ENV{REMOTE_USER} || !$CONFIG{ADMIN} || grep(/^$ENV{REMOTE_USER}$/, split(/[\s\t,;]+/, $CONFIG{ADMIN})) ) {
			foreach my $d (@{$CONFIG{DOMAIN_REPORT}}) {
				print "<li>$TRANSLATE{'Statistics for domain'} '<a href=\"$ENV{SCRIPT_NAME}?host=$h&date=$curday&domain=$d\" target=\"_top\">$d</a>'</li>\n";
			}
			if (exists $CONFIG{DOMAIN_HOST_REPORT}{$h}) {
				foreach my $d (@{$CONFIG{DOMAIN_HOST_REPORT}{$h}}) {
					print "<li>$TRANSLATE{'Statistics for domain'} '<a href=\"$ENV{SCRIPT_NAME}?host=$h&date=$curday&domain=$d\" target=\"_top\">$d</a>'</li>\n";
				}
			}
		} else {
			foreach my $d (@{$CONFIG{DOMAIN_REPORT}}) {
				print "<li>$TRANSLATE{'Statistics for domain'} '<a href=\"$ENV{SCRIPT_NAME}?host=$h&date=$curday&domain=$d\" target=\"_top\">$d</a>'</li>\n" if (!$ENV{REMOTE_USER} || grep(/^$d$/, @{$CONFIG{DOMAIN_USER}{$ENV{REMOTE_USER}}}));
			}
			if (exists $CONFIG{DOMAIN_HOST_REPORT}{$h}) {
				foreach my $d (@{$CONFIG{DOMAIN_HOST_REPORT}{$h}}) {
					print "<li>$TRANSLATE{'Statistics for domain'} '<a href=\"$ENV{SCRIPT_NAME}?host=$h&date=$curday&domain=$d\" target=\"_top\">$d</a>'</li>\n" if (!$ENV{REMOTE_USER} || grep(/^$d$/, @{$CONFIG{DOMAIN_USER}{$ENV{REMOTE_USER}}}));
				}
			}
		}
		print "</ul>" if (($#{$CONFIG{DOMAIN_REPORT}} >= 0) || (scalar keys %{$CONFIG{DOMAIN_HOST_REPORT}} > 0));
		print "</ul>";
	}
	print "</div>\n";
	
}

sub normalyze_date
{
	my ($date, $hour) = @_;

	# Set default to current timestamp	
	my ($s,$m,$h,$mday,$mon,$year,$wd,$yd,$isdst) = localtime(time);
	$mon++;
	$year += 1900;

	my $current = $year . sprintf("%02d",$mon) . sprintf("%02d",$mday);

	# Normalyze date parameter
	if ($date =~ /^(\d{4})(\d{2})(\d{2})$/) {
		$year = $1;
		$mon = $2;
		$mday = $3;
	} elsif ($date =~ /^(\d{4})(\d{2})$/) {
		$year = $1;
		$mon = $2;
		$mday = '00';
	} elsif ($date =~ /^(\d{4})$/) {
		$year = $1;
		$mon = '00';
		$mday = '00';
	}
	$mon = sprintf("%02d",$mon);
	$mday = sprintf("%02d",$mday);

	# Set default labels for graph output
	my $period = $TRANSLATE{'Monthly'};
	my $x_label = $TRANSLATE{'Days%20of%20the%20month'};
	my $begin = '01';
	my $end = '31';
	if ($hour ne '') {
		$period = $TRANSLATE{'Hourly'};
		$x_label = $TRANSLATE{'Minutes%20of%20the%20hour'};
		$begin = '00';
		$end = '60';
	} elsif ($mday ne '00') {
		$period = $TRANSLATE{'Daily'};
		$x_label = $TRANSLATE{'Hours%20of%20the%20day'};
		$begin = '00';
		$end = '23';
	} elsif ($mon eq '00') {
		$period = $TRANSLATE{'Yearly'};
		$x_label = $TRANSLATE{'Months%20of%20the%20year'};
		$end = '12';
	}

	return ($current, $year, $mon, $mday, $period, $x_label, $begin, $end);
}

####
# Show global statistics
####
sub show_stats
{
	my ($hostname, $date, $hour, $domain, $type) = @_;

	my ($current, $year, $mon, $mday, $period, $x_label, $begin, $end) = &normalyze_date($date, $hour);

	my %period_stats = ();
	my $cache_path = $date;
	$cache_path =~ s/(\d{4})(\d{2})(\d{2})/$1\/$2\/$3/;
	$cache_path =~ s/\/00//g;
	# Prevent Out of memory
	if ( ($mday eq '00') && !-e "$CONFIG{OUT_DIR}/$hostname/$cache_path/cache.pm") {
		print "<h3 style=\"color: red;\">No cache file found, please run sa_cache as explain in the documentation (See Caching).</h3>\n";
		return;
	}
	# Use cache files if possible in hour view
	if ($hour && -e "$CONFIG{OUT_DIR}/$hostname/$cache_path/${hour}cache.pm\U$domain\E") {
		my $file = "$CONFIG{OUT_DIR}/$hostname/$cache_path/${hour}cache.pm\U$domain\E";
		do "$file";
		print "$@<br>\n";
	} elsif ($hour && -e "$CONFIG{OUT_DIR}/$hostname/$cache_path/cache.pm\U$domain\E") {
		# For caching usage to limit out of memory problem
		print "<h3 style=\"color: red;\">No cache file yet for this hour, please wait for next run of 'sa_cache --actual-day-only'.</h3>\n";
	# Use cache files if possible in day/month/year view
	} elsif (!$hour && -e "$CONFIG{OUT_DIR}/$hostname/$cache_path/cache.pm\U$domain\E") {
		my $file = "$CONFIG{OUT_DIR}/$hostname/$cache_path/cache.pm\U$domain\E";
		do "$file";
		print "$@<br>\n";
	# No cache file, we need to compute stat from scratch
	} else {
		# Compute statistics for the given period
		for (my $i = "$mon$mday"; $i <= 1231; $i++) {
			$i =~ s/^00/01/;
			$i =~ s/00$/01/;
			if ($i =~ /(\d{2})32/) {
				$i = "$1" . "01";
				$i += 100;
			}
			last if ($i > 1231);
			$i = sprintf("%04d", $i);
			$i =~ /(\d{2})(\d{2})/;
			my $m = "$1";
			my $d = "$2";
			last if (($mon ne '00') && ($m > $mon));

			if ($type eq 'messageflow') {
				# Get sender statistics
				&get_sender_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
				# Get recipient statistics and delivery status
				&get_recipient_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
			} elsif ($type eq 'spamflow') {
				# Get sender statistics
				&get_sender_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
				# Get recipient statistics and delivery status
				&get_recipient_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
				# Get spamming statistics
				&get_spam_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
			} elsif ($type eq 'virusflow') {
				# Get sender statistics
				&get_sender_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
				# Get recipient statistics and delivery status
				&get_recipient_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
				# Get virus statistics
				&get_virus_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
			} elsif ($type eq 'dsnflow') {
				# Get DSN statistics
				&get_dsn_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
			} elsif ($type eq 'rejectflow') {
				# Get sender statistics
				&get_sender_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
				# Get rejection statistics
				&get_rejected_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
				# Get syserr statistics
				&get_syserr_stat($hostname,$year,$m,$d,$hour);
			} elsif ($type eq 'statusflow') {
				# Get sender statistics
				&get_sender_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
				# Get recipient statistics and delivery status
				&get_recipient_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
				# Get rejection statistics
				&get_rejected_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
				# Get syserr statistics
				&get_syserr_stat($hostname,$year,$m,$d,$hour);
				# Get spamming statistics
				&get_spam_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
				# Get virus statistics
				&get_virus_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
			} elsif ($type eq 'authflow') {
				# Get auth statistics
				&get_auth_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
			} elsif ($type eq 'topsender') {
				# Get sender statistics
				&get_sender_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
				&get_recipient_stat($hostname,$year,$m,$d,$mon,$mday,$hour) if ($DOMAIN);
			} elsif ($type eq 'toprecipient') {
				# Get recipient statistics
				&get_sender_stat($hostname,$year,$m,$d,$mon,$mday,$hour) if ($DOMAIN);
				&get_recipient_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
			} elsif ($type eq 'topspam') {
				# Get sender statistics
				&get_sender_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
				# Get recipient statistics and delivery status
				&get_recipient_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
				# Get spamming statistics
				&get_spam_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
			} elsif ($type eq 'topvirus') {
				# Get sender statistics
				&get_sender_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
				# Get recipient statistics and delivery status
				&get_recipient_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
				# Get virus statistics
				&get_virus_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
			} elsif ($type eq 'topdsn') {
				# Get dsn statistics
				&get_dsn_top_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
			} elsif ($type eq 'topreject') {
				# Get sender statistics
				&get_sender_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
				# Get recipient statistics and delivery status
				&get_recipient_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
				# Get rejection statistics
				&get_rejected_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
				# Get syserr statistics
				&get_syserr_stat($hostname,$year,$m,$d,$hour);
			} elsif ($type eq 'toplimit') {
				# Get sender statistics
				&get_sender_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
				# Get recipient statistics and delivery status
				&get_recipient_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
			} elsif (grep(/^$type$/, keys %ANTISPAM_NAME)) {
				# Get spam details
				&get_spamdetail_stat($type,$hostname,$year,$m,$d,$mon,$mday,$hour);
			} elsif ($type eq 'topauth') {
				# Get auth statistics
				&get_auth_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
			} elsif ($type eq 'toppostgrey') {
				&get_postgrey_stat($hostname,$year,$m,$d,$mon,$mday,$hour);
			}
			last if ($mday ne '00');
		}
		if ($type eq 'messageflow') {
			%period_stats = &compute_messageflow($hostname);
		} elsif ($type eq 'spamflow') {
			%period_stats = &compute_spamflow($hostname);
		} elsif ($type eq 'virusflow') {
			%period_stats = &compute_virusflow($hostname);
		} elsif ($type eq 'dsnflow') {
			%period_stats = &compute_dsnflow($hostname);
		} elsif ($type eq 'rejectflow') {
			%period_stats = &compute_rejectflow();
		} elsif ($type eq 'statusflow') {
			&compute_statusflow();
		} elsif ($type eq 'authflow') {
			%period_stats = &compute_authflow();
		} elsif ($type eq 'topsender') {
			&compute_top_sender();
		} elsif ($type eq 'toprecipient') {
			&compute_top_recipient();
		} elsif ($type eq 'topspam') {
			&compute_top_spam();
		} elsif ($type eq 'topvirus') {
			&compute_top_virus();
		} elsif ($type eq 'topdsn') {
			&compute_top_dsn();
		} elsif ($type eq 'topreject') {
			&compute_top_reject();
		} elsif ($type eq 'toplimit') {
			&compute_top_limit();
		} elsif (grep(/^$type$/, keys %ANTISPAM_NAME)) {
			&compute_top_spamdetail($type);
		} elsif ($type eq 'topauth') {
			&compute_top_auth();
		}
	}


	if ($type eq 'messageflow') {
		&summarize_messageflow($begin, $end, %period_stats);
		&display_messageflow($x_label);
	} elsif ($type eq 'spamflow') {
		&summarize_spamflow($begin, $end, %period_stats);
		&display_spamflow($x_label);
	} elsif ($type eq 'virusflow') {
		&summarize_virusflow($begin, $end, %period_stats);
		&display_virusflow($x_label);
	} elsif ($type eq 'dsnflow') {
		&summarize_dsnflow($begin, $end, %period_stats);
		&display_dsnflow($x_label);
	} elsif ($type eq 'rejectflow') {
		&summarize_rejectflow($begin, $end, %period_stats);
		&display_rejectflow($x_label);
	} elsif ($type eq 'statusflow') {
		&display_statusflow($x_label);
	} elsif ($type eq 'authflow') {
		&summarize_authflow($begin, $end, %period_stats);
		&display_authflow($x_label);
	} elsif ($type eq 'topsender') {
		&display_top_sender($hostname, $date, $hour);
	} elsif ($type eq 'toprecipient') {
		&display_top_recipient($hostname, $date, $hour);
	} elsif ($type eq 'topspam') {
		&display_top_spam($hostname, $date, $hour);
	} elsif ($type eq 'topvirus') {
		&display_top_virus($hostname, $date, $hour);
	} elsif ($type eq 'topdsn') {
		&display_top_dsn($hostname, $date, $hour);
	} elsif ($type eq 'topreject') {
		&display_top_reject($hostname, $date, $hour);
	} elsif ($type eq 'toplimit') {
		&display_top_limit($hostname, $date, $hour);
	} elsif (grep(/^$type$/, keys %ANTISPAM_NAME)) {
		&display_top_spamdetail($hostname, $date, $type, $hour);
	} elsif ($type eq 'topauth') {
		&display_top_auth($hostname, $date, $hour);
	}
}


####
# Get senders statistics
####
sub get_sender_stat
{
	my ($hostname, $year, $month, $day, $mon, $mday, $hour) = @_;
	
	my $file = "$CONFIG{OUT_DIR}/$hostname/$year/$month/$day/senders.dat";
	open(IN, $file) || return;
	while (my $l = <IN>) { 
		chomp($l);
		# Format: Hour:Id:Sender:Size:Nrcpts:Relay
		my @data = split(/:/, $l);
		$data[0] =~ /^(\d{2})/;
		next if (($hour ne '') && ($1 != $hour));
		$data[2] ||= '<>';
		$STATS{$data[1]}{hour} = $data[0];
		$STATS{$data[1]}{sender} = $data[2];
		$STATS{$data[1]}{size} = $data[3];
		$STATS{$data[1]}{nrcpt} = $data[4];
		$STATS{$data[1]}{sender_relay} = $data[5];
		my $idx = $month;
		if ($hour ne '') {
			$data[0] =~ /(\d{2})\d{2}$/;
			$idx = sprintf("%02d", $1);
		} elsif ($mday ne '00') {
			$data[0] =~ s/\d{4}$//;
			$idx = sprintf("%02d", $data[0]);
		} elsif ($mon ne '00') {
			$idx = $day;
		}
		$STATS{$data[1]}{idx_sender} = "$idx";
	}
	close(IN);
}

####
# Get recipient statistics
####
sub get_recipient_stat
{
	my ($hostname, $year, $month, $day, $mon, $mday, $hour) = @_;

	my $file = "$CONFIG{OUT_DIR}/$hostname/$year/$month/$day/recipient.dat";
	open(IN, $file) || return;
	while (my $l = <IN>) { 
		chomp($l);
		# Format: Hour:Id:recipient:Relay:Status
		my @data = split(/:/, $l);
		$data[0] =~ /^(\d{2})/;
		next if (($hour ne '') && ($1 != $hour));
		next if ($data[4] =~ /Queued/);
		push(@{$STATS{$data[1]}{rcpt}}, $data[2]);
		push(@{$STATS{$data[1]}{rcpt_relay}}, $data[3]);
		push(@{$STATS{$data[1]}{status}}, $data[4]);
		my $idx = $month;
		if ($hour ne '') {
			$data[0] =~ /(\d{2})\d{2}$/;
			$idx = sprintf("%02d", $1);
		} elsif ($mday ne '00') {
			$data[0] =~ s/\d{4}$//;
			$idx = sprintf("%02d", $data[0]);
		} elsif ($mon ne '00') {
			$idx = $day;
		}
		$STATS{$data[1]}{idx_rcpt} = "$idx";
	}
	close(IN);
}

####
# Get rejected statistics
####
sub get_rejected_stat
{
	my ($hostname, $year, $month, $day, $mon, $mday, $hour) = @_;

	my $file = "$CONFIG{OUT_DIR}/$hostname/$year/$month/$day/rejected.dat";
	open(IN, $file) || return;
	while (my $l = <IN>) { 
		chomp($l);
		# Format: Hour:Id:Rule:Relay:Arg1:Status
		my @data = split(/:/, $l);
		$data[0] =~ /^(\d{2})/;
		next if (($hour ne '') && ($1 != $hour));
		$STATS{$data[1]}{rule} = $data[2];
		$STATS{$data[1]}{sender_relay} = $data[3] if (!$STATS{$data[1]}{sender_relay});
		if ($#data > 4) {
			if ($data[2] eq 'check_relay') {
				$STATS{$data[1]}{sender_relay} = $data[4];
			} elsif ($data[2] eq 'check_rcpt') {
				push(@{$STATS{$data[1]}{chck_rcpt}}, $data[4]);
			} else {
				# $data[2] eq 'check_mail' or POSTFIX
				$STATS{$data[1]}{sender} = $data[4];
			}
			push(@{$STATS{$data[1]}{chck_status}}, $data[5]);
		} else {
			push(@{$STATS{$data[1]}{chck_status}}, $data[4]);
		}
		my $idx = $month;
		if ($hour ne '') {
			$data[0] =~ /(\d{2})\d{2}$/;
			$idx = sprintf("%02d", $1);
		} elsif ($mday ne '00') {
			$data[0] =~ s/\d{4}$//;
			$idx = sprintf("%02d", $data[0]);
		} elsif ($mon ne '00') {
			$idx = $day;
		}
		$STATS{$data[1]}{idx_reject} = "$idx";
	}
	close(IN);
}

####
# Get DSN statistics
####
sub get_dsn_stat
{
	my ($hostname, $year, $month, $day, $mon, $mday, $hour) = @_;

	my %sourceid = ();

	my $file = "$CONFIG{OUT_DIR}/$hostname/$year/$month/$day/dsn.dat";
	open(IN, $file) || return;
	while (my $l = <IN>) { 
		chomp($l);
		# Format: Hour:Id:SourceId:Status
		my @data = split(/:/, $l, 4);
		$data[0] =~ /^(\d{2})/;
		next if (($hour ne '') && ($1 != $hour));
		$STATS{$data[1]}{dsnstatus} = $data[3];
		$STATS{$data[1]}{srcid} = $data[2];
		$sourceid{$data[2]} = $data[1];
		my $idx = $month;
		if ($hour ne '') {
			$data[0] =~ /(\d{2})\d{2}$/;
			$idx = sprintf("%02d", $1);
		} elsif ($mday ne '00') {
			$data[0] =~ s/\d{4}$//;
			$idx = sprintf("%02d", $data[0]);
		} elsif ($mon ne '00') {
			$idx = $day;
		}
		$STATS{$data[1]}{idx_dsn} = "$idx";
	}
	close(IN);

	$file = "$CONFIG{OUT_DIR}/$hostname/$year/$month/$day/senders.dat";
	# Format: Hour:Id:Sender:Size:Nrcpts:Relay
	if (open(IN, $file)) {
		while (my $l = <IN>) { 
			chomp($l);
			# Format: Hour:Id:Sender:Size:Nrcpts:Relay
			my @data = split(/:/, $l);
			$data[0] =~ /^(\d{2})/;
			next if (($hour ne '') && ($1 != $hour));
			$data[2] ||= '<>';
			next if (!exists $STATS{$data[1]});
			$STATS{$data[1]}{hour} = $data[0];
			$STATS{$data[1]}{sender} = $data[2];
			$STATS{$data[1]}{size} = $data[3];
			$STATS{$data[1]}{nrcpt} = $data[4];
			$STATS{$data[1]}{sender_relay} = $data[5];
		}
		close(IN);
	}

	$file = "$CONFIG{OUT_DIR}/$hostname/$year/$month/$day/recipient.dat";
	if (open(IN, $file)) {
		while (my $l = <IN>) {
			chomp($l);
			# Format: Hour:Id:recipient:Relay:Status
			my @data = split(/:/, $l);
			$data[0] =~ /^(\d{2})/;
			next if (($hour ne '') && ($1 != $hour));
			next if (!exists $STATS{$data[1]});
			next if ($data[4] =~ /Queued/);
			push(@{$STATS{$data[1]}{rcpt}}, $data[2]);
			push(@{$STATS{$data[1]}{rcpt_relay}}, $data[3]);
			push(@{$STATS{$data[1]}{status}}, $data[4]);
		}
		close(IN);
	}
}

####
# Get DSN top statistics
####
sub get_dsn_top_stat
{
	my ($hostname, $year, $month, $day, $mon, $mday, $hour) = @_;

	my %sourceid = ();

	my $file = "$CONFIG{OUT_DIR}/$hostname/$year/$month/$day/dsn.dat";
	open(IN, $file) || return;
	while (my $l = <IN>) { 
		chomp($l);
		# Format: Hour:Id:SourceId:Status
		my @data = split(/:/, $l, 4);
		$data[0] =~ /^(\d{2})/;
		next if (($hour ne '') && ($1 != $hour));
		$STATS{$data[1]}{dsnstatus} = $data[3];
		$sourceid{$data[2]} = $data[1];
		my $idx = $month;
		if ($hour ne '') {
			$data[0] =~ /(\d{2})\d{2}$/;
			$idx = sprintf("%02d", $1);
		} elsif ($mday ne '00') {
			$data[0] =~ s/\d{4}$//;
			$idx = sprintf("%02d", $data[0]);
		} elsif ($mon ne '00') {
			$idx = $day;
		}
		$STATS{$data[1]}{idx_dsn} = "$idx";
	}
	close(IN);

	$file = "$CONFIG{OUT_DIR}/$hostname/$year/$month/$day/senders.dat";
	# Format: Hour:Id:Sender:Size:Nrcpts:Relay
	if (open(IN, $file)) {
		while (my $l = <IN>) { 
			chomp($l);
			# Format: Hour:Id:Sender:Size:Nrcpts:Relay
			my @data = split(/:/, $l);
			$data[0] =~ /^(\d{2})/;
			$data[2] ||= '<>';
			next if (!exists $sourceid{$data[1]});
			$STATS{$sourceid{$data[1]}}{sender} = $data[2];
			$STATS{$sourceid{$data[1]}}{sender_relay} = $data[5];
		}
		close(IN);
	}

	$file = "$CONFIG{OUT_DIR}/$hostname/$year/$month/$day/recipient.dat";
	if (open(IN, $file)) {
		while (my $l = <IN>) {
			chomp($l);
			# Format: Hour:Id:recipient:Relay:Status
			my @data = split(/:/, $l);
			$data[0] =~ /^(\d{2})/;
			next if (!exists $sourceid{$data[1]});
			next if ($data[4] eq 'Sent');
			next if ($data[4] =~ /Queued/);
			push(@{$STATS{$sourceid{$data[1]}}{rcpt}}, $data[2]);
		}
		close(IN);
	}
}

####
# Get Spam statistics
####
sub get_spam_stat
{
	my ($hostname, $year, $month, $day, $mon, $mday, $hour) = @_;

	my $file = "$CONFIG{OUT_DIR}/$hostname/$year/$month/$day/spam.dat";
	open(IN, $file) || return;
	while (my $l = <IN>) { 
		chomp($l);
		# Format: Hour:Id:From:To:Spam
		my @data = split(/:/, $l, 5);
		$data[0] =~ /^(\d{2})/;
		next if (($hour ne '') && ($1 != $hour));
		$STATS{$data[1]}{hour} = $data[0] if (!exists $STATS{$data[1]}{hour});
		$STATS{$data[1]}{sender} = $data[2] if (!exists $STATS{$data[1]}{sender});
		push(@{$STATS{$data[1]}{rcpt}}, $data[3]);
		$STATS{$data[1]}{spam} = $data[4];
		my $idx = $month;
		if ($hour ne '') {
			$data[0] =~ /(\d{2})\d{2}$/;
			$idx = sprintf("%02d", $1);
		} elsif ($mday ne '00') {
			$data[0] =~ s/\d{4}$//;
			$idx = sprintf("%02d", $data[0]);
		} elsif ($mon ne '00') {
			$idx = $day;
		}
		$STATS{$data[1]}{idx_spam} = "$idx";
	}
	close(IN);
}

####
# Get Virus statistics
####
sub get_virus_stat
{
	my ($hostname, $year, $month, $day, $mon, $mday, $hour) = @_;
	
	my $file = "$CONFIG{OUT_DIR}/$hostname/$year/$month/$day/virus.dat";
	open(IN, $file) || return;
	my @done = ();
	while (my $l = <IN>) { 
		chomp($l);
		# Format: Hour:Id:file:virus
		my @data = split(/:/, $l, 4);
		$data[0] =~ /^(\d{2})/;
		next if (($hour ne '') && ($1 != $hour));
		$STATS{$data[1]}{hour} = $data[0] if (!exists $STATS{$data[1]}{hour});
		$STATS{$data[1]}{file} = $data[2];
		$STATS{$data[1]}{virus} = $data[3];
		my $idx = $month;
		if ($hour ne '') {
			$data[0] =~ /(\d{2})\d{2}$/;
			$idx = sprintf("%02d", $1);
		} elsif ($mday ne '00') {
			$data[0] =~ s/\d{4}$//;
			$idx = sprintf("%02d", $data[0]);
		} elsif ($mon ne '00') {
			$idx = $day;
		}
		$STATS{$data[1]}{idx_virus} = "$idx";
	}
	close(IN);
}

####
# Get Sys error statistics
####
sub get_syserr_stat
{
	my ($hostname, $year, $month, $day, $hour) = @_;

	my $file = "$CONFIG{OUT_DIR}/$hostname/$year/$month/$day/syserr.dat";
	if (open(IN, $file)) {
		while (my $l = <IN>) { 
			chomp($l);
			# Format: Hour:Id:Message
			my @data = split(/:/, $l, 3);
			$data[0] =~ /^(\d{2})/;
			next if (($hour ne '') && ($1 != $hour));
			shift(@data);
			my $id = shift(@data);
			$STATS{$id}{error} = join(':', @data);
		}
		close(IN);
	}

	$file = "$CONFIG{OUT_DIR}/$hostname/$year/$month/$day/other.dat";
	open(IN, $file) || return;
	while (my $l = <IN>) { 
		chomp($l);
		# Format: Hour:Message
		my @data = split(/:/, $l, 2);
		$data[0] =~ /^(\d{2})/;
		next if (($hour ne '') && ($1 != $hour));
		shift(@data);
		$STATS{$UNIQID}{error} = join(':', @data);
		$UNIQID++;
	}
	close(IN);
}

####
# Get Spam details
####
sub get_spamdetail_stat
{
	my ($type, $hostname, $year, $month, $day, $mon, $mday, $hour) = @_;

	my $file = "$CONFIG{OUT_DIR}/$hostname/$year/$month/$day/$type.dat";
	open(IN, $file) || return;
	while (my $l = <IN>) { 
		chomp($l);
		# Format: Hour:Id:type:score:cache:autolearn:spam
		my @data = split(/:/, $l, 7);
		$data[0] =~ /^(\d{2})/;
		next if (($hour ne '') && ($1 != $hour));
		$STATS{$data[1]}{hour} = $data[0];
		$STATS{$data[1]}{type} = $data[2];
		$STATS{$data[1]}{score} = $data[3];
		$STATS{$data[1]}{cache} = $data[4];
		$STATS{$data[1]}{autolearn} = $data[5];
		$STATS{$data[1]}{spam} = $data[6];
		my $idx = $month;
		if ($hour ne '') {
			$data[0] =~ /(\d{2})\d{2}$/;
			$idx = sprintf("%02d", $1);
		} elsif ($mday ne '00') {
			$data[0] =~ s/\d{4}$//;
			$idx = sprintf("%02d", $data[0]);
		} elsif ($mon ne '00') {
			$idx = $day;
		}
		$STATS{$data[1]}{idx_spamd} = "$idx";
	}
	close(IN);

	$file = "$CONFIG{OUT_DIR}/$hostname/$year/$month/$day/spam.dat";
	open(IN, $file) || return;
	while (my $l = <IN>) { 
		chomp($l);
		# Format: Hour:Id:From:To:Spam
		my @data = split(/:/, $l, 5);
		$data[0] =~ /^(\d{2})/;
		next if (!exists $STATS{$data[1]});
		$STATS{$data[1]}{sender} = $data[2] if (!exists $STATS{$data[1]}{sender});
		push(@{$STATS{$data[1]}{rcpt}}, $data[3]);
	}
	close(IN);
}

####
# Get authent statistics
####
sub get_auth_stat
{
	my ($hostname, $year, $month, $day, $mon, $mday, $hour) = @_;

	my $file = "$CONFIG{OUT_DIR}/$hostname/$year/$month/$day/auth.dat";
	open(IN, $file) || return;
	while (my $l = <IN>) { 
		chomp($l);
		# Format: Hour:Id:Relay:Mech:Type
		my @data = split(/:/, $l);
		$data[0] =~ /^(\d{2})/;
		next if (($hour ne '') && ($1 != $hour));
		push(@{$AUTH{$data[1]}{relay}}, $data[2]);
		push(@{$AUTH{$data[1]}{mech}}, $data[3]);
		push(@{$AUTH{$data[1]}{type}}, $data[4]);

		my $idx = $month;
		if ($hour ne '') {
			$data[0] =~ /(\d{2})\d{2}$/;
			$idx = sprintf("%02d", $1);
		} elsif ($mday ne '00') {
			$data[0] =~ s/\d{4}$//;
			$idx = sprintf("%02d", $data[0]);
		} elsif ($mon ne '00') {
			$idx = $day;
		}
		push(@{$AUTH{$data[1]}{idx}}, "$idx");
	}
	close(IN);
}

####
# Get postgrey statistics
####
sub get_postgrey_stat
{
	my ($hostname, $year, $month, $day, $mon, $mday, $hour) = @_;

	my $file = "$CONFIG{OUT_DIR}/$hostname/$year/$month/$day/postgrey.dat";
	open(IN, $file) || return;
	while (my $l = <IN>) { 
		chomp($l);
		# Format: Hour:Id:Rule:Relay:Arg1:Status
		my @data = split(/:/, $l);
		$data[0] =~ /^(\d{2})/;
		next if (($hour ne '') && ($1 != $hour));
		$STATS{$data[1]}{rule} = $data[2];
		$STATS{$data[1]}{sender_relay} = $data[3] if (!$STATS{$data[1]}{sender_relay});
		if ($#data > 4) {
			if ($data[2] eq 'check_relay') {
				$STATS{$data[1]}{sender_relay} = $data[4];
			} elsif ($data[2] eq 'check_rcpt') {
				push(@{$STATS{$data[1]}{chck_rcpt}}, $data[4]);
			} else {
				# $data[2] eq 'check_mail' or POSTFIX
				$STATS{$data[1]}{sender} = $data[4];
			}
			push(@{$STATS{$data[1]}{chck_status}}, $data[5]);
		} else {
			push(@{$STATS{$data[1]}{chck_status}}, $data[4]);
		}
		my $idx = $month;
		if ($hour ne '') {
			$data[0] =~ /(\d{2})\d{2}$/;
			$idx = sprintf("%02d", $1);
		} elsif ($mday ne '00') {
			$data[0] =~ s/\d{4}$//;
			$idx = sprintf("%02d", $data[0]);
		} elsif ($mon ne '00') {
			$idx = $day;
		}
		$STATS{$data[1]}{idx_reject} = "$idx";
	}
	close(IN);
}


sub set_direction
{
	my ($id, $i, $hostname) = @_;

	# By default all mail are considered issued from local computer.
	my $direction = 'Int_';

	###### Check for sender origine
	# This host is a gateway and it forward mails to an internal hub
	if (!$CONFIG{MAIL_GW} && $CONFIG{MAIL_HUB}) {
		# if message doesn't come from localhost it comes from outside 
		$direction = 'Ext_' if ($STATS{$id}{sender_relay} ne 'localhost');
	# This host received mails from any side
	} elsif (!$CONFIG{MAIL_GW} && !$CONFIG{MAIL_HUB}) {
		# The message is not internal
		if ($STATS{$id}{sender_relay} ne 'localhost') {
			# Check if sender relay match any of our domains
			if (exists $CONFIG{LOCAL_HOST_DOMAIN}{$hostname} && ($#{$CONFIG{LOCAL_HOST_DOMAIN}{$hostname}} > -1) ) {
				if (!grep($STATS{$id}{sender_relay} =~ /\b$_$/i, @{$CONFIG{LOCAL_HOST_DOMAIN}{$hostname}})) {
					$direction = 'Ext_';
				}
			}
			if (exists $CONFIG{LOCAL_DOMAIN} && ($#{$CONFIG{LOCAL_DOMAIN}} > -1)) {
				if (!grep($STATS{$id}{sender_relay} =~ /\b$_$/i, @{$CONFIG{LOCAL_DOMAIN}})) {
					$direction = 'Ext_';
				}
			} else {
			# There's no local domain defined: impossible to know where message comes from
			# Maybe you must review you configuration file or write som pieces of code here
			}
		}
	# This host received all messages from a gateway
	} elsif ($CONFIG{MAIL_GW} && !$CONFIG{MAIL_HUB}) {
		# If sender relay is the gateway, it comes from outside
		$direction = 'Ext_' if (grep($STATS{$id}{sender_relay} =~ /$_/i, split(/[\s\t,;]/, $CONFIG{MAIL_GW}) ));
	# This host is a hub, it received all messages from a gateway and forward them to other host
	} elsif ($CONFIG{MAIL_GW} && $CONFIG{MAIL_HUB}) {
		# If sender relay is the gateway, it comes from outside
		$direction = 'Ext_' if (grep($STATS{$id}{sender_relay} =~ /$_/i, split(/[\s\t,;]/, $CONFIG{MAIL_GW})));
	}

	###### Now check for destination
	# If the recipient relay is localhost, it should be distributed internally
	if ($STATS{$id}{rcpt_relay}[$i] eq 'localhost') {
		$direction .= 'Int';
	# If this host is a mail gateway and the recipient relay match one of
	# our destination hub lets say it should be distributed internally
	} elsif ($CONFIG{MAIL_HUB} && (grep($STATS{$id}{rcpt_relay}[$i] =~ /$_/, split(/[\s\t,;]/, $CONFIG{MAIL_HUB}) )) ) {
		$direction .= 'Int';
	# If the recipient relay match any of our local domain
	# lets say the mail should be distributed internally
	} elsif (exists $CONFIG{LOCAL_HOST_DOMAIN}{$hostname} && ($#{$CONFIG{LOCAL_HOST_DOMAIN}{$hostname}} > -1) ){
		if (grep($STATS{$id}{rcpt_relay}[$i] =~ /\b$_$/i, @{$CONFIG{LOCAL_HOST_DOMAIN}{$hostname}})) {
			$direction .= 'Int';
		} else {
			$direction .= 'Ext';
		}
	} elsif (exists $CONFIG{LOCAL_DOMAIN} && ($#{$CONFIG{LOCAL_DOMAIN}} > -1)) {
		if (grep($STATS{$id}{rcpt_relay}[$i] =~ /\b$_$/i, @{$CONFIG{LOCAL_DOMAIN}})) {
			$direction .= 'Int';
		} else {
			$direction .= 'Ext';
		}
	# Finally his only way is to go outside
	} else {
		$direction .= 'Ext';
	}
	return $direction;
}

sub compute_messageflow
{
	my ($hostname, $mailbox) = @_;

	my %period_stat = ();
	foreach my $id (keys %STATS) {
		if ( ($STATS{$id}{sender} ne 'DSN@localhost') && (exists $STATS{$id}{nrcpt}) ) {
			if (!$DOMAIN || ($STATS{$id}{sender} =~ /$DOMAIN/) || grep(/$DOMAIN/, @{$STATS{$id}{rcpt}})) {
				if ($STATS{$id}{sender_relay} eq 'localhost') {
					$messaging{local_inbound}++;
					$messaging{local_inbound_bytes} += $STATS{$id}{size} || 0;
				} else {
					$messaging{inbound}++;
					$messaging{inbound_bytes} += $STATS{$id}{size} || 0;
				}
				$period_stat{flow}{$STATS{$id}{idx_sender}}{inbound}++;
				$period_stat{flow}{$STATS{$id}{idx_sender}}{inbound_bytes} += $STATS{$id}{size} || 0;
			}
		}

		for (my $i = 0; $i <= $#{$STATS{$id}{rcpt}}; $i++) {
			next if ($DOMAIN && ($STATS{$id}{sender} !~ /$DOMAIN/) && $STATS{$id}{rcpt}[$i] !~ /$DOMAIN/);
			$GLOBAL_STATUS{"$STATS{$id}{status}[$i]"}++;
			$GLOBAL_STATUS{"$STATS{$id}{status}[$i]" . '_bytes'} += $STATS{$id}{size};
			if ($STATS{$id}{status}[$i] eq 'Sent') {
				$period_stat{flow}{$STATS{$id}{idx_rcpt}}{outbound}++;
				$period_stat{flow}{$STATS{$id}{idx_rcpt}}{outbound_bytes} += $STATS{$id}{size};
				$messaging{nbsender}{"$STATS{$id}{sender}"} = '';
				$messaging{nbrcpt}{"$STATS{$id}{rcpt}[$i]"} = '';
				$delivery{'total'}++;
				my $direction = &set_direction($id, $i, $hostname);
				$delivery{$direction}++;
				$direction .= '_bytes';
				$delivery{$direction} += $STATS{$id}{size};
				if ($direction =~ /_Int/) {
					$messaging{local_outbound}++;
					$messaging{local_outbound_bytes} += $STATS{$id}{size} || 0;
				} else {
					$messaging{outbound}++;
					$messaging{outbound_bytes} += $STATS{$id}{size} || 0;
				}
			}
		}
	}
	%STATS = ();
	return %period_stat;
}

sub summarize_messageflow
{
	my ($begin, $end, %period_stat) = @_;

	$messaging{inbound} ||= 0;
	$messaging{local_inbound} ||= 0;
	$messaging{outbound} ||= 0;
	$messaging{local_outbound} ||= 0;
	$messaging{total_inbound} = $messaging{inbound} + $messaging{local_inbound};
	$messaging{total_inbound_bytes} = $messaging{inbound_bytes} + $messaging{local_inbound_bytes};
	$messaging{total_inbound_bytes} = sprintf("%.2f", $messaging{total_inbound_bytes}/$SIZE_UNIT);
	$messaging{inbound_bytes} = sprintf("%.2f", $messaging{inbound_bytes}/$SIZE_UNIT);
	$messaging{local_inbound_bytes} = sprintf("%.2f", $messaging{local_inbound_bytes}/$SIZE_UNIT);
	$messaging{total_outbound} = $messaging{outbound} + $messaging{local_outbound};
	$messaging{total_outbound_bytes} = $messaging{outbound_bytes} + $messaging{local_outbound_bytes};
	$messaging{total_outbound_bytes} = sprintf("%.2f", $messaging{total_outbound_bytes}/$SIZE_UNIT);
	$messaging{outbound_bytes} = sprintf("%.2f", $messaging{outbound_bytes}/$SIZE_UNIT);
	$messaging{local_outbound_bytes} = sprintf("%.2f", $messaging{local_outbound_bytes}/$SIZE_UNIT);
	if (!exists $messaging{lbls}) {
		if ($end ne '60') {
			foreach my $b ("$begin" .. "$end") {
				$messaging{lbls} .= "$b:";
				$messaging{values} .= ($period_stat{flow}{"$b"}{inbound} || 0) . ':';
				$messaging{values1} .= ($period_stat{flow}{"$b"}{outbound} || 0) . ':';
				$messaging{values_bytes} .= (sprintf("%.2f", $period_stat{flow}{"$b"}{inbound_bytes}/$SIZE_UNIT) || 0) . ':';
				$messaging{values1_bytes} .= (sprintf("%.2f", $period_stat{flow}{"$b"}{outbound_bytes}/$SIZE_UNIT) || 0) . ':';
			}
		} else {
			for (my $i = 5; $i <= 60; $i += 5) {
				$messaging{lbls} .= sprintf("%02d", $i) . ":";
				my $count = 0;
				my $count_bytes = 0;
				my $count1 = 0;
				my $count1_bytes = 0;
				foreach my $b (keys %{$period_stat{flow}}) {
					if ( ($b < $i) && ($b >= ($i - 5)) ) {
						$count += $period_stat{flow}{"$b"}{inbound};
						$count1 += $period_stat{flow}{"$b"}{outbound};
						$count_bytes += $period_stat{flow}{"$b"}{inbound_bytes};
						$count1_bytes += $period_stat{flow}{"$b"}{outbound_bytes};
					}
				}
				$messaging{values} .= ($count || 0) . ':';
				$messaging{values1} .= ($count1 || 0) . ':';
				$messaging{values_bytes} .= (sprintf("%.2f", $count_bytes/$SIZE_UNIT) || 0) . ':';
				$messaging{values1_bytes} .= (sprintf("%.2f", $count1_bytes/$SIZE_UNIT) || 0) . ':';
			}
		}
	} else {
		my @values_bytes = split(/:/, $messaging{values_bytes});
		my @values1_bytes = split(/:/, $messaging{values1_bytes});
		$messaging{values_bytes} = '';
		$messaging{values1_bytes} = '';
		foreach (@values_bytes) {
			$messaging{values_bytes} .= (sprintf("%.2f", $_/$SIZE_UNIT) || 0) . ':';
		}
		foreach (@values1_bytes) {
			$messaging{values1_bytes} .= (sprintf("%.2f", $_/$SIZE_UNIT) || 0) . ':';
		}
	}
	$messaging{lbls} =~ s/:$//;
	$messaging{values} =~ s/:$//;
	$messaging{values1} =~ s/:$//;
	$messaging{values_bytes} =~ s/:$//;
	$messaging{values1_bytes} =~ s/:$//;
	$delivery{'Int_Int'} ||= 0;
	$delivery{'Int_Ext'} ||= 0;
	$delivery{'Ext_Ext'} ||= 0;
	$delivery{'Ext_Int'} ||= 0;
	$delivery{'Int_Int_bytes'} = sprintf("%.2f", $delivery{'Int_Int_bytes'}/$SIZE_UNIT);
	$delivery{'Int_Ext_bytes'} = sprintf("%.2f", $delivery{'Int_Ext_bytes'}/$SIZE_UNIT);
	$delivery{'Ext_Ext_bytes'} = sprintf("%.2f", $delivery{'Ext_Ext_bytes'}/$SIZE_UNIT);
	$delivery{'Ext_Int_bytes'} = sprintf("%.2f", $delivery{'Ext_Int_bytes'}/$SIZE_UNIT);
}

sub display_messageflow
{
	my ($x_label) = @_;

	$messaging{inbound_mean} = sprintf("%.2f", $messaging{inbound_bytes} / ($messaging{inbound} || 1));
	$messaging{local_inbound_mean} = sprintf("%.2f", $messaging{local_inbound_bytes} / ($messaging{local_inbound} || 1));
	$messaging{total_inbound_mean} = sprintf("%.2f", $messaging{total_inbound_bytes} / ($messaging{total_inbound} || 1));
	$messaging{outbound_mean} = sprintf("%.2f", $messaging{outbound_bytes} / ($messaging{outbound} || 1));
	$messaging{local_outbound_mean} = sprintf("%.2f", $messaging{local_outbound_bytes} / ($messaging{local_outbound} || 1));
	$messaging{total_outbound_mean} = sprintf("%.2f", $messaging{total_outbound_bytes} / ($messaging{total_outbound} || 1));

	if (!$messaging{total_inbound} && !$messaging{total_outbound}) {
		print qq{<table align="center"><tr><th colspan="2" class="thhead">$TRANSLATE{'No dataset'}</th></tr></table>};
		return;
	}
	# Messaging flows
        print qq{
<table align="center" width="100%"><tr><td valign="top" align="center">

<table>
<tr><th colspan="4" class="thhead">$TRANSLATE{'Messaging flows'}</th></tr>
<tr><td class="tdhead">&nbsp;</td><td class="tdhead">$TRANSLATE{'Messages'}</td><td class="tdhead">$TRANSLATE{'Size'} ($TRANSLATE{$CONFIG{'SIZE_UNIT'}})</td><td class="tdhead">$TRANSLATE{'Mean'}</td></tr>
<tr><td class="tdtop">$TRANSLATE{'Incoming'}</td><td class="tdtopnr">$messaging{inbound}</td><td class="tdtopnr">$messaging{inbound_bytes}</td><td class="tdtopnr">$messaging{inbound_mean}</td></tr>
<tr><td class="tdtop">$TRANSLATE{'Local incoming'}</td><td class="tdtopnr">$messaging{local_inbound}</td><td class="tdtopnr">$messaging{local_inbound_bytes}</td><td class="tdtopnr">$messaging{local_inbound_mean}</td></tr>
<tr><th>$TRANSLATE{'Total incoming'}</th><th align="right">$messaging{total_inbound}</th><th align="right">$messaging{total_inbound_bytes}</th><th align="right">$messaging{total_inbound_mean}</th></tr>
<tr><td class="tdtop">$TRANSLATE{'Outgoing'}</td><td class="tdtopnr">$messaging{outbound}</td><td class="tdtopnr">$messaging{outbound_bytes}</td><td class="tdtopnr">$messaging{outbound_mean}</td></tr>
<tr><td class="tdtop">$TRANSLATE{'Local delivery'}</td><td class="tdtopnr">$messaging{local_outbound}</td><td class="tdtopnr">$messaging{local_outbound_bytes}</td><td class="tdtopnr">$messaging{local_outbound_mean}</td></tr>
<tr><th>$TRANSLATE{'Total outgoing'}</th><th align="right">$messaging{total_outbound}</th><th align="right">$messaging{total_outbound_bytes}</th><th align="right">$messaging{total_outbound_mean}</th></tr>
<tr><td colspan="4" align="center"><img src=\"grafit.cgi?ttfont=$CONFIG{'TTFONT'}&labels=$messaging{lbls}&values=$messaging{values}&values1=$messaging{values1}&legend=$TRANSLATE{'Inbound'}&legend1=$TRANSLATE{'Outbound'}&title=$TRANSLATE{'Messaging%20Flow'}&width=400&height=200&x_label=$x_label&y_label=$TRANSLATE{'Number%20of%20message'}\"></td></tr>
<tr><td colspan="4" align="center"><img src=\"grafit.cgi?ttfont=$CONFIG{'TTFONT'}&labels=$messaging{lbls}&values=$messaging{values_bytes}&values1=$messaging{values1_bytes}&legend=$TRANSLATE{'Inbound'}&legend1=$TRANSLATE{'Outbound'}&title=$TRANSLATE{'Messaging%20Size%20Flow'}&width=400&height=227&x_label=$x_label&y_label=$TRANSLATE{'Size'} ($TRANSLATE{$CONFIG{'SIZE_UNIT'}})\"></td>
</tr>
</table>

</td><td valign="top" align="center">
&nbsp;
</td><td valign="top" align="center">
};


	# Message delivery flows
	$delivery{total} = $GLOBAL_STATUS{Sent} || 1;
	$delivery{total_bytes} = $GLOBAL_STATUS{Sent_bytes} || 1;
	$delivery{lbls} = "$TRANSLATE{'Ext -> Int'}:$TRANSLATE{'Ext -> Ext'}:$TRANSLATE{'Int -> Int'}:$TRANSLATE{'Int -> Ext'}";
	$delivery{'Ext_Int_percent'} = sprintf("%.2f", ($delivery{'Ext_Int'}*100) / $delivery{'total'});
	$delivery{vals} = $delivery{'Ext_Int_percent'} . ':';
	$delivery{'Ext_Ext_percent'} = sprintf("%.2f", ($delivery{'Ext_Ext'}*100) / $delivery{'total'});
	$delivery{vals} .= $delivery{'Ext_Ext_percent'} . ':';
	$delivery{'Int_Int_percent'} = sprintf("%.2f", ($delivery{'Int_Int'}*100) / $delivery{'total'});
	$delivery{vals} .= $delivery{'Int_Int_percent'} . ':';
	$delivery{'Int_Ext_percent'} = sprintf("%.2f", ($delivery{'Int_Ext'}*100) / $delivery{'total'});
	$delivery{vals} .= $delivery{'Int_Ext_percent'};
	my $nbsender = 0;
	my $nbrcpt = 0;
	if (ref $messaging{nbsender} eq 'HASH') {
		$nbsender = scalar keys %{$messaging{nbsender}} || 0;
		$nbrcpt = scalar keys %{$messaging{nbrcpt}} || 0;
		delete $messaging{nbsender};
		delete $messaging{nbrcpt};
	} elsif ($messaging{nbsender} =~ /:/) {
		$nbsender = "<img src=\"grafit.cgi?ttfont=$CONFIG{'TTFONT'}&labels=$messaging{lbls}&values=$messaging{nbsender}&values1=$messaging{nbrcpt}&legend=$TRANSLATE{'Senders'}&legend1=$TRANSLATE{'Recipients'}&title=$TRANSLATE{'Different%20senders/recipients'}&width=400&height=200&x_label=$x_label\">";

	} else {
		$nbsender = $messaging{nbsender} || 0;
		$nbrcpt = $messaging{nbrcpt} || 0;
	}
	if ($CONFIG{SHOW_DIRECTION}) {
		print qq {
<table>
<tr><th colspan="4" class="thhead">$TRANSLATE{'Message delivery flows'}</th></tr>
<tr><td class="tdhead">&nbsp;</td><td class="tdhead">$TRANSLATE{'Messages'}</td><td class="tdhead">$TRANSLATE{'Size'} ($TRANSLATE{$CONFIG{'SIZE_UNIT'}})</td><td class="tdhead">$TRANSLATE{'Percentage'}</td></tr>
<tr><td class="tdtop" nowrap="1">$TRANSLATE{'Internet -> Internal'}</td><td class="tdtopnr">$delivery{'Ext_Int'}</td><td class="tdtopnr">$delivery{'Ext_Int_bytes'}</td><td class="tdtopnr">$delivery{'Ext_Int_percent'} %</td></tr>
<tr><td class="tdtop" nowrap="1">$TRANSLATE{'Internet -> Internet'}</td><td class="tdtopnr">$delivery{'Ext_Ext'}</td><td class="tdtopnr">$delivery{'Ext_Ext_bytes'}</td><td class="tdtopnr">$delivery{'Ext_Ext_percent'} %</td></tr>
<tr><td class="tdtop" nowrap="1">$TRANSLATE{'Internal -> Internal'}</td><td class="tdtopnr">$delivery{'Int_Int'}</td><td class="tdtopnr">$delivery{'Int_Int_bytes'}</td><td class="tdtopnr">$delivery{'Int_Int_percent'} %</td></tr>
<tr><td class="tdtop" nowrap="1">$TRANSLATE{'Internal -> Internet'}</td><td class="tdtopnr">$delivery{'Int_Ext'}</td><td class="tdtopnr">$delivery{'Int_Ext_bytes'}</td><td class="tdtopnr">$delivery{'Int_Ext_percent'} %</td></tr>
<tr><td colspan="4">&nbsp;</td></tr>
<tr><td colspan="4" align="center"><img src=\"grafit.cgi?ttfont=$CONFIG{'TTFONT'}&labels=$delivery{lbls}&values=$delivery{vals}&title=$TRANSLATE{'Delivery%20Direction'}&width=300&height=200&x_label=$TRANSLATE{'Direction'}&y_label=$TRANSLATE{'Percentage%20of%20message'}&vertical=1&show_values=1\"></td></tr>
<tr><td colspan="4">&nbsp;</td></tr>
};
	} else {
		print "<table>\n";
	}
	if ($nbsender !~ /<img/) {
		print qq{<tr><th colspan="4" class="thhead">$TRANSLATE{'Different senders/recipients'}</th></tr>
<tr><td class="tdhead" colspan="2">$TRANSLATE{'Senders'}</td><td class="tdhead" colspan="2">$TRANSLATE{'Recipients'}</td></tr>
<tr><td class="tdtopnc" colspan="2">$nbsender</td><td class="tdtopnc" colspan="2">$nbrcpt</td></tr>
</table>
};
	} else {
		print qq{<tr><th colspan="4" class="thhead">$TRANSLATE{'Different senders/recipients'}</th></tr>
<tr><td colspan="4" align="center">$nbsender</td></tr>
</table>
};
	}
	print "\n</td></tr></table>\n";

}

sub compute_spamflow
{
	my ($hostname, $mailbox) = @_;

	my %period_stat = ();
	foreach my $id (keys %STATS) {
		next if ($DOMAIN && ($STATS{$id}{sender} !~ /$DOMAIN/) && !grep(/$DOMAIN/, @{$STATS{$id}{rcpt}}));
		if (exists $STATS{$id}{spam}) {
			$period_stat{spam}{$STATS{$id}{idx_spam}}++;
			$GLOBAL_STATUS{Spam}++;
			$GLOBAL_STATUS{Spam_bytes} += $STATS{$id}{size};
			if ($STATS{$id}{sender_relay} ne 'localhost') {
				$spam{local_inbound}++;
				$spam{local_inbound_bytes} += $STATS{$id}{size} || 0;
			} else {
				$spam{inbound}++;
				$spam{inbound_bytes} += $STATS{$id}{size} || 0;
			}
			for (my $i = 0; $i <= $#{$STATS{$id}{status}}; $i++) {
				next if ($mailbox && ($STATS{$id}{rcpt}[$i] !~ /$mailbox\@/) );
				if ($STATS{$id}{status}[$i] eq 'Sent') {
					my $direction = &set_direction($id, $i, $hostname);
					$spam{$direction}++;
					$direction .= '_bytes';
					$spam{$direction} += $STATS{$id}{size};
					if ($direction =~ /_Int/) {
						$spam{local_outbound}++;
						$spam{local_outbound_bytes} += $STATS{$id}{size} || 0;
					} else {
						$spam{outbound}++;
						$spam{outbound_bytes} += $STATS{$id}{size} || 0;
					}
				}
			}
		}
	}
	%STATS = ();
	return %period_stat;
}

sub summarize_spamflow
{
	my ($begin, $end, %period_stat) = @_;

	if (!exists $spam{lbls}) {
		if ($end ne '60') {
			foreach ("$begin" .. "$end") {
				$spam{lbls} .= "$_:";
				$spam{values} .= ($period_stat{spam}{"$_"} || 0) . ':';
			}
		} else {
			for (my $i = 5; $i <= 60; $i += 5) {
				$spam{lbls} .= sprintf("%02d", $i) . ":";
				my $count = 0;
				foreach my $b (keys %{$period_stat{spam}}) {
					if ( ($b < $i) && ($b >= ($i - 5)) ) {
						$count += $period_stat{spam}{"$b"};
					}
				}
				$spam{values} .= ($count || 0) . ':';
			}
		}
	}
	$spam{lbls} =~ s/:$//;
	$spam{values} =~ s/:$//;

	$spam{inbound} ||= 0;
	$spam{local_inbound} ||= 0;
	$spam{outbound} ||= 0;
	$spam{local_outbound} ||= 0;
	$spam{total_inbound} = $spam{inbound} + $spam{local_inbound};
	$spam{total_inbound_bytes} = $spam{inbound_bytes} + $spam{local_inbound_bytes};
	$spam{total_outbound} = $spam{outbound} + $spam{local_outbound};
	$spam{total_outbound_bytes} = $spam{outbound_bytes} + $spam{local_outbound_bytes};
	$spam{total_inbound_bytes} = sprintf("%.2f", $spam{total_inbound_bytes}/$SIZE_UNIT);
	$spam{inbound_bytes} = sprintf("%.2f", $spam{inbound_bytes}/$SIZE_UNIT);
	$spam{local_inbound_bytes} = sprintf("%.2f", $spam{local_inbound_bytes}/$SIZE_UNIT);
	$spam{total_outbound_bytes} = sprintf("%.2f", $spam{total_outbound_bytes}/$SIZE_UNIT);
	$spam{outbound_bytes} = sprintf("%.2f", $spam{outbound_bytes}/$SIZE_UNIT);
	$spam{local_outbound_bytes} = sprintf("%.2f", $spam{local_outbound_bytes}/$SIZE_UNIT);

	$spam{'Int_Int'} ||= 0;
	$spam{'Int_Ext'} ||= 0;
	$spam{'Ext_Ext'} ||= 0;
	$spam{'Ext_Int'} ||= 0;

}

sub display_spamflow
{
	my ($x_label) = @_;

        # Spamming flows + Spam delivery flows
        $spam{inbound_mean} = sprintf("%.2f", $spam{inbound_bytes} / ($spam{inbound} || 1));
        $spam{local_inbound_mean} = sprintf("%.2f", $spam{local_inbound_bytes} / ($spam{local_inbound} || 1));
        $spam{total_inbound_mean} = sprintf("%.2f", $spam{total_inbound_bytes} / ($spam{total_inbound} || 1));
        $spam{outbound_mean} = sprintf("%.2f", $spam{outbound_bytes} / ($spam{outbound} || 1));
        $spam{local_outbound_mean} = sprintf("%.2f", $spam{local_outbound_bytes} / ($spam{local_outbound} || 1));
        $spam{total_outbound_mean} = sprintf("%.2f", $spam{total_outbound_bytes} / ($spam{total_outbound} || 1));
        $spam{Ext_Int_mean} = sprintf("%.2f", $spam{Ext_Int} / ($spam{Ext_Int_bytes} || 1));
        $spam{Int_Int_mean} = sprintf("%.2f", $spam{Int_Int} / ($spam{Int_Int_bytes} || 1));
        $spam{Int_Ext_mean} = sprintf("%.2f", $spam{Int_Ext} / ($spam{Int_Ext_bytes} || 1));
        $spam{Ext_Ext_mean} = sprintf("%.2f", $spam{Ext_Ext} / ($spam{Ext_Ext_bytes} || 1));
        $spam{'Int_Int_bytes'} = sprintf("%.2f", $spam{'Int_Int_bytes'}/$SIZE_UNIT);
        $spam{'Int_Ext_bytes'} = sprintf("%.2f", $spam{'Int_Ext_bytes'}/$SIZE_UNIT);
        $spam{'Ext_Ext_bytes'} = sprintf("%.2f", $spam{'Ext_Ext_bytes'}/$SIZE_UNIT);
        $spam{'Ext_Int_bytes'} = sprintf("%.2f", $spam{'Ext_Int_bytes'}/$SIZE_UNIT);

	if (!$spam{total_inbound} && !$spam{total_outbound}) {
		print qq{<table align="center"><tr><th colspan="2" class="thhead">$TRANSLATE{'No dataset'}</th></tr></table>};
		return;
	}

        print qq {
<table align="center">
<tr><th colspan="4" class="thhead">$TRANSLATE{'Spamming flows'}</th></tr>
<tr><td class="tdhead">&nbsp;</td><td class="tdhead">$TRANSLATE{'Messages'}</td><td class="tdhead">$TRANSLATE{'Size'} ($TRANSLATE{$CONFIG{'SIZE_UNIT'}})</td><td class="tdhead">$TRANSLATE{'Mean'}</td></tr>
<tr><td class="tdtop">$TRANSLATE{'Incoming'}</td><td class="tdtopnr">$spam{inbound}</td><td class="tdtopnr">$spam{inbound_bytes}</td><td class="tdtopnr">$spam{inbound_mean}</td></tr>
<tr><td class="tdtop">$TRANSLATE{'Local incoming'}</td><td class="tdtopnr">$spam{local_inbound}</td><td class="tdtopnr">$spam{local_inbound_bytes}</td><td class="tdtopnr">$spam{local_inbound_mean}</td></tr>
<tr><th>$TRANSLATE{'Total incoming'}</th><th align="right">$spam{total_inbound}</th><th align="right">$spam{total_inbound_bytes}</th><th align="right">$spam{total_inbound_mean}</th></tr>
<tr><td class="tdtop">$TRANSLATE{'Outgoing'}</td><td class="tdtopnr">$spam{outbound}</td><td class="tdtopnr">$spam{outbound_bytes}</td><td class="tdtopnr">$spam{outbound_mean}</td></tr>
<tr><td class="tdtop">$TRANSLATE{'Local delivery'}</td><td class="tdtopnr">$spam{local_outbound}</td><td class="tdtopnr">$spam{local_outbound_bytes}</td><td class="tdtopnr">$spam{local_outbound_mean}</td></tr>
<tr><th>$TRANSLATE{'Total outgoing'}</th><th align="right">$spam{total_outbound}</th><th align="right">$spam{total_outbound_bytes}</th><th align="right">$spam{total_outbound_mean}</th></tr>
<tr><td colspan="4" align="center"><img src=\"grafit.cgi?ttfont=$CONFIG{'TTFONT'}&labels=$spam{lbls}&values=$spam{values}&title=$TRANSLATE{'Spamming%20Flow'}&width=400&height=200&x_label=$x_label&y_label=$TRANSLATE{'Number%20of%20spam'}\"></td></tr>
};
	if ($CONFIG{SHOW_DIRECTION}) {
		print qq{
<tr><th colspan="4" class="thhead">$TRANSLATE{'Spam delivery flows'}</th></tr>
<tr><td class="tdhead">&nbsp;</td><td class="tdhead">$TRANSLATE{'Messages'}</td><td class="tdhead">$TRANSLATE{'Size'} ($TRANSLATE{$CONFIG{'SIZE_UNIT'}})</td><td class="tdhead">$TRANSLATE{'Mean'}</td></tr>
<tr><td class="tdtop">$TRANSLATE{'Internet -> Internal'}</td><td class="tdtopnr">$spam{'Ext_Int'}</td><td class="tdtopnr">$spam{'Ext_Int_bytes'}</td><td class="tdtopnr">$spam{Ext_Int_mean}</td></tr>
<tr><td class="tdtop">$TRANSLATE{'Internet -> Internet'}</td><td class="tdtopnr">$spam{'Ext_Ext'}</td><td class="tdtopnr">$spam{'Ext_Ext_bytes'}</td><td class="tdtopnr">$spam{Ext_Ext_mean}</td></tr>
<tr><td class="tdtop">$TRANSLATE{'Internal -> Internal'}</td><td class="tdtopnr">$spam{'Int_Int'}</td><td class="tdtopnr">$spam{'Int_Int_bytes'}</td><td class="tdtopnr">$spam{Int_Int_mean}</td></tr>
<tr><td class="tdtop">$TRANSLATE{'Internal -> Internet'}</td><td class="tdtopnr">$spam{'Int_Ext'}</td><td class="tdtopnr">$spam{'Int_Ext_bytes'}</td><td class="tdtopnr">$spam{Int_Ext_mean}</td></tr>
};
	}
	print "</table>\n";

}

sub compute_virusflow
{
	my ($hostname, $mailbox) = @_;

	my %period_stat = ();
	foreach my $id (keys %STATS) {
		next if ($DOMAIN && ($STATS{$id}{sender} !~ /$DOMAIN/) && !grep(/$DOMAIN/, @{$STATS{$id}{rcpt}}));
		if (exists $STATS{$id}{virus}) {
			$period_stat{virus}{$STATS{$id}{idx_virus}}++;
			$GLOBAL_STATUS{Virus}++;
			$GLOBAL_STATUS{Virus_bytes} += $STATS{$id}{size};
			if ($STATS{$id}{sender_relay} ne 'localhost') {
				$virus{local_inbound}++;
				$virus{local_inbound_bytes} += $STATS{$id}{size} || 0;
			} else {
				$virus{inbound}++;
				$virus{inbound_bytes} += $STATS{$id}{size} || 0;
			}
			for (my $i = 0; $i <= $#{$STATS{$id}{status}}; $i++) {
				next if ($mailbox && ($STATS{$id}{rcpt}[$i] !~ /$mailbox\@/) );
				if ($STATS{$id}{status}[$i] eq 'Sent') {
					my $direction = &set_direction($id, $i, $hostname);
					$virus{$direction}++;
					$direction .= '_bytes';
					$virus{$direction} += $STATS{$id}{size};
					if ($direction =~ /_Int/) {
						$virus{local_outbound}++;
						$virus{local_outbound_bytes} += $STATS{$id}{size} || 0;
					} else {
						$virus{outbound}++;
						$virus{outbound_bytes} += $STATS{$id}{size} || 0;
					}
				}
			}
		}
	}
	%STATS = ();
	return %period_stat;
}

sub summarize_virusflow
{
	my ($begin, $end, %period_stat) = @_;

	$virus{inbound} ||= 0;
	$virus{local_inbound} ||= 0;
	$virus{outbound} ||= 0;
	$virus{local_outbound} ||= 0;
	$virus{total_inbound} = $virus{inbound} + $virus{local_inbound};
	$virus{total_inbound_bytes} = $virus{inbound_bytes} + $virus{local_inbound_bytes};
	$virus{total_outbound} = $virus{outbound} + $virus{local_outbound};
	$virus{total_outbound_bytes} = $virus{outbound_bytes} + $virus{local_outbound_bytes};
	$virus{total_inbound_bytes} = sprintf("%.2f", $virus{total_inbound_bytes}/$SIZE_UNIT);
	$virus{inbound_bytes} = sprintf("%.2f", $virus{inbound_bytes}/$SIZE_UNIT);
	$virus{local_inbound_bytes} = sprintf("%.2f", $virus{local_inbound_bytes}/$SIZE_UNIT);
	$virus{total_outbound_bytes} = sprintf("%.2f", $virus{total_outbound_bytes}/$SIZE_UNIT);
	$virus{outbound_bytes} = sprintf("%.2f", $virus{outbound_bytes}/$SIZE_UNIT);
	$virus{local_outbound_bytes} = sprintf("%.2f", $virus{local_outbound_bytes}/$SIZE_UNIT);

	if (!exists $virus{lbls}) {
		if ($end ne '60') {
			foreach ("$begin" .. "$end") {
				$virus{lbls} .= "$_:";
				$virus{values} .= ($period_stat{virus}{"$_"} || 0) . ':';
			}
		} else {
			for (my $i = 5; $i <= 60; $i += 5) {
				$virus{lbls} .= sprintf("%02d", $i) . ":";
				my $count = 0;
				foreach my $b (keys %{$period_stat{virus}}) {
					if ( ($b < $i) && ($b >= ($i - 5)) ) {
						$count += $period_stat{virus}{"$b"};
					}
				}
				$virus{values} .= ($count || 0) . ':';
			}
		}
	}
	$virus{lbls} =~ s/:$//;
	$virus{values} =~ s/:$//;

	$virus{'Int_Int'} ||= 0;
	$virus{'Int_Ext'} ||= 0;
	$virus{'Ext_Ext'} ||= 0;
	$virus{'Ext_Int'} ||= 0;
}

sub display_virusflow
{
	my ($x_label) = @_;

	# Viruses flows / Viruses delivery flows / syserr flows
	$virus{inbound_mean} = sprintf("%.2f", $virus{inbound_bytes} / ($virus{inbound} || 1));
	$virus{local_inbound_mean} = sprintf("%.2f", $virus{local_inbound_bytes} / ($virus{local_inbound} || 1));
	$virus{total_inbound_mean} = sprintf("%.2f", $virus{total_inbound_bytes} / ($virus{total_inbound} || 1));
	$virus{outbound_mean} = sprintf("%.2f", $virus{outbound_bytes} / ($virus{outbound} || 1));
	$virus{local_outbound_mean} = sprintf("%.2f", $virus{local_outbound_bytes} / ($virus{local_outbound} || 1));
	$virus{total_outbound_mean} = sprintf("%.2f", $virus{total_outbound_bytes} / ($virus{total_outbound} || 1));
	$virus{Ext_Int_mean} = sprintf("%.2f", $virus{Ext_Int} / ($virus{Ext_Int_bytes} || 1));
	$virus{Int_Int_mean} = sprintf("%.2f", $virus{Int_Int} / ($virus{Int_Int_bytes} || 1));
	$virus{Int_Ext_mean} = sprintf("%.2f", $virus{Int_Ext} / ($virus{Int_Ext_bytes} || 1));
	$virus{Ext_Ext_mean} = sprintf("%.2f", $virus{Ext_Ext} / ($virus{Ext_Ext_bytes} || 1));
	$virus{'Int_Int_bytes'} = sprintf("%.2f", $virus{'Int_Int_bytes'}/$SIZE_UNIT);
	$virus{'Int_Ext_bytes'} = sprintf("%.2f", $virus{'Int_Ext_bytes'}/$SIZE_UNIT);
	$virus{'Ext_Ext_bytes'} = sprintf("%.2f", $virus{'Ext_Ext_bytes'}/$SIZE_UNIT);
	$virus{'Ext_Int_bytes'} = sprintf("%.2f", $virus{'Ext_Int_bytes'}/$SIZE_UNIT);

	if (!$virus{total_inbound} && !$virus{total_outbound}) {
		print qq{<table align="center"><tr><th colspan="2" class="thhead">$TRANSLATE{'No dataset'}</th></tr></table>};
		return;
	}

        print qq {
<table align="center">
<tr><th colspan="4" class="thhead">$TRANSLATE{'Viruses flows'}</th></tr>
<tr><td class="tdhead">&nbsp;</td><td class="tdhead">$TRANSLATE{'Messages'}</td><td class="tdhead">$TRANSLATE{'Size'} ($TRANSLATE{$CONFIG{'SIZE_UNIT'}})</td><td class="tdhead">$TRANSLATE{'Mean'}</td></tr>
<tr><td class="tdtop">$TRANSLATE{'Incoming'}</td><td class="tdtopnr">$virus{inbound}</td><td class="tdtopnr">$virus{inbound_bytes}</td><td class="tdtopnr">$virus{inbound_mean}</td></tr>
<tr><td class="tdtop">$TRANSLATE{'Local incoming'}</td><td class="tdtopnr">$virus{local_inbound}</td><td class="tdtopnr">$virus{local_inbound_bytes}</td><td class="tdtopnr">$virus{local_inbound_mean}</td></tr>
<tr><th>$TRANSLATE{'Total incoming'}</th><th align="right">$virus{total_inbound}</th><th align="right">$virus{total_inbound_bytes}</th><th align="right">$virus{total_inbound_mean}</th></tr>
<tr><td class="tdtop">$TRANSLATE{'Outgoing'}</td><td class="tdtopnr">$virus{outbound}</td><td class="tdtopnr">$virus{outbound_bytes}</td><td class="tdtopnr">$virus{outbound_mean}</td></tr>
<tr><td class="tdtop">$TRANSLATE{'Local delivery'}</td><td class="tdtopnr">$virus{local_outbound}</td><td class="tdtopnr">$virus{local_outbound_bytes}</td><td class="tdtopnr">$virus{local_outbound_mean}</td></tr>
<tr><th>$TRANSLATE{'Total outgoing'}</th><th align="right">$virus{total_outbound}</th><th align="right">$virus{total_outbound_bytes}</th><th align="right">$virus{total_outbound_mean}</th></tr>
<tr><td colspan="4" align="center"><img src=\"grafit.cgi?ttfont=$CONFIG{'TTFONT'}&labels=$virus{lbls}&values=$virus{values}&title=$TRANSLATE{'Viruses%20Flow'}&width=400&height=200&x_label=$x_label&y_label=$TRANSLATE{'Number%20of%20virus'}\"></td></tr>
};
	if ($CONFIG{SHOW_DIRECTION}) {
		print qq{
<tr><th colspan="4" class="thhead">$TRANSLATE{'Viruses delivery flows'}</th></tr>
<tr><td class="tdhead">&nbsp;</td><td class="tdhead">$TRANSLATE{'Messages'}</td><td class="tdhead">$TRANSLATE{'Size'} ($TRANSLATE{$CONFIG{'SIZE_UNIT'}})</td><td class="tdhead">$TRANSLATE{'Mean'}</td></tr>
<tr><td class="tdtop">$TRANSLATE{'Internet -> Internal'}</td><td class="tdtopnr">$virus{'Ext_Int'}</td><td class="tdtopnr">$virus{'Ext_Int_bytes'}</td><td class="tdtopnr">$virus{Ext_Int_mean}</td></tr>
<tr><td class="tdtop">$TRANSLATE{'Internet -> Internet'}</td><td class="tdtopnr">$virus{'Ext_Ext'}</td><td class="tdtopnr">$virus{'Ext_Ext_bytes'}</td><td class="tdtopnr">$virus{Ext_Ext_mean}</td></tr>
<tr><td class="tdtop">$TRANSLATE{'Internal -> Internal'}</td><td class="tdtopnr">$virus{'Int_Int'}</td><td class="tdtopnr">$virus{'Int_Int_bytes'}</td><td class="tdtopnr">$virus{Int_Int_mean}</td></tr>
<tr><td class="tdtop">$TRANSLATE{'Internal -> Internet'}</td><td class="tdtopnr">$virus{'Int_Ext'}</td><td class="tdtopnr">$virus{'Int_Ext_bytes'}</td><td class="tdtopnr">$virus{Int_Ext_mean}</td></tr>
};
	}
	print "</table>\n";
}

sub compute_dsnflow
{
	my ($hostname, $mailbox) = @_;

	my %period_stat = ();
	foreach my $id (keys %STATS) {
		next if ($DOMAIN && ($STATS{$STATS{$id}{srcid}}{sender} !~ /$DOMAIN/) && !grep(/$DOMAIN/, @{$STATS{$id}{rcpt}}));
		if (exists $STATS{$id}{dsnstatus}) {
			$period_stat{dsn}{$STATS{$id}{idx_dsn}}++;
			for (my $i = 0; $i <= $#{$STATS{$id}{status}}; $i++) {
				next if ($mailbox && ($STATS{$id}{rcpt}[$i] !~ /$mailbox\@/) );
				if ($STATS{$id}{status}[$i] eq 'Sent') {
					my $direction = &set_direction($id, $i, $hostname);
					$dsn{$direction}++;
					if ($direction =~ /_Int$/) {
						$dsn{local_outbound}++;
					} else {
						$dsn{outbound}++;
					}
				} else {
					$dsn{error}++;
				}
			}
		}
	}
	%STATS = ();
	return %period_stat;
}

sub summarize_dsnflow
{
	my ($begin, $end, %period_stat) = @_;

	$dsn{outbound} ||= 0;
	$dsn{local_outbound} ||= 0;
	$dsn{total_outbound} = $dsn{outbound} + $dsn{local_outbound};
	$dsn{error} ||= 0;
	if (!exists $dsn{lbls}) {
		if ($end ne '60') {
			foreach ("$begin" .. "$end") {
				$dsn{lbls} .= "$_:";
				$dsn{values} .= ($period_stat{dsn}{"$_"} || 0) . ':';
			}
		} else {
			for (my $i = 5; $i <= 60; $i += 5) {
				$dsn{lbls} .= sprintf("%02d", $i) . ":";
				my $count = 0;
				foreach my $b (keys %{$period_stat{dsn}}) {
					if ( ($b < $i) && ($b >= ($i - 5)) ) {
						$count += $period_stat{dsn}{"$b"};
					}
				}
				$dsn{values} .= ($count || 0) . ':';
			}
		}
	}
	$dsn{lbls} =~ s/:$//;
	$dsn{values} =~ s/:$//;

	$dsn{'Int_Int'} ||= 0;
	$dsn{'Int_Ext'} ||= 0;
}

sub display_dsnflow
{
	my ($x_label) = @_;

	# DSN flow
	my $total_dsn = $dsn{total_outbound} + $dsn{error};
	if (!$total_dsn) {
		print qq{<table align="center"><tr><th colspan="2" class="thhead">$TRANSLATE{'No dataset'}</th></tr></table>};
		return;
	}

        print qq {
<table align="center">
<tr><th colspan="2" class="thhead">$TRANSLATE{'DSN flows'}</th></tr>
<tr><td class="tdhead">&nbsp;</td><td class="tdhead">$TRANSLATE{'Messages'}</td></tr>
<tr><td class="tdtop">$TRANSLATE{'Outgoing'}</td><td class="tdtopnr">$dsn{total_outbound}</td></tr>
<tr><td class="tdtop">$TRANSLATE{'In Error'}</td><td class="tdtopnr">$dsn{error}</td></tr>
<tr><th>$TRANSLATE{'Total'}</th><th align="right">$total_dsn</th></tr>
<tr><td colspan="2" align="center"><img src=\"grafit.cgi?ttfont=$CONFIG{'TTFONT'}&labels=$dsn{lbls}&values=$dsn{values}&title=$TRANSLATE{'DSN%20Flow'}&width=400&height=200&x_label=$x_label&y_label=$TRANSLATE{'Number%20of%20dsn'}\"></td></tr>
};
	if ($CONFIG{SHOW_DIRECTION}) {
		print qq{
<tr><th colspan="2" class="thhead">$TRANSLATE{'DSN delivery flows'}</th></tr>
<tr><td class="tdhead">&nbsp;</td><td class="tdhead">$TRANSLATE{'Messages'}</td></tr>
<tr><td class="tdtop">$TRANSLATE{'Internal -> Internal'}</td><td class="tdtopnr">$dsn{'Int_Int'}</td></tr>
<tr><td class="tdtop">$TRANSLATE{'Internal -> Internet'}</td><td class="tdtopnr">$dsn{'Int_Ext'}</td></tr>
};
	}
	print "</table>\n";

}

sub compute_rejectflow
{
	my ($mailbox) = @_;

	my %period_stat = ();
	foreach my $id (keys %STATS) {
		next if ($DOMAIN && ($STATS{$id}{sender} !~ /$DOMAIN/) && !grep(/$DOMAIN/, @{$STATS{$id}{rcpt}}));
		if (exists $STATS{$id}{rule}) {
			next if ($id =~ /r\d{17}/);
			$period_stat{reject}{$STATS{$id}{idx_reject}}++;
			$GLOBAL_STATUS{Rejected}++;
			$GLOBAL_STATUS{Rejected_bytes} += $STATS{$id}{size};
			if ($STATS{$id}{sender_relay} ne 'localhost') {
				$reject{local_inbound}++;
				$reject{local_inbound_bytes} += $STATS{$id}{size};
			 } elsif ($CONFIG{MAIL_HUB} && $STATS{$id}{sender_relay} =~ /$CONFIG{MAIL_HUB}/) {
				$reject{local_inbound}++;
				$reject{local_inbound_bytes} += $STATS{$id}{size};
			} else {
				$reject{inbound}++;
				$reject{inbound_bytes} += ($STATS{$id}{size} || 0);
			}
		}
		if (exists $STATS{$id}{error}) {
			$GLOBAL_STATUS{SysErr}++;
			$GLOBAL_STATUS{SysErr_bytes} += $STATS{$id}{size};
			if ($STATS{$id}{sender_relay} ne 'localhost') {
				$err{local_inbound}++;
				$err{local_inbound_bytes} += $STATS{$id}{size};
			 } elsif ($CONFIG{MAIL_HUB} && $STATS{$id}{sender_relay} =~ /$CONFIG{MAIL_HUB}/) {
				$err{local_inbound}++;
				$err{local_inbound_bytes} += $STATS{$id}{size};
			} else {
				$err{inbound}++;
				$err{inbound_bytes} += $STATS{$id}{size};
			}
		}
	}
	%STATS = ();
	return %period_stat;
}

sub summarize_rejectflow
{
	my ($begin, $end, %period_stat) = @_;

	$reject{inbound} ||= 0;
	$reject{local_inbound} ||= 0;
	$reject{total_inbound} = $reject{inbound} + $reject{local_inbound};
	$reject{total_inbound_bytes} = $reject{inbound_bytes} + $reject{local_inbound_bytes};
	$err{inbound} ||= 0;
	$err{local_inbound} ||= 0;
	$err{total_inbound} = $err{inbound} + $err{local_inbound};
	$err{total_inbound} = $err{inbound} + $err{local_inbound};
	$err{total_inbound_bytes} = $err{inbound_bytes} + $err{local_inbound_bytes};
	$reject{total_inbound_bytes} = sprintf("%.2f", $reject{total_inbound_bytes}/$SIZE_UNIT);
	$reject{inbound_bytes} = sprintf("%.2f", $reject{inbound_bytes}/$SIZE_UNIT);
	$reject{local_inbound_bytes} = sprintf("%.2f", $reject{local_inbound_bytes}/$SIZE_UNIT);
	$err{total_inbound_bytes} = sprintf("%.2f", $err{total_inbound_bytes}/$SIZE_UNIT);
	$err{inbound_bytes} = sprintf("%.2f", $err{inbound_bytes}/$SIZE_UNIT);
	$err{local_inbound_bytes} = sprintf("%.2f", $err{local_inbound_bytes}/$SIZE_UNIT);
	
}

sub display_rejectflow
{
	my ($x_label) = @_;

	$reject{inbound_mean} = sprintf("%.2f", $reject{inbound_bytes} / ($reject{inbound} || 1));
	$reject{local_inbound_mean} = sprintf("%.2f", $reject{local_inbound_bytes} / ($reject{local_inbound} || 1));
	$reject{total_inbound_mean} = sprintf("%.2f", $reject{total_inbound_bytes} / ($reject{total_inbound} || 1));

	if (!$reject{total_inbound} && !$err{total_inbound}) {
		print qq{<table align="center"><tr><th colspan="2" class="thhead">$TRANSLATE{'No dataset'}</th></tr></table>};
		return;
	}

	print qq {
<table align="center">
<tr><th colspan="4" class="thhead">$TRANSLATE{'Rejection flows'}</th></tr>
<tr><td class="tdhead">&nbsp;</td><td class="tdhead">$TRANSLATE{'Messages'}</td><td class="tdhead">$TRANSLATE{'Size'} ($TRANSLATE{$CONFIG{'SIZE_UNIT'}})</td><td class="tdhead">$TRANSLATE{'Mean'}</td></tr>
<tr><td class="tdtop">$TRANSLATE{'Incoming'}</td><td class="tdtopnr">$reject{inbound}</td><td class="tdtopnr">$reject{inbound_bytes}</td><td class="tdtopnr">$reject{inbound_mean}</td></tr>
<tr><td class="tdtop">$TRANSLATE{'Local incoming'}</td><td class="tdtopnr">$reject{local_inbound}</td><td class="tdtopnr">$reject{local_inbound_bytes}</td><td class="tdtopnr">$reject{local_inbound_mean}</td></tr>
<tr><th>$TRANSLATE{'Total incoming'}</th><th align="right">$reject{total_inbound}</th><th align="right">$reject{total_inbound_bytes}</th><th align="right">$reject{total_inbound_mean}</th</tr>
<tr><td colspan="4">&nbsp;</td></tr>
<tr><td colspan="4">&nbsp;</td></tr>
<tr><td colspan="4">&nbsp;</td></tr>
};
	$err{inbound_mean} = sprintf("%.2f", $err{inbound_bytes} / ($err{inbound} || 1));
	$err{local_inbound_mean} = sprintf("%.2f", $err{local_inbound_bytes} / ($err{local_inbound} || 1));
	$err{total_inbound_mean} = sprintf("%.2f", $err{total_inbound_bytes} / ($err{total_inbound} || 1));

	print qq {<tr><th colspan="4" class="thhead">$TRANSLATE{'Syserr flows'}</th></tr>
<tr><td class="tdhead">&nbsp;</td><td class="tdhead">$TRANSLATE{'Messages'}</td><td class="tdhead">$TRANSLATE{'Size'} ($TRANSLATE{$CONFIG{'SIZE_UNIT'}})</td><td class="tdhead">$TRANSLATE{'Mean'}</td></tr>
<tr><td class="tdtop">$TRANSLATE{'Incoming'}</td><td class="tdtopnr">$err{inbound}</td><td class="tdtopnr">$err{inbound_bytes}</td><td class="tdtopnr">$err{inbound_mean}</td></tr>
<tr><td class="tdtop">$TRANSLATE{'Local incoming'}</td><td class="tdtopnr">$err{local_inbound}</td><td class="tdtopnr">$err{local_inbound_bytes}</td><td class="tdtopnr">$err{local_inbound_mean}</td></tr>
<tr><th>$TRANSLATE{'Total incoming'}</th><th align="right">$err{total_inbound}</th><th align="right">$err{total_inbound_bytes}</th><th align="right">$err{total_inbound_mean}</th></tr>
</table>
};

}

sub compute_statusflow
{
	my ($mailbox) = @_;

	foreach my $id (keys %STATS) {
		next if ($DOMAIN && ($STATS{$id}{sender} !~ /$DOMAIN/) && !grep(/$DOMAIN/, @{$STATS{$id}{rcpt}}));
		for (my $i = 0; $i <= $#{$STATS{$id}{status}}; $i++) {
			next if (!$STATS{$id}{rcpt}[$i]);
			next if ($mailbox && ($STATS{$id}{rcpt}[$i] !~ /$mailbox\@/) );
			$GLOBAL_STATUS{"$STATS{$id}{status}[$i]"}++;
			$GLOBAL_STATUS{"$STATS{$id}{status}[$i]" . '_bytes'} += $STATS{$id}{size};
			if ($STATS{$id}{status}[$i] eq 'Sent') {
				if (exists $STATS{$id}{spam}) {
					$GLOBAL_STATUS{Spam_Sent}++;
				} elsif (exists $STATS{$id}{virus}) {
					$GLOBAL_STATUS{Virus_Sent}++;
				}
			}
		}
		if (exists $STATS{$id}{spam}) {
			$GLOBAL_STATUS{Spam}++;
			$GLOBAL_STATUS{Spam_bytes} += $STATS{$id}{size};
		}
		if (exists $STATS{$id}{virus}) {
			$GLOBAL_STATUS{Virus}++;
			$GLOBAL_STATUS{Virus_bytes} += $STATS{$id}{size};
		}
		if (exists $STATS{$id}{rule}) {
			next if ($id =~ /r\d{17}/);
			$GLOBAL_STATUS{Rejected}++;
			$GLOBAL_STATUS{Rejected_bytes} += $STATS{$id}{size};
		}
		if (exists $STATS{$id}{error}) {
			$GLOBAL_STATUS{SysErr}++;
			$GLOBAL_STATUS{SysErr_bytes} += $STATS{$id}{size};
		}
	}
}

sub display_statusflow
{
	my ($x_label) = @_;

        delete $GLOBAL_STATUS{'Queued'};
        delete $GLOBAL_STATUS{'Queued_bytes'};

	if (scalar keys %GLOBAL_STATUS == 0) {
		print qq{<table align="center"><tr><th colspan="2" class="thhead">$TRANSLATE{'No dataset'}</th></tr></table>};
		return;
	}

        print qq{
<table>
<tr><th colspan="4" class="thhead">$TRANSLATE{'Messaging Status'}</th></tr>
<tr><td class="tdhead">&nbsp;</td><td class="tdhead">$TRANSLATE{'Messages'}</td><td class="tdhead">$TRANSLATE{'Size'} ($TRANSLATE{$CONFIG{'SIZE_UNIT'}})</td><td class="tdhead">$TRANSLATE{'Percentage'}</td></tr>
};
        my $delivery_global_total = 1;
        foreach (sort {$GLOBAL_STATUS{$b} <=> $GLOBAL_STATUS{$a}} keys %GLOBAL_STATUS) {
		next if ( ($_ eq '') || /Command rejected/);
                next if (/_bytes/ || /virus /);
		if (/_Sent$/) {
			$delivery_global_total -= $GLOBAL_STATUS{$_};
			next
		}
                $delivery_global_total += $GLOBAL_STATUS{$_};
        }
        my $delivery_total = $GLOBAL_STATUS{Sent} || 1;
        my $delivery_total_bytes = $GLOBAL_STATUS{Sent_bytes} || 1;
        my $total_percent = 0;
	my %status = ();
	my $piecount = 0;
        foreach my $s (sort {$GLOBAL_STATUS{$b} <=> $GLOBAL_STATUS{$a}} keys %GLOBAL_STATUS) {
		next if ( ($s eq '') || ($s =~ /Command rejected/));
                next if ( ($s =~ /_bytes/) || ($s =~ /virus /) );
                my $percent = sprintf("%.2f", ($GLOBAL_STATUS{$s}/$delivery_global_total) * 100);
                $total_percent += $GLOBAL_STATUS{$s};
                if ($s =~ /^(\d{3}) \d\.(\d\.\d)$/) {
                        if (exists $SMTP_ERROR_CODE{$1} || exists $ESMTP_ERROR_CODE{$2}) {
                                print "<tr><td class=\"tdtopn\">$s ",$SMTP_ERROR_CODE{$1} . " " . $ESMTP_ERROR_CODE{$2} , "</td>";
                        } else {
                                print "<tr><td class=\"tdtopn\">$s</td>";
                        }
                } else {
                        print "<tr><td class=\"tdtopn\">$s</td>";
                }
                print "<td class=\"tdtopnr\">$GLOBAL_STATUS{$s}</td><td class=\"tdtopnr\">", sprintf("%.2f", $GLOBAL_STATUS{$s . '_bytes'}/$SIZE_UNIT), "</td><td class=\"tdtopnr\">$percent %</td></tr>\n";
		if ( ($piecount < $MAXPIECOUNT) && ($percent > 1)) {
			$status{lbls} .= "$s ($percent %):";
			$status{values} .= "$percent:";
			$piecount++;
		}
        }
	$status{lbls} =~ s/:$//;
	$status{values} =~ s/:$//;
        print qq{
<tr><td colspan="4" align="center">&nbsp;</td></tr>
<tr><td colspan="4" align="center"><img src=\"grafit.cgi?ttfont=$CONFIG{'TTFONT'}&type=pie&labels=$status{lbls}&values=$status{values}&title=$TRANSLATE{'Messaging%20status'}&width=500&height=300\"></td></tr>
</table>
};

}

sub compute_authflow
{
	my ($mailbox) = @_;

	return if ($DOMAIN);

	my %period_stat = ();
	foreach my $id (keys %AUTH) {
		for (my $i = 0; $i <= $#{$AUTH{$id}{mech}}; $i++) {
			$period_stat{auth}{$AUTH{$id}{type}[$i]}{$AUTH{$id}{idx}[$i]}++;
			$auth{$AUTH{$id}{type}[$i]}{$AUTH{$id}{mech}[$i]}++;
		}
	}
	%AUTH = ();
	return %period_stat;
}

sub summarize_authflow
{
	my ($begin, $end, %period_stat) = @_;

	foreach my $type (keys %{$period_stat{auth}}) {
		if (!exists $auth{$type}{lbls}) {
			if ($end ne '60') {
				foreach ("$begin" .. "$end") {
					$auth{$type}{lbls} .= "$_:";
					$auth{$type}{values} .= ($period_stat{auth}{$type}{"$_"} || 0) . ':';
				}
			} else {
				for (my $i = 5; $i <= 60; $i += 5) {
					$auth{$type}{lbls} .= sprintf("%02d", $i) . ":";
					my $count = 0;
					foreach my $b (keys %{$period_stat{auth}{$type}}) {
						if ( ($b < $i) && ($b >= ($i - 5)) ) {
							$count += $period_stat{auth}{$type}{"$b"};
						}
					}
					$auth{$type}{values} .= ($count || 0) . ':';
				}
			}
		}
		$auth{$type}{lbls} =~ s/:$//;
		$auth{$type}{values} =~ s/:$//;
	}

}

sub display_authflow
{
	my ($x_label) = @_;

	if (scalar keys %auth) {
		print qq{
};
		foreach my $type (sort keys %auth) {
			print qq{
<p>&nbsp;</p>
<table>
<tr><th colspan="2" class="thhead">$TRANSLATE{'SMTP Auth'}: $type</th></tr>
<tr><td class="tdhead">$TRANSLATE{'Mechanism'}</td><td class=\"tdhead\">$TRANSLATE{'Count'}</td></tr>
};
			my $total = 0;
			foreach my $mech (sort keys %{$auth{$type}}) {
				next if ($mech =~ /(lbls|values|x_label)/);
				print "<td class=\"tdtopnr\">$mech</td><td class=\"tdtopnr\">$auth{$type}{$mech}</td></tr>\n";
				$total += $auth{$type}{$mech};
				
			}
			print "<tr><th>$TRANSLATE{'Total'}</th><th align=\"right\">$total</th></tr>\n";
			print "<tr><td colspan=\"2\" align=\"center\"><img src=\"grafit.cgi?ttfont=$CONFIG{'TTFONT'}&labels=$auth{$type}{lbls}&values=$auth{$type}{values}&title=$TRANSLATE{'Authent%20Flow'}:%20$type&width=400&height=200&x_label=$x_label&y_label=$TRANSLATE{'Number%20of%20connection'}\"></td></tr>\n";
		}
		print "</table>\n";
	} else {
		print qq{<table align="center"><tr><th colspan="2" class="thhead">$TRANSLATE{'No dataset'}</th></tr></table>};
	}

}

sub detail_link
{
	my ($hostname, $date, $type, $peri, $name, $hour) = @_;

	$name ||= '<>';

	my ($sec,$min,$h,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time);
	$mon++;
	$date =~ /\d{4}(\d{2})/;
	my $month = $1;
	my @files = ();
	my $path = $CONFIG{OUT_DIR} . '/' . $hostname . '/' . $date;
	$path =~ s/(\d{4})(\d{2})(\d{2})$/$1\/$2\/$3\//;
	if ($date !~ /00$/) {
		if (not opendir(DIR, "$path")) {
			&logerror("Can't open directory $CONFIG{OUT_DIR}: $!\n");
		} else {
			@files = grep { /.*\.dat$/ } readdir(DIR);
			closedir(DIR);
		}
	}
	# Return a link if we still have dat file.
	if ( ($date !~ /00$/) && ($#files >= 0) ) {
		my $tmpname = &decode_str($name);
		return "<a target=\"detail\" href=\"$ENV{SCRIPT_NAME}?host=$hostname&date=$date&hour=$hour&type=$type&peri=$peri&domain=$DOMAIN&search=" . $CGI->escape($name) . "\">" . $CGI->unescape(&decode_str($tmpname)) . "</a>";
	}

	return substr($CGI->unescape(&decode_str($name)), 0, 124);
}

sub compute_top_sender
{
	foreach my $id (keys %STATS) {
		next if ($DOMAIN && ($STATS{$id}{sender} !~ /$DOMAIN/) && !grep(/$DOMAIN/, @{$STATS{$id}{rcpt}}));
		$topsender{email}{$STATS{$id}{sender}}++;
		if ($STATS{$id}{sender} =~ /\@(.*)/) {
			$topsender{domain}{$1}++;
		} else {
			$topsender{domain}{$STATS{$id}{sender}}++;
		}
		$topsender{relay}{$STATS{$id}{sender_relay}}++;	
	}
	%STATS = ();
} 

sub display_top_sender
{
	my ($hostname, $date, $hour) = @_;

	# Top sender statistics
	my $topdomain = '';
	my $top = 0;
	foreach my $d (sort { $topsender{domain}{$b} <=> $topsender{domain}{$a} } keys %{$topsender{domain}}) {
		last if ($top == $CONFIG{TOP});
		$topdomain .= &detail_link($hostname,$date,'sender','domain',$d,$hour) . " ($topsender{domain}{$d})<br>";
		$top++;
	}
	delete $topsender{domain};
	my $totalrelay = 0;
	foreach my $d (keys %{$topsender{relay}}) {
		$totalrelay += $topsender{relay}{$d};
	}
	my $toprelay = '';
	$top = 0;
	my %relays = ();
	my $piecount = 0;
	foreach my $d (sort { $topsender{relay}{$b} <=> $topsender{relay}{$a} } keys %{$topsender{relay}}) {
		last if ($top == $CONFIG{TOP});
		my $percent = sprintf("%.2f", ($topsender{relay}{$d}*100)/$totalrelay);
		$toprelay .= &detail_link($hostname,$date,'sender','relay',$d,$hour) . " ($topsender{relay}{$d})<br>";
		if ( ($piecount < $MAXPIECOUNT) && ($percent > 1)) {
			$relays{lbls} .= "$d ($percent %):";
			$relays{values} .= "$percent:";
			$piecount++;
		}
		$top++;
	}
	delete $topsender{relay};
	$relays{lbls} =~ s/:$//;
	$relays{values} =~ s/:$//;
	if (exists $CONFIG{REPLACE_HOST}) {
		foreach my $pat (keys %{$CONFIG{REPLACE_HOST}}) {
			$toprelay =~ s/$pat/$CONFIG{REPLACE_HOST}{$pat}/g;
		}
	}
	my $topemail = '';
	$top = 0;
	if (!$CONFIG{ANONYMIZE}) {
		foreach my $d (sort { $topsender{email}{$b} <=> $topsender{email}{$a} } keys %{$topsender{email}}) {
			last if ($top == $CONFIG{TOP});
			$topemail .= &detail_link($hostname,$date,'sender','address',$d,$hour) . " ($topsender{email}{$d})<br>";
			$top++;
		}
	}
	%topsender = ();
	if (!$topdomain) {
		print qq{<table align="center"><tr><th colspan="2" class="thhead">$TRANSLATE{'No dataset'}</th></tr></table>};
		return;
	}

	if (!$CONFIG{ANONYMIZE}) {
		print qq {
<table align="left" width="100%">
<tr><th colspan="3" class="thhead">$TRANSLATE{'Senders Statistics'} (top $CONFIG{TOP})</th></tr>
<tr>
<td class="tdhead">$TRANSLATE{'Top Sender Domain'}</td>
<td class="tdhead">$TRANSLATE{'Top Sender Relay'}</td>
<td class="tdhead">$TRANSLATE{'Top Sender Address'}</td></tr>
<tr>
<td class="tdtopn" nowrap valign="top">$topdomain</td>
<td class="tdtopn"  nowrap valign="top">$toprelay</td>
<td class="tdtopn"  nowrap valign="top">$topemail</td>
</tr>
<tr><td colspan="3" align="center">&nbsp;</td></tr>
<tr><td colspan="3" align="center"><img src=\"grafit.cgi?ttfont=$CONFIG{'TTFONT'}&type=pie&labels=$relays{lbls}&values=$relays{values}&title=$TRANSLATE{'Top%20Sender%20Relay'}&width=700&height=500\"></td></tr>
};
	} else {
		print qq {
<table align="center">
<tr><th colspan="2" class="thhead">$TRANSLATE{'Senders Statistics'}</th></tr>
<tr>
<td class="tdhead">$TRANSLATE{'Top Sender Domain'}</td>
<td class="tdhead">$TRANSLATE{'Top Sender Relay'}</td></tr>
<tr>
<td class="tdtopn" nowrap valign="top">$topdomain</td>
<td class="tdtopn" nowrap valign="top">$toprelay</td>
</tr>
<tr><td colspan="2" align="center">&nbsp;</td></tr>
<tr><td colspan="2" align="center"><img src=\"grafit.cgi?ttfont=$CONFIG{'TTFONT'}&type=pie&labels=$relays{lbls}&values=$relays{values}&title=$TRANSLATE{'Top%20Sender%20Relay'}&width=700&height=500\"></td></tr>
};
        }
	print "</table>\n";

}

sub compute_top_recipient
{

	foreach my $id (keys %STATS) {
		if ($DOMAIN) {
			if ($STATS{$id}{sender} =~ /$DOMAIN/) {
				for (my $i = 0; $i <= $#{$STATS{$id}{rcpt}}; $i++) {
					next if ($STATS{$id}{status}[$i] ne 'Sent');
					$toprcpt{email}{$STATS{$id}{rcpt}[$i]}++;
					$STATS{$id}{rcpt}[$i] =~ s/^.*\@//;
					$toprcpt{domain}{$STATS{$id}{rcpt}[$i]}++;
					$toprcpt{relay}{$STATS{$id}{rcpt_relay}[$i]}++;
				}
			} elsif (grep(/$DOMAIN/, @{$STATS{$id}{rcpt}})) {
				for (my $i = 0; $i <= $#{$STATS{$id}{rcpt}}; $i++) {
					next if ($STATS{$id}{status}[$i] ne 'Sent');
					$toprcpt{email}{$STATS{$id}{rcpt}[$i]}++;
					$STATS{$id}{rcpt}[$i] =~ s/^.*\@//;
					$toprcpt{domain}{$STATS{$id}{rcpt}[$i]}++;
					$toprcpt{relay}{$STATS{$id}{rcpt_relay}[$i]}++;
				}
			}
		} else {
			for (my $i = 0; $i <= $#{$STATS{$id}{rcpt}}; $i++) {
				next if ($STATS{$id}{status}[$i] ne 'Sent');
				$toprcpt{email}{$STATS{$id}{rcpt}[$i]}++;
				$STATS{$id}{rcpt}[$i] =~ s/^.*\@//;
				$toprcpt{domain}{$STATS{$id}{rcpt}[$i]}++;
				$toprcpt{relay}{$STATS{$id}{rcpt_relay}[$i]}++;
			}
		}
	}
	%STATS = ();
} 

sub display_top_recipient
{
	my ($hostname, $date, $hour) = @_;

	# Top recipient statistics
	my $topdomain = '';
	my $top = 0;
	foreach my $d (sort { $toprcpt{domain}{$b} <=> $toprcpt{domain}{$a} } keys %{$toprcpt{domain}}) {
		last if ($top == $CONFIG{TOP});
		$topdomain .= &detail_link($hostname,$date,'recipient','domain',$d,$hour) . " ($toprcpt{domain}{$d})<br>";
		$top++;
	}
	delete $toprcpt{domain};
	my $totalrelay = 0;
	foreach my $d (keys %{$toprcpt{relay}}) {
		$totalrelay += $toprcpt{relay}{$d};
	}
	my $toprelay = '';
	$top = 0;
	my %relays = ();
	my $piecount = 0;
	foreach my $d (sort { $toprcpt{relay}{$b} <=> $toprcpt{relay}{$a} } keys %{$toprcpt{relay}}) {
		last if ($top == $CONFIG{TOP});
		my $percent = sprintf("%.2f", ($toprcpt{relay}{$d}*100)/$totalrelay);
		$toprelay .= &detail_link($hostname,$date,'recipient','relay',$d,$hour) . " ($toprcpt{relay}{$d})<br>";
		if ( ($piecount < $MAXPIECOUNT) && ($percent > 1)) {
			$relays{lbls} .= "$d ($percent %):";
			$relays{values} .= "$percent:";
			$piecount++;
		}
		$top++;
	}
	delete $toprcpt{relay};
	if (exists $CONFIG{REPLACE_HOST}) {
		foreach my $pat (keys %{$CONFIG{REPLACE_HOST}}) {
			$toprelay =~ s/$pat/$CONFIG{REPLACE_HOST}{$pat}/g;
		}
	}
	my $topemail = '';
	$top = 0;
	if (!$CONFIG{ANONYMIZE}) {
		foreach my $d (sort { $toprcpt{email}{$b} <=> $toprcpt{email}{$a} } keys %{$toprcpt{email}}) {
			last if ($top == $CONFIG{TOP});
			$topemail .= &detail_link($hostname,$date,'recipient','address',$d,$hour) . " ($toprcpt{email}{$d})<br>";
			$top++;
		}
	}
	%toprcpt = ();
	if (!$topdomain) {
		print qq{<table align="center"><tr><th colspan="2" class="thhead">$TRANSLATE{'No dataset'}</th></tr></table>};
		return;
	}
	if (!$CONFIG{ANONYMIZE}) {
		print qq {
<table align="left" width="100%">
<tr><td colspan="3"><p>&nbsp;</p></td></tr>
<tr><th colspan="3" class="thhead">$TRANSLATE{'Recipients Statistics'} (top $CONFIG{TOP})</th></tr>
<tr>
<td class="tdhead">$TRANSLATE{'Top Recipient Domain'}</td>
<td class="tdhead">$TRANSLATE{'Top Recipient Relay'}</td>
<td class="tdhead">$TRANSLATE{'Top Recipients Address'}</td>
<tr>
<td class="tdtopn" nowrap valign="top">$topdomain</td>
<td class="tdtopn" nowrap valign="top">$toprelay</td>
<td class="tdtopn" nowrap valign="top">$topemail</td>
</tr>
<tr><td colspan="3" align="center">&nbsp;</td></tr>
<tr><td colspan="3" align="center"><img src=\"grafit.cgi?ttfont=$CONFIG{'TTFONT'}&type=pie&labels=$relays{lbls}&values=$relays{values}&title=$TRANSLATE{'Top%20Recipient%20Relay'}&width=700&height=500\"></td></tr>

};
	} else {
		print qq {
<table align="left" width="100%">
<tr><td colspan="2"><p>&nbsp;</p></td></tr>
<tr><th colspan="2" class="thhead">$TRANSLATE{'Recipients Statistics'}</th></tr>
<tr>
<td class="tdhead">$TRANSLATE{'Top Recipient Domain'}</td>
<td class="tdhead">$TRANSLATE{'Top Recipient Relay'}</td>
<tr>
<td class="tdtopn" nowrap valign="top">$topdomain</td>
<td class="tdtopn" nowrap valign="top">$toprelay</td>
</tr>
<tr><td colspan="2" align="center">&nbsp;</td></tr>
<tr><td colspan="2" align="center"><img src=\"grafit.cgi?ttfont=$CONFIG{'TTFONT'}&type=pie&labels=$relays{lbls}&values=$relays{values}&title=$TRANSLATE{'Top%20Recipient%20Relay'}&width=700&height=500\"></td></tr>
};
	}

	print "</td></tr></table>\n";
}

sub compute_top_spam
{

	foreach my $id (keys %STATS) {
		next if ($DOMAIN && ($STATS{$id}{sender} !~ /$DOMAIN/) && !grep(/$DOMAIN/, @{$STATS{$id}{rcpt}}));
		if (exists $STATS{$id}{spam}) {
			$topspam{sender}{$STATS{$id}{sender}}++;
			$STATS{$id}{sender} =~ s/^.*\@//;
			$topspam{domain}{$STATS{$id}{sender}}++;
			$topspam{sender_relay}{$STATS{$id}{sender_relay}}++;
			$topspam{rule}{$STATS{$id}{spam}}++;
			for (my $i = 0; $i <= $#{$STATS{$id}{rcpt}}; $i++) {
				$topspam{rcpt}{$STATS{$id}{rcpt}[$i]}++;
			}
		}
	}
	%STATS = ();
} 

sub display_top_spam
{
	my ($hostname, $date, $hour) = @_;

	# Top spam statistics
	my $toprule = '';
	my $top = 0;
	foreach my $d (sort { $topspam{rule}{$b} <=> $topspam{rule}{$a} } keys %{$topspam{rule}}) {
		last if ($top == $CONFIG{TOP});
		$toprule .= &detail_link($hostname,$date,'spam','rule',$d,$hour) . " ($topspam{rule}{$d})<br>";
		$top++;
	}
	delete $topspam{rule};
	my $topdomain = '';
	$top = 0;
	foreach my $d (sort { $topspam{domain}{$b} <=> $topspam{domain}{$a} } keys %{$topspam{domain}}) {
		last if ($top == $CONFIG{TOP});
		$topdomain .= &detail_link($hostname,$date,'spam','domain',$d,$hour) . " ($topspam{domain}{$d})<br>";
		$top++;
	}
	delete $topspam{domain};
	my $toprelay = '';
	$top = 0;
	foreach my $d (sort { $topspam{sender_relay}{$b} <=> $topspam{sender_relay}{$a} } keys %{$topspam{sender_relay}}) {
		last if ($top == $CONFIG{TOP});
		$toprelay .= &detail_link($hostname,$date,'spam','relay',$d,$hour) . " ($topspam{sender_relay}{$d})<br>";
		$top++;
	}
	delete $topspam{sender_relay};
	if (exists $CONFIG{REPLACE_HOST}) {
		foreach my $pat (keys %{$CONFIG{REPLACE_HOST}}) {
			$toprelay =~ s/$pat/$CONFIG{REPLACE_HOST}{$pat}/g;
		}
	}
	my $topemail = '';
	$top = 0;
	if (!$CONFIG{ANONYMIZE}) {
		foreach my $d (sort { $topspam{sender}{$b} <=> $topspam{sender}{$a} } keys %{$topspam{sender}}) {
			last if ($top == $CONFIG{TOP});
			$topemail .= &detail_link($hostname,$date,'spam','sender',$d,$hour) . " ($topspam{sender}{$d})<br>";
			$top++;
		}
	}
	delete $topspam{sender};
	my $topdest = '';
	$top = 0;
	if (!$CONFIG{ANONYMIZE}) {
		foreach my $d (sort { $topspam{rcpt}{$b} <=> $topspam{rcpt}{$a} } keys %{$topspam{rcpt}}) {
			last if ($top == $CONFIG{TOP});
			next if (($d eq '') || ($d eq '<>'));
			$topdest .= &detail_link($hostname,$date,'spam','recipient',$d,$hour) . " ($topspam{rcpt}{$d})<br>";
			$top++;
		}
	}
	%topspam = ();
	if ($toprule) {
		print qq {
<table align="left" width="100%">
<tr><td colspan="2"><p>&nbsp;</p></td></tr>
<tr><th colspan="2" class="thhead">$TRANSLATE{'Spam Statistics'} (top $CONFIG{TOP})</th></tr>
<tr><td class="tdhead">$TRANSLATE{'Top Spams Rules'}</td><td class="tdtopn">$toprule</td></tr>
<tr><td class="tdhead">$TRANSLATE{'Top Spammers Domain'}</td><td class="tdtopn">$topdomain</td></tr>
<tr><td class="tdhead">$TRANSLATE{'Top Spammers Relays'}</td><td class="tdtopn">$toprelay</td></tr>
};
		print qq{
<tr><td class="tdhead">$TRANSLATE{'Top Spammers Address'}</td><td class="tdtopn">$topemail</td></tr>
} if ($topemail);
		print qq{
<tr><td class="tdhead">$TRANSLATE{'Top Recipients Address'}</td><td class="tdtopn">$topdest</td></tr>
} if ($topdest);
		print "</table>\n";
	} else {
		print qq{<table align="center"><tr><th colspan="2" class="thhead">$TRANSLATE{'No dataset'}</th></tr></table>};
	}
}

sub compute_top_virus
{

	foreach my $id (keys %STATS) {
		next if ($DOMAIN && ($STATS{$id}{sender} !~ /$DOMAIN/) && !grep(/$DOMAIN/, @{$STATS{$id}{rcpt}}));
		if (exists $STATS{$id}{virus}) {
			$topvirus{sender}{$STATS{$id}{sender}}++;
			$topvirus{relay}{$STATS{$id}{sender_relay}}++;
			$topvirus{file}{$STATS{$id}{file}}++;
			$topvirus{virus}{$STATS{$id}{virus}}++;
			for (my $i = 0; $i <= $#{$STATS{$id}{status}}; $i++) {
				$topvirus{rcpt}{$STATS{$id}{rcpt}[$i]}++;
			}
		}
	}
	%STATS = ();
} 

sub display_top_virus
{
	my ($hostname, $date, $hour) = @_;

	print qq{<table align="center"><tr><td valign="center" align="center">};
	# Top virus statistics
	my $topvirus = '';
	my $top = 0;
	foreach my $d (sort { $topvirus{virus}{$b} <=> $topvirus{virus}{$a} } keys %{$topvirus{virus}}) {
		last if ($top == $CONFIG{TOP});
		$topvirus .= &detail_link($hostname,$date,'virus','virus',$d,$hour) . " ($topvirus{virus}{$d})<br>";
		$top++;
	}
	delete $topvirus{virus};
	my $topsender = '';
	$top = 0;
	if (!$CONFIG{ANONYMIZE}) {
		foreach my $d (sort { $topvirus{sender}{$b} <=> $topvirus{sender}{$a} } keys %{$topvirus{sender}}) {
			last if ($top == $CONFIG{TOP});
			$topsender .= &detail_link($hostname,$date,'virus','sender',$d,$hour) . " ($topvirus{sender}{$d})<br>";
			$top++;
		}
	}
	delete $topvirus{sender};
	my $toprelay = '';
	$top = 0;
	foreach my $d (sort { $topvirus{relay}{$b} <=> $topvirus{relay}{$a} } keys %{$topvirus{relay}}) {
		last if ($top == $CONFIG{TOP});
		$toprelay .= &detail_link($hostname,$date,'virus','relay',$d,$hour) . " ($topvirus{relay}{$d})<br>";
		$top++;
	}
	delete $topvirus{relay};
	if (exists $CONFIG{REPLACE_HOST}) {
		foreach my $pat (keys %{$CONFIG{REPLACE_HOST}}) {
			$toprelay =~ s/$pat/$CONFIG{REPLACE_HOST}{$pat}/g;
		}
	}
	my $topfile = '';
	$top = 0;
	foreach my $d (sort { $topvirus{file}{$b} <=> $topvirus{file}{$a} } keys %{$topvirus{file}}) {
		last if ($top == $CONFIG{TOP});
		$topfile .= &detail_link($hostname,$date,'virus','file',$d,$hour) . " ($topvirus{file}{$d})<br>";
		$top++;
	}
	delete $topvirus{file};
	my $topemail = '';
	$top = 0;
	if (!$CONFIG{ANONYMIZE}) {
		foreach my $d (sort { $topvirus{rcpt}{$b} <=> $topvirus{rcpt}{$a} } keys %{$topvirus{rcpt}}) {
			last if ($top == $CONFIG{TOP});
			$topemail .= &detail_link($hostname,$date,'virus','recipient',$d,$hour) . " ($topvirus{rcpt}{$d})<br>";
			$top++;
		}
	}
	if ($topvirus) {
		print qq {
<tr><td colspan="2"><p>&nbsp;</p></td></tr>
<tr><th colspan="2" class="thhead">$TRANSLATE{'Virus Statistics'} (top $CONFIG{TOP})</th></tr>
<tr><td class="tdhead">$TRANSLATE{'Top Virus'}</td><td class="tdtopn">$topvirus</td></tr>
};
		if (!$CONFIG{ANONYMIZE}) {
			print qq {
<tr><td class="tdhead">$TRANSLATE{'Top Virus Senders'}</td><td class="tdtopn">$topsender</td></tr>
};
		}
		print qq {
<tr><td class="tdhead">$TRANSLATE{'Top Virus Relays'}</td><td class="tdtopn">$toprelay</td></tr>
<tr><td class="tdhead">$TRANSLATE{'Top Virus Filenames'}</td><td class="tdtopn">$topfile</td></tr>
};
		if (!$CONFIG{ANONYMIZE}) {
			print qq {
<tr><td class="tdhead">$TRANSLATE{'Top Recipient Address'}</td><td class="tdtopn">$topemail</td></tr>
};
		}
	} else {
		print qq{<tr><th colspan="2" class="thhead">$TRANSLATE{'No dataset'}</th></tr>};
	}

	print "</table>\n";
}

sub compute_top_dsn
{

	foreach my $id (keys %STATS) {
		next if ($DOMAIN && ($STATS{$STATS{$id}{srcid}}{sender} !~ /$DOMAIN/) && !grep(/$DOMAIN/, @{$STATS{$id}{rcpt}}));
		if (exists $STATS{$id}{dsnstatus}) {
			$topdsn{dsnstatus}{$STATS{$id}{dsnstatus}}++;
			$topdsn{sender}{$STATS{$id}{sender}}++;
			$topdsn{relay}{$STATS{$id}{sender_relay}}++;
			for (my $i = 0; $i <= $#{$STATS{$id}{rcpt}}; $i++) {
				$topdsn{rcpt}{$STATS{$id}{rcpt}[$i]}++;
				$topdsn{status}{$STATS{$id}{status}[$i]}++;
			}
		}
	}
	%STATS = ();
} 

sub display_top_dsn
{
	my ($hostname, $date, $hour) = @_;

	print qq{<table align="center"><tr><td valign="center" align="center">};
	# Top dsn statistics
	my $topdsnstatus = '';
	my $top = 0;
	foreach my $d (sort { $topdsn{dsnstatus}{$b} <=> $topdsn{dsnstatus}{$a} } keys %{$topdsn{dsnstatus}}) {
		last if ($top == $CONFIG{TOP});
		$topdsnstatus .= &detail_link($hostname,$date,'dsn','dsnstatus',$d,$hour) . " ($topdsn{dsnstatus}{$d})<br>";
		$top++;
	}
	delete $topdsn{dsnstatus};

	my $topsender = '';
	$top = 0;
	if (!$CONFIG{ANONYMIZE}) {
		foreach my $d (sort { $topdsn{sender}{$b} <=> $topdsn{sender}{$a} } keys %{$topdsn{sender}}) {
			last if ($top == $CONFIG{TOP});
			$topsender .= "$d ($topdsn{sender}{$d})<br>";
			$top++;
		}
	}
	delete $topdsn{sender};
	my $toprelay = '';
	$top = 0;
	foreach my $d (sort { $topdsn{relay}{$b} <=> $topdsn{relay}{$a} } keys %{$topdsn{relay}}) {
		last if ($top == $CONFIG{TOP});
		$toprelay .= "$d ($topdsn{relay}{$d})<br>";
		$top++;
	}
	delete $topdsn{relay};
	if (exists $CONFIG{REPLACE_HOST}) {
		foreach my $pat (keys %{$CONFIG{REPLACE_HOST}}) {
			$toprelay =~ s/$pat/$CONFIG{REPLACE_HOST}{$pat}/g;
		}
	}

	my $toprcpt = '';
	$top = 0;
	if (!$CONFIG{ANONYMIZE}) {
		foreach my $d (sort { $topdsn{rcpt}{$b} <=> $topdsn{rcpt}{$a} } keys %{$topdsn{rcpt}}) {
			last if ($top == $CONFIG{TOP});
			$toprcpt .= "$d ($topdsn{rcpt}{$d})<br>";
			$top++;
		}
	}
	delete $topdsn{rcpt};

	if (!$topdsnstatus) {
		print qq{<table align="center"><tr><th colspan="2" class="thhead">$TRANSLATE{'No dataset'}</th></tr></table>};
		return;
	}
	print qq {
<tr><td colspan="2"><p>&nbsp;</p></td></tr>
<tr><th colspan="2" class="thhead">$TRANSLATE{'DSN Statistics'} (top $CONFIG{TOP})</th></tr>
<tr><td class="tdhead">$TRANSLATE{'Top DSN Status'}</td><td class="tdtopn">$topdsnstatus</td></tr>};
	print qq {
<tr><td class="tdhead">$TRANSLATE{'Top DSN Senders'}</td><td class="tdtopn">$topsender</td></tr>} if (!$CONFIG{ANONYMIZE});
	print qq {
<tr><td class="tdhead">$TRANSLATE{'Top DSN Relays'}</td><td class="tdtopn">$toprelay</td></tr>};
	print qq {
<tr><td class="tdhead">$TRANSLATE{'Top DSN Recipients'}</td><td class="tdtopn">$toprcpt</td></tr>} if (!$CONFIG{ANONYMIZE});
	print qq {
</table>
};
}

sub compute_top_reject
{

	foreach my $id (keys %STATS) {
		next if ($DOMAIN && ($STATS{$id}{sender} !~ /$DOMAIN/) && !grep(/$DOMAIN/, @{$STATS{$id}{rcpt}}));
		if (exists $STATS{$id}{rule}) {
			$topreject{sender}{$STATS{$id}{sender}}++;
			$STATS{$id}{sender} =~ s/^.*\@//;
			$STATS{$id}{sender} ||= 'Unknown';
			$topreject{domain}{$STATS{$id}{sender}}++;
			$topreject{relay}{$STATS{$id}{sender_relay}}++;
			$topreject{rule}{$STATS{$id}{rule}}++;
			for (my $i = 0; $i <= $#{$STATS{$id}{chck_status}}; $i++) {
				next if ($STATS{$id}{chck_status}[$i] =~ /Queued/);
				$topreject{chck_status}{$STATS{$id}{chck_status}[$i]}++;
			}
		}
		if (exists $STATS{$id}{error}) {
			# Skip already registered as rejection
			if (!exists $STATS{$id}{rule}) {
				$toperr{$STATS{$id}{error}}++;
			}
		}
	}
	%STATS = ();
} 

sub display_top_reject
{
	my ($hostname, $date, $hour) = @_;

	print qq{<table align="center"><tr><td valign="center" align="center">};

	# Top rejection statistics
	my $toprule = '';
	my $top = 0;
	foreach my $d (sort { $topreject{rule}{$b} <=> $topreject{rule}{$a} } keys %{$topreject{rule}}) {
		last if ($top == $CONFIG{TOP});
		$toprule .= &detail_link($hostname,$date,'reject','rule',$d,$hour) . " ($topreject{rule}{$d})<br>";
		$top++;
	}
	delete $topreject{rule};
	my $topdomain = '';
	$top = 0;
	foreach my $d (sort { $topreject{domain}{$b} <=> $topreject{domain}{$a} } keys %{$topreject{domain}}) {
		last if ($top == $CONFIG{TOP});
		if ($d ne '<>') {
			$topdomain .= &detail_link($hostname,$date,'reject','domain',$d,$hour) . " ($topreject{domain}{$d})<br>";
		} else {
			$topdomain .= "$d ($topreject{domain}{$d})<br>";
		}
		$top++;
	}
	delete $topreject{domain};
	my $toprelay = '';
	$top = 0;
	foreach my $d (sort { $topreject{relay}{$b} <=> $topreject{relay}{$a} } keys %{$topreject{relay}}) {
		last if ($top == $CONFIG{TOP});
		$toprelay .= &detail_link($hostname,$date,'reject','relay',$d,$hour) . " ($topreject{relay}{$d})<br>";
		$top++;
	}
	delete $topreject{relay};
	if (exists $CONFIG{REPLACE_HOST}) {
		foreach my $pat (keys %{$CONFIG{REPLACE_HOST}}) {
			$toprelay =~ s/$pat/$CONFIG{REPLACE_HOST}{$pat}/g;
		}
	}
	my $topstatus = '';
	$top = 0;
	foreach my $d (sort { $topreject{chck_status}{$b} <=> $topreject{chck_status}{$a} } keys %{$topreject{chck_status}}) {
		last if ($top == $CONFIG{TOP});
		if ($d =~ /^(\d{3}) \d\.(\d\.\d)$/) {
			if (exists $SMTP_ERROR_CODE{$1} || exists $ESMTP_ERROR_CODE{$2}) {
				$topstatus .= &detail_link($hostname,$date,'reject','status',"$d $SMTP_ERROR_CODE{$1} $ESMTP_ERROR_CODE{$2}",$hour);
			} else {
				$topstatus .= &detail_link($hostname,$date,'reject','status',$d,$hour);
			}
		} else {
			$topstatus .= &detail_link($hostname,$date,'reject','status',$d,$hour);
		}
		$topstatus .= " ($topreject{chck_status}{$d})<br>";
		$top++;
	}

	delete $topreject{status};
	my $topemail = '';
	$top = 0;
	if (!$CONFIG{ANONYMIZE}) {
		foreach my $d (sort { $topreject{sender}{$b} <=> $topreject{sender}{$a} } keys %{$topreject{sender}}) {
			last if ($top == $CONFIG{TOP});
			$topemail .= &detail_link($hostname,$date,'reject','address',$d,$hour) . " ($topreject{sender}{$d})<br>";
			$top++;
		}
	}
	%topreject =();
	if (!$toprule && (scalar keys %toperr == 0)) {
		print qq{<table align="center"><tr><th colspan="2" class="thhead">$TRANSLATE{'No dataset'}</th></tr></table>};
		return;
	}
	if ($toprule) {
		print qq {
<table>
<tr><th colspan="2" class="thhead">$TRANSLATE{'Rejection Statistics'} (top $CONFIG{TOP})</th></tr>
<tr><td class="tdhead">$TRANSLATE{'Top Rules'}</td><td class="tdtopn">$toprule</td></tr>
<tr><td class="tdhead">$TRANSLATE{'Top Domains'}</td><td class="tdtopn">$topdomain</td></tr>
<tr><td class="tdhead">$TRANSLATE{'Top Relays'}</td><td class="tdtopn">$toprelay</td></tr>
};
		if (!$CONFIG{ANONYMIZE}) {
			print qq {
<tr><td class="tdhead">$TRANSLATE{'Top Senders'}</td><td class="tdtopn">$topemail</td></tr>
};
		}
		print qq {
<tr><td class="tdhead">$TRANSLATE{'Top status'}</td><td class="tdtopn">$topstatus</td></tr>
};
		print "</table>\n<p>&nbsp;</p>";
	}

        if (scalar keys %toperr > 0) {
                $top = 0;
                print "<table>\n";
                print "<tr><th colspan=\"2\" class=\"thhead\">$TRANSLATE{'System messages'}</th></tr>\n";
                print "<tr><td class=\"tdhead\">$TRANSLATE{'Message'}</td><td class=\"tdhead\">$TRANSLATE{'Count'}</td></tr>\n";
                foreach my $msg (sort {$toperr{$b} <=> $toperr{$a}} keys %toperr) {
			my $display = $msg;
			$display =~ s/</\&lt;/g;
			$display =~ s/>/\&gt;/g;
                        if ($msg =~ /^(\d{3}) \d\.(\d\.\d)$/) {
                                if (exists $SMTP_ERROR_CODE{$1} || exists $ESMTP_ERROR_CODE{$2}) {
                                        print "<tr><td class=\"tdtopn\">$display $SMTP_ERROR_CODE{$1} $ESMTP_ERROR_CODE{$2}</td><td class=\"tdtopnr\">$toperr{$msg}</td><tr>\n";
                                } else {
                                        print "<tr><td class=\"tdtopn\">$display</td><td class=\"tdtopnr\">$toperr{$msg}</td><tr>\n";
                                }
                        } else {
                                print "<tr><td class=\"tdtopn\">$display</td><td class=\"tdtopnr\">$toperr{$msg}</td><tr>\n";
                        }
                        $top++;
                }
                print "</table>\n";
        }

}

sub compute_top_limit
{

	foreach my $id (keys %STATS) {
		next if ($DOMAIN && ($STATS{$id}{sender} !~ /$DOMAIN/) && !grep(/$DOMAIN/, @{$STATS{$id}{rcpt}}));
		if ($STATS{$id}{nrcpt} > $CONFIG{MAX_RCPT}) {
			push(@{$topmaxrcpt{$STATS{$id}{nrcpt}}{sender}}, $STATS{$id}{sender});
			push(@{$topmaxrcpt{$STATS{$id}{nrcpt}}{sa_id}}, $id);
		}
		if ($STATS{$id}{size} && $STATS{$id}{nrcpt}) {
			if ($STATS{$id}{size} > $CONFIG{MAX_SIZE}) {
				$topmaxsize{$id}{size} = $STATS{$id}{size};
				$topmaxsize{$id}{sender} = $STATS{$id}{sender};
				$topmaxsize{$id}{nrcpt} = $STATS{$id}{nrcpt};
			}
		}
	}
	%STATS = ();
} 

sub display_top_limit
{
	my ($hostname, $date, $hour) = @_;

	if ((scalar keys %topmaxrcpt == 0) && (scalar keys %topmaxsize == 0)) {
		print qq{<table align="center"><tr><th colspan="2" class="thhead">$TRANSLATE{'No dataset'}</th></tr></table>};
		return;
	}

	if (scalar keys %topmaxrcpt > 0) {
		print qq{
<table align="center" width="100%"><tr><td valign="center" align="center">
<tr><th colspan="2" class="thhead">$TRANSLATE{'Max Number of Recipients'} (top $CONFIG{TOP})</th></tr>
<tr><td class="tdhead">$TRANSLATE{'Number of Recipients'}</td><td class="tdhead">$TRANSLATE{'Senders'}</td></tr>
};
		my $top = 0;
		foreach my $nb (sort { $b <=> $a } keys %topmaxrcpt) {
			last if ($top == $CONFIG{TOP});
			print "<tr><td class=\"tdtopn\">$nb</td><td class=\"tdtopn\">";
			for (my $i = 0; $i <= $#{$topmaxrcpt{$nb}{sender}}; $i++) {
				my $whosend = $topmaxrcpt{$nb}{sender}[$i];
				$whosend =~ s/^.*\@/anonymized\@/ if ($CONFIG{ANONYMIZE});
				print "$whosend (", &detail_link($hostname,$date,'sender','topmax',$topmaxrcpt{$nb}{sa_id}[$i],$hour), ")<br>\n";
			}
			print "</td><tr>\n";
			$top++;
		}
		print "</table>\n<p>&nbsp;</p>";
	}

	if (scalar keys %topmaxsize > 0) {
		my $top = 0;
		print qq{
<table align="center" width="100%"><tr><td valign="center" align="center">
<tr><th colspan="3" class="thhead">$TRANSLATE{'Max Size Senders'} (top $CONFIG{TOP})</th></tr>
<tr><td class="tdhead">$TRANSLATE{'Message size'}</td><td class="tdhead">$TRANSLATE{'Number of Recipients'}</td><td class="tdhead">$TRANSLATE{'Senders'}</td></tr>
};
		foreach my $id (sort { ($topmaxsize{$b}{size}*$topmaxsize{$b}{nrcpt}) <=> ($topmaxsize{$a}{size}*$topmaxsize{$b}{nrcpt}) } keys %topmaxsize) {
			last if ($top == $CONFIG{TOP});
			$topmaxsize{$id}{sender} =~ s/^.*\@/anonymized\@/ if ($CONFIG{ANONYMIZE});
			print "<tr><td class=\"tdtopn\">$topmaxsize{$id}{size}</td><td class=\"tdtopn\">$topmaxsize{$id}{nrcpt}</td><td class=\"tdtopn\">$topmaxsize{$id}{sender} (", &detail_link($hostname,$date,'sender','topmax',$id,$hour), ")</td><tr>\n";
			$top++;
		}
		print "</table>\n";
	}

}

sub compute_top_spamdetail
{
	my ($type) = @_;

	foreach my $id (keys %STATS) {
		next if ($DOMAIN && ($STATS{$id}{sender} !~ /$DOMAIN/) && !grep(/$DOMAIN/, @{$STATS{$id}{rcpt}}));
		$topspamdetail{$type}{score}{$STATS{$id}{score}}++ if ($STATS{$id}{score});
		$topspamdetail{$type}{rule}{$STATS{$id}{spam}}++;
		$topspamdetail{$type}{cache}{$STATS{$id}{cache}}++ if ($STATS{$id}{cache});
		$topspamdetail{$type}{autolearn}{$STATS{$id}{autolearn}}++ if ($STATS{$id}{autolearn});
	}
	%STATS = ();
} 

sub display_top_spamdetail
{
	my ($hostname, $date, $type, $hour) = @_;

	if (scalar keys %{$topspamdetail{$type}} == 0) {
		print qq{<table align="center"><tr><th colspan="2" class="thhead">$TRANSLATE{'No dataset'}</th></tr></table>};
		return;
	}

	if (exists $topspamdetail{$type}{rule}) {
		print qq{
<table align="center"><tr><td valign="center" align="center">
<tr><th colspan="3" class="thhead">$TRANSLATE{'Top Spams'} (top $CONFIG{TOP})</th></tr>
<tr><td class="tdhead">$TRANSLATE{'Count'}</td><td class="tdhead">$TRANSLATE{'Rule'}</td></tr>
};
		my $top = 0;
		foreach my $spam (sort { $topspamdetail{$type}{rule}{$b} <=> $topspamdetail{$type}{rule}{$a} } keys %{$topspamdetail{$type}{rule}}) {
			last if ($top == $CONFIG{TOP});
			print "<tr><td class=\"tdtopn\">$topspamdetail{$type}{rule}{$spam}</td><td class=\"tdtopn\">", &detail_link($hostname,$date,'spam_'.$VIEW,'rule',$spam,$hour) . "</td><tr>\n";
			$top++;
		}
		print "</table>\n<p>&nbsp;</p>\n";
	}
	delete $topspamdetail{$type}{rule};

print "<table align=\"left\" width=\"700px\"><tr><td valign=\"top\" align=\"center\">\n";
	if (exists $topspamdetail{$type}{score} && (scalar keys %{$topspamdetail{$type}{score}} > 0)) {
		print qq{
<table align="center"><tr><td valign="top" align="center">
<tr><th colspan="2" class="thhead">$TRANSLATE{'Top spam scores'}</th></tr>
<tr><td class="tdhead">$TRANSLATE{'Score'}</td><td class="tdhead">$TRANSLATE{'Count'}</td></tr>
};
		my $top = 0;
		foreach my $nb (sort { $topspamdetail{$type}{score}{$b} <=> $topspamdetail{$type}{score}{$a} } keys %{$topspamdetail{$type}{score}}) {
			last if ($top == $CONFIG{TOP});
			print "<tr><td class=\"tdtopnr\">", &detail_link($hostname,$date,'spam_'.$VIEW,'score',$nb,$hour), "</td><td class=\"tdtopnr\">$topspamdetail{$type}{score}{$nb}</td></tr>";
			$top++;
		}
		print "</table>\n";
	}
	delete $topspamdetail{$type}{score};
print "</td><td valign=\"top\" align=\"center\">\n";
	if (exists $topspamdetail{$type}{cache} && (scalar keys %{$topspamdetail{$type}{cache}} > 0) ) {
		print qq{
<table align="center"><tr><td valign="top" align="center">
<tr><th colspan="2" class="thhead">$TRANSLATE{'Caching statistics'}</th></tr>
<tr><td class="tdhead">$TRANSLATE{'Cache'}</td><td class="tdhead">$TRANSLATE{'Count'}</td></tr>
};
		my $top = 0;
		foreach my $nb (sort { $topspamdetail{$type}{cache}{$b} <=> $topspamdetail{$type}{cache}{$a} } keys %{$topspamdetail{$type}{cache}}) {
			last if ($top == $CONFIG{TOP});
			print "<tr><td class=\"tdtopn\">", &detail_link($hostname,$date,'spam_'.$VIEW,'cache',$nb,$hour), "</td><td class=\"tdtopnr\">$topspamdetail{$type}{cache}{$nb}</td></tr>";
			$top++;
		}
		print "</table>\n";
	}
	delete $topspamdetail{$type}{cache};

print "</td><td valign=\"top\" align=\"center\">\n";

	if (exists $topspamdetail{$type}{autolearn} && (scalar keys %{$topspamdetail{$type}{autolearn}} > 0) ) {
		print qq{
<table align="center"><tr><td valign="top" align="center">
<tr><th colspan="2" class="thhead">$TRANSLATE{'Autolearn Statistics'}</th></tr>
<tr><td class="tdhead">$TRANSLATE{'Autolearn'}</td><td class="tdhead">$TRANSLATE{'Count'}</td></tr>
};
		my $top = 0;
		foreach my $nb (sort { $topspamdetail{$type}{autolearn}{$b} <=> $topspamdetail{$type}{autolearn}{$a} } keys %{$topspamdetail{$type}{autolearn}}) {
			last if ($top == $CONFIG{TOP});
			print "<tr><td class=\"tdtopn\">", &detail_link($hostname,$date,'spam_'.$VIEW,'autolearn',$nb,$hour), "</td><td class=\"tdtopnr\">$topspamdetail{$type}{autolearn}{$nb}</td></tr>";
			$top++;
		}
		print "</table>\n<p>&nbsp;</p>";
	}
	print "</td></tr></table>\n";

	delete $topspamdetail{$type}{autolearn};

}

sub compute_top_auth
{
	return if ($DOMAIN);

	foreach my $id (keys %AUTH) {
		$topauth{authid}{$id} += ($#{$AUTH{$id}{relay}} + 1);
		for (my $i = 0; $i <= $#{$AUTH{$id}{relay}}; $i++) {
			$topauth{relay}{$AUTH{$id}{relay}[$i]}++;
			$topauth{mech}{$AUTH{$id}{mech}[$i]}++;
		}
	}
	%AUTH = ();
}

sub display_top_auth
{
	my ($hostname, $date, $hour) = @_;

	if (scalar keys %{$topauth{authid}} == 0) {
		print qq{<table align="center"><tr><th colspan="2" class="thhead">$TRANSLATE{'No dataset'}</th></tr></table>};
		return;
	}

	my $topmech = '';
	foreach my $k (sort {$topauth{mech}{$b} <=> $topauth{mech}{$a} } keys %{$topauth{mech}} ) {
		$topmech .= "$k ($topauth{mech}{$k})<br>\n";
	}
	delete $topauth{mech};
	my $toprelay = '';
	my $top = 0;
	foreach my $k (sort {$topauth{relay}{$b} <=> $topauth{relay}{$a} } keys %{$topauth{relay}} ) {
		last if ($top == $CONFIG{TOP});
		$toprelay .= "$k ($topauth{relay}{$k})<br>\n";
		$top++;
	}
	delete $topauth{relay};
	my $topid = '';
	$top = 0;
	foreach my $k (sort {$topauth{authid}{$b} <=> $topauth{authid}{$a} } keys %{$topauth{authid}} ) {
		last if ($top == $CONFIG{TOP});
		my $user = $k;
		$user = "user_$top" if ($CONFIG{ANONYMIZE});
		$topid .= "$user ($topauth{authid}{$k})<br>\n";
		$top++;
	}
	print qq{
<table align="center" width="100%"><tr><td valign="center" align="center">
<tr><th colspan="3" class="thhead">$TRANSLATE{'SMTP Auth Statistics'} (top $CONFIG{TOP})</th></tr>
<tr><td class="tdhead">$TRANSLATE{'Top Mechanism'}</td><td class="tdhead">$TRANSLATE{'Top Relay'}</td><td class="tdhead">$TRANSLATE{'Top Authid'}</td></tr>
<tr><td class="tdtopn">$topmech</td><td class="tdtopn">$toprelay</td><td class="tdtopn">$topid</td></tr>
</table>
};

}

sub show_detail
{
	my ($hostname, $date, $hour, $type, $peri, $search) = @_;

	my $path = $CONFIG{OUT_DIR} . '/' . $hostname . '/' . $date;
	$path =~ s/(\d{4})(\d{2})(\d{2})$/$1\/$2\/$3\//;
	$search = '' if ($search eq '<>');
	my %lstat = ();
	if ($type eq 'sender') {
		%lstat = &get_sender_detail($path, $peri, $search, $hour);
	} elsif ($type eq 'recipient') {
		%lstat = &get_recipient_detail($path, $peri, $search, $hour);
	} elsif ($type eq 'reject') {
		%lstat = &get_reject_detail($path, $peri, $search, $hour);
	} elsif ($type eq 'spam') {
		%lstat = &get_spam_detail($path, $peri, $search, $hour);
	} elsif ($type =~ /spam_(.*)/) {
		%lstat = &get_spaminfo_detail($path, $1, $peri, $search, $hour);
	} elsif ($type eq 'virus') {
		%lstat = &get_virus_detail($path, $peri, $search, $hour);
	} elsif ($type eq 'dsn') {
		%lstat = &get_dsn_detail($path, $peri, $search, $hour);
	} elsif ($type eq 'dsnsrc') {
		%lstat = &get_dsnsrc_detail($path, $peri, $search, $hour);
	} else {
		print "BAD DETAIL TYPE\n";
	}

	print qq{<form><table align="center"><tr><td class="smalltitle">$search</td></tr></table><table>\n<tr><th>&nbsp;</th><th>$TRANSLATE{'Hour'}</th><th>Id</th>};
	if ($type eq 'dsn') {
		print qq{<th>$TRANSLATE{'Original Id'}</th><th>$TRANSLATE{'Original Recipient'}</th>};
	}
	print qq{<th>$TRANSLATE{'Sender'}</th>};
	print qq{<th>$TRANSLATE{'Size'}</th>} if ($type ne 'dsn');
	print qq{<th>$TRANSLATE{'Sender Relay'}</th>};
	print qq{<th>$TRANSLATE{'Recipients'}</th>\n};
	if ($type !~ /spam|reject/) {
		print qq{<th>$TRANSLATE{'Recipient Relay'}</th>\n};
	}
	if ($type !~ /spam/) {
		print qq{<th>$TRANSLATE{'Status'}</th>\n};
	}
	if (!grep(/$type/, 'dsn', 'dsnsrc', 'sender', 'recipient')) {
		if ($type eq 'spam') {
			print qq{<th nowrap="1">$TRANSLATE{'Spam'}</th>\n};
		} elsif ($type =~ /spam_/) {
			print qq{<th>$TRANSLATE{'Score'}</th><th>$TRANSLATE{'Cache'}</th><th>$TRANSLATE{'Autolearn'}</th><th>$TRANSLATE{'Spam'}</th>\n};
		} elsif ($type eq 'virus') {
			print qq{<th>$TRANSLATE{'Virus'}</th><th>$TRANSLATE{'File'}</th>\n};
		} else {
			print qq{<th>$TRANSLATE{'Rule'}</th>\n};
		}
	}
	print "</tr>\n";
	my $line = 1;
	foreach my $id (sort { $lstat{$a}{hour} <=> $lstat{$b}{hour} } keys %lstat) {
		next if ($DOMAIN && ($lstat{$id}{sender} !~ /$DOMAIN/) && !grep(/$DOMAIN/, @{$lstat{$id}{rcpt}}));
		last if ($line > $CONFIG{MAX_LINE});
		$lstat{$id}{hour} =~ s/(\d{2})(\d{2})(\d{2})/$1:$2:$3/;
		if (length($lstat{$id}{hour}) == 2) {
			$lstat{$id}{hour} .= ':00:00';
		}
		$lstat{$id}{sender} =~ s/^.*\@/anonymized\@/ if ($CONFIG{ANONYMIZE});
		if (exists $CONFIG{REPLACE_HOST}) {
			foreach my $pat (keys %{$CONFIG{REPLACE_HOST}}) {
				$lstat{$id}{sender_relay} =~ s/$pat/$CONFIG{REPLACE_HOST}{$pat}/g;
			}
		}
		$lstat{$id}{sender} ||= '&nbsp;';
		$lstat{$id}{size} ||= '&nbsp;';
		$lstat{$id}{sender_relay} ||= '&nbsp;';
		print qq{<tr valign="top"><td class="tdtopn">$line</td><td class="tdtopn">$lstat{$id}{hour}</td><td class="tdtopn">$id</td>};
		if ($type eq 'dsn') {
			$lstat{$id}{srcid} = &detail_link($hostname,$date,'sender','id',$lstat{$id}{srcid}, $hour);
			print qq{<td class="tdtopn" nowrap="1">$lstat{$id}{srcid}</td><td class="tdtopn" nowrap="1">$lstat{$id}{orig_rcpt}</td>};
		}
		print qq{<td class="tdtopn" nowrap="1">$lstat{$id}{sender}</td>};
		print qq{<td class="tdtopn">$lstat{$id}{size}</td>} if ($type ne 'dsn');
		print qq{<td class="tdtopn">$lstat{$id}{sender_relay}</td>};
		print "<td class=\"tdtopn\" nowrap=\"1\">";
		if (defined $lstat{$id}{chck_rcpt}) {
			if ($CONFIG{ANONYMIZE}) {
				map { s/^.*\@/anonymized\@/ } @{$lstat{$id}{rcpt}};
			}
			if ($#{$lstat{$id}{chck_rcpt}} > 0) {
				if (grep(!/$lstat{$id}{chck_rcpt}[0]/, @{$lstat{$id}{chck_rcpt}})) {
					my $onchange = "document.getElementById('relay_$id').selectedIndex = this.selectedIndex; document.getElementById('status_$id').selectedIndex = this.selectedIndex;";
					print "<select id=\"rcpt_$id\" name=\"rcpt_$id\" onchange=\"$onchange\">\n";
					for (my $i = 0; $i <= $#{$lstat{$id}{chck_rcpt}}; $i++) {
						print "<option name=\"rcpt_$i\">$lstat{$id}{chck_rcpt}[$i]</option>\n";
					}
					print "</select>\n";
				} else {
					print $lstat{$id}{chck_rcpt}[0], '(x', ($#{$lstat{$id}{chck_rcpt}}+1), ')';
				}
			} else {
				print $lstat{$id}{chck_rcpt}[0];
			}
		} elsif (defined $lstat{$id}{rcpt}) {
			if ($CONFIG{ANONYMIZE}) {
				map { s/^.*\@/anonymized\@/ } @{$lstat{$id}{rcpt}};
			}
			if ($#{$lstat{$id}{rcpt}} > 0) {
				if (grep(!/$lstat{$id}{rcpt}[0]/, @{$lstat{$id}{rcpt}})) {
					my $onchange = "document.getElementById('relay_$id').selectedIndex = this.selectedIndex; document.getElementById('status_$id').selectedIndex = this.selectedIndex;";
					print "<select id=\"rcpt_$id\" name=\"rcpt_$id\" onchange=\"$onchange\">\n";
					for (my $i = 0; $i <= $#{$lstat{$id}{rcpt}}; $i++) {
						print "<option name=\"rcpt_$i\">$lstat{$id}{rcpt}[$i]</option>\n";
					}
					print "</select>\n";
				} else {
					print $lstat{$id}{rcpt}[0], '(x', ($#{$lstat{$id}{rcpt}}+1), ')';
				}
			} else {
				print $lstat{$id}{rcpt}[0];
			}
		} else {
			print "&nbsp;"
		}
		print "</td>";
		if ($type !~ /spam|reject/) {
			print "<td class=\"tdtopn\">";
			if (defined $lstat{$id}{rcpt_relay} && ($#{$lstat{$id}{rcpt_relay}} >= 0)) {
				if (exists $CONFIG{REPLACE_HOST}) {
					foreach my $pat (keys %{$CONFIG{REPLACE_HOST}}) {
						map { s/$pat/$CONFIG{REPLACE_HOST}{$pat}/g } @{$lstat{$id}{rcpt_relay}};
					}
				}
				if ( ($#{$lstat{$id}{rcpt_relay}} > 0) && grep(!/$lstat{$id}{rcpt_relay}[0]/, @{$lstat{$id}{rcpt_relay}})) {
					my $onchange = "document.getElementById('rcpt_$id').selectedIndex = this.selectedIndex; document.getElementById('status_$id').selectedIndex = this.selectedIndex;";
					print "<select id=\"relay_$id\" name=\"relay_$id\" onchange=\"$onchange\">\n";
					for (my $i = 0; $i <= $#{$lstat{$id}{rcpt_relay}}; $i++) {
						print "<option name=\"relay_$i\">", ($lstat{$id}{rcpt_relay}[$i] || 'localhost'), "</option>\n";
					}
					print "</select>\n";
				} else {
					print $lstat{$id}{rcpt_relay}[0];
				}
			} else {
				print "&nbsp;"
			}
			print "</td>";
		}
		if ($type !~ /spam/) {
			print "<td class=\"tdtopn\" nowrap=\"1\">";
			if (defined $lstat{$id}{chck_status}) {
				if ( ($#{$lstat{$id}{chck_status}} > 0) && grep(!/$lstat{$id}{chck_status}[0]/, @{$lstat{$id}{chck_status}})) {
					my $onchange = "document.getElementById('rcpt_$id').selectedIndex = this.selectedIndex; document.getElementById('relay_$id').selectedIndex = this.selectedIndex;";
					print "<select id=\"status_$id\" name=\"status_$id\" onchange=\"$onchange\">\n";
					for (my $i = 0; $i <= $#{$lstat{$id}{chck_status}}; $i++) {
						print "<option name=\"status_$i\">$lstat{$id}{chck_status}[$i]</option>\n";
					}
					print "</select>\n";
				} else {
					print $lstat{$id}{chck_status}[0];
				}
			} elsif (defined $lstat{$id}{status}) {
				if ( ($#{$lstat{$id}{status}} > 0) && grep(!/$lstat{$id}{status}[0]/, @{$lstat{$id}{status}})) {
					my $onchange = "document.getElementById('rcpt_$id').selectedIndex = this.selectedIndex; document.getElementById('relay_$id').selectedIndex = this.selectedIndex;";
					print "<select id=\"status_$id\" name=\"status_$id\" onchange=\"$onchange\">\n";
					for (my $i = 0; $i <= $#{$lstat{$id}{status}}; $i++) {
						print "<option name=\"status_$i\">$lstat{$id}{status}[$i]</option>\n";
					}
					print "</select>\n";
				} else {
					print $lstat{$id}{status}[0];
				}
			} else {
				print "&nbsp;"
			}
			print "</td>";
		}
		if (!grep(/$type/, 'dsn', 'dsnsrc', 'sender', 'recipient')) {
			if ($type eq 'spam') {
				$lstat{$id}{spam} ||= '&nbsp;';
				print qq{<td class="tdtopn">$lstat{$id}{spam}</td>};
			} elsif ($type =~ /spam_/) {
				$lstat{$id}{spam} ||= '&nbsp;';
				$lstat{$id}{score} ||= '&nbsp;';
				$lstat{$id}{cache} ||= '&nbsp;';
				$lstat{$id}{autolearn} ||= '&nbsp;';
				$lstat{$id}{spam} = $CGI->unescape(&decode_str($lstat{$id}{spam}));
				print qq{<td class="tdtopn">$lstat{$id}{score}</td><td class="tdtopn">$lstat{$id}{cache}</td><td class="tdtopn">$lstat{$id}{autolearn}</td><td class="tdtopn" nowrap="1">$lstat{$id}{spam}</td>};
			} elsif ($type eq 'virus') {
				$lstat{$id}{virus} ||= '&nbsp;';
				print qq{<td class="tdtopn">$lstat{$id}{virus}</td><td class="tdtopn">$lstat{$id}{file}</td>};
			} else {
				$lstat{$id}{rule} ||= '&nbsp;';
				print qq{<td class="tdtopn">$lstat{$id}{rule}</td>};
			}
		}
		print "</tr>\n";
		$line++;
	}
	print "</table>\n</form>\n";
}

sub get_sender_detail
{
	my ($path, $peri, $search, $hour) = @_;

	my %local_stat = ();
	my $file = "$path/senders.dat";
	# Format: Hour:Id:Sender:Size:Nrcpts:Relay
	if (open(IN, $file)) {
		while (my $l = <IN>) {
			chomp($l);
			# Format: Hour:Id:Sender:Size:Nrcpts:Relay
			my @data = split(/:/, $l);
			$data[0] =~ /^(\d{2})/;
			next if (($hour ne '') && ($1 != $hour));
			$data[2] ||= '<>';
			if ($peri eq 'domain') {
				if (!$search) {
					next if ($data[2] ne '<>');
				} else {
					next if ($data[2] !~ /$search/);
				}
			} elsif ($peri eq 'relay') {
				next if ($data[5] ne $search);
			} elsif ($peri eq 'address') {
				if (!$search) {
					next if ($data[2] ne '<>');
				} else {
					next if ($data[2] ne $search);
				}
			} elsif ( ($peri eq 'topmax') || ($peri eq 'id')) {
				next if ($data[1] ne $search);
			}
			$local_stat{$data[1]}{hour} = $data[0];
			$local_stat{$data[1]}{sender} = $data[2];
			$local_stat{$data[1]}{size} = $data[3];
			$local_stat{$data[1]}{nrcpt} = $data[4];
			$local_stat{$data[1]}{sender_relay} = $data[5];
		}
		close(IN);
	}
	$file = "$path/recipient.dat";
	if (open(IN, $file)) {
		while (my $l = <IN>) {
			chomp($l);
			# Format: Hour:Id:recipient:Relay:Status
			my @data = split(/:/, $l);
			$data[0] =~ /^(\d{2})/;
			next if (($hour ne '') && ($1 != $hour));
			next if (!exists $local_stat{$data[1]});
			if ($data[4] !~ /Queued/) {
				push(@{$local_stat{$data[1]}{rcpt}}, $data[2]);
				push(@{$local_stat{$data[1]}{rcpt_relay}}, $data[3]);
				push(@{$local_stat{$data[1]}{status}}, $data[4]);
			}
		}
		close(IN);
	}

	$file = "$path/rejected.dat";
	if (open(IN, $file)) {
		while (my $l = <IN>) {
			chomp($l);
			# Format: Hour:Id:Rule:Relay:Arg1:Status
			my @data = split(/:/, $l);
			$data[0] =~ /^(\d{2})/;
			next if (($hour ne '') && ($1 != $hour));
			next if (!exists $local_stat{$data[1]});
			$local_stat{$data[1]}{rule} = $data[2];
			$local_stat{$data[1]}{sender_relay} = $data[3] if (!$local_stat{$data[1]}{sender_relay});
			if ($#data > 4) {
				if ($data[2] eq 'check_relay') {
					$local_stat{$data[1]}{sender_relay} = $data[4];
				} elsif ($data[2] eq 'check_rcpt') {
					push(@{$local_stat{$data[1]}{chck_rcpt}}, $data[4]);
				} else {
					# $data[2] eq 'check_mail' or POSTFIX
					$local_stat{$data[1]}{sender} = $data[4];
				}
				push(@{$local_stat{$data[1]}{chck_status}}, $data[5]);
			} else {
				push(@{$local_stat{$data[1]}{chck_status}}, $data[4]);
			}
		}
		close(IN);
	}
	$file = "$path/spam.dat";
	if (open(IN, $file)) {
		while (my $l = <IN>) {
			chomp($l);
			# Format: Hour:Id:From:To:Spam
			my @data = split(/:/, $l, 5);
			$data[0] =~ /^(\d{2})/;
			next if (($hour ne '') && ($1 != $hour));
			next if (!exists $local_stat{$data[1]});
			$local_stat{$data[1]}{hour} = $data[0] if (!exists $local_stat{$data[1]}{hour});
			$local_stat{$data[1]}{sender} = $data[2] if (!exists $local_stat{$data[1]}{sender});
			push(@{$local_stat{$data[1]}{rcpt}}, $data[3]);
			$local_stat{$data[1]}{spam} = $data[4];
		}
		close(IN);
	}
	$file = "$path/virus.dat";
	if (open(IN, $file)) {
		while (my $l = <IN>) {
			chomp($l);
			# Format: Hour:Id:file:virus
			my @data = split(/:/, $l, 4);
			$data[0] =~ /^(\d{2})/;
			next if (($hour ne '') && ($1 != $hour));
			next if (!exists $local_stat{$data[1]});
			$local_stat{$data[1]}{hour} = $data[0] if (!exists $local_stat{$data[1]}{hour});
			$local_stat{$data[1]}{file} = $data[2];
			$local_stat{$data[1]}{virus} = $data[3];
		}
		close(IN);
	}
	$file = "$path/syserr.dat";
	if (open(IN, $file)) {
		while (my $l = <IN>) {
			chomp($l);
			# Format: Hour:Id:Message
			my @data = split(/:/, $l, 3);
			next if ($data[2] !~ /\s/); # Skip single word error
			$data[0] =~ /^(\d{2})/;
			next if (($hour ne '') && ($1 != $hour));
			next if (!exists $local_stat{$data[1]});
			$l =~ /^\d+:([^\:]+):(.*)/;
			shift(@data);
			shift(@data);
			$local_stat{$1}{error} = join(':', @data);
		}
		close(IN);
	}
	return %local_stat;
}

sub get_recipient_detail
{
	my ($path, $peri, $search, $hour) = @_;

	my %local_stat = ();

	my $file = "$path/recipient.dat";
	if (open(IN, $file)) {
		while (my $l = <IN>) {
			chomp($l);
			# Format: Hour:Id:recipient:Relay:Status
			my @data = split(/:/, $l);
			$data[0] =~ /^(\d{2})/;
			$data[3] ||= '<>';
			next if (($hour ne '') && ($1 != $hour));
			if ($peri eq 'domain') {
				next if ($data[2] !~ /$search/);
			} elsif ($peri eq 'relay') {
				next if ($data[3] ne $search);
			} elsif ($peri eq 'address') {
				next if ($data[2] ne $search);
			}
			if ($data[4] =~ /Sent/) {
				push(@{$local_stat{$data[1]}{rcpt}}, $data[2]);
				push(@{$local_stat{$data[1]}{rcpt_relay}}, $data[3]);
				push(@{$local_stat{$data[1]}{status}}, $data[4]);
			}
		}
		close(IN);
	}


	# Format: Hour:Id:Sender:Size:Nrcpts:Relay
	$file = "$path/senders.dat";
	if (open(IN, $file)) {
		while (my $l = <IN>) { 
			chomp($l);
			# Format: Hour:Id:Sender:Size:Nrcpts:Relay
			my @data = split(/:/, $l);
			$data[0] =~ /^(\d{2})/;
			next if (($hour ne '') && ($1 != $hour));
			next if (!exists $local_stat{$data[1]});
			$data[2] ||= '<>';
			$local_stat{$data[1]}{hour} = $data[0];
			$local_stat{$data[1]}{sender} = $data[2];
			$local_stat{$data[1]}{size} = $data[3];
			$local_stat{$data[1]}{nrcpt} = $data[4];
			$local_stat{$data[1]}{sender_relay} = $data[5];
		}
		close(IN);
	}
	$file = "$path/rejected.dat";
	if (open(IN, $file)) {
		while (my $l = <IN>) {
			chomp($l);
			# Format: Hour:Id:Rule:Relay:Arg1:Status
			my @data = split(/:/, $l);
			$data[0] =~ /^(\d{2})/;
			next if (($hour ne '') && ($1 != $hour));
			next if (!exists $local_stat{$data[1]});
			$local_stat{$data[1]}{rule} = $data[2];
			$local_stat{$data[1]}{sender_relay} = $data[3] if (!$local_stat{$data[1]}{sender_relay});
			if ($#data > 4) {
				if ($data[2] eq 'check_relay') {
					$local_stat{$data[1]}{sender_relay} = $data[4];
				} elsif ($data[2] eq 'check_rcpt') {
					push(@{$local_stat{$data[1]}{chck_rcpt}}, $data[4]);
				} else {
					# $data[2] eq 'check_mail' or POSTFIX
					$local_stat{$data[1]}{sender} = $data[4];
				}
				push(@{$local_stat{$data[1]}{chck_status}}, $data[5]);
			} else {
				push(@{$local_stat{$data[1]}{chck_status}}, $data[4]);
			}
		}
		close(IN);
	}
	$file = "$path/spam.dat";
	if (open(IN, $file)) {
		while (my $l = <IN>) {
			chomp($l);
			# Format: Hour:Id:From:To:Spam
			my @data = split(/:/, $l, 5);
			$data[0] =~ /^(\d{2})/;
			next if (($hour ne '') && ($1 != $hour));
			next if (!exists $local_stat{$data[1]});
			$local_stat{$data[1]}{hour} = $data[0] if (!exists $local_stat{$data[1]}{hour});
			$local_stat{$data[1]}{sender} = $data[2] if (!exists $local_stat{$data[1]}{sender});
			push(@{$local_stat{$data[1]}{rcpt}}, $data[3]);
			$local_stat{$data[1]}{spam} = $data[4];
		}
		close(IN);
	}
	$file = "$path/virus.dat";
	if (open(IN, $file)) {
		while (my $l = <IN>) {
			chomp($l);
			# Format: Hour:Id:file:virus
			my @data = split(/:/, $l, 4);
			$data[0] =~ /^(\d{2})/;
			next if (($hour ne '') && ($1 != $hour));
			next if (!exists $local_stat{$data[1]});
			$local_stat{$data[1]}{hour} = $data[0] if (!exists $local_stat{$data[1]}{hour});
			$local_stat{$data[1]}{file} = $data[2];
			$local_stat{$data[1]}{virus} = $data[3];
		}
		close(IN);
	}
	$file = "$path/syserr.dat";
	if (open(IN, $file)) {
		while (my $l = <IN>) {
			chomp($l);
			# Format: Hour:Id:Message
			my @data = split(/:/, $l, 3);
			next if ($data[2] !~ /\s/); # Skip single word error
			$data[0] =~ /^(\d{2})/;
			next if (($hour ne '') && ($1 != $hour));
			next if (!exists $local_stat{$data[1]});
			shift(@data);
			my $id = shift(@data);
			$local_stat{$id}{error} = join(':', @data);
		}
		close(IN);
	}
	return %local_stat;
}

sub get_reject_detail
{
	my ($path, $peri, $search, $hour) = @_;

	my %local_stat = ();

	my $file = "$path/rejected.dat";
	if (open(IN, $file)) {
		while (my $l = <IN>) {
			chomp($l);
			# Format: Hour:Id:Rule:Relay:Arg1:Status
			my @data = split(/:/, $l);
			$data[0] =~ /^(\d{2})/;
			next if (($hour ne '') && ($1 != $hour));
			if ($peri eq 'rule') {
				next if ($data[2] !~ /$search/);
			} elsif ($peri eq 'relay') {
				next if ($data[3] ne $search);
			} elsif ($peri eq 'status') {
				next if ($data[-1] !~ /$search/);
			}
			$local_stat{$data[1]}{rule} = $data[2];
			$local_stat{$data[1]}{sender_relay} = $data[3];
			if ($#data > 4) {
				if ($data[2] eq 'check_relay') {
					$local_stat{$data[1]}{sender_relay} = $data[4];
				} elsif ($data[2] eq 'check_rcpt') {
					push(@{$local_stat{$data[1]}{chck_rcpt}}, $data[4]);
				} else {
					# $data[2] eq 'check_mail' or POSTFIX
					$local_stat{$data[1]}{sender} = $data[4];
				}
				push(@{$local_stat{$data[1]}{chck_status}}, $data[5]);
			} else {
				push(@{$local_stat{$data[1]}{chck_status}}, $data[4]);
			}
		}
		close(IN);
	}
	$file = "$path/senders.dat";
	# Format: Hour:Id:Sender:Size:Nrcpts:Relay
	if (open(IN, $file)) {
		while (my $l = <IN>) { 
			chomp($l);
			# Format: Hour:Id:Sender:Size:Nrcpts:Relay
			my @data = split(/:/, $l);
			$data[0] =~ /^(\d{2})/;
			next if (($hour ne '') && ($1 != $hour));
			$data[2] ||= '<>';
			next if (!exists $local_stat{$data[1]});
			if ($peri eq 'domain') {
				if ($data[2] !~ /$search/) {
					delete $local_stat{$data[1]};
					next;
				}
			} elsif ($peri eq 'address') {
				if ($data[2] ne $search) {
					delete $local_stat{$data[1]};
					next;
				}
			} elsif ($peri eq 'relay') {
				if ($data[5] ne $search) {
					delete $local_stat{$data[1]};
					next;
				}
			}
			$local_stat{$data[1]}{hour} = $data[0];
			$local_stat{$data[1]}{sender} = $data[2];
			$local_stat{$data[1]}{size} = $data[3];
			$local_stat{$data[1]}{nrcpt} = $data[4];
			$local_stat{$data[1]}{sender_relay} = $data[5];
		}
		close(IN);
	}
	return %local_stat;
}

sub get_spam_detail
{
	my ($path, $peri, $search, $hour) = @_;

	my %local_stat = ();

	my $file = "$path/spam.dat";
	if (open(IN, $file)) {
		while (my $l = <IN>) {
			chomp($l);
			# Format: Hour:Id:From:To:Spam
			my @data = split(/:/, $l, 5);
			$data[0] =~ /^(\d{2})/;
			next if (($hour ne '') && ($1 != $hour));
			if ($peri eq 'rule') {
				next if ($data[4] ne $search);
			} elsif ($peri eq 'sender') {
				next if ($data[2] ne $search);
			} elsif ($peri eq 'domain') {
				next if ($data[2] !~ /$search/);
			} elsif ($peri eq 'recipient') {
				next if ($data[3] ne $search);
			}
			$local_stat{$data[1]}{hour} = $data[0] if (!exists $local_stat{$data[1]}{hour});
			$local_stat{$data[1]}{sender} = $data[2] if (!exists $local_stat{$data[1]}{sender});
			$local_stat{$data[1]}{spam} = $data[4];
			push(@{$local_stat{$data[1]}{rcpt}}, $data[3]);
		}
		close(IN);
	}
	$file = "$path/recipient.dat";
	if (open(IN, $file)) {
		my $i = 0;
		while (my $l = <IN>) {
			chomp($l);
			# Format: Hour:Id:recipient:Relay:Status
			my @data = split(/:/, $l);
			$data[0] =~ /^(\d{2})/;
			next if (($hour ne '') && ($1 != $hour));
			next if (!exists $local_stat{$data[1]});
			if ($peri eq 'recipient') {
				next if ($data[2] !~ /$search/);
			}
			if (($data[4] !~ /Queued/) && !grep(/^$data[2]$/, @{$local_stat{$data[1]}{rcpt}}) ) {
				push(@{$local_stat{$data[1]}{rcpt}}, $data[2]);
				push(@{$local_stat{$data[1]}{rcpt_relay}}, $data[3]);
				push(@{$local_stat{$data[1]}{status}}, $data[4]);
			}
		}
		close(IN);
	}
	$file = "$path/senders.dat";
	# Format: Hour:Id:Sender:Size:Nrcpts:Relay
	if (open(IN, $file)) {
		my $i = 0;
		while (my $l = <IN>) { 
			chomp($l);
			# Format: Hour:Id:Sender:Size:Nrcpts:Relay
			my @data = split(/:/, $l);
			$data[0] =~ /^(\d{2})/;
			next if (($hour ne '') && ($1 != $hour));
			$data[2] ||= '<>';
			next if (!exists $local_stat{$data[1]});
			if ($peri eq 'relay') {
				next if ($data[5] !~ /$search/);
			}
			$local_stat{$data[1]}{hour} = $data[0];
			$local_stat{$data[1]}{sender} = $data[2];
			$local_stat{$data[1]}{size} = $data[3];
			$local_stat{$data[1]}{nrcpt} = $data[4];
			$local_stat{$data[1]}{sender_relay} = $data[5];
		}
		close(IN);
	}
	foreach my $id (keys %local_stat) {
		if ($peri eq 'relay') {
			if (!grep(/$search/, @{$local_stat{$id}{rcpt_relay}}) && ($local_stat{$id}{sender_relay} !~ /$search/) ) {
				delete($local_stat{$id});
			}
		}
	}

	return %local_stat;
}

sub get_spaminfo_detail
{
	my ($path, $type, $peri, $search, $hour) = @_;

	my %local_stat = ();

	my $file = "$path/$type.dat";
	open(IN, $file) || return;
	while (my $l = <IN>) { 
		chomp($l);
		# Format: Hour:Id:type:score:cache:autolearn:spam
		my @data = split(/:/, $l, 7);
		$data[0] =~ /^(\d{2})/;
		next if (($hour ne '') && ($1 != $hour));
		if ($peri eq 'rule') {
			next if ($data[6] ne $search);
		} elsif ($peri eq 'score') {
			next if ($data[3] ne $search);
		} elsif ($peri eq 'autolearn') {
			next if ($data[5] ne $search);
		} elsif ($peri eq 'cache') {
			next if ($data[4] ne $search);
		}
		$local_stat{$data[1]}{hour} = $data[0];
		$local_stat{$data[1]}{score} = $data[3];
		$local_stat{$data[1]}{spam} = $data[6];
		$local_stat{$data[1]}{cache} = $data[4];
		$local_stat{$data[1]}{autolearn} = $data[5];
	}
	close(IN);

	$file = "$path/spam.dat";
	if (open(IN, $file)) {
		while (my $l = <IN>) {
			chomp($l);
			# Format: Hour:Id:From:To:Spam
			my @data = split(/:/, $l, 5);
			next if (!exists $local_stat{$data[1]});
			$local_stat{$data[1]}{sender} = $data[2];
			$local_stat{$data[1]}{spam} = "$data[4]: " . $local_stat{$data[1]}{spam};
			push(@{$local_stat{$data[1]}{rcpt}}, $data[3]);
		}
		close(IN);
	}
	$file = "$path/recipient.dat";
	if (open(IN, $file)) {
		while (my $l = <IN>) {
			chomp($l);
			# Format: Hour:Id:recipient:Relay:Status
			my @data = split(/:/, $l);
			next if (!exists $local_stat{$data[1]});
			if ($data[4] !~ /Queued/) {
				push(@{$local_stat{$data[1]}{rcpt}}, $data[2]);
				push(@{$local_stat{$data[1]}{rcpt_relay}}, $data[3]);
				push(@{$local_stat{$data[1]}{status}}, $data[4]);
			}
		}
		close(IN);
	}
	$file = "$path/senders.dat";
	# Format: Hour:Id:Sender:Size:Nrcpts:Relay
	if (open(IN, $file)) {
		while (my $l = <IN>) { 
			chomp($l);
			# Format: Hour:Id:Sender:Size:Nrcpts:Relay
			my @data = split(/:/, $l);
			next if (!exists $local_stat{$data[1]});
			$local_stat{$data[1]}{sender} = $data[2];
			$local_stat{$data[1]}{size} = $data[3];
			$local_stat{$data[1]}{nrcpt} = $data[4];
			$local_stat{$data[1]}{sender_relay} = $data[5];
		}
		close(IN);
	}

	return %local_stat;
}

sub get_virus_detail
{
	my ($path, $peri, $search, $hour) = @_;

	my %local_stat = ();

	my $file = "$path/virus.dat";
	if (open(IN, $file)) {
		while (my $l = <IN>) {
			chomp($l);
			# Format: Hour:Id:file:virus
			my @data = split(/:/, $l, 4);
			$data[0] =~ /^(\d{2})/;
			next if (($hour ne '') && ($1 != $hour));
			if ($peri eq 'virus') {
				next if ($data[3] !~ /$search/);
			} elsif ($peri eq 'file') {
				next if ($data[2] !~ /$search/);
			}
			$local_stat{$data[1]}{hour} = $data[0] if (!exists $local_stat{$data[1]}{hour});
			$local_stat{$data[1]}{file} = $data[2];
			$local_stat{$data[1]}{virus} = $data[3];
		}
		close(IN);
	}

	$file = "$path/senders.dat";
	# Format: Hour:Id:Sender:Size:Nrcpts:Relay
	if (open(IN, $file)) {
		while (my $l = <IN>) { 
			chomp($l);
			# Format: Hour:Id:Sender:Size:Nrcpts:Relay
			my @data = split(/:/, $l);
			$data[0] =~ /^(\d{2})/;
			next if (($hour ne '') && ($1 != $hour));
			$data[2] ||= '<>';
			next if (!exists $local_stat{$data[1]});
			if ($peri eq 'sender') {
				next if ($data[3] ne $search);
			} elsif ($peri eq 'relay') {
				next if ($data[2] ne $search);
			}
			$local_stat{$data[1]}{hour} = $data[0];
			$local_stat{$data[1]}{sender} = $data[2];
			$local_stat{$data[1]}{size} = $data[3];
			$local_stat{$data[1]}{nrcpt} = $data[4];
			$local_stat{$data[1]}{sender_relay} = $data[5];
		}
		close(IN);
	}

	$file = "$path/recipient.dat";
	if (open(IN, $file)) {
		while (my $l = <IN>) {
			chomp($l);
			# Format: Hour:Id:recipient:Relay:Status
			my @data = split(/:/, $l);
			$data[0] =~ /^(\d{2})/;
			next if (($hour ne '') && ($1 != $hour));
			next if (!exists $local_stat{$data[1]});
			if ($peri eq 'recipient') {
				next if ($data[2] !~ /$search/);
			}
			if ($data[4] !~ /Queued/) {
				push(@{$local_stat{$data[1]}{rcpt}}, $data[2]);
				push(@{$local_stat{$data[1]}{rcpt_relay}}, $data[3]);
				push(@{$local_stat{$data[1]}{status}}, $data[4]);
			} else {
				push(@{$local_stat{$data[1]}{rcpt}}, $data[2]);
			}
		}
		close(IN);
	}
	return %local_stat;
}

sub get_dsn_detail
{
	my ($path, $peri, $search, $hour) = @_;

	my %local_stat = ();
	my %sourceid = ();
	my $file = "$path/dsn.dat";
	if (open(IN, $file)) {
		while (my $l = <IN>) {
			chomp($l);
			# Format: Hour:Id:SourceId:Status
			my @data = split(/:/, $l, 4);
			$data[0] =~ /^(\d{2})/;
			next if (($hour ne '') && ($1 != $hour));
			if ($peri eq 'dsnstatus') {
				next if ($data[3] !~ /$search/);
			}
			$local_stat{$data[1]}{hour} = $data[0] if (!exists $local_stat{$data[1]}{hour});
			push(@{$local_stat{$data[1]}{dsnstatus}}, $data[3]);
			$local_stat{$data[1]}{srcid} = $data[2];
			$sourceid{$data[2]} = $data[1];
		}
		close(IN);
	}

	$file = "$path/senders.dat";
	# Format: Hour:Id:Sender:Size:Nrcpts:Relay
	if (open(IN, $file)) {
		while (my $l = <IN>) { 
			chomp($l);
			# Format: Hour:Id:Sender:Size:Nrcpts:Relay
			my @data = split(/:/, $l);
			$data[0] =~ /^(\d{2})/;
			next if (($hour ne '') && ($1 != $hour));
			$data[2] ||= '<>';
			next if (!exists $local_stat{$data[1]});
			$local_stat{$data[1]}{hour} = $data[0];
			$local_stat{$data[1]}{sender} = $data[2];
			$local_stat{$data[1]}{size} = $data[3];
			$local_stat{$data[1]}{nrcpt} = $data[4];
			$local_stat{$data[1]}{sender_relay} = $data[5];
		}
		close(IN);
	}

	$file = "$path/recipient.dat";
	if (open(IN, $file)) {
		while (my $l = <IN>) {
			chomp($l);
			# Format: Hour:Id:recipient:Relay:Status
			my @data = split(/:/, $l);
			$data[0] =~ /^(\d{2})/;
			next if (($hour ne '') && ($1 != $hour));
			next if ($data[4] =~ /Queued/);
			if (exists $local_stat{$data[1]}) {
				push(@{$local_stat{$data[1]}{rcpt}}, $data[2]);
				push(@{$local_stat{$data[1]}{rcpt_relay}}, $data[3]);
				push(@{$local_stat{$data[1]}{status}}, $data[4]);
			} elsif (exists $sourceid{$data[1]}) {
				$local_stat{$sourceid{$data[1]}}{orig_rcpt} = $data[2];
			}
		}
		close(IN);
	}
	%sourceid = ();
	foreach my $k (keys %local_stat) {
		delete $local_stat{$k} if (!exists $local_stat{$k}{dsnstatus});
	}
	return %local_stat;
}

sub check_auth
{
	# Allow if site with no auth or user is an admin
	return 1 if (!$ENV{REMOTE_USER} || !$CONFIG{ADMIN} || grep(/^$ENV{REMOTE_USER}$/, split(/[\s\t,;]+/, $CONFIG{ADMIN})));

	# If the domain is not in the domain list
	if ($DOMAIN && grep(/^$DOMAIN$/, @{$CONFIG{DOMAIN_USER}{$ENV{REMOTE_USER}}}) ) {
		return 1;
	} else {
		&logerror("Access denied.");
	}
	return 0;

}

sub decode_str
{
        my ($str) = @_;

	$str =~ s/=\?(.*?)\?Q\?(.*?)\?=/decode_qp($2)/ige;
	$str =~ s/=\?(.*?)\?B\?(.*?)\?=/decode_base64($2)/ige;

	return $str;
}



####
# Display all host statistics collected
####
sub get_list_host
{
	if (not opendir(DIR, "$CONFIG{OUT_DIR}")) {
		&logerror("Can't open directory $CONFIG{OUT_DIR}: $!\n");
		return;
	}
	my @dirs = grep { !/^\./ && -d "$CONFIG{OUT_DIR}/$_" } readdir(DIR);
	closedir(DIR);

	return @dirs;	
}

####
# Normalyze CGI parameters.
####
sub secure_params
{
	if ($HOST && ($HOST =~ s/[^a-z0-9\-\_\.\@]//ig)) {
		return "host: $HOST";
	} elsif ($CURDATE && ($CURDATE =~ s/[^0-9\/]//g)) {
		return "date: $CURDATE";
	} elsif ($DOMAIN && ($DOMAIN =~ s/[^a-z0-9\-\_\.\@]//ig)) {
		return "domain: $DOMAIN";
	} elsif ($TYPE && ($TYPE =~ s/[^a-z\_]//ig)) {
		return "type: $TYPE";
	} elsif ($HOUR && ($HOUR =~ s/[^0-9]//g)) {
		return "hour: $HOUR";
	} elsif ($LANG && ($LANG =~ s/[^a-z\_]//ig)) {
		return "lang: $LANG";
	} elsif ($VIEW && ($VIEW =~ s/[^a-z]//g)) {
		return "view: $VIEW";
	} elsif ($PERI && ($PERI =~ s/[^a-z]//g)) {
		return "peri: $PERI";
	}

	return "";
}

####
# Return current date of the form YYYY/MM/DD
####
sub get_curdate
{
	my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time);
	$mon++;
	$mon = sprintf("%02d", $mon);
	$mday = sprintf("%02d", $mday);
	$year += 1900;

	return "$year/$mon/$mday"

}
