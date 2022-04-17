from sqlalchemy import Integer, String, create_engine, Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///hhORM.sqlite', echo=False)
Base = declarative_base()


class UserT(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    password = Column(String, nullable=False)

    def __init__(self, email, password):
        self.email = email
        self.password = password


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def check_login(email, password):
    sess = Session()
    if sess.query(UserT).filter(UserT.email == email).first() is not None:
        if sess.query(UserT).filter(UserT.password == password).first() is not None:
            return True
    return False


if __name__ == '__main__':
    sess = Session()
    # session.add(UserT('asd@asfg.ru', 53453))
    # session.commit()
    print(check_login('test@test.ru', 123))