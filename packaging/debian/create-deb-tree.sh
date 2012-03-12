#!/bin/sh
#
# Script used to create the Debian package tree. This script must be
# executed in his directory
#
cd ../../
perl Makefile.PL \
  INSTALLDIRS=vendor \
  QUIET=1 \
  LOGFILE=/var/log/mail.log \
  BINDIR=/usr/bin \
  CONFDIR=/etc \
  PIDDIR=/var/run \
  BASEDIR=/var/lib/sendmailanalyzer \
  HTMLDIR=/usr/share/apache2/sendmailanalyzer \
  MANDIR=/usr/share/man/man3 \
  DOCDIR=/usr/share/doc/sendmailanalyzer \
  DESTDIR=packaging/debian/sendmailanalyzer || exit 1

make && make install

cd packaging/debian/
