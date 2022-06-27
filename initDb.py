
from app import app, db,users_messages, Users, Messages

db.create_all()

# user1 = Users(username="user1",password="12345678", uuid="user1")
# user2 = Users(username="user2", password="12345678", uuid="user2")

# r1 = Messages(message="xup", sender="user1")
# r2 = Messages(message="yo", sender="user2")
# r3 = Messages(message="how far", read=True, sender="user1")
# db.session.add_all([user1,user2, r1, r2, r3])
# users = Users.query.all()
# message = Messages.query.filter_by(id=1).first()
# for user in users:
#     message.participants.append(user)
# message = Messages.query.filter_by(id=2).first()
# for user in users:
#     message.participants.append(user)
# print(message.participants)
# db.session.commit()