drop table if exists Items;
drop table if exists Users;
drop table if exists Categories;
drop table if exists Bids;
create table Users(
	userID varchar(255) NOT NULL,
	rating int NOT NULL,
	location varchar(255),
	country varchar(255),
	primary key(userID));
create table Items(
	itemID int NOT NULL,
	name varchar(255) NOT NULL,
	currently float NOT NULL,
	first_bid float NOT NULL,
	number_of_bids int NOT NULL,
	buy_price float,
	started time NOT NULL,
	ends time NOT NULL,
	userID varchar(255) NOT NULL,
	description varchar(255),
	primary key(itemID),
	foreign key(userID) references Users(userID));
create table Bids(
	itemID int NOT NULL,
	userID varchar(255) NOT NULL,
	time time NOT NULL,
	amount float NOT NULL,
	foreign key(itemID) references Items(itemID),
	foreign key(userID) references Users(userID));
create table Categories(
	itemID int NOT NULL,
	category varchar(255) NOT NULL,
	foreign key(itemID) references Bids(itemID));
