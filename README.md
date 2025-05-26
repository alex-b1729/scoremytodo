# ScoreMyTodo

A daily todo list that tracks how much you've accomplished each day. 

## Features
* Each day starts a new Todo list.
* Add tasks to a list until midnight. 
* Check-off tasks util noon the next day.
* Each receives a score from 0-100 for the percentage of tasks completed.
* Track your accomplishments on your Dashboard. 
* Set your preferred timezone or set individual for a particular Todo lists. 

## Stack
* Django
* HTMX
* JavaScript
* Bootstrap

## Todo
### High priority
* Add Dashboard
* Allow users to add tasks until DailyList.day_end_dt and allow checking off tasks util DailyList.locked_dt
* Reorder tasks w/i list

### Medium priority
* Allow user to edit DailyList.notes
* Formalize / update color scheme
* Unify / fix frontend look
  * Index
  * Login / register
* Support for shareable/public lists
  * Chron job that deletes old unauthenticated user lists
  * Add shareable list toggle
  * Add link to share a shareable list

### Low priority 
* Favicon
* Support for users to export their data
* Add task priority
