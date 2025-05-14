from django.apps import AppConfig
from . import signals


class SheetsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sheets'
    def ready(self):
        """
        Initialization code that runs when Django starts.
        Useful for signal registration and other startup tasks.
        """
        # Import and register signals
verbose_name = "Handball Management"

def ready(self):
    # Import signals module after models are loaded
    from .signals import create_player_stats, update_player_stats
    from django.db.models.signals import post_save
    
    # Connect signals
    post_save.connect(
        create_player_stats, 
        sender='handball.Match',
        dispatch_uid="create_player_stats"
    )
    post_save.connect(
        update_player_stats,
        sender='handball.MatchEvent',
        dispatch_uid="update_player_stats"
    )

def ready(self):
    # Run one-time setup tasks
    if not hasattr(self, 'already_run'):
        from .setup import initialize_seasons
        initialize_seasons()
        self.already_run = True