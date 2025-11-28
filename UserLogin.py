from flask import url_for
from flask_login import UserMixin

from services import UserService


class UserLogin(UserMixin):
    def fromDB(self, db, user_id):
        user_service = UserService(db)
        self.__user = user_service.get_user_by_id(user_id=user_id)
        return self

    def create(self, user):
        self.__user = user
        return self

    def get_id(self):
        return str(self.__user.id)

    def getSurname(self):
        return self.__user.surname if self.__user else "Без фамилии"

    def getName(self):
        return self.__user.name if self.__user else "Без имени"

    def getEmail(self):
        return self.__user.email if self.__user else "Без Email"

    def getPhone(self):
        return self.__user.phone if self.__user else "Номер не известен"

    def getAvatar(self, app):
        img = None
        if not self.__user.avatar:
            try:
                with app.open_resource(app.root_path + url_for('static', filename="images/default.png"), 'rb') as f:
                    img = f.read()
            except FileNotFoundError as e:
                print("Не найден аватар по умолчанию: " + str(e))
        else:
            img = self.__user.avatar

        return img

    def verifyExt(self, filename):
        ext = filename.split('.', 1)[-1]
        if ext == 'png' or ext == 'PNG':
            return True
        return False