from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .firebase_service import FirebaseService

# Get the User model
User = get_user_model()

@receiver(post_save, sender=User)
def update_firebase_user(sender, instance, created, **kwargs):
    """
    Signal handler to update Firebase user when Django user is updated
    """
    if not created and instance.firebase_uid:
        # Only update Firebase if certain fields have changed
        try:
            # Prepare update properties
            properties = {}
            
            # Check for email update (requires special handling in Firebase)
            if instance.email:
                properties['email'] = instance.email
            
            # Check for display name update
            if instance.first_name or instance.last_name:
                display_name = instance.first_name
                if instance.first_name and instance.last_name:
                    display_name = f"{instance.first_name} {instance.last_name}"
                properties['display_name'] = display_name
            
            # Only make API call if there are changes to update
            if properties:
                FirebaseService.update_user(instance.firebase_uid, properties)
        except Exception as e:
            # Log the error but don't raise an exception
            print(f"Error updating Firebase user: {str(e)}")
            pass 