import os
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, select
from sqlalchemy.orm import sessionmaker

from models.application import Application
from models.user import User

load_dotenv()

# SQLALCHEMY cheatsheet

    # # # Advanced Filtering Patterns 

    # stmt = select(Application).where(
    #     Application.status == "applied",
    #     Application.company.ilike("%Nagarro%") # Case-insensitive partial match
    # )

    # # Explicit OR condition
    # stmt = select(Application).where(
    #     or_(Application.status == "interview", Application.status == "offer")
    # )

    # status_list = ["applied", "interviewing"]
    # stmt = select(Application).where(Application.status.in_(status_list))

    # # Shorthand for: .where(Application.status == "applied")
    # stmt = select(Application).filter_by(status="applied")

    # # # Precise Result Fetching Operators

    # session.get(Model, id)	
    # Fetches directly by Primary Key. Bypasses writing a full select() statement entirely. Checks identity map first.	
    # Fetching a single row by ID (highly optimized).

    # .one_or_none()	
    # Returns exactly one object or None. Raises an error if multiple rows match.	
    # Safe unique queries (e.g., lookup by unique slug or email).

    # .first()	
    # Returns the first result or None. Does not throw an error if multiple match.	
    # Getting the latest record or when you don't care about duplicates.

    # .one()	
    # Returns exactly one object. Raises an exception if None or if multiple rows match.	
    # Crucial endpoints where missing data indicates a critical application error.

    # # # Performance & Scaling

    # Pagination for get_all endpoints:
    # def retrieve_all_paginated(session, page: int = 1, per_page: int = 20):
    # stmt = (
    #     select(Application)
    #     .order_by(Application.id)
    #     .limit(per_page)
    #     .offset((page - 1) * per_page)
    # )
    # return session.scalars(stmt).all()


    # If Application model has relationships (belongs to an User, etc.), SQLAlchemy defaults to Lazy Loading ==> N+1 query problem ==> eager loading to fix (fetches relationships in a single optimized query)
    # Pre-fetches the 'interviews' relationship simultaneously
    # stmt = select(Application).options(selectinload(Application.interviews))


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

# APPLICATIONS

def retrieve_applications_all_alchemy(session):
    stmt = select(Application).order_by(Application.id)
    applications = session.scalars(stmt).all()

    all_apps = [app.to_dict() for app in applications]

    # OLD
    # for app in applications:
    #     all_apps.append({
    #         "id": app.id,
    #         "company": app.company,
    #         "title": app.title,
    #         "date_applied": app.date_applied,
    #         "status": app.status,
    #         "date_interview": app.date_interview
    #     })
    return all_apps

def retrieve_application_id_alchemy(session, app_id):
    # OLD
    # stmt = select(Application).where(Application.id == app_id)
    # application: Application | None = session.scalars(stmt).one_or_none()

    # cleaner alternative, fetches directly by primary key
    application = session.get(Application, app_id)

    if application is None:
        return None
    
    return application.to_dict()

def insert_application_alchemy(session, data):
    app = Application(**data)
    session.add(app)
    session.flush()
    session.refresh(app)

    return app.to_dict()

def update_application_id_alchemy(session, app_id, data):
    # if not data:
    #     return None
    application = session.get(Application, app_id)

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

def delete_application_id_alchemy(session, app_id):
    application = session.get(Application, app_id)

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