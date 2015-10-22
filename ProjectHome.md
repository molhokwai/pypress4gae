This project is also on github.com (http://github.com/mdmcginn/pp4gae) - not yet sure where we will keep the latest code. It was moved to solve license problems.

Developed with web2py
http://www.web2py.com

The base of this project is WordPressClone: http://www.web2py.com/appliances/default/show/36

The first step goal is to make it work on GAE.
Second step is to make basic HTML formatting work in posts, able to change the themes, create a back-end management portal. (We've made some progress in making it compatible with Wordpress's 2010 theme.)

Final goal is to make it work like a real wordpress. Advanced features like RSS/anti-spam will be implemented.

Here is a previous example (under development):
http://pp4gae.appspot.com


Release 1 (step 1 done!)
Fully works on GAE, add/edit/delete functions for post/page/link/category is ready.
Default login email and password are both 'admin'.
Remember to change password after logged in.

Known Issues: no pagination.


Download: http://pypress4gae.googlecode.com/files/pp4gae-0.1.1.tar.gz

Deploy instructions:
first>
> edit app.xml line 1 "application: {{your\_app\_name}}"
second>
> enter web2py/ and execute "appcfg.py update ./"

Notes: Maybe it won't work right after deployed, wait minutes or hours for GAE server to finish indexing the database.


Any suggestion or bug please put in to Issues of this project.