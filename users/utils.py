from django.db.models import Avg
def calculate_asana_overall_accuracy(asana):
    return asana.postures.aggregate(Avg('accuracy'))['accuracy__avg']

def calculate_user_overall_accuracy(user):
    return user.posture_accuracies.aggregate(Avg('accuracy'))['accuracy__avg']