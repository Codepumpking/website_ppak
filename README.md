Simple dashboard website using python

To start the webstie:

Open WSL terminal

Create mysql database
```
docker run --name my-mysql -e MYSQL_ROOT_PASSWORD={your_password} -d -p 3306:3306 mysql:latest
```

Run run mysql
```
docker exec -it my-mysql mysql -u root -p
```

Run SQL query to create DB needed for website
```
CREATE DATABASE board_db;
USE board_db;

CREATE TABLE posts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    content TEXT NOT NULL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Run Server
```
pip install flask pymysql
python app.py
```

