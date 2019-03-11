OWScheduler Database Specs
=========================

## Players
- Each player is identified by their (unique) email
- Each player has:
	- Name
	- Alias
	- Password
	- Roles
	- Battlenet ID
	- University
- Each player can have multiple roles/skills. For example, they can be a "Tank" and "Healer"

## Teams
- Each team is made up of *6* players
- There can be an unlimited amount of teams
- Each team should be identified by an ID so that they can be reused
- Each team should be able to set an "alias" so they can be referenced by a name like "Blue Team"


## Matches
- Each match has 2 teams
- Each match occurs on a specific map
- A match ID should be set in order to reference result of a match
- There is one team on capture and one on defense
- There is a clear winner/loser

## Time Slot
- The week should be split into many time slots
- Each time slot specifies a day and an hour
- The key of the time slot is both the day and hour
- Each entry includes which players are available during the given time slot

## Attribute Variable Types
### Player
- Email -> VARCHAR(320)
- Name -> VARCHAR(100)
- Password -> passwordfield(?) max characters = 64
- Skill/Role -> VARCHAR(7) {damage, tank, support}
- BattlenetID -> VARCHAR(20)
- University -> VARCHAR(64)
- SkillRating -> INT

### Team
- TeamID -> INT
- SR_avg -> INT
- Team_Alias -> VARCHAR(32)

### Matches
- MatchID -> INT
- Map -> VARCHAR(32)

### Time_Slot
- DayOfWeek -> VARCHAR(8) {monday, tuesday, wednesday, thursday, friday, saturday, sunday}
- Hour -> INT
