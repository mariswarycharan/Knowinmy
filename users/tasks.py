from celery import shared_task
from django.db import transaction
from django.contrib.auth.models import User, Group
import pandas as pd
from .models import *
from django.core.files.storage import default_storage
from django.utils import timezone
from django.db.models import F

@shared_task
def process_excel_file(file_path, admin_user_id, no_of_persons_onboard_by_client, tenant_id):
    tenant = Tenant.objects.get(id=tenant_id)
    print(no_of_persons_onboard_by_client, "kkkkkkkkkkkkkkkkkkkkkkkkk")
    print(admin_user_id, "pppppppppppppppppppppppppppppppppppppppp")
    print(tenant,"line no 14 from tasks.py ")

    try:
        print("Starting file processing...")
        # Load the file from storage
        file_full_path = default_storage.path(file_path)
        print(file_full_path, "File path")

        df = pd.read_excel(file_full_path, nrows=no_of_persons_onboard_by_client, engine='openpyxl')
        print(df, "DataFrame loaded")

        user_objs = []
        role_dict = {}
        trainer_count = 0
        student_count = 0

        with transaction.atomic():
            for i, row in df.iterrows():
                print(f"Processing row {i}: {row}")
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

            # Bulk create users
            User.objects.bulk_create(user_objs)
            print("Users created")

            # Fetch admin_user instance
            admin_user = User.objects.get(id=admin_user_id)
            print(admin_user, "Admin user fetched")

            # Fetch or create ClientOnboarding record for admin_user
            client_onboarding, created = ClientOnboarding.objects.get_or_create(
                client=admin_user, tenant=tenant)
            print(client_onboarding, "ClientOnboarding fetched or created")

            if client_onboarding:
                print("Entered if block")
                for user in user_objs:
                    role = role_dict[user.username]
                    print(f"User {user.username} role: {role}")
                    group, _ = Group.objects.get_or_create(name=role.capitalize())
                    user.groups.add(group)
                    print(f"Added {user.username} to group {group.name}")

                    if role == 'trainer':
                        TrainerLogDetail.objects.create(
                            trainer_name=user,
                            onboarded_by=admin_user,
                            no_of_asanas_created=0,
                            created_at=timezone.now(),
                            updated_at=timezone.now(),
                            tenant=tenant
                        )
                        trainer_count += 1
                        print(f"Trainer count updated: {trainer_count}")

                    else:
                        StudentLogDetail.objects.create(
                            student_name=user,
                            added_by=admin_user,
                            created_at=timezone.now(),
                            updated_at=timezone.now(),
                            tenant=tenant
                        )
                        student_count += 1
                        print(f"Student count updated: {student_count}")

                # Update ClientOnboarding only once after processing all users
                print(f"Updating ClientOnboarding - Trainers: {trainer_count}, Students: {student_count}")
                client_onboarding.trainers_onboarded += trainer_count
                client_onboarding.students_onboarded += student_count
                client_onboarding.save()  # Save the updated counts to the database
                print(f"Updated ClientOnboarding: Trainers {client_onboarding.trainers_onboarded}, Students {client_onboarding.students_onboarded}")
            else:
                print("CLIENT ONBOARDINGS NOT FOUND")

        # Cleanup the uploaded file
        default_storage.delete(file_path)
        return "Users onboarded successfully?"

    except Exception as e:
        print(f"Error processing file: {e}")
        return f"Error processing file: {e}"
