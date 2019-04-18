# Documentaion for deploying on Google Cloud Compute Engine

---

### Setting up Google Cloud Compute Engine
** - Create a compute engine vm instance with the following specs **
	
	Ubuntu 16.04+ x64
	CPU: 16+ cores
	Memory: 16+ GBs
	Hard disk capacity: 10 GBs
	Allow Http & Https connections

** - In order to have a test on development server, we need to add a firewall rule **
	
	Explore to "VPC network --> Firewall rules" in google cloud console & click "CREATE FIREWALL RULE" to create a rule.
	Specify name of the rule.
	Select "All instances in the network" from Targets drop-down list.
	Set "Source IP Ranges" field value as "0.0.0.0/0".
	Set "Specified protocols and ports" field value as "tcp:8000".

---

### Install development environment
** - Run following commands in sequence **

	sudo apt-get update
	sudo apt install python3
	sudo apt install python3-django
	sudo apt install python3-opencv
	sudo apt install python3-pip
	sudo pip3 install opencv-python

** - Clone the bitbucket repository and explore to it and create 2 directories in "static" folder **
	
	sudo mkdir ./static/result
	sudo mkdir ./static/upload

** - Download neural network pre-trained models **

Run following commands on the repository folder.

	cd ./static/models
	sh getModels.sh

Once you download all the models, you will be able to run the development server by running command: 

"python3 manage.py runserver 0:8000".

Open Mozila Firefox browser and confirm application running by visiting http://xxx.xxx.xxx.xxx:8000 (Hereby, host ip-address is the external ip-address of the VM instance).

---

### How to deploy web application to ssl server using nginx & gunicorn
** - Install required packages **

	sudo apt install nginx
	sudo pip3 install gunicorn
	
** - Setup gunicorn configuration as following **
	
Create a conf file with the following command.
	
	sudo vi /etc/systemd/system/site.service
	
Copy the following content and paste to the above file. Hereby, you should specify path to the project source folder to "WorkingDirectory" field.
	
	[Unit]
	Description=Slouch Detection Website
	After=network.target
	
	[Service]
	User=sergioalbertocorreia
	Group=www-data
	WorkingDirectory=/home/sergioalbertocorreia/slouch_mvp-webapp 
	ExecStart=/usr/local/bin/gunicorn --workers 4 --bind unix:/var/tmp/site.sock -m 007 slouchdetection.wsgi:application
	
	[Install]
	WantedBy=multi-user.target
	

Enable website by running following commands.

	sudo systemctl start site
	sudo systemctl enable site
	//sudo systemctl daemon-reload
	
** - Setup SSL/TLS configuration **

Create self-signed certificate as following.

	sudo mkdir /etc/nginx/ssl
	sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/nginx/ssl/nginx.key -out /etc/nginx/ssl/nginx.crt
	
Replace the content of "/etc/nginx/sites-available/default" file

	server {
        listen 443 ssl default_server;
		listen 80 default_server;
        server_name slouchdetection.posturepanda.com;

        ssl_certificate /etc/nginx/ssl/nginx.crt;
        ssl_certificate_key /etc/nginx/ssl/nginx.key;

        location / {	               
        	include proxy_params;
	        proxy_pass http://unix:/var/tmp/site.sock;
        }
	}
	
Finally, restart nginx and give a full permission to the 2 folders("result", "upload") with the following commands.
	
	sudo service nginx restart
	sudo chmod 777 ./static/result
	sudo chmod 777 ./static/upload

After all, you'll be able to see the web application deployed successfully!!!