# Discord Bot
This is the bot, I have created for client, who has a GTA 5 script shop on Disocord. Bot will provide customers with functionalities of their convinient purchases.
*The code of the bot was reviewed and approved by senior developer*.

## Functionalities:
- Ticket system. In order to ask a question you can create a new ticket, which will see only staff;
- Orders system. Ticket can be converted to the order by staff with adding 0 to N developers for one order. Developer can set progress of work, customer can reject the order and ask for changes. Manager can remove ticket at any time. Customer is asker to send feedback and rate after order applying;
- Payment system. Manager can set payment of the order and aprove payment, if client has payed at any time.
- System of anonymous communication. In order to prevent headhunting developers by clients avoiding market, there is the system, with which client, manager and developer can communicate with each other, however don't see an account of each other.
- Survey system;
- New members tracking system;
- Sales funnel. For the marketing system, there is sales funnel in google docs, in which bot imports data of orders;
- Statistics;

## Technologies:
- Backend: Python 3.11
- Python frameworks:
  - Discord.py 2.2.3 (Connection to discord API)
  - Pycord v2.4 (Stable, functional API for discord)
  - Gspread 5.7.1 (API for google docs)
- Database: MySQL

## Database:
- [Logical model](https://prnt.sc/FFo7Eyng9d08)
- [Physical model](https://prnt.sc/qD8YsOxljK1z)

### [Schematic User Flow](https://drive.google.com/file/d/1bgakxRN3J8YYytL3u-Ugx7sjT3rRknbi/view?usp=sharing)

## Installing
1. Install [Docker](https://docs.docker.com/engine/install/ubuntu/)
2. Create Docker network for bot
```shell
docker network create bot-network
```
3. Run MySQL image
```shell
docker pull mysql/mysql-server
docker run --restart=always --network bot-network --mount type=bind,src=/root/mysql/my.cnf,dst=/etc/my.cnf --mount type=bind,src=/root/mysql/data,dst=/var/lib/mysql --network-alias mysql --name mysql_instance -e MYSQL_ROOT_PASSWORD=passw -p 3360:3306 -d mysql/mysql-server
```
4. Create user
```shell
docker exec -it mysql_instance mysql -uroot -ppassw
```
```shell
  CREATE USER 'bot'@'localhost' IDENTIFIED BY '6PYatF21';
GRANT ALL PRIVILEGES ON *.* TO 'bot'@'localhost' WITH GRANT OPTION;
CREATE USER 'bot'@'%' IDENTIFIED BY '6PYatF21';
GRANT ALL PRIVILEGES ON *.* TO 'bot'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;
exit
```
5. Create DB
```shell
docker exec -it mysql_instance mysql -uroot -ppassw
```
```shell
CREATE DATABASE botdb;
exit
```
6. Check connection
```shell
mysql --host=127.0.0.1 --port=3360 --user=bot --protocol=TCP --password=6PYatF21 botdb
```
mysql --host=127.0.0.1 --user=root bot
5. Import DB
```shell
docker exec -i mysql_instance mysql botdb -uroot -ppassw  < /root/bot-1/crebas.sql
```
5. Build bot image
```shell
docker build --tag discord-bot .
```
6. Run bot image
```shell
docker run --restart=always --network bot-network --name discord-bot -d discord-bot
```