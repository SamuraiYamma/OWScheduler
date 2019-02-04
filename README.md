OWScheduler
==========

This program is intended for use by Users who want to generate balanced scrimmages


## Contents

* **/docs**
    -All documentation is in here
    
* **/LICENSE**
    -Refer to this for the licensing and copying rights
    
* **/testing**
    -All testing cases can be found here
   
* **/setup.py**
    -Package and Distribution management
  
* **/README.md**
    -The current document you are viewing, should contain all the information you might look for, unless it's in patch notes

Below you will find the project goals with every release.

## Required Features
These are features we need to use to receive full marks on the assignment

* **Testing**
    - Django uses Python's standard module unittest for testing. Details on writing tests can be found [here](https://docs.djangoproject.com/en/2.1/topics/testing/overview/)
    
* **Checkstyle**
    - Python has a checkstyle feature known as pycodestyle
    
* **FindBugs**
    - [Pychecker](http://pychecker.sourceforge.net) is a feature to help spot bugs in our code. There might be a better program for this.
    - [PyLint](https://www.pylint.org) seems to combine checkstyle and findbugs, but it may need to be investigated.

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
    
* **Scheduler**
    - Makes multiple schedules based on factors of Schedules, Rank, Role
        - Schedule starts by splitting players into groups by schedule. For each schedule block with 12 or more players, the players are split into two groups by roles, 
        so each group has as close to the same roles as possible. After this, if the average rank is too unequal, then swap players of the same role between teams if their rank is uneven.
    - This is initiated by a User who makes a list of all the Users (By Battle.net ID) they want to have a scrimmage with (A list of 12 or more users). Once everyone has been added to a list, you can simply hit "Make matches" to get all possible schedules. User should be able to choose which times they wish to view.
        - Matchmakers can be any user who wants to see a possible schedule with certain users. If they wish to prompt the users, they need to be a registered admin of group/university  
           
* **Prompter**
    - Takes the generated scheduler and prompts all associated users if it is acceptable
        - Users who have been scheduled for a certain time by a group administrator will receive a notification detailing the date and time of the scrimmage
    - If schedule is denied, then the schedule is reworked and is sent out again
        - Users have the choice to RSVP for their match. If not enough users rsvp for the match (under 12) 24 hours before the match, the scheduler is prompted to cancel
    - Once matches begin, it waits for the input of Win/Loss statistics to attach to each User Profile
        - This is manual input, a simple W or L for either team
        - This also take into account what map was played
        - Should allow matchmakers to edit results after they've accepted the match setup

## Version 2

* **Scheduler**
    - Add a function to add Universities/Groups
        - TBD how to implement this functionality
    
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
