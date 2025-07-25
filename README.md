# ScoreMyTodo

Daily todo lists that track the percentage of tasks you complete.

## How it works
* Each day starts a new todo list.
* Create & update todo list tasks until midnight. 
* Check-off tasks until noon the next day. 
* Each day's todo list receives a score from 0-100 for the percentage of tasks you check off. 
* Track your accomplishments on your Dashboard. 
* Set your preferred timezone or set the timezone of individual todo lists. 

## Stack
* [Django](https://www.djangoproject.com/) (5.2.1)
* [HTMX](https://htmx.org/)
* JavaScript
* [Bootstrap](https://getbootstrap.com/)
* [Cal-Heatmap](https://cal-heatmap.com/)

## Todo

### High priority
* Reorder tasks w/i list

### Medium priority
* Formalize & update color scheme
* Unify / fix frontend look
  * Index
  * Login / register

### Low priority 
* Favicon
* Support for users to export their data
* Add task priority
* Add task categories / headings
* Support for shareable/public lists
  * Chron job that deletes old unauthenticated user lists
  * Add shareable list toggle
  * Add link to share a shareable list
