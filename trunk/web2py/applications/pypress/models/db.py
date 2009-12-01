# try something like
try:
    #db=SQLDB("sqlite://db.db")
    db=DAL("sqlite://db.db")
except:
    db=DAL("gae")
    session.connect(request,response,db=db )
#print db.tables

import datetime

db.define_table('posts',
    #SQLField('post_title', required=True),
    #SQLField('post_text', 'text'),
    #SQLField('post_time', 'datetime', default=datetime.datetime.today()),
    #SQLField('post_type', required=True),
    #SQLField('post_category', required=True))
    Field('post_title', required=True),
    Field('post_text', 'text'),
    Field('post_time', 'datetime', default=datetime.datetime.today()),
    Field('post_type', required=True),
    Field('post_category', required=True))
    #Field('post_category_ids', required=True))
    

db.define_table('comments',
    #SQLField('post_id', db.posts, required=True),
    #SQLField('comment_author'),
    #SQLField('comment_author_email', required=True),
    #SQLField('comment_author_website'),
    #SQLField('comment_text', 'text', required=True),
    #SQLField('comment_time', 'datetime', required=True, default=datetime.datetime.today()))
    Field('post_id', db.posts, required=True),
    Field('comment_author'),
    Field('comment_author_email', required=True),
    Field('comment_author_website'),
    Field('comment_text', 'text', required=True),
    Field('comment_time', 'datetime', required=True, default=datetime.datetime.today()))

db.define_table('categories',
    #SQLField('category_name', required=True))
    Field('category_name', required=True))
    
db.define_table('links',
    #SQLField('link_title', required=True),
    #SQLField('link_url', required=True))
    Field('link_title', required=True),
    Field('link_url', required=True))

db.posts.post_type.requires = IS_IN_SET(['post', 'page'])
#db.posts.post_category.requires = IS_IN_DB(db, 'categories.id', 'categories.category_name')

post_labels = {
    'post_title':'Title',
    'post_text':'Post',
    'post_time':'Post Date',
    'post_type':'Type',
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