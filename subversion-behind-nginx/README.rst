#######################
Subversion behind nginx
#######################

=======
Content
=======

docker
	Apache2, Subversion and WebSVN running in debian container,
	repositories stored at /srv/subversion 

kkauthd
	Authentication daemon for nginx's module_http_auth_request
	
	Requirements:
	
	* beaker
	* bottle
	* peewee
	* pymysql
	* uWSGI

mod_auth_remote
	Retrive username from request header

nginx
	nginx configruation files

srv-subversion
	/srv/subversion
