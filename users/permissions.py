from unicodedata import name

def check_client(user):
    if user.is_superuser:
        return True
    return user.groups.filter(name="Client").exists() 

def check_trainer(user):
    if user.is_superuser:
        return True
    return user.groups.filter(name="Trainer").exists()  or  check_client(user) 

def check_student(user):
    if user.is_superuser:
        return True
    return user.groups.filter(name="Student").exists() or check_trainer(user) or user.is_superuser or check_client(user) 

def check_superuser(user):
    return user.is_superuser