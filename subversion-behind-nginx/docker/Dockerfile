FROM debian:jessie
MAINTAINER paxnil <root@paxnil.com>

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y apache2-mpm-prefork libapache2-mod-svn websvn && apt-get clean

COPY 000-default.conf /etc/apache2/sites-available/
COPY mod_auth_remote.so /usr/lib/apache2/modules/
RUN echo "Listen 8081" > /etc/apache2/ports.conf
RUN echo "ServerName 127.0.0.1" >> /etc/apache2/apache2.conf
RUN echo "umask 002" >> /etc/apache2/envvars
RUN echo "LoadModule auth_remote_module /usr/lib/apache2/modules/mod_auth_remote.so" > /etc/apache2/mods-available/auth_remote.load
RUN ln -s ../mods-available/auth_remote.load /etc/apache2/mods-enabled/
RUN sed -i 's/www-data/svn-data/g' /etc/apache2/envvars
RUN sed -i 's/^LogLevel warn/LogLevel crit/g' /etc/apache2/apache2.conf
RUN rm /etc/apache2/conf-enabled/other-vhosts-access-log.conf

RUN mv /etc/websvn/config.php /etc/websvn/config.php~
RUN ln -s /srv/subversion/etc/websvn-config.php /etc/websvn/config.php

RUN groupadd -g 41011 svn-data
RUN useradd -u 41011 -g 41011 svn-data

EXPOSE 8081
CMD ["/usr/sbin/apache2ctl", "-D", "FOREGROUND"]
