%define uname sendmailanalyzer
%define webdir %{_localstatedir}/www/%{uname}
%define rundir %{_localstatedir}/run
%define _unpackaged_files_terminate_build 0

Name: %{uname}
Epoch: 0
Version: 8.5
Release: 1%{?dist}
Summary: Sendmail/Postfix log analyser with graphical reports

Group: System Environment/Daemons
License: GPLv3+
URL: http://sareport.darold.net/
Source0: http://downloads.sourceforge.net/%{name}/%{uname}-%{version}.tar.gz
BuildArch: noarch
BuildRoot: %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

Requires: libpng
Requires: gd
Requires: httpd
Requires: perl(:MODULE_COMPAT_%(eval "`%{__perl} -V:version`"; echo $version))
Requires: vixie-cron

%description
%{uname} continuously read your mail log file to generate
periodical HTML and graph reports. All reports are shown throught
a CGI web interface. It reports all you ever wanted to know about
email trafic on your network. You can also use it in ISP environment
with per domain report.

%prep
%setup -q -n %{uname}-%{version}

# create default crontab entry
%{__cat} > %{uname}.cron << _EOF1_
# Sendmail log reporting daily cache
#0 1 * * *     root  %{_bindir}/sa_cache > /dev/null 2>&1
# Daemon restart after maillog logrotate (cron jobs at 4:04 every day)
# Feel free to replace this line by an entry in /etc/logrotate.d/syslog
#4 4 * * *     root  /etc/rc.d/init.d/sendmailanalyzer restart > /dev/null 2>&1
# On huge MTA you may want to have five minutes caching
#*/5 * * * *   root  %{_bindir}/sa_cache -a > /dev/null 2>&1

_EOF1_

# create default httpd configuration
%{__cat} > httpd-%{uname}.conf << _EOF2_
#
# By default %{uname} statistics are only accessible from the local host.
# 
#Alias /sareport %{webdir}
#
#<Directory %{webdir}>
#    Options ExecCGI
#    AddHandler cgi-script .cgi
#    DirectoryIndex sa_report.cgi
#    Order deny,allow
#    Deny from all
#    Allow from 127.0.0.1
#    Allow from ::1
#    # Allow from .example.com
#</Directory>

_EOF2_

# create README.RPM
%{__cat} > README.RPM << _EOF3_

1. Start $PNAME daemon with: /etc/rc.d/init.d/sendmailanalyzer start
   or /sbin/service sendmailanalyzer start

2. Uncomment the entries in %{_sysconfdir}/httpd/conf.d/%{uname}.conf.

3. Restart and ensure that httpd is running.

4. Browse to http://localhost/sareport/ to ensure that things are working
   properly.

5. If necessary, give additional hosts access to %{uname} by adding them to
   %{_sysconfdir}/httpd/conf.d/%{uname}.conf.

6. Setup a cronjob to run sa_cache and restart %{uname} daemon after maillog
   logrotate. Uncomment the entries in %{_sysconfdir}/cron.d/%{uname} or
   create a custom cronjob.

_EOF3_

%build
# Make Perl and SendmailAnalyzer distrib files
%{__perl} Makefile.PL \
    INSTALLDIRS=vendor \
    QUIET=1 \
    LOGFILE=/var/log/maillog \
    BINDIR=%{_bindir} \
    CONFDIR=%{_sysconfdir} \
    PIDDIR=%{rundir} \
    BASEDIR=%{_localstatedir}/lib/%{uname} \
    HTMLDIR=%{webdir} \
    MANDIR=%{_mandir}/man3 \
    DOCDIR=%{_docdir}/%{uname}-%{version} \
    DESTDIR=%{buildroot} < /dev/null
%{__make}


# nope, gotta love perl

%install
%{__rm} -rf %{buildroot}
# set up path structure
%{__install} -d -m 0755 %{buildroot}/%{_bindir}
%{__install} -d -m 0755 %{buildroot}/%{_sysconfdir}
%{__install} -d -m 0755 %{buildroot}/%{_localstatedir}/lib/%{uname}
%{__install} -d -m 0755 %{buildroot}/%{_localstatedir}/run
%{__install} -d -m 0755 %{buildroot}/%{webdir}
%{__install} -d -m 0755 %{buildroot}/%{webdir}/lang


# Make distrib files
%{__make} install \
	DESTDIR=%{buildroot}

# Remove empty perl directory
%{__rm} -rf %{buildroot}/usr/lib

%{__install} -D -m 0644 %{uname}.cron \
    %{buildroot}/%{_sysconfdir}/cron.d/%{uname}
%{__install} -D -m 0644 httpd-%{uname}.conf \
    %{buildroot}/%{_sysconfdir}/httpd/conf.d/%{uname}.conf
%{__install} -D -m 0644 doc/%{uname}.3 \
    %{buildroot}/%{_mandir}/man3/%{uname}.3
%{__install} -D -m 0644 salogo.png \
    %{buildroot}/%{webdir}/salogo.png
%{__install} -Dpm 0755 start_scripts/sendmailanalyzer %{buildroot}%{_sysconfdir}/rc.d/init.d/sendmailanalyzer

%clean
%{__rm} -rf %{buildroot}

%post
if [ $1 -eq 1 ]; then
    /sbin/chkconfig --add sendmailanalyzer
fi

%preun
if [ $1 -eq 0 ]; then
    /sbin/service sendmailanalyzer stop &>/dev/null || :
    /sbin/chkconfig --del sendmailanalyzer
fi


%files
%defattr(0644,root,root,0755)
%doc Change* INSTALL README TODO README.RPM
%attr(0755,root,root) %{_bindir}/%{uname}
%attr(0755,root,root) %{_bindir}/sa_cache
%attr(0644,root,root) %{_mandir}/man3/%{uname}.3.gz
%attr(0644,root,root) %{webdir}/salogo.png
%attr(0755,root,root) %{webdir}/grafit.cgi
%attr(0755,root,root) %{webdir}/sa_report.cgi
%attr(0644,root,root) %{webdir}/lang/ERROR_CODE
%attr(0644,root,root) %{webdir}/lang/en_US
%attr(0644,root,root) %{webdir}/lang/fr_FR
%attr(0644,root,root) %{webdir}/lang/sp_SP
%attr(0755,root,root) %{_sysconfdir}/rc.d/init.d/sendmailanalyzer
%config(noreplace) %{_sysconfdir}/%{uname}.conf
%config(noreplace) %{_sysconfdir}/cron.d/%{uname}
%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{uname}.conf
%dir %{_localstatedir}/lib/%{uname}
%dir %{_localstatedir}/run
%dir %{webdir}

%changelog
* Wed Jan 20 2010 Gilles Darold <gilles@darold.net>
- Fix overide of httpd sendmailanalyzer.conf

* Wed Dec 30 2009 Gilles Darold <gilles@darold.net>
- first packaging attempt

