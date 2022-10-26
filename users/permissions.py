from unicodedata import name


def check_trainer(user):
    return user.groups.filter(name="Trainer").exists() or user.is_superuser

def check_student(user):
    return user.groups.filter(name="Student").exists() or check_trainer(user)