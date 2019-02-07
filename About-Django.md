# About Django

## File System
```
-OWScheduler/  
|  
|---- OWScheduler/
|	      |  
|	      |---- settings.py  
|	      |---- urls.py  
|---- scheduler/  
|	      |---- admin.py  
|	      |---- models.py  
|	      |---- views.py  
|	      |---- urls.py  
|	      |---- templates/  
|	      |	      |---- any .html files  
|	      |---- static/  
|	      |	      |---- any .js files  
|	      |	      |---- any .css files  
```

### OWScheduler Folder

#### settings.py

This is where we include our installed apps (right now, we just need to include 'scheduler.apps.SchdulerConfig') and any extras (for example, jquery).

#### urls.py

This is where we include the urls for our main website. We include any extensions for our urls. So '' is just \<www.example.com\>, or the home page. We might want to include 'user/\<int:user\_id\>' for the user pages, and so on. 'admin/' is for us to control the website itself.

### scheduler Folder

#### admin.py

This is where we can include controls for us. For example, we can include the ability to add or remove users. 

#### models.py

Our models go here. An example would include the "player" model, where we specify the fields for the model. Here we can specify that a player has an email, which is a CharField(), and maybe an age, which would be an IntField(). There's also a function parameter for passwords. An "id" will be created by django, so we can reference specific users. It's an auto-incrementing integer (first user id=1, second id=2, etc.).

#### urls.py

Here are urls specific to the "scheduler" app. This can include a simple www.example.com/user/ url, or extend to be www.example.com/scheduler/user/1. 

##### Our URL's
- /home -> the home page!
- /players -> list of all the players
- /teams -> list of all the teams
- /team/{teamID} -> a specific's team page
- /player/{battlenetID} -> a specific player's profile
- /player/{battlenetID}/account -> a player's account management
- /admin -> the admin page!


#### Templates

Django has its own language for templates, but it's built into html. So our home.html, user\_page.html, and other like files would be here. This is just for setting up the content of our webpages. 

#### Static

Static files are any extra files we want to include. For example, we might want to include a css file to choose a cool font or make cool borders. Or maybe we want to include a jquery file that changes what the login button looks like when the user finishes entering in both their username and password. The sky's the limit.
