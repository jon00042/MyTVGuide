import sqlalchemy

from db.base import DbManager
from db.entities import Like, Show, User

db = DbManager()

def create_user(email, fullname, hashed_pw):
    user = User()
    user.email = email
    user.fullname = fullname
    user.hashed_pw = hashed_pw
    return db.save(user)

def get_user_by_email(email):
    return db.open().query(User).filter(User.email == email).one()

def get_user_by_id(user_id):
    return db.open().query(User).filter(User.id == user_id).one()

def save_show(api_id, title, image_url):
    try:
        show = db.open().query(Show).filter(Show.api_id == api_id).one()
        return show
    except sqlalchemy.orm.exc.NoResultFound:
        pass
    except Exception as ex:
        print(ex)
    show = Show()
    show.api_id = api_id
    show.title = title
    show.image_url = image_url
    try:
        db.save(show)
    except Exception as ex:
        print(ex)
    return show

def add_like(user_id, show_id):
    user = db.open().query(User).filter(User.id == user_id).one()
    show = db.open().query(Show).filter(Show.id == show_id).one()
    like = Like()
    like.user = user
    like.show = show
    db.save(like)

def del_like(user_id, show_id):
    like = db.open().query(Like).filter(sqlalchemy.and_(Like.user_id == user_id, Like.show_id == show_id)).one()
    db.delete(like)

