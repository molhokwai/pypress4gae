# try something like
try:
    db=DAL("sqlite://db.db")
except:
    db=DAL("gae")
    session.connect(request,response,db=db )

import base64
import datetime

db.define_table('blog_info',
    Field('name', required=True),
    Field('title'),
    Field('description'),
    Field('keywords'))

db.define_table('users',
    Field('alias'),
    Field('email', required=True),
    Field('password','password', required=True),
    Field('post_time','datetime', default=datetime.datetime.today()))

db.define_table('posts',
    Field('post_title', required=True),
    Field('post_text', 'text'),
    Field('post_time', 'datetime', default=datetime.datetime.today()),
    Field('post_type', required=True),
    Field('post_author', required=True),
    Field('post_category', required=True))
    

db.define_table('comments',
    Field('post_id', db.posts, required=True),
    Field('comment_author'),
    Field('comment_author_email', required=True),
    Field('comment_author_website'),
    Field('comment_text', 'text', required=True),
    Field('comment_time', 'datetime', required=True, default=datetime.datetime.today()))

db.define_table('categories',
    Field('category_name', required=True))
    
db.define_table('links',
    Field('link_title', required=True),
    Field('link_url', required=True))

db.posts.post_type.requires = IS_IN_SET(['post', 'page'])
db.posts.post_author.requires = IS_IN_DB(db, 'user.id', 'user.alias')
db.posts.post_category.requires = IS_IN_DB(db, 'categories.id', 'categories.category_name')

user_labels = {
    'alias':'Alias',
    'email':'Email',
    'password':'Password',
    'post_time':'Post Date'
}

post_labels = {
    'post_title':'Title',
    'post_text':'Post',
    'post_time':'Post Date',
    'post_type':'Type',
    'post_author':'Author',
    'post_category':'Category'
}

comment_labels = {
    'comment_author':'Name',
    'comment_author_email':'Email',
    'comment_author_website':'Website',
    'comment_text':'Comment',
    'post_id':'Post ID'
}

link_labels = {
    'link_title':'Name',
    'link_url':'URL'
}

cat_labels = {
    'category_name':'Name'
}

def database_init():
    if not db().select(db.blog_info.ALL):
        db.users.insert(alias='admin',email='admin',password=base64.b64encode('admin'))
        admin=db().select(db.users.ALL)[0]

        db.blog_info.insert(
                        name='[web2py] PyPress',
                        description='Just another PyPress weblog',
                        title='PyPress - a web2py powered weblog',
                        keywords='web2py, Gluon, Python, Enterprise, Web, Framework, PyPress')

        db.categories.insert(
                        category_name='uncategorized')
        db.categories.insert(
                        category_name='news')
                        
        cats=db().select(db.categories.ALL)

        db.posts.insert(
                        post_title='Hello world!', 
                        post_text='Welcome to PyPress. This is your first post. Edit or delete it, then start blogging!',
                        post_type='post',
                        post_author=admin.id,
                        post_category=cats[0].id)
        db.posts.insert(
                        post_title='Welcome to PyPress', 
                        post_text='This is the Python version of WordPress. Enjoy.',
                        post_type='post',
                        post_author=admin.id,
                        post_category=cats[1].id)
        
        posts=db().select(db.posts.ALL)
        
        db.comments.insert(
                        post_id=posts[0].id,
                        comment_author='Richard',
                        comment_author_email='zrx550@gmail.com',
                        comment_text="Hi, this is a comment. To delete a comment, just log in and view the post's comments. There you will have the option to edit or delete them.")
        db.comments.insert(
                        post_id=posts[0].id,
                        comment_author='Mr PyPress',
                        comment_author_email='zrx550@gmail.com',
                        comment_text='Another comment')
        db.comments.insert(
                        post_id=posts[1].id,
                        comment_author='Richard',
                        comment_author_web='http://www.google.com',
                        comment_author_email='zrx550@gmail.com',
                        comment_text='This is a comment')
        
        db.links.insert(
                        link_title='web2py',
                        link_url='http://www.web2py.com')
        db.links.insert(
                        link_title='WordPressClone',
                        link_url='http://www.web2py.com/appliances/default/show/36')
        db.links.insert(
                        link_title='pypress4gae',
                        link_url='http://code.google.com/p/pypress4gae')


database_init()
