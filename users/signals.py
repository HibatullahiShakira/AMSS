# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.core.mail import send_mail
# from .models import User, Business
#
#
# @receiver(post_save, sender=User)
# def send_business_email_verification(sender, instance, created, **kwargs):
#     if created:
#         business = instance.business
#         if business and business.business_email:
#             token = business.generate_verification_token()
#             #
#             email_subject = 'Verify your business email'
#             email_message = f'Please use the following token to verify your business email: {token}'
#             from_email = 'AMS@gmail.com'
#             recipient_list = [business.business_email]
#
#             send_mail(
#                 email_subject,
#                 email_message,
#                 from_email,
#                 recipient_list,
#                 fail_silently=False,
#             )
