import os
import secrets
from PIL import Image, ExifTags
from flask import url_for, current_app
from flask_mail import Message
from flaskblog import mail


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)

    output_size = (250, 250)
    i = Image.open(form_picture)

    # Handle EXIF orientation
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = dict(i._getexif().items())

        if exif[orientation] == 3:
            i = i.rotate(180, expand=True)
        elif exif[orientation] == 6:
            i = i.rotate(270, expand=True)
        elif exif[orientation] == 8:
            i = i.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        # cases: image doesn't have getexif
        pass

    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', 
                  sender='admin@learn-catalan.com', 
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('users.reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this message and no changes will be made
'''
    mail.send(msg)