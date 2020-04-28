FROM httpd

RUN apt-get update -yqq && apt-get install -y \
  build-essential \
  cron \
  git \
  perl \
  supervisor \
  procps \
  libcgi-session-perl \
  && apt-get clean

RUN git clone https://github.com/darold/sendmailanalyzer.git /tmp/sendmailanalyzer

WORKDIR /tmp/sendmailanalyzer

RUN perl Makefile.PL && make && make install && rm -rf /tmp/sendmailanalyzer

WORKDIR /usr/local/sendmailanalyzer

COPY supervisord.conf /etc/supervisor/supervisord.conf

COPY httpd.conf /usr/local/apache2/conf/httpd.conf

COPY sa_cache.sh /etc/cron.daily/sa_cache.sh

RUN mkdir -p /var/www/htdocs

CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]

