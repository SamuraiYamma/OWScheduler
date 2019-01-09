OWScheduler
==========

This program is intended for use by Users who want to generate balanced scrimmages

Below you will find the project goals with every release.

## Alpha

* **User Profiles**
    - Create user profile objects
    
* **Database**
    - Store user profiles
    
* **Engine**
    - View items in the database

## Version 1

* **User Profiles**
    - User can create a profile where they input their Battlenet ID, Name, University, Schedule, Emails, Rank and Roles
    
* **Database**
    - Stores user profiles
        - Name
        - Battlenet ID
        - University
        - Schedule
        - Email
        - Rank
        - Role(s)
    - Match statistics
        - Who won
        - Map
        - Players
            - Roles played
            - Characters played
        - KDA ?
        - 
    
* **Scheduler**
    - Makes multiple schedules based on factors of Schedules, Rank, Role
        - TODO: decide precedence. Which is most important?
    - This is initiated by a User who makes a list of all the Users (By Battle.net ID) they want to have a scrimmage with (A list of 12 or more users). Once everyone has been added to a list, you can simply hit "Make matches" to get all possible schedules. User should be able to choose which times they wish to view.
        - Might consider separating users from matchmakers here. Should everyone be able to make matches? Or rather, does everyone want/need to make matches?
     
* **Prompter**
    - Takes the generated scheduler and prompts all associated users if it is acceptable
        - Who does this prompt?
    - If schedule is denied, then the schedule is reworked and is sent out again
        - What changes when schedule is reworked?
    - Once matches begin, it waits for the input of Win/Loss statistics to attach to each User Profile
        - This also take into account what map was played
        - Should allow matchmakers to edit results after they've accepted the match setup

## Version 2

* **Scheduler**
    - Add a function to add Universities
    
* **Statistics access**
    - Gives users access to their own stats, as well as the stats of the people at their university
    
* **Web Portal**
    - Have a web page where users can go to log in and review/change their information

## Version 3

* **Make option for creating a schedule optimized by map win rates**

* **Discord Linked**
    - Auto create chat groups/teams bby moving users to different channels for scrims, help automation of processes

## Version 4
* **Mobile App**
