import django_tables2 as tables
from .models import *



class ClientTable(tables.Table):
    trainers_onboarded=tables.Column(verbose_name="Number trainers onboarded",accessor='clientonboarding.trainers_onboarded')
    students_onboarded =tables.Column(verbose_name="Numberof students onboarded ",accessor='clientonboarding.students_onboarded')
    class Meta:
        model=Order
        fields=('name','subscription','amount','status')