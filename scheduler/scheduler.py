
from .models import Player, TimeSlot, Match, Team

def no_restriction_schedule( schedule):
    list = TimeSlot.objects.all() #filter by each time slot in each day consecutively, and get the player names

    #each item in list is a list of players
    for item in list:
        if len(item.players_available) > 12:
            print("" + item.dayOfWeek + ":" + item.hour)







