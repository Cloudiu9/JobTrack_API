import os
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, select
from sqlalchemy.orm import sessionmaker
from models.application import Application
from models.user import User

load_dotenv()

DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME =os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")

DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME
)

engine = create_engine(
    DATABASE_URL,
)

SessionFactory = sessionmaker(
    bind=engine,
)

# HELPER
def _get_user_application(session, app_id: int, user_id: int) -> Application | None:
    application = session.get(Application, app_id)
    if application is None or application.user_id != user_id:
        return None
    return application

# APPLICATIONS

def retrieve_applications_alchemy(session, user_id: int, page: int, limit: int):
    # offset = skip offset many applications
    # if on first page, don't skip any, get limit first apps
    # if page > 1, skip first page, decrement page by 1 because first page is 1 not 0
    if page == 1:
        offset = 0
    else:
        offset = (page - 1) * limit

    stmt = select(Application).where(Application.user_id == user_id).order_by(Application.id).limit(limit).offset(offset)
    applications = session.scalars(stmt).all()

    # for user privacy, to_dict excludes user_id
    user_apps = [app.to_dict() for app in applications]

    return user_apps

def retrieve_application_id_alchemy(session, app_id, user_id):
    # cleaner alternative, fetches directly by primary key
    application = _get_user_application(session, app_id, user_id)

    if application is None:
        return None
    
    return application.to_dict()

def insert_application_alchemy(session, data):
    app = Application(**data)
    session.add(app)
    session.flush()
    session.refresh(app)

    return app.to_dict()

def update_application_id_alchemy(session, app_id, data, user_id):
    # if not data:
    #     return None
    application = _get_user_application(session, app_id, user_id)

    if application is None:
        return None

    # seems to be wrong, doesn't cause actual changes in the DB
    # because it just works on a copy of the application
    # to_dict() created a copy
    # application_dict = application.to_dict()

    # for column in application_dict.keys():
    #     if column in data:
    #         application_dict[column] = data[column]

    all_columns = set(Application.__table__.columns.keys())
    excluded_columns = {"id"}

    valid_columns = all_columns - excluded_columns

    for key, value in data.items():
        if key in valid_columns:
            setattr(application, key, value)

    return application.to_dict()

def delete_application_id_alchemy(session, app_id, user_id):
    application = _get_user_application(session, app_id, user_id)

    if application is None:
        return None

    application_dict = application.to_dict()

    session.delete(application)
    return application_dict

# USER

def register_user_alchemy(session, data):
    new_user = User(**data)
    session.add(new_user)
    session.flush()
    session.refresh(new_user)

    return new_user.to_dict()

def get_user_by_email_alchemy(session, email):
    stmt = select(User).where(User.email == email)
    registered_user = session.scalar(stmt)

    return registered_user

def retrieve_users_all_alchemy(session):
    stmt = select(User).order_by(User.id)
    users = session.scalars(stmt).all()

    all_users = [user.to_dict() for user in users]

    return all_users

def retrieve_user_id_alchemy(session, user_id):
    user = session.get(User, user_id)

    if user is None:
        return None
    
    return user.to_dict()