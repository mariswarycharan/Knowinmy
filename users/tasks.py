from celery import shared_task
from django.db import transaction
from django.contrib.auth.models import User, Group
import pandas as pd
from .models import TrainerLogDetail, StudentLogDetail
from django.core.files.storage import default_storage
from django.utils import timezone


print("llllllllllllllllllllllll")
@shared_task()
def process_excel_file( file_path, admin_user_id, no_of_persons_onboard_by_client):
    print(no_of_persons_onboard_by_client,"kkkkkkkkkkkkkkkkkkkkkkkkk")
    print(admin_user_id,"pppppppppppppppppppppppppppppppppppppppp  ")
    try:
        # Load the file from storage
        print("users....")
        file_full_path = default_storage.path(file_path)
        print(file_full_path,"ooooooooooooooooooooooooooooooooooooooo")
        print("ooooooooooooooooooooooooooooooooooooooooookfndkmnm o")
        df = pd.read_excel(file_full_path, nrows=no_of_persons_onboard_by_client, engine='openpyxl')
        print(df,"lolllll")
        
        user_objs = []
        role_dict = {}
        
        with transaction.atomic():
            for i, row in df.iterrows():
                username = row['username']
                email = row['email']
                first_name = row['first_name']
                last_name = row['last_name']
                password = row['password']
                role = row['roles'].lower()

                user_details = User(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                )
                user_details.set_password(password)
                user_objs.append(user_details)
                role_dict[username] = role

            User.objects.bulk_create(user_objs)
            
            # Fetch admin_user instance
           
            admin_user = User.objects.get(id=admin_user_id)
            print(admin_user,"lolllllllllll")

            for user in user_objs:
                role = role_dict[user.username]
                group, _ = Group.objects.get_or_create(name=role.capitalize())
                user.groups.add(group)
                print(f"Added {user.username} to group {group.name}")

                if role == 'trainer':
                    TrainerLogDetail.objects.create(
                        trainer_name=user,
                        onboarded_by=admin_user,
                        no_of_asanas_created=0,
                        created_at=timezone.now(),
                        updated_at=timezone.now()
                    )
                else:
                    StudentLogDetail.objects.create(
                        student_name=user,
                        added_by=admin_user,
                        created_at=timezone.now(),
                        updated_at=timezone.now()
                    )
        
        # Cleanup the uploaded file
        default_storage.delete(file_path)
        return f"Users onboarded successfully???"
        
    except Exception as e:
        print(f"Error processing file: {e}")
